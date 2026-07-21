import pytest
import os
import sys
import httpx
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import AsyncSessionLocal
from models.db_models import WorkPermit
from sqlalchemy import select

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_permit_creation_and_persistence():
    # 1. Login to get a token
    async with httpx.AsyncClient() as client:
        login_res = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "adminpass"}
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        # 2. Successfully create permit
        permit_payload = {
            "permit_type": "hot_work",
            "location": "Zone-D Sub-station",
            "zone": "Zone-D",
            "issued_by": "Ahmed Al-Rashid",
            "worker_names": ["Worker-902", "Worker-113"],
            "expires_at": datetime.now(timezone.utc).isoformat(),
            "notes": "Routine hot work maintenance"
        }
        headers = {"Authorization": f"Bearer {token}"}
        create_res = await client.post(
            f"{BASE_URL}/api/permits",
            json=permit_payload,
            headers=headers
        )
        assert create_res.status_code == 200
        permit_data = create_res.json()
        assert "permit_id" in permit_data
        permit_id = permit_data["permit_id"]

        # 3. Verify Database Persistence
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkPermit).where(WorkPermit.permit_id == permit_id)
            )
            db_permit = result.scalar_one_or_none()
            assert db_permit is not None
            assert db_permit.permit_type == "hot_work"
            assert db_permit.zone == "Zone-D"
            assert db_permit.issued_by == "Ahmed Al-Rashid"

@pytest.mark.asyncio
async def test_permit_validation_failures():
    async with httpx.AsyncClient() as client:
        # Get login token
        login_res = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "adminpass"}
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Payload with missing required fields (e.g. missing zone)
        bad_payload = {
            "permit_type": "hot_work",
            "location": "Zone-D Sub-station",
            "issued_by": "Ahmed Al-Rashid",
            "expires_at": datetime.now(timezone.utc).isoformat()
        }
        res = await client.post(
            f"{BASE_URL}/api/permits",
            json=bad_payload,
            headers=headers
        )
        assert res.status_code == 422  # Validation error

@pytest.mark.asyncio
async def test_permit_auth_failures():
    async with httpx.AsyncClient() as client:
        permit_payload = {
            "permit_type": "hot_work",
            "location": "Zone-D Sub-station",
            "zone": "Zone-D",
            "issued_by": "Ahmed Al-Rashid",
            "worker_names": ["Worker-902"],
            "expires_at": datetime.now(timezone.utc).isoformat()
        }
        # No Authorization header
        res = await client.post(
            f"{BASE_URL}/api/permits",
            json=permit_payload
        )
        assert res.status_code == 401

        # Invalid token
        res = await client.post(
            f"{BASE_URL}/api/permits",
            json=permit_payload,
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert res.status_code == 401
