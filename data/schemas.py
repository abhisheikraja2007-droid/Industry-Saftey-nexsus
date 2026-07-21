"""
Pydantic schemas — canonical data shapes for sensors, equipment,
permits, alerts, and reports. Source-agnostic (Kaggle or synthetic).
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
import uuid


# ─── SENSOR ─────────────────────────────────────────────────

class SensorReadingCreate(BaseModel):
    sensor_id:   str
    sensor_type: str   # gas_ch4 | gas_co | gas_h2s | temp | humidity | smoke
    location:    str
    zone:        str
    value:       float
    unit:        str
    raw_payload: Optional[Dict[str, Any]] = None


class SensorReadingOut(SensorReadingCreate):
    id:        str
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── EQUIPMENT ───────────────────────────────────────────────

class EquipmentStatusCreate(BaseModel):
    equipment_id:   str
    name:           str
    equipment_type: str
    zone:           str
    status:         str   # online | fault | offline | maintenance
    temperature:    Optional[float] = None
    vibration:      Optional[float] = None
    rpm:            Optional[float] = None
    extra:          Optional[Dict[str, Any]] = None


class EquipmentStatusOut(EquipmentStatusCreate):
    id:        str
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── WORK PERMIT ─────────────────────────────────────────────

class WorkPermitCreate(BaseModel):
    permit_id:    str = Field(default_factory=lambda: f"WP-{uuid.uuid4().hex[:8].upper()}")
    permit_type:  str   # hot_work | confined_space | electrical | excavation
    location:     str
    zone:         str
    issued_by:    str
    worker_names: List[str] = []
    expires_at:   datetime
    notes:        Optional[str] = None


class WorkPermitOut(WorkPermitCreate):
    id:        str
    status:    str
    issued_at: datetime

    class Config:
        from_attributes = True


# ─── ALERT ───────────────────────────────────────────────────

class AlertOut(BaseModel):
    id:              str
    alert_code:      str
    severity:        str
    risk_score:      int
    message:         str
    zone:            Optional[str]
    source_events:   List[Dict[str, Any]]
    acknowledged:    bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved:        bool
    created_at:      datetime

    class Config:
        from_attributes = True


# ─── INCIDENT REPORT ─────────────────────────────────────────

class IncidentReportOut(BaseModel):
    id:                  str
    title:               str
    summary:             str
    ai_explanation:      Optional[str]
    risk_score:          int
    severity:            str
    zone:                Optional[str]
    events_involved:     List[Dict[str, Any]]
    recommended_actions: Optional[List[str]]
    created_at:          datetime

    class Config:
        from_attributes = True


# ─── SHIFT ───────────────────────────────────────────────────

class ShiftLogCreate(BaseModel):
    shift_type:   str   # morning | afternoon | night
    supervisor:   str
    worker_count: int
    zones_active: List[str] = []
    start_time:   datetime
    notes:        Optional[str] = None


class ShiftLogOut(ShiftLogCreate):
    id:       str
    end_time: Optional[datetime]

    class Config:
        from_attributes = True


# ─── DASHBOARD ───────────────────────────────────────────────

class ZoneRisk(BaseModel):
    zone:       str
    risk_score: int
    risk_level: str


class DashboardSummary(BaseModel):
    global_risk_score:  int
    risk_level:         str
    active_alerts:      int
    critical_alerts:    int
    equipment_faults:   int
    active_permits:     int
    current_shift:      Optional[ShiftLogOut]
    zone_risks:         List[ZoneRisk]
    triggered_rules:    List[str]
    last_updated:       datetime


# ─── WEBSOCKET MESSAGE ────────────────────────────────────────

class WSMessage(BaseModel):
    type:    str   # sensor_update | alert | risk_score | report_ready | ppe_update
    payload: Dict[str, Any]
    ts:      datetime = Field(default_factory=datetime.utcnow)
