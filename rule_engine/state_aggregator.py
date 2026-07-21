"""
State Aggregator — collects latest readings from all data sources
and builds the unified SystemState for rule evaluation.
"""
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from rule_engine.rules import SystemState


# In-memory store (replaced by DB queries in full async path)
_latest: Dict[str, Any] = {
    "sensors":   {},   # zone -> {gas_ch4, gas_co, gas_h2s, temp}
    "equipment": {},   # equipment_id -> {status, temperature, vibration}
    "permits":   [],   # list of active permit dicts
    "shift":     None, # current shift dict
    "ppe":       {},   # zone -> ppe_status
}


def update_sensor(zone: str, sensor_type: str, value: float) -> None:
    if zone not in _latest["sensors"]:
        _latest["sensors"][zone] = {}
    _latest["sensors"][zone][sensor_type] = value


def update_equipment(equipment_id: str, data: Dict[str, Any]) -> None:
    _latest["equipment"][equipment_id] = data


def update_permits(permits: List[Dict[str, Any]]) -> None:
    _latest["permits"] = permits


def update_shift(shift: Dict[str, Any]) -> None:
    _latest["shift"] = shift


def update_ppe(zone: str, status: str) -> None:
    _latest["ppe"][zone] = status


def set_shift_change_flag(value: bool) -> None:
    _latest["shift_change"] = value


def build_state(zone: str = "Zone-D") -> SystemState:
    """Build a SystemState snapshot for the given zone."""
    sensors   = _latest["sensors"].get(zone, {})
    equipment = _latest["equipment"]
    permits   = _latest["permits"]
    shift     = _latest["shift"]
    ppe       = _latest["ppe"]

    # Gas readings
    gas_ch4 = sensors.get("gas_ch4", 0.0)
    gas_co  = sensors.get("gas_co",  0.0)
    gas_h2s = sensors.get("gas_h2s", 0.0)
    temp    = sensors.get("temp",    20.0)

    # Equipment
    equip_fault  = any(eq.get("status") == "fault" for eq in equipment.values())
    equip_temps  = [eq.get("temperature", 0) for eq in equipment.values() if eq.get("temperature")]
    max_temp     = max(equip_temps) if equip_temps else 20.0
    vibrations   = [eq.get("vibration", 0) for eq in equipment.values() if eq.get("vibration")]
    max_vib      = max(vibrations) if vibrations else 0.0

    # Fan
    fan_eq = equipment.get("FAN-01", {})
    exhaust_fan_on = fan_eq.get("status", "online") in ("online", "running")

    # Permits
    hot_work_active = any(
        p.get("permit_type") == "hot_work" and p.get("zone") == zone
        for p in permits
    )

    # PPE
    ppe_status  = ppe.get(zone, "unknown")
    ppe_missing = ppe_status == "non_compliant"
    worker_in_zone = ppe_status in ("compliant", "non_compliant")

    # Shift change
    shift_change = _latest.get("shift_change", False)

    return SystemState(
        gas_ch4         = gas_ch4,
        gas_co          = gas_co,
        gas_h2s         = gas_h2s,
        equip_temp      = max_temp,
        vibration       = max_vib,
        hot_work_active = hot_work_active,
        exhaust_fan_on  = exhaust_fan_on,
        worker_in_zone  = worker_in_zone,
        ppe_missing     = ppe_missing,
        fire_detected   = False,
        worker_present  = worker_in_zone,
        shift_change    = shift_change,
        equip_fault     = equip_fault,
        gas_leak        = gas_ch4 > 25 or gas_h2s > 5,
        zone            = zone,
        active_zones    = list(_latest["sensors"].keys()),
    )


def get_all_zones_states() -> Dict[str, SystemState]:
    """Build state snapshots for every zone with sensor data."""
    zones = list(_latest["sensors"].keys())
    if not zones:
        from data.synthetic.generator import ZONES
        zones = ZONES
    return {z: build_state(z) for z in zones}
