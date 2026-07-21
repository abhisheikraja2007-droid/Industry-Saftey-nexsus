"""
FastAPI main application entry point.
"""
from __future__ import annotations
import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

logging.basicConfig(
    level   = getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Prometheus Metrics ───────────────────────────────────────
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"]
)
RISK_SCORE_GAUGE = Gauge("current_risk_score", "Current system risk score")
WS_CLIENTS_GAUGE = Gauge("ws_active_clients", "Active WebSocket clients")
ALERT_COUNTER = Counter("alerts_total", "Total alerts generated", ["severity"])

# ─── Rate Limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


# ─── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Industrial Safety AI — starting up …")

    # Initialize DB (create tables if not exists)
    try:
        from database import init_db
        await init_db()
        logger.info("✅ Database schema initialized.")
    except Exception as e:
        logger.warning(f"Database schema initialization failed: {e}")

    # Seed default users
    try:
        from models.user import User
        from utils.auth import hash_password
        from sqlalchemy import select
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(User).limit(1))
            if not res.first():
                logger.info("Seeding default users: admin, supervisor, operator...")
                admin_user = User(
                    username="admin",
                    hashed_password=hash_password("adminpass"),
                    role="admin"
                )
                supervisor_user = User(
                    username="supervisor",
                    hashed_password=hash_password("superpass"),
                    role="supervisor"
                )
                operator_user = User(
                    username="operator",
                    hashed_password=hash_password("operpass"),
                    role="operator"
                )
                session.add_all([admin_user, supervisor_user, operator_user])
                await session.commit()
                logger.info("✅ Default users seeded.")
    except Exception as e:
        logger.warning(f"Failed to seed users: {e}")

    # 1. Wire up dependencies
    from websocket.ws_manager import ws_manager
    from services.correlation_engine import correlation_engine
    correlation_engine.set_dependencies(None, ws_manager)

    # Load alerts, reports, and permits from DB
    try:
        from api.alerts import load_alerts_from_db
        from api.reports import load_reports_from_db
        from api.permits import load_permits_from_db
        await load_alerts_from_db()
        await load_reports_from_db()
        await load_permits_from_db()
        logger.info("✅ Alerts, reports, and permits loaded from DB.")
    except Exception as e:
        logger.warning(f"Failed to load initial data from DB: {e}")

    # 2. Train / load anomaly model & seed database history if empty
    try:
        from ai_models.anomaly_detector import anomaly_detector
        from database import AsyncSessionLocal
        from models.db_models import SensorReading
        from sqlalchemy import select, func

        model_loaded = anomaly_detector.load()

        # Only generate history data if model not loaded OR DB is empty
        async with AsyncSessionLocal() as session:
            cnt = await session.execute(select(func.count(SensorReading.id)))
            db_empty = cnt.scalar() == 0

        if not model_loaded or db_empty:
            logger.info("Generating synthetic history (72h) — this may take up to 30s …")
            try:
                from data.synthetic.generator import generate_sensor_history
                loop = asyncio.get_event_loop()
                df = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: generate_sensor_history(hours=72)),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("History generation timed out — skipping seeding, using saved model if available.")
                df = None

            if df is not None and not model_loaded:
                anomaly_detector.train(df)

            if df is not None and db_empty:
                logger.info("Seeding historical sensors table with 72h data...")
                db_readings = []
                for _, row in df.iterrows():
                    db_readings.append(SensorReading(
                        sensor_id=f"SENS-{row['zone']}-{row['sensor_type'].upper()}",
                        sensor_type=row['sensor_type'],
                        location=row['zone'],
                        zone=row['zone'],
                        value=float(row['value']),
                        unit=row['unit'],
                        timestamp=row['timestamp'],
                        raw_payload={}
                    ))
                async with AsyncSessionLocal() as session:
                    session.add_all(db_readings)
                    await session.commit()
                logger.info(f"Seeding completed. Inserted {len(db_readings)} rows.")
        else:
            logger.info("✅ Anomaly model loaded from disk, DB already has history — skipping seeding.")
    except Exception as e:
        logger.warning(f"Anomaly model / history DB seeding failed (non-fatal): {e}")


    # 3. Seed initial state from synthetic data
    try:
        from data.synthetic.generator import (
            generate_current_sensor_reading, generate_shift_log,
            ZONES, EQUIPMENT_CATALOG
        )
        from rule_engine.state_aggregator import (
            update_sensor, update_equipment, update_shift
        )
        # Seed sensors
        for zone in ZONES:
            reading = generate_current_sensor_reading(zone)
            for key, val in reading.items():
                if key != "zone":
                    update_sensor(zone, key.replace("gas_", "gas_"), val)
        # Seed equipment
        for eq in EQUIPMENT_CATALOG:
            update_equipment(eq["id"], {**eq, "status": "online", "temperature": 65.0, "vibration": 0.8})
        # Seed shift
        update_shift(generate_shift_log())
        logger.info("✅ Initial synthetic state seeded.")
    except Exception as e:
        logger.warning(f"State seeding failed (non-fatal): {e}")

    # 4. Start MQTT listener
    try:
        from services.mqtt_listener import mqtt_listener
        mqtt_listener.set_engine(correlation_engine)
        mqtt_listener.set_loop(asyncio.get_event_loop())
        mqtt_listener.start()
        logger.info("✅ MQTT listener started.")
    except Exception as e:
        logger.warning(f"MQTT listener failed (non-fatal): {e}")

    logger.info("✅ All systems ready. Dashboard at http://localhost:3000")
    yield

    # ─── Shutdown ────────────────────────────────────────────
    logger.info("Shutting down …")
    try:
        from services.mqtt_listener import mqtt_listener
        mqtt_listener.stop()
    except Exception:
        pass


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title       = "Industrial Safety Intelligence API",
    description = "Real-time compound hazard detection system",
    version     = "1.0.0",
    docs_url    = "/docs",
    lifespan    = lifespan,
)

