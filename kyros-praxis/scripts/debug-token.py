#!/usr/bin/env python3
"""
Debug JWT token
"""
import asyncio
import httpx
from jose import jwt

BASE_URL = "http://localhost:8000"

async def debug_token():
    """Debug JWT token"""
    print("=== Debugging JWT Token ===")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Login
        response = await client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return

        token_data = response.json()
        token = token_data["access_token"]

        # Decode token (without verification, just to see contents)
        try:
            # Try with the secret from .env
            SECRET_KEY = "local-test-secret-key-do-not-use-in-production"
            ALGORITHM = "HS512"
            JWT_ISSUER = "kyros-praxis"
            JWT_AUDIENCE = "kyros-app"

            decoded = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options={"verify_signature": False}  # Don't verify for debugging
            )

            print("\nDecoded token:")
            for key, value in decoded.items():
                print(f"  {key}: {value}")

        except Exception as e:
            print(f"❌ Failed to decode token: {e}")

        # Check user in database
        from sqlalchemy import create_engine, text
        engine = create_engine("sqlite:///./services/orchestrator/orchestrator.db")

        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM users WHERE username = 'testuser'"))
            user = result.fetchone()

            if user:
                print("\nUser in database:")
                print(f"  ID: {user[0]}")
                print(f"  Username: {user[1]}")
                print(f"  Email: {user[2]}")
            else:
                print("\n❌ User not found in database")

if __name__ == "__main__":
    asyncio.run(debug_token())