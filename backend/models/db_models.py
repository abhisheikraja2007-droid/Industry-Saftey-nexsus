"""
SQLAlchemy ORM models for all Industrial Safety AI tables.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class SensorReading(Base):
    __tablename__ = "sensors"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sensor_id   = Column(String(64), nullable=False, index=True)
    sensor_type = Column(String(32), nullable=False)
    location    = Column(String(128), nullable=False)
    zone        = Column(String(64), nullable=False, index=True)
    value       = Column(Float, nullable=False)
    unit        = Column(String(16), nullable=False)
    raw_payload = Column(JSONB)
    timestamp   = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class EquipmentStatus(Base):
    __tablename__ = "equipment_status"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id   = Column(String(64), nullable=False, index=True)
    name           = Column(String(128), nullable=False)
    equipment_type = Column(String(64), nullable=False)
    zone           = Column(String(64), nullable=False)
    status         = Column(String(32), nullable=False)
    temperature    = Column(Float)
    vibration      = Column(Float)
    rpm            = Column(Float)
    extra          = Column(JSONB)
    timestamp      = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class WorkPermit(Base):
    __tablename__ = "work_permits"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permit_id    = Column(String(64), unique=True, nullable=False)
    permit_type  = Column(String(64), nullable=False)
    location     = Column(String(128), nullable=False)
    zone         = Column(String(64), nullable=False, index=True)
    status       = Column(String(32), nullable=False, default="active")
    issued_by    = Column(String(128), nullable=False)
    worker_names = Column(ARRAY(Text))
    issued_at    = Column(DateTime(timezone=True), server_default=func.now())
    expires_at   = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True))
    notes        = Column(Text)


class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_code      = Column(String(64), nullable=False)
    severity        = Column(String(16), nullable=False)
    risk_score      = Column(Integer, nullable=False)
    message         = Column(Text, nullable=False)
    zone            = Column(String(64))
    source_events   = Column(JSONB, nullable=False, default=list)
    acknowledged    = Column(Boolean, nullable=False, default=False)
    acknowledged_by = Column(String(128))
    acknowledged_at = Column(DateTime(timezone=True))
    resolved        = Column(Boolean, nullable=False, default=False)
    resolved_at     = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title               = Column(String(256), nullable=False)
    summary             = Column(Text, nullable=False)
    ai_explanation      = Column(Text)
    risk_score          = Column(Integer, nullable=False)
    severity            = Column(String(16), nullable=False)
    zone                = Column(String(64))
    events_involved     = Column(JSONB, nullable=False, default=list)
    recommended_actions = Column(ARRAY(Text))
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ShiftLog(Base):
    __tablename__ = "shift_logs"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shift_type   = Column(String(16), nullable=False)
    supervisor   = Column(String(128), nullable=False)
    worker_count = Column(Integer, nullable=False)
    zones_active = Column(ARRAY(Text))
    start_time   = Column(DateTime(timezone=True), nullable=False)
    end_time     = Column(DateTime(timezone=True))
    notes        = Column(Text)


class PPEDetection(Base):
    __tablename__ = "ppe_detections"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id        = Column(String(64), nullable=False, index=True)
    location         = Column(String(128), nullable=False)
    zone             = Column(String(64), nullable=False)
    ppe_status       = Column(String(32), nullable=False)
    workers_detected = Column(Integer, nullable=False, default=0)
    violations       = Column(JSONB, nullable=False, default=list)
    confidence       = Column(Float, nullable=False)
    image_path       = Column(String(512))
    raw_detections   = Column(JSONB)
    timestamp        = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class SystemStateSnapshot(Base):
    __tablename__ = "system_state_snapshots"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_score      = Column(Integer, nullable=False)
    risk_level      = Column(String(16), nullable=False)
    triggered_rules = Column(JSONB, nullable=False, default=list)
    anomaly_flags   = Column(JSONB, nullable=False, default=list)
    zone_scores     = Column(JSONB, nullable=False, default=dict)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
