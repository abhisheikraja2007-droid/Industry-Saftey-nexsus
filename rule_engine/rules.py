"""
Rule Engine — deterministic safety rule evaluation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class SystemState:
    """Aggregated snapshot of the entire facility state."""
    # Gas (ppm)
    gas_ch4:        float = 0.0
    gas_co:         float = 0.0
    gas_h2s:        float = 0.0
    # Temperature (°C)
    equip_temp:     float = 20.0
    # Vibration (mm/s)
    vibration:      float = 0.0
    # Booleans
    hot_work_active: bool = False
    exhaust_fan_on:  bool = True
    worker_in_zone:  bool = False
    ppe_missing:     bool = False
    fire_detected:   bool = False
    worker_present:  bool = False
    shift_change:    bool = False
    equip_fault:     bool = False
    gas_leak:        bool = False
    # Metadata
    zone:            str  = "unknown"
    active_zones:    List[str] = field(default_factory=list)


@dataclass
class RuleResult:
    rule_code:   str
    triggered:   bool
    severity:    str   # WARNING | HIGH | CRITICAL
    score_delta: int
    message:     str
    zone:        Optional[str] = None


@dataclass
class Rule:
    code:        str
    condition:   Callable[[SystemState], bool]
    severity:    str
    score_delta: int
    message:     str


SAFETY_RULES: List[Rule] = [
    Rule(
        code="GAS_HOT_WORK",
        condition=lambda s: s.gas_ch4 > 25 and s.hot_work_active,
        severity="HIGH",
        score_delta=40,
        message="⚠️ CH4 > 25 ppm with active hot-work permit. Ignition risk is HIGH.",
    ),
    Rule(
        code="GAS_FAN_OFF",
        condition=lambda s: s.gas_ch4 > 25 and not s.exhaust_fan_on,
        severity="CRITICAL",
        score_delta=60,
        message="🚨 CH4 > 25 ppm with ventilation failure. Gas accumulation is CRITICAL.",
    ),
    Rule(
        code="PPE_ZONE",
        condition=lambda s: s.ppe_missing and s.worker_in_zone,
        severity="HIGH",
        score_delta=35,
        message="⛑️ Worker detected in hazard zone without required PPE.",
    ),
    Rule(
        code="FIRE_WORKER",
        condition=lambda s: s.fire_detected and s.worker_present,
        severity="CRITICAL",
        score_delta=70,
        message="🔥 Fire detected with worker presence. IMMEDIATE EVACUATION required.",
    ),
    Rule(
        code="SHIFT_FAULT_GAS",
        condition=lambda s: s.shift_change and s.equip_fault and s.gas_leak,
        severity="CRITICAL",
        score_delta=80,
        message="🔴 Shift change occurred during equipment fault + gas leak. Situational awareness breakdown.",
    ),
    Rule(
        code="TEMP_OVERHEAT",
        condition=lambda s: s.equip_temp > 85,
        severity="HIGH",
        score_delta=30,
        message="🌡️ Equipment temperature exceeds 85°C. Overheating risk.",
    ),
    Rule(
        code="CO_THRESHOLD",
        condition=lambda s: s.gas_co > 50,
        severity="WARNING",
        score_delta=20,
        message="💨 CO concentration > 50 ppm. Exposure health risk.",
    ),
    Rule(
        code="H2S_THRESHOLD",
        condition=lambda s: s.gas_h2s > 10,
        severity="HIGH",
        score_delta=45,
        message="☠️ H2S > 10 ppm. Immediately dangerous to life threshold approaching.",
    ),
    Rule(
        code="CONFINED_GAS",
        condition=lambda s: s.gas_ch4 > 20 and "confined_space" in str(s.__dict__),
        severity="HIGH",
        score_delta=50,
        message="⚠️ Gas detected near confined space entry. Atmospheric testing required.",
    ),
    Rule(
        code="VIBRATION_FAULT",
        condition=lambda s: s.vibration > 7.5,
        severity="WARNING",
        score_delta=15,
        message="📳 Equipment vibration exceeds safe limit. Mechanical inspection needed.",
    ),
]


def evaluate_rules(state: SystemState) -> List[RuleResult]:
    """Evaluate all safety rules against current system state."""
    results = []
    for rule in SAFETY_RULES:
        try:
            triggered = rule.condition(state)
        except Exception:
            triggered = False
        results.append(RuleResult(
            rule_code   = rule.code,
            triggered   = triggered,
            severity    = rule.severity,
            score_delta = rule.score_delta if triggered else 0,
            message     = rule.message if triggered else f"{rule.code}: OK",
            zone        = state.zone,
        ))
    return results


def get_triggered_rules(state: SystemState) -> List[RuleResult]:
    """Return only triggered rules."""
    return [r for r in evaluate_rules(state) if r.triggered]
