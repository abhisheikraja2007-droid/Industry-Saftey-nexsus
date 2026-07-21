"""
Scenario Runner — plays back the scripted 9-step demo sequence via
direct HTTP REST API calls to the FastAPI backend.
No MQTT broker required.

Usage:
    python simulator/scenario_runner.py --speed 2.0
"""
from __future__ import annotations
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import urllib.request
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.synthetic.generator import DEMO_STEPS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [SCENARIO] %(message)s")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")


# Global Token
JWT_TOKEN = None

def post(path: str, payload: dict) -> dict:
    """Simple HTTP POST using only stdlib (no requests dep needed)."""
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if JWT_TOKEN:
        headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        logger.warning(f"POST {path} → HTTP {e.code}: {body[:200]}")
        return {}
    except Exception as e:
        logger.warning(f"POST {path} failed: {e}")
        return {}


def get(path: str) -> dict:
    url = f"{API_BASE}{path}"
    headers = {}
    if JWT_TOKEN:
        headers["Authorization"] = f"Bearer {JWT_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"GET {path} failed: {e}")
        return {}


def ingest_sensor(zone: str, sensor_type: str, value: float, unit: str = "ppm"):
    return post("/api/sensor-data", {
        "sensor_id":   f"{sensor_type.upper()}-{zone}-DEMO",
        "sensor_type": sensor_type,
        "location":    f"{zone} Sensor Array",
        "zone":        zone,
        "value":       value,
        "unit":        unit,
    })


def ingest_equipment(equipment_id: str, name: str, zone: str, status: str,
                     temperature: float, vibration: float):
    return post("/api/equipment-status", {
        "equipment_id":   equipment_id,
        "name":           name,
        "equipment_type": "fan",
        "zone":           zone,
        "status":         status,
        "temperature":    temperature,
        "vibration":      vibration,
    })


def issue_permit(zone: str, permit_type: str):
    expires = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
    return post("/api/permits", {
        "permit_type":  permit_type,
        "location":     f"{zone} Sub-station 3",
        "zone":         zone,
        "issued_by":    "Ahmed Al-Rashid",
        "worker_names": ["Worker-442", "Worker-318"],
        "expires_at":   expires,
        "notes":        f"DEMO: {permit_type.replace('_', ' ')} in hazardous area",
    })


def log_shift(shift_type: str, supervisor: str, workers: int):
    return post("/api/shifts", {
        "shift_type":   shift_type,
        "supervisor":   supervisor,
        "worker_count": workers,
        "zones_active": ["Zone-D", "Zone-C"],
        "start_time":   datetime.now(timezone.utc).isoformat(),
        "notes":        "DEMO: Shift change during incident",
    })


