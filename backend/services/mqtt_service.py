import os
import paho.mqtt.client as mqtt
import json
from ..models import database, models

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT} with result code {rc}")
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())
        db = next(database.get_db())
        
        # Example naive processing
        if msg.topic.startswith("sensors/gas"):
            sensor = models.Sensor(
                sensor_type="gas",
                location=data.get("location", "unknown"),
                value=data.get("value", 0.0)
            )
            db.add(sensor)
            db.commit()
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
