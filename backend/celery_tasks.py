"""
Celery tasks for async processing.
"""
from __future__ import annotations
import logging
from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="generate_report", bind=True, max_retries=2)
def generate_report_task(self, zone: str, risk_score: int, risk_level: str, rules: list):
    """Background task to generate LLM incident report."""
    try:
        import asyncio
        from ai_models.llm_engine import get_llm_engine
        from rule_engine.rules import RuleResult

        rule_results = [
            RuleResult(
                rule_code=r["rule_code"],
                triggered=True,
                severity=r["severity"],
                score_delta=r.get("score_delta", 0),
                message=r["message"],
            )
            for r in rules
        ]

        llm = get_llm_engine()
        loop = asyncio.new_event_loop()
        report = loop.run_until_complete(
            llm.generate_incident_report(
                zone=zone,
                risk_score=risk_score,
                risk_level=risk_level,
                triggered_rules=rule_results,
                sensor_data={},
                anomaly_flag=False,
                anomaly_score=0.0,
                permits=[],
                equipment={},
                timestamp="",
            )
        )
        loop.close()
        logger.info("Report generated for zone %s, score=%d", zone, risk_score)
        return report
    except Exception as exc:
        logger.error("Report task failed: %s", exc)
        raise self.retry(exc=exc, countdown=5)
