"""
FastAPI — Sensor routes
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, model_validator

from services.correlation_engine import get_correlation_engine
from rule_engine.state_aggregator import _latest

router = APIRouter(prefix="/api", tags=["sensors"])


class SensorIn(BaseModel):
    sensor_id:   str
    sensor_type: str
    location:    str
    zone:        str
    value:       float
    unit:        str = "ppm"

    @model_validator(mode="after")
    def validate_ranges(self) -> "SensorIn":
        # Reject empty or whitespace-only sensor_id
        if not self.sensor_id or not self.sensor_id.strip():
            raise ValueError("sensor_id cannot be empty or whitespace")

        # Reject HTML/script injection in sensor_id
        dangerous_chars = ["<", ">", "&", "\"", "'"]
        if any(c in self.sensor_id for c in dangerous_chars):
            raise ValueError(f"sensor_id contains invalid characters: {self.sensor_id}")

        # Reject SQL injection patterns in location/zone fields
        sql_patterns = ["'", "\"", ";", "--", "/*", "*/", "DROP", "SELECT", "INSERT", "DELETE", "UNION"]
        for field_name, field_val in [("location", self.location), ("zone", self.zone)]:
            for pattern in sql_patterns:
                if pattern.upper() in field_val.upper():
                    raise ValueError(f"{field_name} contains suspicious characters: {field_val}")

        # Validate gas concentrations cannot be negative
        if (self.sensor_type.startswith("gas_") or self.sensor_type in ("ch4", "co", "h2s")) and self.value < 0.0:
            raise ValueError(f"Gas concentration cannot be negative: {self.value}")

        # Temperature physical lower bound
        if self.sensor_type == "temp" and self.value < -273.15:
            raise ValueError(f"Temperature cannot be below absolute zero: {self.value}")

        return self


@router.post("/sensor-data")
async def ingest_sensor(data: SensorIn):
    engine = get_correlation_engine()
    await engine.on_sensor_reading(data.dict())
    return {"status": "ok", "zone": data.zone, "value": data.value}


@router.get("/sensors")
async def get_latest_sensors():
    """Return latest reading per zone per sensor type."""
    return {"sensors": _latest["sensors"], "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/sensors/heatmap")
async def get_heatmap():
    """Zone-level risk scores for the heatmap."""
    engine    = get_correlation_engine()
    breakdown = engine.get_zone_breakdown()
    return {"zones": breakdown, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/sensors/history")
async def get_sensor_history(
    zone:        Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    hours:       int = Query(24, ge=1, le=168),
):
    from sqlalchemy import select
    from database import AsyncSessionLocal
    from models.db_models import SensorReading
    from datetime import datetime, timedelta, timezone

    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    async with AsyncSessionLocal() as session:
        query = select(SensorReading).where(SensorReading.timestamp >= since)
        if zone:
            query = query.where(SensorReading.zone == zone)
        if sensor_type:
            query = query.where(SensorReading.sensor_type == sensor_type)
            
        query = query.order_by(SensorReading.timestamp.asc())
        
        result = await session.execute(query)
        readings = result.scalars().all()
        
        history = []
        for r in readings:
            history.append({
                "sensor_id": r.sensor_id,
                "sensor_type": r.sensor_type,
                "zone": r.zone,
                "value": r.value,
                "unit": r.unit,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            })
        return {"history": history, "total": len(history)}
