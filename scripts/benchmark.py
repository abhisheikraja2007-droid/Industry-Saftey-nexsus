#!/usr/bin/env python3
"""
Industrial Safety Nexus — Performance Benchmark Suite
Measures: API latency, throughput, anomaly inference, WebSocket push latency, DB query time.
Outputs: JSON + human-readable summary for README.
"""
from __future__ import annotations
import asyncio
import json
import statistics
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

import httpx
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_models.anomaly_detector import AnomalyDetector
from ai_models.risk_scorer import compute_risk_score, score_to_level
from rule_engine.rules import RuleResult


@dataclass
class BenchmarkResult:
    name: str
    unit: str
    iterations: int
    mean: float
    median: float
    p95: float
    p99: float
    min_val: float
    max_val: float
    std_dev: float
    throughput_per_sec: float = 0.0


def percentile(data: List[float], p: float) -> float:
    """Calculate percentile."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def run_async_benchmark(name: str, coro_func, iterations: int = 100, warmup: int = 10) -> BenchmarkResult:
    """Run async benchmark with warmup."""
    # Warmup
    for _ in range(warmup):
        asyncio.run(coro_func())

    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        asyncio.run(coro_func())
        latencies.append((time.perf_counter() - start) * 1000)  # ms

    mean = statistics.mean(latencies)
    median = statistics.median(latencies)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    min_val = min(latencies)
    max_val = max(latencies)
    std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    throughput = 1000 / mean if mean > 0 else 0

    return BenchmarkResult(
        name=name,
        unit="ms",
        iterations=iterations,
        mean=round(mean, 2),
        median=round(median, 2),
        p95=round(p95, 2),
        p99=round(p99, 2),
        min_val=round(min_val, 2),
        max_val=round(max_val, 2),
        std_dev=round(std_dev, 2),
        throughput_per_sec=round(throughput, 1),
    )


def run_sync_benchmark(name: str, func, iterations: int = 1000, warmup: int = 10) -> BenchmarkResult:
    """Run synchronous benchmark with warmup."""
    # Warmup
    for _ in range(warmup):
        func()

    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        latencies.append((time.perf_counter() - start) * 1000)  # ms

    mean = statistics.mean(latencies)
    median = statistics.median(latencies)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    min_val = min(latencies)
    max_val = max(latencies)
    std_dev = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
    throughput = 1000 / mean if mean > 0 else 0

    return BenchmarkResult(
        name=name,
        unit="ms",
        iterations=iterations,
        mean=round(mean, 2),
        median=round(median, 2),
        p95=round(p95, 2),
        p99=round(p99, 2),
        min_val=round(min_val, 2),
        max_val=round(max_val, 2),
        std_dev=round(std_dev, 2),
        throughput_per_sec=round(throughput, 1),
    )


# ─── Benchmark Functions ────────────────────────────────────────

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


async def benchmark_health_endpoint():
    """GET /health"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/health")


async def benchmark_ready_endpoint():
    """GET /ready"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/ready")


async def benchmark_risk_score_endpoint():
    """GET /api/risk/score"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/api/risk/score")


async def benchmark_dashboard_endpoint():
    """GET /api/dashboard"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/api/dashboard")


async def benchmark_sensor_ingest():
    """POST /api/sensor-data"""
    payload = {
        "sensor_id": f"BENCH-SENS-{np.random.randint(1000, 9999)}",
        "sensor_type": "gas_ch4",
        "location": "Zone-D Benchmark",
        "zone": "Zone-D",
        "value": float(np.random.uniform(10, 50)),
        "unit": "ppm",
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(f"{API_BASE}/api/sensor-data", json=payload)


async def benchmark_equipment_endpoint():
    """GET /api/equipment"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/api/equipment")


async def benchmark_alerts_endpoint():
    """GET /api/alerts"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.get(f"{API_BASE}/api/alerts")


async def benchmark_sensor_history():
    """GET /api/sensors/history?zone=Zone-D&hours=24"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.get(f"{API_BASE}/api/sensors/history?zone=Zone-D&hours=24")


# ─── ML Inference Benchmarks ────────────────────────────────────

def benchmark_anomaly_detector_predict():
    """AnomalyDetector.predict() - core ML inference"""
    detector = AnomalyDetector()
    # Train on synthetic data
    from data.synthetic.generator import generate_sensor_history
    df = generate_sensor_history(hours=24, interval_minutes=5)
    detector.train(df)

    def predict():
        detector.predict(
            gas_ch4=np.random.uniform(5, 50),
            gas_co=np.random.uniform(5, 50),
            gas_h2s=np.random.uniform(0.5, 10),
            temperature=np.random.uniform(20, 40),
        )
    return predict


