"""
Synthetic Data Generator
========================
Generates and seeds the database with realistic industrial data for testing.
Run this script once during project setup when real datasets are not available.
"""

import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://safety_user:safety_password@localhost:5432/safety_intelligence")
engine = create_engine(DATABASE_URL)

ZONES = ["Zone_A", "Zone_B", "Zone_C", "Restricted_Zone"]
EQUIPMENT_IDS = ["EQ-101", "EQ-102", "EQ-103", "EQ-104"]
PERMIT_TYPES = ["HOT_WORK", "COLD_WORK", "ELECTRICAL", "CONFINED_SPACE"]


def generate_sensors(n=500):
    print(f"Generating {n} sensor readings...")
    rows = []
    for _ in range(n):
        ts = datetime.utcnow() - timedelta(hours=random.randint(0, 48))
        rows.append({
            "sensor_type": random.choice(["gas", "temperature", "pressure"]),
            "location": random.choice(ZONES),
            "value": round(random.uniform(0.0, 120.0), 2),
            "timestamp": ts.isoformat()
        })
    return rows


def generate_equipment_status(n=100):
    print(f"Generating {n} equipment status records...")
    rows = []
    for eid in EQUIPMENT_IDS:
        for _ in range(n // len(EQUIPMENT_IDS)):
            ts = datetime.utcnow() - timedelta(hours=random.randint(0, 48))
            rows.append({
                "equipment_id": eid,
                "status": random.choice(["RUNNING", "IDLE", "FAULT", "OFFLINE"]),
                "temperature": round(random.uniform(20.0, 95.0), 2),
                "timestamp": ts.isoformat()
            })
    return rows


def generate_work_permits(n=20):
    print(f"Generating {n} work permits...")
    rows = []
    for i in range(n):
        issued = datetime.utcnow() - timedelta(hours=random.randint(0, 24))
        rows.append({
            "permit_id": f"WP-{1000 + i}",
            "permit_type": random.choice(PERMIT_TYPES),
            "location": random.choice(ZONES),
            "status": random.choice(["ACTIVE", "ACTIVE", "CLOSED"]),
            "issued_at": issued.isoformat()
        })
    return rows


def seed_database():
    sensors = generate_sensors(500)
    equipment = generate_equipment_status(100)
    permits = generate_work_permits(20)

    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO sensors (sensor_type, location, value, timestamp)
            VALUES (:sensor_type, :location, :value, :timestamp)
        """), sensors)

        conn.execute(text("""
            INSERT INTO equipment_status (equipment_id, status, temperature, timestamp)
            VALUES (:equipment_id, :status, :temperature, :timestamp)
        """), equipment)

        conn.execute(text("""
            INSERT INTO work_permits (permit_id, permit_type, location, status, issued_at)
            VALUES (:permit_id, :permit_type, :location, :status, :issued_at)
            ON CONFLICT (permit_id) DO NOTHING
        """), permits)

        conn.commit()

    print("Synthetic database seeding complete!")


if __name__ == "__main__":
    seed_database()
