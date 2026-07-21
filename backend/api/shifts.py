"""Shifts API routes"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from rule_engine.state_aggregator import update_shift, _latest

router = APIRouter(prefix="/api", tags=["shifts"])

_shifts: List[dict] = []


class ShiftIn(BaseModel):
    shift_type:   str
    supervisor:   str
    worker_count: int
    zones_active: List[str] = []
    start_time:   str
    notes:        Optional[str] = None


from database import save_shift_log_db

@router.post("/shifts")
async def log_shift(data: ShiftIn):
    shift = {**data.dict(), "id": str(len(_shifts) + 1)}
    _shifts.insert(0, shift)
    update_shift(shift)
    try:
        await save_shift_log_db(shift)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to persist shift to DB: {e}")
    return shift


@router.get("/shifts")
async def get_shifts():
    current = _latest.get("shift")
    return {
        "current_shift": current,
        "recent_shifts":  _shifts[:10],
    }
