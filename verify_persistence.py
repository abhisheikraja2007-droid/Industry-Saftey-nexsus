import urllib.request
import json
import sys

BASE = "http://localhost:8000"

def check(endpoint, expected_field, min_value=0):
    try:
        with urllib.request.urlopen(BASE + endpoint, timeout=10) as r:
            data = json.loads(r.read().decode())
            val = data.get(expected_field, 0)
            if isinstance(val, list):
                val = len(val)
            if val >= min_value:
                print(f"[OK] {endpoint} has {val} items.")
                return True
            else:
                print(f"[FAIL] {endpoint} has {val} items, expected > {min_value}.")
                return False
    except Exception as e:
        print(f"[FAIL] {endpoint} failed: {e}")
        return False

print("=== Phase 1: Persistence Verification ===")
ok = True
ok &= check("/api/alerts", "total", 1)
ok &= check("/api/incident-reports", "total", 1)
ok &= check("/api/sensors/history?zone=Zone-D&hours=24", "total", 1)

try:
    req = urllib.request.Request(
        BASE + "/api/auth/login",
        data=b'{"username":"admin","password":"adminpass"}',
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        if r.status == 200:
            print("[OK] Admin user login successful.")
        else:
            print("[FAIL] Admin login failed with status:", r.status)
            ok = False
except Exception as e:
    print(f"[FAIL] Admin login error: {e}")
    ok = False

if not ok:
    sys.exit(1)
print("[PASS] All persistence checks passed.")
