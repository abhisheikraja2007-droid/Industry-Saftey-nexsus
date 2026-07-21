"""
Unit tests for input validation rules (sensor, permit, shift).
Verifies boundary conditions, mandatory field checks, and sanitization.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# SensorIn is the actual pydantic model used by the sensors API
from api.sensors import SensorIn as SensorReading


class TestSensorValidation:
    """Sensor reading input validation boundary tests."""

    def test_valid_gas_ch4(self):
        data = dict(sensor_id="SENS-001", sensor_type="gas_ch4",
                    location="Zone-A", zone="Zone-A", value=25.0, unit="ppm")
        s = SensorReading(**data)
        assert s.value == 25.0

    def test_negative_gas_value_rejected(self):
        with pytest.raises(Exception):
            SensorReading(sensor_id="X", sensor_type="gas_ch4",
                          location="Z", zone="Z", value=-1.0, unit="ppm")

    def test_zero_gas_value_accepted(self):
        s = SensorReading(sensor_id="SENS-001", sensor_type="gas_ch4",
                          location="Zone-A", zone="Zone-A", value=0.0, unit="ppm")
        assert s.value == 0.0

    def test_negative_temperature_accepted(self):
        """Temperatures can be negative (arctic conditions)."""
        s = SensorReading(sensor_id="SENS-002", sensor_type="temp",
                          location="Zone-A", zone="Zone-A", value=-15.0, unit="°C")
        assert s.value == -15.0

    def test_empty_sensor_id_rejected(self):
        with pytest.raises(Exception):
            SensorReading(sensor_id="", sensor_type="gas_ch4",
                          location="Zone-A", zone="Zone-A", value=5.0, unit="ppm")

    def test_whitespace_only_sensor_id_rejected(self):
        with pytest.raises(Exception):
            SensorReading(sensor_id="   ", sensor_type="gas_ch4",
                          location="Zone-A", zone="Zone-A", value=5.0, unit="ppm")

    def test_xss_injection_in_sensor_id_sanitized(self):
        """Sensor IDs should not allow HTML/script injection."""
        with pytest.raises(Exception):
            SensorReading(
                sensor_id="<script>alert(1)</script>",
                sensor_type="gas_ch4",
                location="Zone-A", zone="Zone-A",
                value=5.0, unit="ppm"
            )

    def test_sql_injection_in_zone_sanitized(self):
        """Zone fields should not allow SQL injection."""
        with pytest.raises(Exception):
            SensorReading(
                sensor_id="SENS-001",
                sensor_type="gas_ch4",
                location="' OR '1'='1",
                zone="' OR '1'='1",
                value=5.0, unit="ppm"
            )

    def test_missing_required_fields_rejected(self):
        with pytest.raises(Exception):
            SensorReading(sensor_type="gas_ch4", location="Zone-A", value=5.0)

    def test_unknown_sensor_type_accepted(self):
        """Unknown sensor types may be accepted for extensibility."""
        s = SensorReading(sensor_id="SENS-003", sensor_type="custom_sensor",
                          location="Zone-A", zone="Zone-A", value=50.0, unit="units")
        assert s.sensor_type == "custom_sensor"
