import time
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Normally we'd import the models from a shared package, but for the hackathon we'll just execute raw SQL or redefine a lightweight model
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://safety_user:safety_password@localhost:5432/safety_intelligence")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def evaluate_rules():
    db = SessionLocal()
    try:
        # Example Rule: Gas Level > Threshold AND Hot Work Permit Active -> High Risk
        # 1. Check for active hot work permits
        result = db.execute("SELECT location FROM work_permits WHERE status='ACTIVE' AND permit_type='HOT_WORK'")
        active_hot_work_locations = [row[0] for row in result]
        
        # 2. Check for high gas levels in those locations
        for location in active_hot_work_locations:
            gas_readings = db.execute(f"SELECT value FROM sensors WHERE sensor_type='gas' AND location='{location}' ORDER BY timestamp DESC LIMIT 1")
            for row in gas_readings:
                if row[0] > 50.0:
                    print(f"CRITICAL HAZARD DETECTED: High gas level ({row[0]}) in {location} with active Hot Work Permit!")
                    # In a real scenario, we would insert an alert into the DB here
                    # db.execute("INSERT INTO alerts ...")
                    # db.commit()
    except Exception as e:
        print(f"Error evaluating rules: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting deterministic Python Rule Engine...")
    while True:
        evaluate_rules()
        time.sleep(5)
