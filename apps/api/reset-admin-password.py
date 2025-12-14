#!/usr/bin/env python3
"""
Reset admin password script
Directly updates the password in the database
"""
import asyncio
import sys
from passlib.context import CryptContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import from app
sys.path.insert(0, '/home/thomas/kyros-praxis/apps/api')
from app.db.models import User
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_password(email: str, new_password: str):
    """Reset user password."""
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        # Hash new password
        hashed = pwd_context.hash(new_password)
        
        # Update password
        await session.execute(
            update(User)
            .where(User.email == email)
            .values(password_hash=hashed)
        )
        await session.commit()
        
        print(f"✅ Password reset for: {email}")
        print(f"   New password: {new_password}")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset-admin-password.py <email> <new_password>")
        print("Example: python reset-admin-password.py admin@example.com NewPass123!")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    print(f"Resetting password for: {email}")
    asyncio.run(reset_password(email, password))
