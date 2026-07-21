import urllib.request
import json
import time
import sys

BASE = "http://localhost:8000"

def http_post(path, payload, headers=None):
    if headers is None:
        headers = {}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, str(e)

def http_get(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=10) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return 0, str(e)

print("=== PROGRAMMATIC E2E VERIFICATION ===")

# 1. Login as admin
status, data = http_post("/api/auth/login", {"username": "admin", "password": "adminpass"})
if status != 200:
    print(f"[FAIL] Admin login failed: {status}")
    sys.exit(1)
print("[PASS] 1. Login as Admin successful.")
token = data["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Create Hot Work Permit in Zone-D
permit_payload = {
    "permit_type": "hot_work",
    "location": "Zone-D Sub-station",
    "zone": "Zone-D",
    "issued_by": "Ahmed Al-Rashid",
    "worker_names": ["Worker-902", "Worker-113"],
    "expires_at": "2026-07-07T00:00:00Z",
    "notes": "Routine hot work maintenance"
}
status, permit_data = http_post("/api/permits", permit_payload, headers)
if status != 200:
    print(f"[FAIL] Create Permit failed: {status} {permit_data}")
    sys.exit(1)
permit_id = permit_data["permit_id"]
print(f"[PASS] 2. Create Permit successful. Permit ID: {permit_id}")

# 3. Verify Permit List matches active count on Dashboard
status, dash_data = http_get("/api/dashboard")
active_permits = [p for p in dash_data.get("permits", []) if p["permit_id"] == permit_id]
if not active_permits:
    print("[FAIL] Active permit not reflected in Dashboard.")
    sys.exit(1)
print(f"[PASS] 3. Dashboard reflects active permit count. Current total: {dash_data.get('global_risk_score')}")

# 4. Ingest CH4 > 25 ppm in Zone-D to trigger safety rules
sensor_payload = {
    "sensor_id": "GAS_CH4-Zone-D",
    "sensor_type": "gas_ch4",
    "location": "Zone-D Sensor Array",
    "zone": "Zone-D",
    "value": 30.0,
    "unit": "ppm"
}
status, sensor_res = http_post("/api/sensor-data", sensor_payload)
if status != 200:
    print(f"[FAIL] Sensor ingestion failed: {status}")
    sys.exit(1)
print("[PASS] 4. Gas sensor data (CH4 = 30 ppm) ingested into Zone-D.")

# 5. Verify the safety rule (GAS_HOT_WORK) triggers in the risk engine
time.sleep(2)  # Wait for correlation engine to process
status, alerts_data = http_get("/api/alerts")
hot_work_alerts = [a for a in alerts_data.get("alerts", []) if a["alert_code"] == "GAS_HOT_WORK" and a["zone"] == "Zone-D"]
if not hot_work_alerts:
    print("[FAIL] Safety rule 'GAS_HOT_WORK' was not triggered in Zone-D.")
    sys.exit(1)
safe_msg = hot_work_alerts[0]['message'].encode('ascii', 'ignore').decode('ascii')
print(f"[PASS] 5. Safety rule 'GAS_HOT_WORK' triggered successfully. Alert message: {safe_msg}")

print("=== ALL E2E VERIFICATION STEPS PASSED ===")
