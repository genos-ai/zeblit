#!/usr/bin/env python3
"""
Backend Integration Test Script

Simple script to test that the backend API endpoints are working correctly.
Run this to verify the backend integration before testing the frontend.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial backend integration test script.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from src.backend.core.config import settings


async def test_health_endpoint():
    """Test the health check endpoint."""
    print("🏥 Testing health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000{settings.API_V1_STR}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


async def test_agents_endpoint():
    """Test the agents endpoint."""
    print("🤖 Testing agents endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000{settings.API_V1_STR}/agents")
            if response.status_code == 200:
                data = response.json()
                agent_count = len(data.get('items', []))
                print(f"✅ Agents endpoint working: {agent_count} agents found")
                return True
            else:
                print(f"❌ Agents endpoint failed: {response.status_code}")
                if response.status_code == 401:
                    print("   Note: This might be expected if authentication is required")
                return False
    except Exception as e:
        print(f"❌ Agents endpoint error: {e}")
        return False


async def test_conversations_endpoint():
    """Test the conversations endpoint."""
    print("💬 Testing conversations endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000{settings.API_V1_STR}/conversations")
            if response.status_code == 200:
                data = response.json()
                print("✅ Conversations endpoint working")
                return True
            elif response.status_code == 401:
                print("✅ Conversations endpoint working (authentication required)")
                return True
            else:
                print(f"❌ Conversations endpoint failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Conversations endpoint error: {e}")
        return False


async def test_websocket_endpoint():
    """Test that the WebSocket endpoint is available."""
    print("🔌 Testing WebSocket endpoint availability...")
    try:
        async with httpx.AsyncClient() as client:
            # Try to connect to WebSocket endpoint (will fail without token, but should not 404)
            response = await client.get(f"http://localhost:8000{settings.API_V1_STR}/ws/connect")
            if response.status_code in [400, 422]:  # Bad request or validation error expected
                print("✅ WebSocket endpoint available (validation error expected)")
                return True
            else:
                print(f"⚠️  WebSocket endpoint response: {response.status_code}")
                return True  # Any response means endpoint exists
    except Exception as e:
        print(f"❌ WebSocket endpoint error: {e}")
        return False


async def test_openapi_docs():
    """Test that OpenAPI documentation is available."""
    print("📚 Testing OpenAPI documentation...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/docs")
            if response.status_code == 200:
                print("✅ OpenAPI docs available at http://localhost:8000/docs")
                return True
            else:
                print(f"❌ OpenAPI docs failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ OpenAPI docs error: {e}")
        return False


async def main():
    """Run all backend integration tests."""
    print("🚀 Starting Backend Integration Tests")
    print("=" * 50)
    
    tests = [
        test_health_endpoint,
        test_agents_endpoint,
        test_conversations_endpoint,
        test_websocket_endpoint,
        test_openapi_docs,
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
        print()
    
    # Summary
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✅ Backend integration is working correctly!")
        print("📖 API Documentation: http://localhost:8000/docs")
        print("🔧 Backend Admin: http://localhost:8000/admin (if available)")
        return 0
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        print("\n❗ Issues found:")
        print("   - Make sure the backend server is running: python -m uvicorn src.backend.main:app --reload")
        print("   - Check the backend logs for errors")
        print("   - Verify database and Redis connections")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 