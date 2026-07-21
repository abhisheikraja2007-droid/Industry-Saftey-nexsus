from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SensorBase(BaseModel):
    sensor_type: str
    location: str
    value: float

class SensorCreate(SensorBase):
    pass

class Sensor(SensorBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class AlertBase(BaseModel):
    risk_score: float
    severity: str
    message: str

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    alert_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class IncidentReportBase(BaseModel):
    summary: str
    ai_explanation: str
    risk_score: float

class IncidentReportCreate(IncidentReportBase):
    pass

class IncidentReport(IncidentReportBase):
    report_id: int
    created_at: datetime

    class Config:
        orm_mode = True
