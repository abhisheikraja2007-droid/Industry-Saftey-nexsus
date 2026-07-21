#!/usr/bin/env python3
"""
Chaos Testing Script — Industrial Safety AI
Tests recovery from container failures including:
  - PostgreSQL crash and recovery
  - Redis crash and recovery
  - Mosquitto restart
  - Backend restart
  - Network partition simulation (stop/start container)
"""

import subprocess
import time
import urllib.request
import json
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CHAOS] %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"


def http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception:
        return None, {}


def wait_for_ready(max_wait=60, label="backend"):
    log.info(f"Waiting for {label} to recover...")
    for _ in range(max_wait):
        status, data = http_get(f"{BASE_URL}/ready")
        if status == 200:
            log.info(f"✅ {label} recovered and /ready = 200")
            return True
        time.sleep(1)
    log.error(f"❌ {label} did not recover within {max_wait}s")
    return False


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        log.warning(f"Command failed: {cmd}\n{result.stderr}")
    return result.returncode == 0


def check_data_integrity():
    log.info("Checking data integrity after chaos...")
    status, data = http_get(f"{BASE_URL}/api/alerts")
    if status != 200:
        log.error(f"❌ /api/alerts returned {status} after chaos")
        return False
    
    status, data = http_get(f"{BASE_URL}/api/incident-reports")
    if status != 200:
        log.error(f"❌ /api/incident-reports returned {status} after chaos")
        return False

    log.info(f"✅ Data integrity: alerts={data.get('total', 0)}, reports check OK")
    return True


def test_postgres_crash():
    log.info("=" * 60)
    log.info("CHAOS TEST 1: Kill PostgreSQL container")
    log.info("=" * 60)
    
    # Record baseline data counts
    _, alerts_before = http_get(f"{BASE_URL}/api/alerts")
    alerts_before_count = alerts_before.get("total", 0)
    log.info(f"Before kill: {alerts_before_count} alerts")

    run("docker stop industrial-safety-ai-postgres-1")
    log.info("PostgreSQL stopped. Checking backend resilience...")
    time.sleep(5)
    
    # Backend should still serve in-memory data
    status, _ = http_get(f"{BASE_URL}/api/alerts")
    if status == 200:
        log.info("✅ Backend still serving from in-memory cache while DB is down")
    else:
        log.warning(f"⚠️  Backend returned {status} while DB is down")
    
    # Restart postgres
    run("docker start industrial-safety-ai-postgres-1")
    log.info("PostgreSQL restarted. Waiting for recovery...")
    time.sleep(15)

    status, data = http_get(f"{BASE_URL}/ready")
    if status == 200 and data.get("checks", {}).get("postgres") == "ok":
        log.info("✅ Postgres reconnected, /ready checks postgres=ok")
    else:
        log.error(f"❌ Postgres not recovered: {data}")
        return False

    # Verify data still intact
    _, alerts_after = http_get(f"{BASE_URL}/api/alerts")
    alerts_after_count = alerts_after.get("total", 0)
    log.info(f"After recovery: {alerts_after_count} alerts")
    
    if alerts_after_count >= alerts_before_count:
        log.info("✅ Data integrity maintained after PostgreSQL chaos")
        return True
    else:
        log.error(f"❌ Data loss detected: before={alerts_before_count}, after={alerts_after_count}")
        return False


def test_redis_crash():
    log.info("=" * 60)
    log.info("CHAOS TEST 2: Kill Redis container")
    log.info("=" * 60)
    
    run("docker stop industrial-safety-ai-redis-1")
    log.info("Redis stopped. Waiting 5 seconds...")
    time.sleep(5)

    # API should still function (Redis is only used by Celery)
    status, _ = http_get(f"{BASE_URL}/api/dashboard")
    if status == 200:
        log.info("✅ Backend still functional with Redis down (Celery degraded)")
    else:
        log.warning(f"⚠️  Dashboard returned {status} with Redis down")

    run("docker start industrial-safety-ai-redis-1")
    log.info("Redis restarted.")
    time.sleep(10)
    
    status, data = http_get(f"{BASE_URL}/ready")
    if data.get("checks", {}).get("redis") == "ok":
        log.info("✅ Redis recovered")
        return True
    else:
        log.error(f"❌ Redis not recovered: {data}")
        return False


def test_mqtt_restart():
    log.info("=" * 60)
    log.info("CHAOS TEST 3: Restart Mosquitto MQTT broker")
    log.info("=" * 60)
    
    run("docker restart industrial-safety-ai-mosquitto-1")
    log.info("Mosquitto restarted. Waiting 10 seconds for MQTT listener to reconnect...")
    time.sleep(10)
    
    status, data = http_get(f"{BASE_URL}/ready")
    if data.get("checks", {}).get("mqtt") == "ok":
        log.info("✅ MQTT reconnected after broker restart")
        return True
    else:
        log.error(f"❌ MQTT not reconnected: {data}")
        return False


def test_backend_restart():
    log.info("=" * 60)
    log.info("CHAOS TEST 4: Restart backend container")
    log.info("=" * 60)
    
    _, alerts_before = http_get(f"{BASE_URL}/api/alerts")
    alerts_before_count = alerts_before.get("total", 0)
    
    run("docker restart industrial-safety-ai-backend-1")
    log.info("Backend restarting... waiting 30 seconds")
    time.sleep(30)
    
    recovered = wait_for_ready(60, "backend")
    if not recovered:
        return False

    _, alerts_after = http_get(f"{BASE_URL}/api/alerts")
    alerts_after_count = alerts_after.get("total", 0)
    
    if alerts_after_count == alerts_before_count:
        log.info(f"✅ Data persisted after restart: {alerts_after_count} alerts")
        return True
    else:
        log.error(f"❌ Data loss after restart: before={alerts_before_count}, after={alerts_after_count}")
        return False


def main():
    log.info("Starting Industrial Safety AI Chaos Test Suite")
    
    # Verify baseline health
    status, data = http_get(f"{BASE_URL}/health")
    if status != 200:
        log.error(f"Backend is not healthy before chaos tests: {status}")
        sys.exit(1)
    log.info(f"Baseline: backend healthy, risk_score={data.get('risk_score', 'N/A')}")

    results = {}
    results["postgres_crash"] = test_postgres_crash()
    results["redis_crash"] = test_redis_crash()
    results["mqtt_restart"] = test_mqtt_restart()
    results["backend_restart"] = test_backend_restart()

    log.info("=" * 60)
    log.info("CHAOS TEST RESULTS")
    log.info("=" * 60)
    all_passed = True
    for test, passed in results.items():
        icon = "✅" if passed else "❌"
        log.info(f"  {icon} {test}: {'PASS' if passed else 'FAIL'}")
        if not passed:
            all_passed = False

    log.info("=" * 60)
    if all_passed:
        log.info("✅ All chaos tests PASSED — system is resilient")
        sys.exit(0)
    else:
        log.error("❌ Some chaos tests FAILED — review above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