def run_demo(speed: float = 1.0, step_delay: float = 8.0):
    global JWT_TOKEN
    logger.info(f"🎭 Checking backend connectivity at {API_BASE} …")
    health = get("/health")
    if not health:
        logger.error(f"❌ Cannot reach backend at {API_BASE}. Make sure uvicorn is running first.")
        sys.exit(1)
    logger.info(f"✅ Backend healthy: {health}")

    # Authenticate to get a token
    logger.info("🔑 Authenticating as admin...")
    login_resp = post("/api/auth/login", {"username": "admin", "password": "adminpass"})
    if login_resp and "access_token" in login_resp:
        JWT_TOKEN = login_resp["access_token"]
        logger.info("🔓 Authentication successful.")
    else:
        logger.warning("⚠️ Authentication failed. Continuing without token.")

    logger.info(f"📋 Starting 9-step demo scenario at {speed}x speed\n")

    active_permit_id = None

    for step_data in DEMO_STEPS:
        step  = step_data["step"]
        zone  = step_data["zone"]
        label = step_data["label"]
        desc  = step_data["description"]

        print(f"\n{'='*65}")
        print(f"  STEP {step}/{len(DEMO_STEPS)}: {label}")
        print(f"  {desc}")
        print(f"{'='*65}")

        # ── 1. Ingest gas sensor readings ───────────────────
        for gas, key in [("gas_ch4", "gas_ch4"), ("gas_co", "gas_co"), ("gas_h2s", "gas_h2s")]:
            result = ingest_sensor(zone, gas, step_data[key])
            logger.debug(f"  → sensor {gas}: {step_data[key]} ppm → {result}")
            time.sleep(0.2)

        # ── 2. Equipment status ─────────────────────────────
        eq_status = step_data.get("equipment_status", "online")
        temp      = 90.0 if eq_status == "fault" else 65.0
        vib       = 0.2  if eq_status == "fault" else 0.8
        ingest_equipment("FAN-01", "Exhaust Fan Zone-D", zone, eq_status, temp, vib)
        logger.info(f"  ⚙️  FAN-01 status: {eq_status.upper()} | temp={temp}°C")

        # ── 3. Permit (steps 3-7) ───────────────────────────
        if step == 3 and step_data.get("permit_type"):
            resp = issue_permit(zone, step_data["permit_type"])
            active_permit_id = resp.get("permit_id")
            logger.info(f"  📝 Work permit issued: {active_permit_id} ({step_data['permit_type']})")

        # Cancel permit in step 9 (remediation)
        if step == 9 and active_permit_id:
            cancel_url = f"/api/permits/{active_permit_id}"
            try:
                headers = {}
                if JWT_TOKEN:
                    headers["Authorization"] = f"Bearer {JWT_TOKEN}"
                req = urllib.request.Request(
                    f"{API_BASE}{cancel_url}?status=cancelled",
                    headers=headers,
                    method="PATCH"
                )
                urllib.request.urlopen(req, timeout=5)
                logger.info(f"  🔕 Permit {active_permit_id} cancelled.")
            except Exception as e:
                logger.debug(f"  Permit cancel: {e}")

        # ── 4. Shift change (step 5) ────────────────────────
        if step == 5:
            log_shift("night", "James O'Brien", 23)
            logger.info("  👥 Shift change logged: Night shift, James O'Brien (23 workers)")

        # ── 5. Read back current dashboard state ────────────
        dash = get("/api/dashboard")
        score     = dash.get("global_risk_score", "?")
        level     = dash.get("risk_level", "?")
        n_alerts  = dash.get("active_alerts", 0)
        triggered = dash.get("triggered_rules", [])
        print(f"\n  [Risk Score] Score: {score}/100  Level: {level}")
        print(f"  [Alerts] Active Alerts: {n_alerts}")
        if triggered:
            print(f"  [Rules] Triggered Rules: {', '.join(triggered)}")

        # ── 6. Generate incident report at CRITICAL step ────
        if step == 8:
            logger.info("  Triggering AI incident report generation ...")
            post("/api/incident-report/generate", {"zone": zone, "risk_score": int(score) if isinstance(score, (int, float)) else 85})
            time.sleep(1)

        delay = step_delay / speed
        print(f"\n  [Timer] Waiting {delay:.1f}s before next step ...")
        time.sleep(delay)

    print(f"\n{'='*65}")
    print("  [Success] Demo scenario complete!")
    print(f"{'='*65}")

    # Final dashboard state
    dash  = get("/api/dashboard")
    print(f"\n  Final Risk Score : {dash.get('global_risk_score')}/100  [{dash.get('risk_level')}]")
    print(f"  Active Alerts    : {dash.get('active_alerts')}")
    reports = get("/api/incident-reports")
    print(f"  Incident Reports : {reports.get('total', 0)}")
    print(f"\n  Open the dashboard at: http://127.0.0.1:3000\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Industrial Safety AI — Demo Scenario Runner (HTTP mode, no MQTT needed)"
    )
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Playback speed multiplier (default 1.0)")
    parser.add_argument("--delay", type=float, default=8.0,
                        help="Seconds between steps at 1x speed (default 8)")
    parser.add_argument("--api",   type=str,   default="http://127.0.0.1:8000",
                        help="Backend API base URL")
    args = parser.parse_args()

    API_BASE = args.api
    run_demo(speed=args.speed, step_delay=args.delay)
