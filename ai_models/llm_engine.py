"""
LLM Engine — generates human-readable explanations and incident reports.
Supports OpenAI GPT-4o (cloud) with rule-based fallback (no API key needed).
"""
from __future__ import annotations
import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── PROMPT TEMPLATES ─────────────────────────────────────────

INCIDENT_PROMPT = """You are an industrial safety expert AI assistant.

SITUATION:
- Facility zone: {zone}
- Timestamp: {timestamp}
- Global risk score: {risk_score}/100 ({risk_level})

TRIGGERED SAFETY RULES:
{rules_text}

CURRENT SENSOR READINGS:
- CH4 (methane): {gas_ch4} ppm (safe limit: 25 ppm)
- CO (carbon monoxide): {gas_co} ppm (safe limit: 50 ppm)
- H2S (hydrogen sulphide): {gas_h2s} ppm (safe limit: 10 ppm)
- Equipment temperature: {equip_temp}°C

ANOMALY DETECTION:
- Anomaly detected: {anomaly_flag}
- Anomaly confidence: {anomaly_score:.0%}

ACTIVE WORK PERMITS:
{permits_text}

EQUIPMENT STATUS:
{equipment_text}

TASK:
1. Write a concise (3–4 sentences) incident summary explaining the compound hazard.
2. Identify the root cause chain.
3. List 4 specific, actionable recommended actions in priority order.
4. Estimate the incident severity and potential consequences if unaddressed.

Format your response as:
SUMMARY: <your summary>
ROOT CAUSE: <root cause chain>
ACTIONS:
1. <action>
2. <action>
3. <action>
4. <action>
SEVERITY: <severity and consequences>
"""

ALERT_EXPLANATION_PROMPT = """You are an industrial safety AI. In 2 sentences, explain why this alert is dangerous and what the immediate action should be.

Alert: {alert_code}
Message: {message}
Zone: {zone}
Risk Score: {risk_score}/100

Response format: <explanation> | IMMEDIATE ACTION: <action>"""


# ─── LLM ENGINE ──────────────────────────────────────────────

