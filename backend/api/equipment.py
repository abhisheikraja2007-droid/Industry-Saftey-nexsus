"""Equipment API routes"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.correlation_engine import get_correlation_engine
from rule_engine.state_aggregator import _latest

router = APIRouter(prefix="/api", tags=["equipment"])


class EquipmentIn(BaseModel):
    equipment_id:   str
    name:           str
    equipment_type: str
    zone:           str
    status:         str
    temperature:    Optional[float] = None
    vibration:      Optional[float] = None
    rpm:            Optional[float] = None


@router.post("/equipment-status")
async def ingest_equipment(data: EquipmentIn):
    engine = get_correlation_engine()
    await engine.on_equipment_update(data.dict())
    return {"status": "ok", "equipment_id": data.equipment_id}


@router.get("/equipment")
async def get_equipment():
    return {"equipment": _latest["equipment"]}
