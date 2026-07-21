import time
import json
import random
import paho.mqtt.client as mqtt
import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

client = mqtt.Client("Simulator")

def connect_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT)
        client.loop_start()
        print("Simulator connected to MQTT")
        return True
    except Exception as e:
        print(f"Failed to connect: {e}")
        return False

def simulate_data():
    zones = ["Zone_A", "Zone_B", "Zone_C", "Restricted_Zone"]
    
    while True:
        # Simulate gas sensor
        gas_level = random.uniform(0.0, 50.0)
        # Occasionally spike it
        if random.random() > 0.9:
            gas_level = random.uniform(80.0, 150.0)
            
        payload = {
            "sensor_type": "gas",
            "location": random.choice(zones),
            "value": round(gas_level, 2)
        }
        
        client.publish("sensors/gas", json.dumps(payload))
        print(f"Published: {payload}")
        time.sleep(5)

if __name__ == "__main__":
    if connect_mqtt():
        simulate_data()
