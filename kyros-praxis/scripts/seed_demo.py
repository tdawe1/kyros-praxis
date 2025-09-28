"""
Seed demo data for local development.

Creates a demo user (if missing) and a few sample jobs via the Orchestrator API.

Usage:
  # Ensure orchestrator is running on :8000 and venv has deps
  $ cd services/orchestrator && source .venv/bin/activate
  $ python scripts/seed_demo.py

Environment:
  ORCH_URL: Base URL of orchestrator (default: http://localhost:8000)
  DEMO_EMAIL: User email/username (default: user@example.com)
  DEMO_PASSWORD: Password (default: password123)
"""

from __future__ import annotations

import os
import sys
from typing import Optional


def ensure_user(email: str, password: str) -> Optional[int]:
    """Create the demo user if it does not exist. Returns user id or None on failure."""
    try:
        # Import from monorepo path regardless of CWD
        sys.path.append(os.getcwd())
        from services.orchestrator.secure_database import SecureDatabase  # type: ignore
        # Ensure tables exist (create on first run)
        try:
            from services.orchestrator.database import engine  # type: ignore
            from services.orchestrator.models import Base  # type: ignore
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass

        db_path = os.path.join(os.getcwd(), "services", "orchestrator", "orchestrator.db")
        db = SecureDatabase(f"sqlite:///{db_path}")

        # Try to create user. Returns None on duplicate.
        return db.create_user(email, email, password)
    except Exception as e:
        print(f"[seed] Skipped user creation (likely exists): {e}")
        return None


def get_token(base_url: str, email: str, password: str) -> str:
    import httpx
    try:
        resp = httpx.post(
            f"{base_url}/auth/login",
            json={"username": email, "password": password},
            timeout=10,
        )
    except httpx.ConnectError as e:
        raise SystemExit(
            f"[seed] Could not connect to orchestrator at {base_url}.\n"
            "Make sure it is running: 'uvicorn services.orchestrator.main:app --reload --port 8000'"
        ) from e

    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError("No access_token in login response")
    return token


def create_jobs(base_url: str, token: str) -> None:
    import httpx

    titles = [
        "Demo: Ingest repository and analyze agents",
        "Demo: Run daily sync and cleanup",
        "Demo: Validate PR gate and tests",
    ]
    headers = {"Authorization": f"Bearer {token}"}
    for t in titles:
        r = httpx.post(
            f"{base_url}/api/v1/jobs",
            json={"title": t},
            headers=headers,
            timeout=10,
        )
        if r.is_success:
            print(f"[seed] Created job: {r.json().get('name')}")
        else:
            print(f"[seed] Failed to create job '{t}': {r.status_code} {r.text}")


def main() -> None:
    base_url = os.getenv("ORCH_URL", "http://localhost:8000")
    email = os.getenv("DEMO_EMAIL", "user@example.com")
    password = os.getenv("DEMO_PASSWORD", "password123")

    print(f"[seed] Using orchestrator: {base_url}")
    ensure_user(email, password)
    token = get_token(base_url, email, password)
    print("[seed] Authenticated, seeding jobs...")
    create_jobs(base_url, token)
    print("[seed] Done.")


if __name__ == "__main__":
    main()
