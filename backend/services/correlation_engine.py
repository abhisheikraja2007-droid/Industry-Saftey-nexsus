"""
Central Correlation Engine.
Receives events, updates state, runs rules + anomaly detection, scores risk,
creates alerts, and triggers LLM reporting.
"""
from __future__ import annotations
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rule_engine.rules import get_triggered_rules, RuleResult
from rule_engine.state_aggregator import (
    update_sensor, update_equipment, update_permits,
    update_shift, update_ppe, set_shift_change_flag,
    build_state, get_all_zones_states
)
from ai_models.anomaly_detector import get_anomaly_detector
from ai_models.risk_scorer import compute_risk_score, zone_risk_breakdown, score_to_level
from ai_models.llm_engine import get_llm_engine

logger = logging.getLogger(__name__)


class CorrelationEngine:
    def __init__(self):
        self._current_risk_score = 0
        self._previous_risk_score = 0
        self._active_rule_codes: set = set()
        self._anomaly_scores: Dict[str, float] = {}
        self._vision_score: float = 0.0
        self._db = None
        self._ws_manager = None

    def set_dependencies(self, db_session_factory, ws_manager):
        self._db = db_session_factory
        self._ws_manager = ws_manager

    # ─── Event Handlers ──────────────────────────────────────

    async def on_sensor_reading(self, data: Dict[str, Any]) -> None:
        """Process incoming sensor reading."""
        zone        = data.get("zone", "unknown")
        sensor_type = data.get("sensor_type", "")
        value       = float(data.get("value", 0))

        # Update in-memory state
        update_sensor(zone, sensor_type, value)

        # Persist to DB
        from database import save_sensor_reading_db
        try:
            await save_sensor_reading_db(data)
        except Exception as e:
            logger.warning(f"Failed to persist sensor reading to DB: {e}")

        # Run anomaly detection on gas sensors
        if sensor_type.startswith("gas_") or sensor_type == "temp":
            await self._run_anomaly_detection(zone)

        # Re-evaluate risk
        await self._evaluate_and_broadcast(zone)

        # Broadcast sensor update
        if self._ws_manager:
            await self._ws_manager.broadcast({
                "type":    "sensor_update",
                "payload": {
                    "zone":        zone,
                    "sensor_type": sensor_type,
                    "value":       value,
                    "unit":        data.get("unit", ""),
                    "timestamp":   datetime.now(timezone.utc).isoformat(),
                },
                "ts": datetime.now(timezone.utc).isoformat(),
            })

    async def on_equipment_update(self, data: Dict[str, Any]) -> None:
        """Process equipment status update."""
        equipment_id = data.get("equipment_id", "")
        update_equipment(equipment_id, data)

        # Persist to database
        from database import save_equipment_status_db
        try:
            await save_equipment_status_db(data)
        except Exception as e:
            logger.warning(f"Failed to persist equipment status to DB: {e}")

        zone = data.get("zone", "Zone-A")
        await self._evaluate_and_broadcast(zone)

        if self._ws_manager:
            await self._ws_manager.broadcast({
                "type":    "equipment_update",
                "payload": data,
                "ts":      datetime.now(timezone.utc).isoformat(),
            })

    async def on_permit_update(self, permits: List[Dict[str, Any]]) -> None:
        """Process work permit update."""
        update_permits(permits)
        # Re-evaluate all zones
        for zone in get_all_zones_states().keys():
            await self._evaluate_and_broadcast(zone)
        if self._ws_manager:
            await self._ws_manager.broadcast({
                "type":    "permit_update",
                "payload": permits,
                "ts":      datetime.now(timezone.utc).isoformat(),
            })

    async def on_shift_change(self, data: Dict[str, Any]) -> None:
        """Process shift change event."""
        update_shift(data)
        
        async def reset_flag():
            set_shift_change_flag(True)
            await asyncio.sleep(30)  # Flag active for 30s after shift change
            set_shift_change_flag(False)
            
        asyncio.create_task(reset_flag())

    async def on_ppe_detection(self, data: Dict[str, Any]) -> None:
        """Process PPE detection result."""
        zone   = data.get("zone", "unknown")
        status = data.get("ppe_status", "unknown")
        update_ppe(zone, status)

        # Persist to database
        from database import save_ppe_detection_db
        try:
            await save_ppe_detection_db(data)
        except Exception as e:
            logger.warning(f"Failed to persist PPE detection to DB: {e}")

        non_compliance = len(data.get("violations", []))
        self._vision_score = min(1.0, non_compliance * 0.33)
        await self._evaluate_and_broadcast(zone)

    # ─── Core Evaluation ─────────────────────────────────────

    async def _run_anomaly_detection(self, zone: str) -> float:
        """Run Isolation Forest on current zone sensors."""
        from rule_engine.state_aggregator import _latest
        sensors = _latest["sensors"].get(zone, {})
        detector = get_anomaly_detector()
        try:
            is_anomaly, score = detector.predict(
                gas_ch4     = sensors.get("gas_ch4", 0),
                gas_co      = sensors.get("gas_co",  0),
                gas_h2s     = sensors.get("gas_h2s", 0),
                temperature = sensors.get("temp",    20),
            )
            self._anomaly_scores[zone] = score
            return score
        except Exception as e:
            logger.debug(f"Anomaly detection error: {e}")
            return 0.0

    async def _evaluate_and_broadcast(self, zone: str) -> None:
        """Full evaluation cycle: rules → score → alerts → broadcast."""
        try:
            state    = build_state(zone)
            triggered = get_triggered_rules(state)

            new_rule_codes = {r.rule_code for r in triggered}
            anomaly_score  = self._anomaly_scores.get(zone, 0.0)

            new_score = compute_risk_score(
                triggered_rules = triggered,
                anomaly_score   = anomaly_score,
                vision_score    = self._vision_score,
                base_score      = self._current_risk_score,
            )

            score_changed     = abs(new_score - self._current_risk_score) >= 3
            new_rules_fired   = new_rule_codes - self._active_rule_codes

            if score_changed or new_rules_fired:
                self._previous_risk_score = self._current_risk_score
                self._current_risk_score  = new_score
                self._active_rule_codes   = new_rule_codes

                level, color = score_to_level(new_score)

                # Persist system state snapshot to DB
                from database import save_system_snapshot_db
                try:
                    await save_system_snapshot_db({
                        "risk_score": new_score,
                        "risk_level": level,
                        "triggered_rules": [r.rule_code for r in triggered],
                        "anomaly_flags": [zone] if anomaly_score > 0.5 else [],
                        "zone_scores": {zone: new_score}
                    })
                except Exception as e:
                    logger.warning(f"Failed to persist state snapshot to DB: {e}")

                # Broadcast risk score update
                if self._ws_manager:
                    await self._ws_manager.broadcast({
                        "type": "risk_score",
                        "payload": {
                            "risk_score":     new_score,
                            "risk_level":     level,
                            "color":          color,
                            "zone":           zone,
                            "triggered_rules": [r.rule_code for r in triggered],
                            "anomaly_score":  anomaly_score,
                            "timestamp":      datetime.now(timezone.utc).isoformat(),
                        },
                        "ts": datetime.now(timezone.utc).isoformat(),
                    })

                # Create alert for newly triggered rules
                for rule in triggered:
                    if rule.rule_code in new_rules_fired:
                        await self._create_alert(rule, new_score, zone)

                # Auto-generate incident report if CRITICAL
                if new_score >= 81 and self._previous_risk_score < 81:
                    asyncio.create_task(
                        self._generate_incident_report(zone, new_score, level, triggered)
                    )

        except Exception as e:
            logger.error(f"Correlation evaluation error: {e}", exc_info=True)

    async def _create_alert(
        self, rule: RuleResult, risk_score: int, zone: str
    ) -> None:
        """Create alert record and broadcast."""
        alert_data = {
            "alert_code":    rule.rule_code,
            "severity":      rule.severity,
            "risk_score":    risk_score,
            "message":       rule.message,
            "zone":          zone,
            "source_events": [],
            "created_at":    datetime.now(timezone.utc).isoformat(),
        }
        from api.alerts import add_alert
        await add_alert(alert_data)
        if self._ws_manager:
            await self._ws_manager.broadcast({
                "type":    "alert",
                "payload": alert_data,
                "ts":      datetime.now(timezone.utc).isoformat(),
            })
        logger.warning(f"ALERT [{rule.severity}] {rule.rule_code}: {rule.message}")

    async def _generate_incident_report(
        self, zone: str, risk_score: int, risk_level: str,
        triggered_rules: List[RuleResult]
    ) -> None:
        """Generate LLM incident report and broadcast."""
        try:
            from rule_engine.state_aggregator import _latest
            sensors   = _latest["sensors"].get(zone, {})
            equipment = _latest["equipment"]
            permits   = _latest["permits"]

            llm    = get_llm_engine()
            report = await llm.generate_incident_report(
                zone            = zone,
                risk_score      = risk_score,
                risk_level      = risk_level,
                triggered_rules = triggered_rules,
                sensor_data     = sensors,
                anomaly_flag    = self._anomaly_scores.get(zone, 0) > 0.5,
                anomaly_score   = self._anomaly_scores.get(zone, 0),
                permits         = permits,
                equipment       = equipment,
                timestamp       = datetime.now(timezone.utc).isoformat(),
            )

            from api.reports import add_report
            added_report = await add_report(report)

            if self._ws_manager:
                await self._ws_manager.broadcast({
                    "type":    "report_ready",
                    "payload": added_report,
                    "ts":      datetime.now(timezone.utc).isoformat(),
                })
            logger.info(f"Incident report generated for {zone} (score={risk_score})")
        except Exception as e:
            logger.error(f"Incident report generation failed: {e}", exc_info=True)

    # ─── Getters ─────────────────────────────────────────────

    @property
    def current_risk_score(self) -> int:
        return self._current_risk_score

    def get_zone_breakdown(self) -> dict:
        zones = get_all_zones_states()
        return zone_risk_breakdown(zones, self._anomaly_scores)


# Singleton
correlation_engine = CorrelationEngine()


def get_correlation_engine() -> CorrelationEngine:
    return correlation_engine
