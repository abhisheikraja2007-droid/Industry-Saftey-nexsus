"""Alerts API routes"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["alerts"])

# In-memory alert store
_alerts: List[dict] = []


async def add_alert(alert: dict) -> dict:
    from database import save_alert_db
    db_id = await save_alert_db(alert)
    alert["id"] = db_id
    _alerts.insert(0, alert)  # newest first
    # Keep last 100
    if len(_alerts) > 100:
        _alerts.pop()
    return alert


async def load_alerts_from_db():
    global _alerts
    from database import load_all_alerts_db
    try:
        loaded = await load_all_alerts_db()
        _alerts.clear()
        _alerts.extend(loaded)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load alerts from DB: {e}")


@router.get("/alerts")
async def list_alerts(
    severity:     Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    limit:        int = Query(50, ge=1, le=200),
):
    results = _alerts
    if severity:
        results = [a for a in results if a.get("severity") == severity.upper()]
    if acknowledged is not None:
        results = [a for a in results if a.get("acknowledged") == acknowledged]
    return {"alerts": results[:limit], "total": len(results)}


from fastapi import APIRouter, Query, Depends
from utils.auth import get_current_user, require_role

@router.patch("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    from database import update_alert_ack_db
    from datetime import datetime, timezone
    ack_time = datetime.now(timezone.utc)
    acknowledged_by = current_user.get("username", "unknown")
    
    success = await update_alert_ack_db(alert_id, acknowledged_by, ack_time)
    
    for a in _alerts:
        if str(a.get("id")) == alert_id:
            a["acknowledged"]    = True
            a["acknowledged_by"] = acknowledged_by
            a["acknowledged_at"] = ack_time.isoformat()
            return {"status": "acknowledged", "alert_id": alert_id}
            
    if success:
        return {"status": "acknowledged", "alert_id": alert_id}
    return {"status": "not_found"}


@router.delete("/alerts/{alert_id}")
async def resolve_alert(alert_id: str, current_user: dict = Depends(require_role(["admin", "supervisor"]))):
    from database import update_alert_resolve_db
    from datetime import datetime, timezone
    res_time = datetime.now(timezone.utc)
    
    success = await update_alert_resolve_db(alert_id, res_time)
    
    for a in _alerts:
        if str(a.get("id")) == alert_id:
            a["resolved"]    = True
            a["resolved_at"] = res_time.isoformat()
            return {"status": "resolved"}
            
    if success:
        return {"status": "resolved"}
    return {"status": "not_found"}
