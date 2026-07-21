"""Work Permit API routes"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from services.correlation_engine import get_correlation_engine
from rule_engine.state_aggregator import _latest, update_permits
from database import save_work_permit_db, update_work_permit_status_db, load_all_permits_db

router = APIRouter(prefix="/api", tags=["permits"])

# In-memory permit store (DB-backed in production)
_permits: List[dict] = []


async def load_permits_from_db():
    global _permits
    try:
        loaded = await load_all_permits_db()
        _permits = loaded
        update_permits(_permits)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to load permits from DB: {e}")


class PermitIn(BaseModel):
    permit_type:  str
    location:     str
    zone:         str
    issued_by:    str
    worker_names: List[str] = []
    expires_at:   str
    notes:        Optional[str] = None


from utils.auth import require_role, get_current_user
from fastapi import Depends

@router.post("/permits")
async def create_permit(data: PermitIn, current_user: dict = Depends(require_role(["admin", "supervisor"]))):
    import uuid
    permit = {
        **data.dict(),
        "permit_id": f"WP-{uuid.uuid4().hex[:8].upper()}",
        "status":    "active",
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    _permits.append(permit)
    update_permits(_permits)
    try:
        await save_work_permit_db(permit)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to persist permit to DB: {e}")
    engine = get_correlation_engine()
    await engine.on_permit_update(_permits)
    return permit


@router.get("/permits")
async def list_permits():
    active = [p for p in _permits if p.get("status") == "active"]
    return {"permits": active, "total": len(active)}


@router.patch("/permits/{permit_id}")
async def update_permit(permit_id: str, status: str, current_user: dict = Depends(require_role(["admin", "supervisor"]))):
    cancelled_at = None
    for p in _permits:
        if p.get("permit_id") == permit_id:
            p["status"] = status
            if status == "cancelled":
                p["cancelled_at"] = datetime.now(timezone.utc).isoformat()
                cancelled_at = p["cancelled_at"]
            break
    try:
        await update_work_permit_status_db(permit_id, status, cancelled_at)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to update permit status in DB: {e}")
    update_permits(_permits)
    return {"status": "updated", "permit_id": permit_id}