class LLMEngine:
    def __init__(self):
        self.client      = None
        self.use_openai  = bool(OPENAI_API_KEY)
        if self.use_openai:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
                logger.info("LLM Engine: OpenAI GPT-4o configured.")
            except ImportError:
                logger.warning("openai package not installed — using fallback.")
                self.use_openai = False
        else:
            logger.info("LLM Engine: No API key — using rule-based fallback.")

    async def generate_incident_report(
        self,
        zone:          str,
        risk_score:    int,
        risk_level:    str,
        triggered_rules: List[Any],
        sensor_data:   Dict[str, float],
        anomaly_flag:  bool,
        anomaly_score: float,
        permits:       List[Dict],
        equipment:     Dict[str, Any],
        timestamp:     str,
    ) -> Dict[str, Any]:
        """Generate a full incident report (AI or fallback)."""

        rules_text = "\n".join(
            f"- [{r.severity}] {r.rule_code}: {r.message}"
            for r in triggered_rules
        ) or "None triggered"

        permits_text = "\n".join(
            f"- {p.get('permit_type','unknown').upper()} in {p.get('location','?')} (issued by {p.get('issued_by','?')})"
            for p in permits
        ) or "No active permits"

        equipment_text = "\n".join(
            f"- {eid}: {edata.get('status','?')} | temp={edata.get('temperature','?')}°C"
            for eid, edata in equipment.items()
        ) or "No equipment data"

        prompt = INCIDENT_PROMPT.format(
            zone         = zone,
            timestamp    = timestamp,
            risk_score   = risk_score,
            risk_level   = risk_level,
            rules_text   = rules_text,
            gas_ch4      = sensor_data.get("gas_ch4", 0),
            gas_co       = sensor_data.get("gas_co",  0),
            gas_h2s      = sensor_data.get("gas_h2s", 0),
            equip_temp   = sensor_data.get("temp",    0),
            anomaly_flag = "YES" if anomaly_flag else "NO",
            anomaly_score = anomaly_score,
            permits_text = permits_text,
            equipment_text = equipment_text,
        )

        if self.use_openai and self.client:
            return await self._openai_call(prompt, risk_score, zone, triggered_rules)
        else:
            return self._rule_based_report(
                zone, risk_score, risk_level, triggered_rules, sensor_data
            )

    async def _openai_call(
        self, prompt: str, risk_score: int, zone: str, triggered_rules: List[Any]
    ) -> Dict[str, Any]:
        try:
            resp = await self.client.chat.completions.create(
                model    = "gpt-4o",
                messages = [{"role": "user", "content": prompt}],
                max_tokens = 600,
                temperature = 0.3,
            )
            text = resp.choices[0].message.content
            return self._parse_llm_response(text, zone, risk_score, triggered_rules)
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return self._rule_based_report(zone, risk_score, "HIGH", triggered_rules, {})

    def _parse_llm_response(
        self, text: str, zone: str, risk_score: int, triggered_rules: List[Any]
    ) -> Dict[str, Any]:
        lines    = text.strip().split("\n")
        summary  = ""
        root     = ""
        actions  = []
        severity = ""
        for line in lines:
            if line.startswith("SUMMARY:"):
                summary = line.replace("SUMMARY:", "").strip()
            elif line.startswith("ROOT CAUSE:"):
                root = line.replace("ROOT CAUSE:", "").strip()
            elif line.strip() and line[0].isdigit() and "." in line:
                actions.append(line.split(".", 1)[1].strip())
            elif line.startswith("SEVERITY:"):
                severity = line.replace("SEVERITY:", "").strip()

        return {
            "title":               f"Compound Hazard — {zone} — Risk {risk_score}",
            "summary":             summary or text[:500],
            "ai_explanation":      f"ROOT CAUSE: {root}\n\nSEVERITY: {severity}",
            "recommended_actions": actions or ["Evacuate zone", "Alert safety team", "Shut down hot-work permit"],
            "risk_score":          risk_score,
        }

    def _rule_based_report(
        self,
        zone:            str,
        risk_score:      int,
        risk_level:      str,
        triggered_rules: List[Any],
        sensor_data:     Dict[str, float],
    ) -> Dict[str, Any]:
        """Deterministic fallback report when no LLM is available."""
        rule_codes = [r.rule_code for r in triggered_rules if r.triggered]
        messages   = [r.message   for r in triggered_rules if r.triggered]

        summary = (
            f"A compound hazard has been detected in {zone} with a risk score of {risk_score}/100 ({risk_level}). "
            f"The following safety rules were triggered: {', '.join(rule_codes)}. "
            "Multiple concurrent hazard conditions require immediate coordinated response."
        )
        if "GAS_HOT_WORK" in rule_codes:
            summary += " Flammable gas detected in area with active hot-work permit creates ignition risk."
        if "GAS_FAN_OFF" in rule_codes:
            summary += " Ventilation failure is causing gas accumulation."

        actions = []
        if "GAS_HOT_WORK" in rule_codes or "GAS_FAN_OFF" in rule_codes:
            actions.append("Immediately revoke all hot-work permits in affected zone.")
            actions.append("Restore exhaust ventilation or implement forced ventilation.")
        if "PPE_ZONE" in rule_codes:
            actions.append("Issue PPE to non-compliant workers or evacuate them from the hazard zone.")
        if "CO_THRESHOLD" in rule_codes or "H2S_THRESHOLD" in rule_codes:
            actions.append("Activate self-contained breathing apparatus (SCBA) protocol.")
        actions += [
            "Alert the safety supervisor and escalate to emergency response team.",
            "Initiate continuous atmospheric monitoring until readings return to safe levels.",
        ]

        return {
            "title":               f"Safety Alert — {zone} — {risk_level}",
            "summary":             summary,
            "ai_explanation":      "\n".join(messages),
            "recommended_actions": actions[:6],
            "risk_score":          risk_score,
        }

    async def explain_alert(
        self, alert_code: str, message: str, zone: str, risk_score: int
    ) -> str:
        """Generate a short explanation for a single alert."""
        if self.use_openai and self.client:
            try:
                prompt = ALERT_EXPLANATION_PROMPT.format(
                    alert_code = alert_code,
                    message    = message,
                    zone       = zone,
                    risk_score = risk_score,
                )
                resp = await self.client.chat.completions.create(
                    model    = "gpt-4o",
                    messages = [{"role": "user", "content": prompt}],
                    max_tokens = 150,
                )
                return resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Alert explanation failed: {e}")

        return f"{message} | IMMEDIATE ACTION: Alert safety supervisor and inspect {zone}."


# Singleton
llm_engine = LLMEngine()


def get_llm_engine() -> LLMEngine:
    return llm_engine
