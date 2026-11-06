#!/usr/bin/env python3
"""
Industrial Safety Nexus — ONNX Export Script
Exports Isolation Forest anomaly detector to ONNX format for production deployment.
Verifies inference parity between sklearn and ONNX Runtime.
"""
from __future__ import annotations
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_models.anomaly_detector import AnomalyDetector
from data.synthetic.generator import generate_sensor_history


def export_isolation_forest_to_onnx(
    model_path: str = "ai_models/saved/isolation_forest.pkl",
    scaler_path: str = "ai_models/saved/scaler.pkl",
    onnx_path: str = "ai_models/saved/anomaly_detector.onnx",
    opset: int = 14,
) -> Dict[str, Any]:
    """
    Export trained Isolation Forest + StandardScaler to ONNX.
    Returns export metadata.
    """
    try:
        import onnx
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError:
        print("❌ skl2onnx not installed. Run: pip install skl2onnx onnx onnxruntime")
        return {"success": False, "error": "Missing dependencies"}

    # Load trained model and scaler
    import pickle

    detector = AnomalyDetector()

    # Train if not already trained
    if not detector.trained:
        print("🔄 Training Isolation Forest on synthetic data...")
        df = generate_sensor_history(hours=72, interval_minutes=5)
        detector.train(df)
        print(f"✅ Trained on {len(df)} samples")

    # Ensure model is loaded
    if not detector.load():
        print("❌ Failed to load model")
        return {"success": False, "error": "Model load failed"}

    # Prepare initial type for ONNX conversion
    # Input: [gas_ch4, gas_co, gas_h2s, temperature, hour, weekday] = 6 features
    initial_type = [("float_input", FloatTensorType([None, 6]))]

    # Convert the pipeline: StandardScaler -> IsolationForest
    # We need to export both scaler and model
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    pipeline = Pipeline([
        ("scaler", detector.scaler),
        ("model", detector.model),
    ])

    print(f"📦 Converting to ONNX (opset={opset})...")
    try:
        onnx_model = convert_sklearn(
            pipeline,
            initial_types=initial_type,
            target_opset=opset,
            options={IsolationForest: {"zipmap": False}},
        )
    except Exception as e:
        print(f"❌ ONNX conversion failed: {e}")
        return {"success": False, "error": str(e)}

    # Save ONNX model
    onnx_path = Path(onnx_path)
    onnx_path.parent.mkdir(parents=True, exist_ok=True)
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

    print(f"✅ ONNX model saved to: {onnx_path}")

    # Verify ONNX model
    import onnxruntime as ort

    sess = ort.InferenceSession(str(onnx_path))
    input_name = sess.get_inputs()[0].name
    output_names = [o.name for o in sess.get_outputs()]
    print(f"   Inputs:  {input_name} -> {sess.get_inputs()[0].shape}")
    print(f"   Outputs: {output_names}")

    return {
        "success": True,
        "onnx_path": str(onnx_path),
        "input_name": input_name,
        "output_names": output_names,
        "opset": opset,
        "features": 6,
    }


def verify_onnx_parity(
    onnx_path: str = "ai_models/saved/anomaly_detector.onnx",
    num_samples: int = 1000,
    tolerance: float = 1e-4,
) -> Dict[str, Any]:
    """
    Verify ONNX Runtime inference matches sklearn inference.
    Returns parity metrics.
    """
    import onnxruntime as ort
    import pickle

    # Load sklearn model
    detector = AnomalyDetector()
    if not detector.load():
        if not detector.trained:
            print("🔄 Training for verification...")
            df = generate_sensor_history(hours=24, interval_minutes=5)
            detector.train(df)

    # Load ONNX session
    sess = ort.InferenceSession(onnx_path)
    input_name = sess.get_inputs()[0].name

    # Generate test samples
    np.random.seed(42)
    test_samples = np.random.uniform(0, 100, (num_samples, 6)).astype(np.float32)

    # Sklearn predictions
    sklearn_preds = []
    sklearn_scores = []
    for sample in test_samples:
        is_anomaly, score = detector.predict(
            gas_ch4=float(sample[0]),
            gas_co=float(sample[1]),
            gas_h2s=float(sample[2]),
            temperature=float(sample[3]),
            ts=None,  # hour/weekday from sample[4], sample[5]
        )
        # Note: detector.predict uses hour/weekday from datetime, not from sample
        # For fair comparison, we need to use the same hour/weekday
        # Let's just use the decision_function directly
        X_scaled = detector.scaler.transform(sample.reshape(1, -1))
        raw_score = detector.model.decision_function(X_scaled)[0]
        pred = detector.model.predict(X_scaled)[0]
        sklearn_preds.append(pred == -1)
        sklearn_scores.append(float(np.clip((-raw_score + 0.5) / 1.0, 0.0, 1.0)))

    # ONNX predictions
    onnx_outputs = sess.run(None, {input_name: test_samples})
    # IsolationForest in ONNX outputs: [predictions, scores] typically
    # Let's check the output structure
    if len(onnx_outputs) == 2:
        onnx_preds_raw, onnx_scores_raw = onnx_outputs
        onnx_preds = onnx_preds_raw.flatten() == -1
        onnx_scores = onnx_scores_raw.flatten()
    else:
        # Single output (predictions only)
        onnx_preds = onnx_outputs[0].flatten() == -1
        onnx_scores = np.zeros(num_samples)

    # Compare
    pred_match = np.mean(np.array(sklearn_preds) == np.array(onnx_preds))
    score_diff = np.mean(np.abs(np.array(sklearn_scores) - onnx_scores[:num_samples]))

    results = {
        "samples_tested": num_samples,
        "prediction_agreement": float(pred_match),
        "mean_score_difference": float(score_diff),
        "max_score_difference": float(np.max(np.abs(np.array(sklearn_scores) - onnx_scores[:num_samples]))),
        "parity_passed": pred_match >= (1 - tolerance) and score_diff < tolerance,
        "tolerance": tolerance,
    }

    print(f"\n🔍 PARITY VERIFICATION ({num_samples} samples)")
    print(f"   Prediction Agreement: {pred_match * 100:.4f}%")
    print(f"   Mean Score Diff:      {score_diff:.6f}")
    print(f"   Max Score Diff:       {results['max_score_difference']:.6f}")
    print(f"   Parity Passed:        {'✅ YES' if results['parity_passed'] else '❌ NO'}")

    return results


