"""
Test script for console capture system.

Run this after starting the server to test console functionality.
"""

import asyncio
import json
import aiohttp
from uuid import uuid4


async def test_console_capture():
    """Test console capture system via REST API."""
    base_url = "http://localhost:8000/api/v1"
    
    # Test credentials (use a real JWT token from login)
    email = "john.doe@example.com"
    password = "securepassword123"
    
    async with aiohttp.ClientSession() as session:
        print("\n=== Testing Console Capture System ===\n")
        
        # 1. Login to get JWT token
        print("1. Logging in...")
        login_data = {"email": email, "password": password}
        async with session.post(f"{base_url}/auth/login", json=login_data) as resp:
            if resp.status != 200:
                print(f"❌ Login failed: {await resp.text()}")
                return
            login_result = await resp.json()
            token = login_result["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
        
        # 2. Get user's projects
        print("\n2. Getting projects...")
        async with session.get(f"{base_url}/projects", headers=headers) as resp:
            if resp.status != 200:
                print(f"❌ Failed to get projects: {await resp.text()}")
                return
            projects = await resp.json()
            if not projects:
                print("❌ No projects found. Create a project first.")
                return
            project_id = projects[0]["id"]
            print(f"✅ Using project: {projects[0]['name']} (ID: {project_id})")
        
        # 3. Store some console logs
        print("\n3. Storing console logs...")
        log_levels = ["log", "info", "warn", "error", "debug"]
        for i, level in enumerate(log_levels):
            log_data = {
                "level": level,
                "message": f"Test {level} message {i+1}",
                "source": "test_console_capture.py",
                "line": 50 + i
            }
            async with session.post(
                f"{base_url}/console/projects/{project_id}/logs",
                headers=headers,
                json=log_data
            ) as resp:
                if resp.status == 200:
                    print(f"✅ Stored {level} log")
                else:
                    print(f"❌ Failed to store {level} log: {await resp.text()}")
        
        # 4. Store an error with stack trace
        print("\n4. Storing error with stack trace...")
        error_data = {
            "message": "TypeError: Cannot read property 'foo' of undefined",
            "stack": "TypeError: Cannot read property 'foo' of undefined\n    at Object.<anonymous> (/app/src/index.js:10:15)\n    at Module._compile (internal/modules/cjs/loader.js:1063:30)",
            "type": "TypeError",
            "filename": "/app/src/index.js",
            "line": 10,
            "column": 15,
            "is_unhandled": True
        }
        async with session.post(
            f"{base_url}/console/projects/{project_id}/errors",
            headers=headers,
            json=error_data
        ) as resp:
            if resp.status == 200:
                print("✅ Stored error log")
            else:
                print(f"❌ Failed to store error: {await resp.text()}")
        
        # 5. Get console logs
        print("\n5. Retrieving console logs...")
        async with session.get(
            f"{base_url}/console/projects/{project_id}/logs?count=10",
            headers=headers
        ) as resp:
            if resp.status == 200:
                logs = await resp.json()
                print(f"✅ Retrieved {len(logs)} logs:")
                for log in logs[:3]:  # Show first 3
                    print(f"   - [{log['level']}] {log['message']}")
            else:
                print(f"❌ Failed to get logs: {await resp.text()}")
        
        # 6. Get errors
        print("\n6. Retrieving errors...")
        async with session.get(
            f"{base_url}/console/projects/{project_id}/errors",
            headers=headers
        ) as resp:
            if resp.status == 200:
                errors = await resp.json()
                print(f"✅ Retrieved {len(errors)} errors")
                if errors:
                    print(f"   Latest error: {errors[0]['message']}")
            else:
                print(f"❌ Failed to get errors: {await resp.text()}")
        
        # 7. Get console stats
        print("\n7. Getting console statistics...")
        async with session.get(
            f"{base_url}/console/projects/{project_id}/stats",
            headers=headers
        ) as resp:
            if resp.status == 200:
                stats = await resp.json()
                print("✅ Console statistics:")
                for level, count in stats.items():
                    print(f"   - {level}: {count}")
            else:
                print(f"❌ Failed to get stats: {await resp.text()}")
        
        # 8. Get AI context
        print("\n8. Getting AI console context...")
        async with session.get(
            f"{base_url}/console/projects/{project_id}/context",
            headers=headers
        ) as resp:
            if resp.status == 200:
                context = await resp.json()
                print("✅ AI Console context:")
                print(f"   - Error count: {context['error_count']}")
                print(f"   - Has errors: {context['has_errors']}")
                if context.get('most_common_error'):
                    print(f"   - Most common error: {context['most_common_error']}")
            else:
                print(f"❌ Failed to get context: {await resp.text()}")
        
        print("\n=== Console Capture Test Complete ===\n")


if __name__ == "__main__":
    asyncio.run(test_console_capture()) 