# Set allowed origins explicitly when credentials are enabled
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://localhost:3443",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins     = allowed_origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# Register SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ─── Routers ─────────────────────────────────────────────────
from api.sensors   import router as sensors_router
from api.equipment import router as equipment_router
from api.permits   import router as permits_router
from api.alerts    import router as alerts_router
from api.risk      import router as risk_router
from api.reports   import router as reports_router
from api.shifts    import router as shifts_router
from api.auth      import router as auth_router
from websocket.ws_handler import router as ws_router

app.include_router(sensors_router)
app.include_router(equipment_router)
app.include_router(permits_router)
app.include_router(alerts_router)
app.include_router(risk_router)
app.include_router(reports_router)
app.include_router(shifts_router)
app.include_router(auth_router)
app.include_router(ws_router)

@app.get("/health", tags=["probes"])
async def health():
    from services.correlation_engine import correlation_engine
    from websocket.ws_manager import ws_manager
    score = correlation_engine.current_risk_score
    clients = ws_manager.connection_count
    RISK_SCORE_GAUGE.set(score)
    WS_CLIENTS_GAUGE.set(clients)
    return {"status": "ok", "risk_score": score, "ws_clients": clients}


@app.get("/ready", tags=["probes"])
async def ready():
    """Deep readiness probe — checks DB, Redis, and MQTT connectivity."""
    checks = {}
    ok = True

    # Check PostgreSQL
    try:
        from database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"fail: {e}"
        ok = False

    # Check Redis
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"fail: {e}"
        ok = False

    # Check MQTT broker
    try:
        import socket
        s = socket.create_connection((os.getenv("MQTT_BROKER", "mosquitto"), int(os.getenv("MQTT_PORT", "1883"))), timeout=2)
        s.close()
        checks["mqtt"] = "ok"
    except Exception as e:
        checks["mqtt"] = f"fail: {e}"
        ok = False

    status_code = 200 if ok else 503
    return JSONResponse(content={"ready": ok, "checks": checks}, status_code=status_code)


@app.get("/live", tags=["probes"])
async def live():
    """Liveness probe — checks process health and disk space."""
    import shutil
    disk = shutil.disk_usage("/")
    disk_free_pct = disk.free / disk.total * 100
    healthy = disk_free_pct > 5  # fail if <5% disk remaining
    return JSONResponse(
        content={"alive": healthy, "disk_free_pct": round(disk_free_pct, 1)},
        status_code=200 if healthy else 503
    )


@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    from services.correlation_engine import correlation_engine
    from websocket.ws_manager import ws_manager
    RISK_SCORE_GAUGE.set(correlation_engine.current_risk_score)
    WS_CLIENTS_GAUGE.set(ws_manager.connection_count)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
