"""
Kaggle Dataset Downloader
==========================
Attempts to download predefined datasets from Kaggle if API credentials are available.
Falls back silently - the synthetic generator will be used instead.

Required: A `kaggle.json` API credentials file placed at ~/.kaggle/kaggle.json

Predefined datasets:
  - Gas Sensor:   uciml/gas-sensor-array-under-dynamic-gas-mixtures
  - Predictive:   stephanmatzka/predictive-maintenance-dataset-ai4i-2020
"""

import os
import subprocess

DATASETS = [
    {"name": "Gas Sensor Monitoring",     "slug": "uciml/gas-sensor-array-under-dynamic-gas-mixtures"},
    {"name": "Equipment Monitoring",      "slug": "stephanmatzka/predictive-maintenance-dataset-ai4i-2020"},
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")


def try_download():
    kaggle_credentials = os.path.expanduser("~/.kaggle/kaggle.json")

    # If credentials file doesn't exist, try loading from .env file or environment variables
    if not os.path.exists(kaggle_credentials):
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        username, key = "", ""
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("KAGGLE_USERNAME="):
                            username = line.strip().split("=", 1)[1].strip()
                        elif line.strip().startswith("KAGGLE_KEY="):
                            key = line.strip().split("=", 1)[1].strip()
            except Exception:
                pass

        if not username:
            username = os.getenv("KAGGLE_USERNAME", "").strip()
        if not key:
            key = os.getenv("KAGGLE_KEY", "").strip()

        if username and key:
            try:
                os.makedirs(os.path.dirname(kaggle_credentials), exist_ok=True)
                import json
                with open(kaggle_credentials, "w", encoding="utf-8") as f:
                    json.dump({"username": username, "key": key}, f)
                print(f"Created Kaggle credentials file at: {kaggle_credentials}")
            except Exception as e:
                print(f"Failed to create Kaggle credentials file: {e}")

    if not os.path.exists(kaggle_credentials):
        print("Kaggle credentials not found (~/.kaggle/kaggle.json or .env). Skipping download.")
        print("Synthetic datasets will be used instead.\n")
        return False

    print("Kaggle credentials found. Attempting to download predefined datasets...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    success_count = 0

    for ds in DATASETS:
        print(f"  Downloading: {ds['name']} ({ds['slug']})...")
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d", ds["slug"], "--unzip", "-p", OUTPUT_DIR],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  [OK] {ds['name']} downloaded successfully.")
            success_count += 1
        else:
            print(f"  [FAILED] {ds['name']}: {result.stderr.strip()}")

    print(f"\n{success_count}/{len(DATASETS)} datasets downloaded.\n")
    return success_count > 0


if __name__ == "__main__":
    try_download()
