from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from .database import Base

class Sensor(Base):
    __tablename__ = "sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_type = Column(String, index=True)
    location = Column(String, index=True)
    value = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class EquipmentStatus(Base):
    __tablename__ = "equipment_status"
    
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, index=True)
    status = Column(String)
    temperature = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class WorkPermit(Base):
    __tablename__ = "work_permits"
    
    permit_id = Column(String, primary_key=True, index=True)
    permit_type = Column(String)
    location = Column(String, index=True)
    status = Column(String)
    issued_at = Column(DateTime(timezone=True))

class Alert(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(Integer, primary_key=True, index=True)
    risk_score = Column(Float)
    severity = Column(String)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class IncidentReport(Base):
    __tablename__ = "incident_reports"
    
    report_id = Column(Integer, primary_key=True, index=True)
    summary = Column(Text)
    ai_explanation = Column(Text)
    risk_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
