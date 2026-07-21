"""
Isolation Forest anomaly detector for sensor data.
Trained on historical sensor readings at startup.
"""
from __future__ import annotations
import os
import pickle
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_PATH  = Path("/app/ai_models/saved/isolation_forest.pkl")
SCALER_PATH = Path("/app/ai_models/saved/scaler.pkl")

# Fallback local paths for development
if not MODEL_PATH.parent.exists():
    MODEL_PATH  = Path("ai_models/saved/isolation_forest.pkl")
    SCALER_PATH = Path("ai_models/saved/scaler.pkl")


class AnomalyDetector:
    """Isolation Forest anomaly detector for multi-variate sensor streams."""

    FEATURES = ["gas_ch4", "gas_co", "gas_h2s", "temperature", "hour", "weekday"]

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model:  IsolationForest = None
        self.scaler: StandardScaler  = None
        self.trained = False

    # ─── Training ────────────────────────────────────────────

    def train(self, df: pd.DataFrame) -> None:
        """
        Train on historical sensor DataFrame.
        Expected columns: timestamp, zone, sensor_type, value
        """
        logger.info("Training Isolation Forest anomaly detector …")

        # Pivot to wide format
        wide = df.pivot_table(
            index   = ["timestamp", "zone"],
            columns = "sensor_type",
            values  = "value",
            aggfunc = "mean",
        ).reset_index()

        # Ensure expected columns
        for col in ["gas_ch4", "gas_co", "gas_h2s", "temp"]:
            if col not in wide.columns:
                wide[col] = 0.0

        wide.rename(columns={"temp": "temperature"}, inplace=True)
        wide["hour"]    = pd.to_datetime(wide["timestamp"]).dt.hour
        wide["weekday"] = pd.to_datetime(wide["timestamp"]).dt.weekday

        X = wide[self.FEATURES].fillna(0).values

        self.scaler = StandardScaler()
        X_scaled    = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators  = 100,
            contamination = self.contamination,
            random_state  = 42,
            n_jobs        = -1,
        )
        self.model.fit(X_scaled)
        self.trained = True

        # Persist
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH,  "wb") as f:
            pickle.dump(self.model,  f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)

        logger.info(f"Isolation Forest trained on {len(X)} samples — saved to {MODEL_PATH}")

    def load(self) -> bool:
        """Load persisted model. Returns True if successful."""
        try:
            with open(MODEL_PATH,  "rb") as f:
                self.model  = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            self.trained = True
            logger.info("Anomaly detector loaded from disk.")
            return True
        except FileNotFoundError:
            logger.warning("No saved anomaly model found — will train from scratch.")
            return False

    # ─── Inference ───────────────────────────────────────────

    def predict(
        self,
        gas_ch4: float,
        gas_co:  float,
        gas_h2s: float,
        temperature: float,
        ts: datetime = None,
    ) -> Tuple[bool, float]:
        """
        Returns (is_anomaly: bool, anomaly_score: float 0-1).
        Higher score = more anomalous.
        """
        if not self.trained:
            # Return not anomalous if not trained
            return False, 0.0

        ts = ts or datetime.utcnow()
        X  = np.array([[
            gas_ch4, gas_co, gas_h2s, temperature, ts.hour, ts.weekday()
        ]])
        X_scaled = self.scaler.transform(X)

        # IsolationForest: -1 = anomaly, +1 = normal
        prediction = self.model.predict(X_scaled)[0]
        raw_score  = self.model.decision_function(X_scaled)[0]  # more negative = more anomalous

        # Normalise to 0–1 (higher = more anomalous)
        score = float(np.clip((-raw_score + 0.5) / 1.0, 0.0, 1.0))
        is_anomaly = prediction == -1

        return is_anomaly, round(score, 3)


# Singleton
anomaly_detector = AnomalyDetector()


def get_anomaly_detector() -> AnomalyDetector:
    return anomaly_detector