def benchmark_onnx_inference(
    onnx_path: str = "ai_models/saved/anomaly_detector.onnx",
    iterations: int = 10000,
) -> Dict[str, float]:
    """Benchmark ONNX Runtime inference speed."""
    import onnxruntime as ort
    import time

    sess = ort.InferenceSession(onnx_path)
    input_name = sess.get_inputs()[0].name

    # Warmup
    dummy = np.random.uniform(0, 100, (1, 6)).astype(np.float32)
    for _ in range(100):
        sess.run(None, {input_name: dummy})

    # Benchmark
    test_batch = np.random.uniform(0, 100, (iterations, 6)).astype(np.float32)

    start = time.perf_counter()
    for i in range(iterations):
        sess.run(None, {input_name: test_batch[i:i+1]})
    elapsed = time.perf_counter() - start

    per_sample_ms = (elapsed / iterations) * 1000
    throughput = iterations / elapsed

    print(f"\n⚡ ONNX RUNTIME BENCHMARK ({iterations} iterations)")
    print(f"   Per-sample latency: {per_sample_ms:.3f} ms")
    print(f"   Throughput:         {throughput:.0f} samples/sec")

    return {
        "iterations": iterations,
        "latency_ms": round(per_sample_ms, 3),
        "throughput_per_sec": round(throughput, 0),
    }


def main():
    print("=" * 70)
    print("INDUSTRIAL SAFETY NEXUS — ONNX EXPORT & VERIFICATION")
    print("=" * 70)

    # Step 1: Export to ONNX
    print("\n📦 STEP 1: Export Isolation Forest to ONNX")
    print("-" * 70)
    export_result = export_isolation_forest_to_onnx()

    if not export_result["success"]:
        print(f"❌ Export failed: {export_result.get('error')}")
        sys.exit(1)

    # Step 2: Verify parity
    print("\n🔍 STEP 2: Verify ONNX-Sklearn Parity")
    print("-" * 70)
    parity_result = verify_onnx_parity(export_result["onnx_path"])

    # Step 3: Benchmark ONNX
    print("\n⚡ STEP 3: Benchmark ONNX Runtime")
    print("-" * 70)
    bench_result = benchmark_onnx_inference(export_result["onnx_path"])

    # Save combined results
    combined = {
        "export": export_result,
        "parity": parity_result,
        "benchmark": bench_result,
    }

    out_path = Path(__file__).parent.parent / "onnx_export_results.json"
    with open(out_path, "w") as f:
        json.dump(combined, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {out_path}")

    # Summary
    print("\n" + "=" * 70)
    print("ONNX EXPORT SUMMARY")
    print("=" * 70)
    print(f"Model:           {export_result['onnx_path']}")
    print(f"Input Features:  {export_result['features']}")
    print(f"Opset:           {export_result['opset']}")
    print(f"Parity:          {'✅ PASSED' if parity_result['parity_passed'] else '❌ FAILED'}")
    print(f"  Prediction Agreement: {parity_result['prediction_agreement']*100:.2f}%")
    print(f"  Score Difference:     {parity_result['mean_score_difference']:.6f}")
    print(f"ONNX Latency:    {bench_result['latency_ms']:.3f} ms/sample")
    print(f"ONNX Throughput: {bench_result['throughput_per_sec']:.0f} samples/sec")


if __name__ == "__main__":
    main()