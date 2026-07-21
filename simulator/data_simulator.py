"""
MQTT Data Simulator — publishes synthetic sensor readings at configurable intervals.
Uses real data from ai4i2020.csv (UCI AI4I Predictive Maintenance Dataset) for equipment telemetry.
Run standalone: python data_simulator.py
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.synthetic.generator import (
    generate_current_sensor_reading, generate_work_permit,
    generate_shift_log, ZONES, EQUIPMENT_CATALOG
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL    = float(os.getenv("SIM_INTERVAL", "5.0"))  # seconds between readings


# ─── Load ai4i2020.csv (UCI Predictive Maintenance Dataset) ─────────
_csv_data = None
_csv_index = 0

def _load_csv_data():
    """Load the AI4I 2020 Predictive Maintenance Dataset."""
    global _csv_data
    csv_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "raw", "ai4i2020.csv"),
        "/app/data/raw/ai4i2020.csv",
    ]
    for path in csv_paths:
        if os.path.exists(path):
            try:
                _csv_data = pd.read_csv(path)
                logger.info(f"✅ Loaded ai4i2020.csv: {len(_csv_data)} rows of real equipment data")
                logger.info(f"   Columns: {list(_csv_data.columns)}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
    logger.warning("⚠️ ai4i2020.csv not found — using random equipment data fallback")
    return False


def _get_equipment_reading_from_csv(equipment: dict) -> dict:
    """Get equipment reading from real CSV data."""
    global _csv_index, _csv_data

    if _csv_data is None:
        # Fallback to random
        return {
            **equipment,
            "status":      "online",
            "temperature": round(random.uniform(60, 75), 1),
            "vibration":   round(random.uniform(0.5, 1.2), 3),
            "rpm":         round(random.uniform(1400, 1500), 0),
        }

    row = _csv_data.iloc[_csv_index % len(_csv_data)]

    # Map CSV columns to equipment fields:
    # - "Air temperature [K]" → convert K to °C
    # - "Rotational speed [rpm]" → RPM
    # - "Torque [Nm]" → vibration (scaled)
    # - "Machine failure" → status
    # - "Tool wear [min]" → wear indicator
    air_temp_c = float(row["Air temperature [K]"]) - 273.15
    process_temp_c = float(row["Process temperature [K]"]) - 273.15
    rpm = float(row["Rotational speed [rpm]"])
    torque = float(row["Torque [Nm]"])
    tool_wear = int(row["Tool wear [min]"])
    failure = int(row["Machine failure"])

    # Add per-equipment offset to make each piece of equipment unique
    eq_offset = sum(ord(c) for c in equipment["id"]) % 10

    status = "fault" if failure == 1 else "online"
    # Use process temperature + offset for equipment temperature
    temperature = round(process_temp_c + eq_offset, 1)
    # Scale torque to vibration range (0.3 - 2.0)
    vibration = round(max(0.3, torque * 0.02), 3)
    # Use actual RPM with minor offset
    actual_rpm = round(rpm + eq_offset * 5, 0)

    # Determine failure type from CSV columns for richer alerts
    failure_types = []
    if int(row.get("TWF", 0)) == 1: failure_types.append("tool_wear")
    if int(row.get("HDF", 0)) == 1: failure_types.append("heat_dissipation")
    if int(row.get("PWF", 0)) == 1: failure_types.append("power")
    if int(row.get("OSF", 0)) == 1: failure_types.append("overstrain")
    if int(row.get("RNF", 0)) == 1: failure_types.append("random")

    return {
        **equipment,
        "status":        status,
        "temperature":   temperature,
        "vibration":     vibration,
        "rpm":           actual_rpm,
        "tool_wear":     tool_wear,
        "torque_nm":     round(torque, 1),
        "failure_types": failure_types,
        "data_source":   "ai4i2020_csv",
        "csv_row":       int(_csv_index % len(_csv_data)),
        "product_quality": str(row.get("Type", "L")),
    }


def connect_mqtt() -> mqtt.Client:
    client = mqtt.Client(client_id="safety-simulator")
    retries = 0
    while retries < 10:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()
            logger.info(f"Simulator connected to MQTT at {MQTT_BROKER}:{MQTT_PORT}")
            return client
        except Exception as e:
            logger.warning(f"MQTT connect failed ({e}), retry {retries+1}/10 …")
            time.sleep(5)
            retries += 1
    raise RuntimeError("Could not connect to MQTT broker")


def publish(client: mqtt.Client, topic: str, payload: dict) -> None:
    client.publish(topic, json.dumps(payload), qos=1)
    logger.debug(f"→ {topic}: {payload}")


def run_simulator():
    global _csv_index

    # Load CSV data at startup
    _load_csv_data()

    client = connect_mqtt()
    tick   = 0

    logger.info(f"Simulator running — interval={INTERVAL}s")

    while True:
        try:
            # ── Sensor readings ──────────────────────────────
            for zone in ZONES:
                reading = generate_current_sensor_reading(zone)
                for gas in ["gas_ch4", "gas_co", "gas_h2s"]:
                    publish(client, f"safety/sensors/gas/{zone.lower().replace(' ', '-')}", {
                        "sensor_id":   f"{gas.upper()}-{zone}",
                        "sensor_type": gas,
                        "location":    f"{zone} Sensor Array",
                        "zone":        zone,
                        "value":       reading[gas],
                        "unit":        "ppm",
                        "timestamp":   datetime.now(timezone.utc).isoformat(),
                    })
                publish(client, f"safety/sensors/temp/{zone.lower().replace(' ', '-')}", {
                    "sensor_id":   f"TEMP-{zone}",
                    "sensor_type": "temp",
                    "location":    f"{zone} Temperature",
                    "zone":        zone,
                    "value":       reading["temp"],
                    "unit":        "°C",
                    "timestamp":   datetime.now(timezone.utc).isoformat(),
                })

            # ── Equipment telemetry from CSV (every 3 ticks) ──
            if tick % 3 == 0:
                for eq in EQUIPMENT_CATALOG:
                    eq_reading = _get_equipment_reading_from_csv(eq)
                    publish(client, f"safety/equipment/{eq['id'].lower()}", {
                        **eq_reading,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                # Advance CSV row pointer
                _csv_index += 1

                # Log progress every 100 CSV rows
                if _csv_data is not None and _csv_index % 100 == 0:
                    row_pct = (_csv_index % len(_csv_data)) / len(_csv_data) * 100
                    logger.info(f"📊 CSV data progress: row {_csv_index % len(_csv_data)}/{len(_csv_data)} ({row_pct:.1f}%)")

            # ── Shift log (every 60 ticks ≈ 5 min) ──────────
            if tick % 60 == 0:
                shift = generate_shift_log()
                publish(client, "safety/shifts/change", {
                    **shift,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            # ── Random permit (every 120 ticks ≈ 10 min) ────
            if tick % 120 == 0 and random.random() < 0.3:
                zone   = random.choice(ZONES[:3])
                permit = generate_work_permit(zone)
                publish(client, "safety/permits/new", {
                    **permit,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

            tick += 1
            time.sleep(INTERVAL)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Simulator error: {e}")
            time.sleep(2)

    client.loop_stop()
    client.disconnect()
    logger.info("Simulator stopped.")


if __name__ == "__main__":
    run_simulator()

