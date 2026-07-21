"""
Unit tests for the rule engine.
"""
from rule_engine.rules import SystemState, evaluate_rules, get_triggered_rules

def test_gas_hot_work_rule():
    # Normal state
    state = SystemState(gas_ch4=10.0, hot_work_active=True, zone="Zone-D")
    triggered = get_triggered_rules(state)
    assert not any(r.rule_code == "GAS_HOT_WORK" for r in triggered)

    # Trigger state
    state = SystemState(gas_ch4=30.0, hot_work_active=True, zone="Zone-D")
    triggered = get_triggered_rules(state)
    assert any(r.rule_code == "GAS_HOT_WORK" for r in triggered)

def test_gas_fan_off_rule():
    # Fan is on, gas high
    state = SystemState(gas_ch4=30.0, exhaust_fan_on=True, zone="Zone-D")
    triggered = get_triggered_rules(state)
    assert not any(r.rule_code == "GAS_FAN_OFF" for r in triggered)

    # Fan is off, gas high
    state = SystemState(gas_ch4=30.0, exhaust_fan_on=False, zone="Zone-D")
    triggered = get_triggered_rules(state)
    assert any(r.rule_code == "GAS_FAN_OFF" for r in triggered)
