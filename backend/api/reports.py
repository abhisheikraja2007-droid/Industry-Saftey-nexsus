"""Incident Reports API"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["reports"])

# In-memory report store
_reports: List[dict] = []


async def add_report(report: dict) -> dict:
    from database import save_report_db
    from datetime import datetime, timezone
    report.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    db_id = await save_report_db(report)
    report["id"] = db_id
    _reports.insert(0, report)
    # Keep last 100
    if len(_reports) > 100:
        _reports.pop()
    return report


async def load_reports_from_db():
    global _reports
    from database import load_all_reports_db
    try:
        loaded = await load_all_reports_db()
        _reports.clear()
        _reports.extend(loaded)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load reports from DB: {e}")


@router.get("/incident-reports")
async def list_reports(limit: int = 20):
    return {"reports": _reports[:limit], "total": len(_reports)}


@router.get("/incident-report/{report_id}")
async def get_report(report_id: str):
    for r in _reports:
        if str(r.get("id")) == report_id:
            return r
    return {"error": "not_found"}


class ReportRequest(BaseModel):
    zone:       str = "Zone-D"
    risk_score: int = 85


@router.post("/incident-report/generate")
async def generate_report(req: ReportRequest, background_tasks: BackgroundTasks):
    """Manually trigger AI incident report generation."""
    from services.correlation_engine import get_correlation_engine
    from rule_engine.state_aggregator import build_state
    from rule_engine.rules import get_triggered_rules
    from ai_models.risk_scorer import score_to_level

    state    = build_state(req.zone)
    triggered = get_triggered_rules(state)
    level, _ = score_to_level(req.risk_score)

    async def _generate():
        engine = get_correlation_engine()
        await engine._generate_incident_report(req.zone, req.risk_score, level, triggered)

    background_tasks.add_task(_generate)
    return {"status": "generating", "zone": req.zone}
