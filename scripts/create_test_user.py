#!/usr/bin/env python3
"""
Create a default test user for CLI testing.

Creates a 'root' admin user with a known API key for testing purposes.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2025-01-11): Initial test user creation script.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from modules.backend.core.database import get_db
from modules.backend.models.user import User
from modules.backend.services.auth import AuthService
from modules.backend.services.api_key_db import APIKeyServiceDB
from modules.backend.core.security import get_password_hash


async def create_test_user():
    """Create a test user with known credentials."""
    
    # Test user details
    TEST_USER = {
        'username': 'root',
        'email': 'root@zeblit.local',
        'full_name': 'Root Administrator',
        'password': 'admin123',  # Simple password for testing
        'role': 'admin'
    }
    
    print("🔧 Creating test user for CLI testing...")
    
    async for session in get_db():
        try:
            # Check if user already exists
            stmt = select(User).where(User.username == TEST_USER['username'])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ User '{TEST_USER['username']}' already exists (ID: {existing_user.id})")
                user = existing_user
            else:
                # Create new user
                hashed_password = get_password_hash(TEST_USER['password'])
                
                user = User(
                    username=TEST_USER['username'],
                    email=TEST_USER['email'],
                    full_name=TEST_USER['full_name'],
                    hashed_password=hashed_password,
                    role=TEST_USER['role'],
                    is_active=True,
                    email_verified=True  # Auto-verify for testing
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                print(f"✅ Created user '{TEST_USER['username']}' (ID: {user.id})")
            
            # Create API key using the API key service
            api_key_service = APIKeyServiceDB(session)
            
            # Create a test API key
            try:
                api_key_obj, actual_api_key = await api_key_service.create_api_key(
                    user_id=user.id,
                    name="CLI Test Key",
                    expires_in_days=365,  # Valid for 1 year
                    metadata={"client_type": "cli", "purpose": "testing"}
                )
                
                print(f"✅ Created API key for user '{TEST_USER['username']}'")
                
                print(f"\n📋 Test User Created Successfully!")
                print(f"Username: {TEST_USER['username']}")
                print(f"Email: {TEST_USER['email']}")
                print(f"Password: {TEST_USER['password']}")
                print(f"Role: {TEST_USER['role']}")
                print(f"User ID: {user.id}")
                
                print(f"\n🔑 For CLI testing:")
                print(f"API Key: {actual_api_key}")
                print(f"\nTo test the CLI:")
                print(f"zeblit auth login --api-key {actual_api_key}")
                
                return user, actual_api_key
                
            except Exception as e:
                print(f"⚠️  Failed to create API key: {e}")
                print(f"User created successfully, but you'll need to create an API key manually")
                return user, None
            
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def main():
    """Main entry point."""
    try:
        result = await create_test_user()
        if isinstance(result, tuple):
            user, api_key = result
            if api_key:
                print(f"\n🎉 Test setup complete! You can now test the CLI with the root user and API key.")
            else:
                print(f"\n⚠️  User created but API key creation failed. Please create an API key manually.")
        else:
            user = result
            print(f"\n🎉 Test setup complete! You can now test the CLI with the root user.")
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
