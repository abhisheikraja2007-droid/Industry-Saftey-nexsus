"""
Async SQLAlchemy database engine and session factory.
"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://safety_user:safety_pass@localhost:5432/safety_db"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency for DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables (used only in dev; prod uses init.sql)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


from datetime import datetime, timezone

def parse_iso_datetime(dt_str):
    if not dt_str:
        return None
    if isinstance(dt_str, datetime):
        return dt_str
    try:
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


async def save_alert_db(a: dict) -> str:
    """Save an alert dict to DB and return the string ID."""
    from models.db_models import Alert
    import json
    
    # Ensure source_events is a list
    source_events = a.get("source_events", [])
    if isinstance(source_events, str):
        try:
            source_events = json.loads(source_events)
        except Exception:
            source_events = []
            
    # Parse times
    acknowledged_at = parse_iso_datetime(a.get("acknowledged_at"))
    resolved_at = parse_iso_datetime(a.get("resolved_at"))
    created_at = parse_iso_datetime(a.get("created_at")) or datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        db_alert = Alert(
            alert_code=a.get("alert_code"),
            severity=a.get("severity"),
            risk_score=int(a.get("risk_score", 0)),
            message=a.get("message"),
            zone=a.get("zone"),
            source_events=source_events,
            acknowledged=bool(a.get("acknowledged", False)),
            acknowledged_by=a.get("acknowledged_by"),
            acknowledged_at=acknowledged_at,
            resolved=bool(a.get("resolved", False)),
            resolved_at=resolved_at,
            created_at=created_at
        )
        session.add(db_alert)
        await session.commit()
        await session.refresh(db_alert)
        return str(db_alert.id)


async def update_alert_ack_db(alert_id: str, acknowledged_by: str, acknowledged_at: datetime) -> bool:
    from models.db_models import Alert
    from sqlalchemy import select
    import uuid
    
    try:
        uuid_id = uuid.UUID(alert_id)
    except ValueError:
        return False
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.id == uuid_id))
        db_alert = result.scalar_one_or_none()
        if db_alert:
            db_alert.acknowledged = True
            db_alert.acknowledged_by = acknowledged_by
            db_alert.acknowledged_at = acknowledged_at
            await session.commit()
            return True
        return False


async def update_alert_resolve_db(alert_id: str, resolved_at: datetime) -> bool:
    from models.db_models import Alert
    from sqlalchemy import select
    import uuid
    
    try:
        uuid_id = uuid.UUID(alert_id)
    except ValueError:
        return False
        
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Alert).where(Alert.id == uuid_id))
        db_alert = result.scalar_one_or_none()
        if db_alert:
            db_alert.resolved = True
            db_alert.resolved_at = resolved_at
            await session.commit()
            return True
        return False


async def save_report_db(r: dict) -> str:
    """Save an incident report dict to DB and return the string ID."""
    from models.db_models import IncidentReport
    import json
    
    events_involved = r.get("events_involved", [])
    if isinstance(events_involved, str):
        try:
            events_involved = json.loads(events_involved)
        except Exception:
            events_involved = []
            
    recommended_actions = r.get("recommended_actions", [])
    if not isinstance(recommended_actions, list):
        recommended_actions = [recommended_actions]
        
    created_at = parse_iso_datetime(r.get("created_at")) or datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        db_report = IncidentReport(
            title=r.get("title", "Safety Incident"),
            summary=r.get("summary", ""),
            ai_explanation=r.get("ai_explanation"),
            risk_score=int(r.get("risk_score", 0)),
            severity=r.get("severity", "HIGH"),
            zone=r.get("zone"),
            events_involved=events_involved,
            recommended_actions=recommended_actions,
            created_at=created_at
        )
        session.add(db_report)
        await session.commit()
        await session.refresh(db_report)
        return str(db_report.id)


async def save_sensor_reading_db(s: dict) -> None:
    """Save a sensor reading to the DB with range checking."""
    from models.db_models import SensorReading
    
    val = float(s.get("value", 0.0))
    sensor_type = s.get("sensor_type", "")
    
    # Reject negative gas concentrations or invalid values
    if (sensor_type.startswith("gas_") or sensor_type in ("ch4", "co", "h2s")) and val < 0.0:
        raise ValueError(f"Invalid gas concentration value: {val}")
    if sensor_type == "temp" and val < -273.15:
        raise ValueError(f"Invalid temperature: {val}")
        
    timestamp = parse_iso_datetime(s.get("timestamp")) or datetime.now(timezone.utc)
    
    async with AsyncSessionLocal() as session:
        db_reading = SensorReading(
            sensor_id=s.get("sensor_id", "unknown"),
            sensor_type=sensor_type,
            location=s.get("location", "unknown"),
            zone=s.get("zone", "unknown"),
            value=val,
            unit=s.get("unit", "ppm"),
            raw_payload=s,
            timestamp=timestamp
        )
        session.add(db_reading)
        await session.commit()


async def load_all_alerts_db() -> list:
    from models.db_models import Alert
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Alert).order_by(desc(Alert.created_at)).limit(100))
        db_alerts = result.scalars().all()
        alerts_list = []
        for a in db_alerts:
            alerts_list.append({
                "id": str(a.id),
                "alert_code": a.alert_code,
                "severity": a.severity,
                "risk_score": a.risk_score,
                "message": a.message,
                "zone": a.zone,
                "source_events": a.source_events,
                "acknowledged": a.acknowledged,
                "acknowledged_by": a.acknowledged_by,
                "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                "resolved": a.resolved,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            })
        return alerts_list


async def load_all_reports_db() -> list:
    from models.db_models import IncidentReport
    from sqlalchemy import select, desc
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(IncidentReport).order_by(desc(IncidentReport.created_at)).limit(100))
        db_reports = result.scalars().all()
        reports_list = []
        for r in db_reports:
            reports_list.append({
                "id": str(r.id),
                "title": r.title,
                "summary": r.summary,
                "ai_explanation": r.ai_explanation,
                "risk_score": r.risk_score,
                "severity": r.severity,
                "zone": r.zone,
                "events_involved": r.events_involved,
                "recommended_actions": r.recommended_actions,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        return reports_list


async def save_equipment_status_db(eq: dict) -> None:
    from models.db_models import EquipmentStatus
    async with AsyncSessionLocal() as session:
        db_eq = EquipmentStatus(
            equipment_id=eq.get("equipment_id") or eq.get("id"),
            name=eq.get("name"),
            equipment_type=eq.get("equipment_type") or eq.get("type"),
            zone=eq.get("zone"),
            status=eq.get("status"),
            temperature=eq.get("temperature"),
            vibration=eq.get("vibration"),
            rpm=eq.get("rpm"),
            extra=eq.get("extra", {})
        )
        session.add(db_eq)
        await session.commit()


async def save_work_permit_db(p: dict) -> None:
    from models.db_models import WorkPermit
    expires_at = parse_iso_datetime(p.get("expires_at")) or datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        db_permit = WorkPermit(
            permit_id=p.get("permit_id"),
            permit_type=p.get("permit_type"),
            location=p.get("location"),
            zone=p.get("zone"),
            status=p.get("status", "active"),
            issued_by=p.get("issued_by"),
            worker_names=p.get("worker_names", []),
            expires_at=expires_at,
            notes=p.get("notes")
        )
        session.add(db_permit)
        await session.commit()


async def update_work_permit_status_db(permit_id: str, status: str, cancelled_at=None) -> bool:
    from models.db_models import WorkPermit
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(WorkPermit).where(WorkPermit.permit_id == permit_id))
        db_permit = result.scalar_one_or_none()
        if db_permit:
            db_permit.status = status
            if cancelled_at:
                db_permit.cancelled_at = parse_iso_datetime(cancelled_at)
            await session.commit()
            return True
        return False


async def save_shift_log_db(s: dict) -> None:
    from models.db_models import ShiftLog
    start_time = parse_iso_datetime(s.get("start_time")) or datetime.now(timezone.utc)
    end_time = parse_iso_datetime(s.get("end_time"))
    async with AsyncSessionLocal() as session:
        db_shift = ShiftLog(
            shift_type=s.get("shift_type"),
            supervisor=s.get("supervisor"),
            worker_count=s.get("worker_count", 0),
            zones_active=s.get("zones_active", []),
            start_time=start_time,
            end_time=end_time,
            notes=s.get("notes")
        )
        session.add(db_shift)
        await session.commit()


async def save_ppe_detection_db(p: dict) -> None:
    from models.db_models import PPEDetection
    timestamp = parse_iso_datetime(p.get("timestamp")) or datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        db_ppe = PPEDetection(
            camera_id=p.get("camera_id", "unknown"),
            location=p.get("location", "unknown"),
            zone=p.get("zone", "unknown"),
            ppe_status=p.get("ppe_status"),
            workers_detected=p.get("workers_detected", 0),
            violations=p.get("violations", []),
            confidence=p.get("confidence", 1.0),
            image_path=p.get("image_path"),
            raw_detections=p.get("raw_detections", {}),
            timestamp=timestamp
        )
        session.add(db_ppe)
        await session.commit()


async def save_system_snapshot_db(snap: dict) -> None:
    from models.db_models import SystemStateSnapshot
    async with AsyncSessionLocal() as session:
        db_snap = SystemStateSnapshot(
            risk_score=snap.get("risk_score", 0),
            risk_level=snap.get("risk_level", "SAFE"),
            triggered_rules=snap.get("triggered_rules", []),
            anomaly_flags=snap.get("anomaly_flags", []),
            zone_scores=snap.get("zone_scores", {})
        )
        session.add(db_snap)
        await session.commit()


async def load_all_permits_db() -> list:
    from models.db_models import WorkPermit
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(WorkPermit).where(WorkPermit.status == "active"))
        db_permits = result.scalars().all()
        return [{
            "permit_id": p.permit_id,
            "permit_type": p.permit_type,
            "location": p.location,
            "zone": p.zone,
            "status": p.status,
            "issued_by": p.issued_by,
            "worker_names": p.worker_names,
            "expires_at": p.expires_at.isoformat() if p.expires_at else None,
            "issued_at": p.issued_at.isoformat() if p.issued_at else None,
            "notes": p.notes
        } for p in db_permits]


