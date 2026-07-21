"""
MQTT Listener — subscribes to all safety/# topics and
feeds data into the correlation engine.
"""
from __future__ import annotations
import asyncio
import json
import logging
import os
import threading
from typing import Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "1883"))


class MQTTListener:
    def __init__(self):
        self.client    = mqtt.Client(client_id="safety-backend")
        self.loop      = None
        self.engine    = None
        self._running  = False

        self.client.on_connect    = self._on_connect
        self.client.on_message    = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def set_engine(self, engine) -> None:
        self.engine = engine

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    def start(self) -> None:
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            self._running = True
            thread = threading.Thread(target=self.client.loop_forever, daemon=True)
            thread.start()
            logger.info(f"MQTT listener started — broker={MQTT_BROKER}:{MQTT_PORT}")
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}. Will retry in background.")
            # Non-fatal — system works without MQTT (HTTP endpoints still function)

    def stop(self) -> None:
        self._running = False
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected. Subscribing to safety/#")
            client.subscribe("safety/#", qos=1)
        else:
            logger.error(f"MQTT connect failed: rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"MQTT unexpected disconnect rc={rc}")

    def _on_message(self, client, userdata, msg):
        if not self.engine or not self.loop:
            return
        try:
            topic   = msg.topic  # e.g. safety/sensors/gas/zone-d
            payload = json.loads(msg.payload.decode("utf-8"))

            if "sensors" in topic:
                coro = self.engine.on_sensor_reading(payload)
            elif "equipment" in topic:
                coro = self.engine.on_equipment_update(payload)
            elif "permits" in topic:
                coro = self.engine.on_permit_update(payload if isinstance(payload, list) else [payload])
            elif "shifts" in topic:
                coro = self.engine.on_shift_change(payload)
            elif "ppe" in topic:
                coro = self.engine.on_ppe_detection(payload)
            else:
                return

            asyncio.run_coroutine_threadsafe(coro, self.loop)
        except Exception as e:
            logger.error(f"MQTT message processing error: {e}")


# Singleton
mqtt_listener = MQTTListener()


def get_mqtt_listener() -> MQTTListener:
    return mqtt_listener
