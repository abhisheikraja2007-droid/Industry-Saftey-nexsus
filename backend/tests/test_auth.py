"""
Unit Tests for JWT Authentication utilities.
Tests password hashing, JWT generation/decoding, token rotation, and lockout.
"""

import pytest
import os
from datetime import timedelta

# Set test JWT secret before importing auth module
os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"

from utils.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_jwt_secrets, get_active_secret
)
from fastapi import HTTPException


class TestPasswordHashing:
    def test_hash_and_verify_correct_password(self):
        hashed = hash_password("testpassword123")
        assert verify_password("testpassword123", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        hashed = hash_password("testpassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_hash_is_different_each_time(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses salt

    def test_empty_password_can_be_hashed(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True


class TestJWTTokens:
    def test_create_and_decode_access_token(self):
        token = create_access_token({"sub": "testuser", "role": "admin"})
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "testuser"
        assert payload["role"] == "admin"

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token({"sub": "testuser"})
        payload = decode_token(token)
        assert payload["sub"] == "testuser"
        assert payload.get("refresh") is True

    def test_expired_token_raises_401(self):
        token = create_access_token({"sub": "testuser"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401
        assert "expired" in exc.value.detail.lower()

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not.a.valid.token")
        assert exc.value.status_code == 401

    def test_token_rotation_accepts_old_secret(self):
        # Simulate key rotation: old key + new key
        os.environ["JWT_SECRET"] = "old-key,new-key"
        # Token was issued with old key
        import jwt as pyjwt
        old_token = pyjwt.encode({"sub": "user"}, "old-key", algorithm="HS256")
        # Should still be decodable with rotation
        try:
            payload = decode_token(old_token)
            assert payload["sub"] == "user"
        finally:
            os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"

    def test_get_jwt_secrets_returns_list(self):
        os.environ["JWT_SECRET"] = "key1,key2,key3"
        secrets = get_jwt_secrets()
        assert len(secrets) == 3
        assert secrets[0] == "key1"
        os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"

    def test_get_active_secret_returns_first(self):
        os.environ["JWT_SECRET"] = "primary-key,secondary-key"
        assert get_active_secret() == "primary-key"
        os.environ["JWT_SECRET"] = "test-secret-key-for-unit-tests"