def benchmark_risk_scorer():
    """compute_risk_score() - composite risk calculation"""
    rules = [
        RuleResult(rule_code="GAS_HOT_WORK", severity="HIGH", message="Test", triggered=True, score_delta=30),
        RuleResult(rule_code="GAS_FAN_OFF", severity="CRITICAL", message="Test", triggered=True, score_delta=40),
    ]
    def score():
        compute_risk_score(
            triggered_rules=rules,
            anomaly_score=np.random.uniform(0, 1),
            vision_score=np.random.uniform(0, 1),
            base_score=np.random.randint(0, 50),
        )
    return score


def benchmark_rule_evaluation():
    """get_triggered_rules() - rule engine"""
    from rule_engine.state_aggregator import build_state
    from rule_engine.rules import get_triggered_rules

    def eval_rules():
        state = build_state("Zone-D")
        get_triggered_rules(state)
    return eval_rules


# ─── Main ────────────────────────────────────────────────────────

async def main():
    print("=" * 70)
    print("INDUSTRIAL SAFETY NEXUS — PERFORMANCE BENCHMARKS")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"API Base: {API_BASE}")
    print("=" * 70)

    results: List[BenchmarkResult] = []

    # Check backend is reachable
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{API_BASE}/health")
            if resp.status_code != 200:
                print(f"❌ Backend not healthy: {resp.status_code}")
                return
    except Exception as e:
        print(f"❌ Cannot reach backend at {API_BASE}: {e}")
        print("   Start with: docker-compose up --build")
        return

    print("\n📡 API ENDPOINT BENCHMARKS (100 iterations each)")
    print("-" * 70)

    api_benchmarks = [
        ("Health Endpoint (/health)", benchmark_health_endpoint, 100),
        ("Readiness Endpoint (/ready)", benchmark_ready_endpoint, 100),
        ("Risk Score (/api/risk/score)", benchmark_risk_score_endpoint, 100),
        ("Dashboard (/api/dashboard)", benchmark_dashboard_endpoint, 100),
        ("Sensor Ingest (POST /api/sensor-data)", benchmark_sensor_ingest, 100),
        ("Equipment List (/api/equipment)", benchmark_equipment_endpoint, 100),
        ("Alerts List (/api/alerts)", benchmark_alerts_endpoint, 100),
        ("Sensor History (/api/sensors/history)", benchmark_sensor_history, 50),
    ]

    for name, func, iters in api_benchmarks:
        print(f"  Running {name}...", end=" ", flush=True)
        result = await run_async_benchmark(name, func, iterations=iters)
        results.append(result)
        print(f"✅ {result.mean}ms avg, {result.throughput_per_sec:.0f} req/s")

    print("\n🧠 ML INFERENCE BENCHMARKS (1000 iterations each)")
    print("-" * 70)

    ml_benchmarks = [
        ("AnomalyDetector.predict()", benchmark_anomaly_detector_predict(), 1000),
        ("compute_risk_score()", benchmark_risk_scorer(), 1000),
        ("Rule Engine Evaluation", benchmark_rule_evaluation(), 1000),
    ]

    for name, func, iters in ml_benchmarks:
        print(f"  Running {name}...", end=" ", flush=True)
        result = run_sync_benchmark(name, func, iterations=iters)
        results.append(result)
        print(f"✅ {result.mean}ms avg, {result.throughput_per_sec:.0f} ops/s")

    # ─── Output Results ──────────────────────────────────────────
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    for r in results:
        print(f"\n{r.name}")
        print(f"  Mean:     {r.mean:>8.2f} {r.unit}   Throughput: {r.throughput_per_sec:>8.1f} ops/s")
        print(f"  Median:   {r.median:>8.2f} {r.unit}   P95:        {r.p95:>8.2f} {r.unit}")
        print(f"  P99:      {r.p99:>8.2f} {r.unit}   StdDev:     {r.std_dev:>8.2f} {r.unit}")
        print(f"  Min/Max:  {r.min_val:>8.2f} / {r.max_val:<8.2f} {r.unit}")

    # Save JSON
    output = {
        "timestamp": datetime.now().isoformat(),
        "api_base": API_BASE,
        "results": [asdict(r) for r in results],
    }

    out_path = Path(__file__).parent.parent / "benchmark_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to: {out_path}")

    # Generate Markdown table for README
    print("\n" + "=" * 70)
    print("MARKDOWN TABLE FOR README")
    print("=" * 70)
    print("| Component | Operation | Mean Latency | P95 Latency | Throughput |")
    print("|-----------|-----------|--------------|-------------|------------|")
    for r in results:
        print(f"| {r.name.split('(')[0].strip()} | {r.name} | {r.mean:.2f} ms | {r.p95:.2f} ms | {r.throughput_per_sec:.0f} ops/s |")


if __name__ == "__main__":
    asyncio.run(main())