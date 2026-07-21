"""
Composite risk scorer.
Combines: rule engine score + anomaly detector + YOLO vision score.
"""
from __future__ import annotations
from typing import List, Tuple
from rule_engine.rules import RuleResult


RISK_LEVELS = {
    (0,  30): ("SAFE",     "#22c55e"),
    (31, 60): ("WARNING",  "#eab308"),
    (61, 80): ("HIGH",     "#f97316"),
    (81, 100): ("CRITICAL", "#ef4444"),
}


def score_to_level(score: int) -> Tuple[str, str]:
    """Returns (level_label, hex_color)."""
    for (lo, hi), (label, color) in RISK_LEVELS.items():
        if lo <= score <= hi:
            return label, color
    return "CRITICAL", "#ef4444"


def compute_risk_score(
    triggered_rules:   List[RuleResult],
    anomaly_score:     float = 0.0,   # 0–1, from Isolation Forest
    vision_score:      float = 0.0,   # 0–1, from YOLO PPE non-compliance
    base_score:        int   = 0,
) -> int:
    """
    Composite risk score (0–100).

    Components:
    - Rule engine:    sum of score_deltas for triggered rules (dominant)
    - Anomaly score:  0–20 contribution (scaled from Isolation Forest confidence)
    - Vision score:   0–15 contribution (scaled from YOLO non-compliance rate)
    - Base score:     carried-over score from previous tick (exponential decay)
    """
    # Rule component (capped at 80 to leave room for anomaly/vision)
    rule_score = min(80, sum(r.score_delta for r in triggered_rules if r.triggered))

    # Anomaly component: anomaly_score 0–1 → 0–20
    anomaly_contribution = int(anomaly_score * 20)

    # Vision component: vision_score 0–1 → 0–15
    vision_contribution = int(vision_score * 15)

    # Decay previous score (10% decay per tick)
    decayed_base = int(base_score * 0.9)

    # Composite
    raw = max(decayed_base, rule_score + anomaly_contribution + vision_contribution)
    return min(100, max(0, raw))


def zone_risk_breakdown(
    zone_states: dict,  # zone -> SystemState
    anomaly_scores: dict = None,  # zone -> float
) -> dict:
    """Compute per-zone risk scores for heatmap."""
    from rule_engine.rules import evaluate_rules
    anomaly_scores = anomaly_scores or {}
    breakdown = {}
    for zone, state in zone_states.items():
        rules     = evaluate_rules(state)
        triggered = [r for r in rules if r.triggered]
        score     = compute_risk_score(
            triggered_rules = triggered,
            anomaly_score   = anomaly_scores.get(zone, 0.0),
        )
        level, color = score_to_level(score)
        breakdown[zone] = {
            "risk_score":     score,
            "risk_level":     level,
            "color":          color,
            "triggered_rules": [r.rule_code for r in triggered],
        }
    return breakdown
