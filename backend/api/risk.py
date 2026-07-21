"""Risk Score and Dashboard API"""
from datetime import datetime, timezone
from fastapi import APIRouter
from services.correlation_engine import get_correlation_engine
from rule_engine.state_aggregator import _latest

router = APIRouter(prefix="/api", tags=["risk"])


@router.get("/risk-score")
@router.get("/risk/score")
async def get_risk_score():
    engine    = get_correlation_engine()
    score     = engine.current_risk_score
    breakdown = engine.get_zone_breakdown()
    from ai_models.risk_scorer import score_to_level
    level, color = score_to_level(score)
    return {
        "risk_score":  score,
        "risk_level":  level,
        "color":       color,
        "zone_breakdown": breakdown,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }


@router.get("/dashboard")
async def get_dashboard():
    """Aggregated dashboard summary."""
    from api.alerts import _alerts
    from api.permits import _permits
    engine    = get_correlation_engine()
    score     = engine.current_risk_score
    breakdown = engine.get_zone_breakdown()
    from ai_models.risk_scorer import score_to_level
    level, color = score_to_level(score)

    active_alerts   = [a for a in _alerts if not a.get("resolved")]
    critical_alerts = [a for a in active_alerts if a.get("severity") == "CRITICAL"]
    active_permits  = [p for p in _permits if p.get("status") == "active"]
    equipment       = _latest.get("equipment", {})
    equip_faults    = sum(1 for e in equipment.values() if e.get("status") == "fault")

    return {
        "global_risk_score": score,
        "risk_level":        level,
        "color":             color,
        "active_alerts":     len(active_alerts),
        "critical_alerts":   len(critical_alerts),
        "equipment_faults":  equip_faults,
        "active_permits":    len(active_permits),
        "permits":           active_permits,
        "zone_risks":        breakdown,
        "current_shift":     _latest.get("shift"),
        "triggered_rules":   list(engine._active_rule_codes),
        "last_updated":      datetime.now(timezone.utc).isoformat(),
    }
