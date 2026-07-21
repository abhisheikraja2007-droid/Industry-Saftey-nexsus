"""
Secrets Management Documentation
=================================
This file documents how secrets should be managed in production.
It provides utilities for validating secret strength.

NEVER commit real secrets to version control.
"""

import os
import sys
import secrets
import string
import hashlib


def generate_jwt_secret(length: int = 64) -> str:
    """Generate a cryptographically secure random JWT secret."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_jwt_secret(secret: str) -> list[str]:
    """Validate JWT secret strength. Returns list of issues (empty = OK)."""
    issues = []
    if len(secret) < 32:
        issues.append(f"JWT_SECRET too short ({len(secret)} chars). Minimum 32 required.")
    if secret == "super-secret-key-change-me-in-production":
        issues.append("JWT_SECRET is the default placeholder — MUST be changed for production.")
    if secret.lower() == secret:
        issues.append("JWT_SECRET should contain mixed case characters.")
    return issues


def check_production_secrets():
    """Audit all required environment variables for production readiness."""
    print("=== Secrets Audit ===")
    issues = []

    jwt_secret = os.getenv("JWT_SECRET", "")
    if not jwt_secret:
        issues.append("JWT_SECRET is not set.")
    else:
        jwt_issues = validate_jwt_secret(jwt_secret)
        issues.extend(jwt_issues)
        if not jwt_issues:
            # Show hash of the secret (not the secret itself)
            h = hashlib.sha256(jwt_secret.encode()).hexdigest()[:12]
            print(f"  ✅ JWT_SECRET is set (sha256 prefix: {h}...)")

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        issues.append("DATABASE_URL is not set.")
    elif "safety_pass" in db_url:
        issues.append("DATABASE_URL uses default password — change for production.")
    else:
        print("  ✅ DATABASE_URL is set")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key:
        print("  ⚠️  OPENAI_API_KEY is not set (AI incident reports will be template-only)")
    else:
        print("  ✅ OPENAI_API_KEY is set")

    if issues:
        print(f"\n  ❌ Found {len(issues)} secret issue(s):")
        for issue in issues:
            print(f"     - {issue}")
        return False

    print("  ✅ All secrets validation passed")
    return True


def print_secret_setup_guide():
    """Print instructions for setting up production secrets."""
    new_jwt_secret = generate_jwt_secret()
    print("""
╔══════════════════════════════════════════════════════════╗
║          Production Secrets Setup Guide                  ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. Generate a secure JWT secret (example below):        ║
║  2. Add to Docker Compose as environment variable or     ║
║     use Docker Secrets / Kubernetes Secrets / Vault      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

Example .env file (DO NOT commit to git):
─────────────────────────────────────────
""")
    print(f"JWT_SECRET={new_jwt_secret}")
    print("DATABASE_URL=postgresql+asyncpg://user:STRONG_PASSWORD@postgres:5432/safety_db")
    print("REDIS_URL=redis://:STRONG_REDIS_PASSWORD@redis:6379/0")
    print("OPENAI_API_KEY=sk-your-key-here")
    print("GRAFANA_PASSWORD=StrongGrafanaPass123!")
    print("""
─────────────────────────────────────────

JWT Key Rotation (zero-downtime):
──────────────────────────────────
# Step 1: Add new key as primary, keep old key for validation
JWT_SECRET=NEW_KEY,OLD_KEY

# Step 2: After 7 days (refresh tokens expire), remove old key
JWT_SECRET=NEW_KEY

Docker Secrets (production recommended):
────────────────────────────────────────
# Create secrets
echo "my-jwt-secret" | docker secret create jwt_secret -
echo "strong-password" | docker secret create db_password -

# Reference in docker-compose.yml
secrets:
  jwt_secret:
    external: true
  db_password:
    external: true
""")


if __name__ == "__main__":
    if "--check" in sys.argv:
        ok = check_production_secrets()
        sys.exit(0 if ok else 1)
    elif "--guide" in sys.argv:
        print_secret_setup_guide()
    else:
        print("Usage:")
        print("  python secrets_manager.py --check   # Audit current secrets")
        print("  python secrets_manager.py --guide   # Show setup instructions")
