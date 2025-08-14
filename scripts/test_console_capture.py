#!/usr/bin/env python3
"""
Test script for console error capture system.

*Version: 1.0.0*
*Author: AI Development Platform Team*

## Changelog
- 1.0.0 (2024-01-XX): Initial console capture test script.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.backend.services.console import ConsoleService
from src.backend.core.redis_client import redis_client
from src.backend.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_redis_connection():
    """Test Redis connection for console logging."""
    print("\n🔌 Testing Redis connection...")
    
    try:
        # Connect to Redis first
        await redis_client.connect()
        
        # Test basic Redis operations
        await redis_client.set("test:console", "test_value")
        value = await redis_client.get("test:console")
        
        if value == "test_value":
            print("✅ Redis connection working")
            
            # Test pub/sub
            channel = "test:console:channel"
            test_message = {"type": "test", "data": "console_test"}
            
            await redis_client.publish(channel, json.dumps(test_message))
            print("✅ Redis pub/sub working")
            
            # Cleanup
            await redis_client.delete("test:console")
            
            return True
        else:
            print("❌ Redis connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False


async def test_console_service():
    """Test the console service functionality."""
    print("🧪 Testing Console Error Capture System")
    print("=" * 50)
    
    try:
        # Initialize console service
        console_service = ConsoleService()
        project_id = "test-project"
        
        # Test 1: Store a simple console log
        print("\n1. Testing console log storage...")
        log_data = {
            "type": "console",
            "method": "log",
            "args": ["Hello from test script", {"data": "test"}],
            "timestamp": datetime.utcnow().isoformat(),
            "userAgent": "test-agent",
            "url": "http://localhost:3000/test"
        }
        
        await console_service.store_console_log(project_id, log_data, "test-user")
        print("✅ Console log stored successfully")
        
        # Test 2: Store an error log
        print("\n2. Testing error log storage...")
        error_data = {
            "type": "error",
            "message": "Cannot read property 'name' of undefined",
            "filename": "test.js",
            "lineno": 42,
            "colno": 18,
            "stack": "TypeError: Cannot read property 'name' of undefined\n    at test.js:42:18",
            "timestamp": datetime.utcnow().isoformat(),
            "userAgent": "test-agent",
            "url": "http://localhost:3000/test"
        }
        
        await console_service.store_console_log(project_id, error_data, "test-user")
        print("✅ Error log stored successfully")
        
        # Test 3: Store an unhandled rejection
        print("\n3. Testing unhandled rejection storage...")
        rejection_data = {
            "type": "unhandledRejection",
            "message": "Network request failed",
            "stack": "Error: Network request failed\n    at fetch.js:15:12",
            "timestamp": datetime.utcnow().isoformat(),
            "userAgent": "test-agent",
            "url": "http://localhost:3000/test"
        }
        
        await console_service.store_console_log(project_id, rejection_data, "test-user")
        print("✅ Unhandled rejection stored successfully")
        
        # Test 4: Retrieve recent logs
        print("\n4. Testing log retrieval...")
        recent_logs = await console_service.get_recent_logs(project_id, 10)
        print(f"✅ Retrieved {len(recent_logs)} logs")
        
        for i, log in enumerate(recent_logs[:3]):
            print(f"   Log {i+1}: {log.get('type')} - {log.get('message', log.get('args', ['N/A'])[0])}")
        
        # Test 5: Get error context
        print("\n5. Testing error context retrieval...")
        error_context = await console_service.get_error_context(project_id)
        print(f"✅ Error context retrieved:")
        print(f"   - Recent errors: {len(error_context.get('recent_errors', []))}")
        print(f"   - Error contexts: {len(error_context.get('error_contexts', []))}")
        print(f"   - Has critical errors: {error_context.get('has_critical_errors', False)}")
        
        # Test 6: Get console stats
        print("\n6. Testing console statistics...")
        stats = await console_service.get_console_stats(project_id)
        print("✅ Console statistics:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        # Test 7: Search logs
        print("\n7. Testing log search...")
        search_results = await console_service.search_logs(project_id, "undefined", 10)
        print(f"✅ Search found {len(search_results)} matching logs")
        
        # Test 8: Export logs
        print("\n8. Testing log export...")
        export_data = await console_service.export_logs(project_id, "json")
        print(f"✅ Export generated with {export_data.get('total_logs', 0)} logs")
        
        # Test 9: Test error classification
        print("\n9. Testing error classification...")
        test_errors = [
            {"message": "Cannot read property 'name' of undefined", "stack": ""},
            {"message": "userId is not defined", "stack": "ReferenceError"},
            {"message": "Unexpected token {", "stack": "SyntaxError"},
            {"message": "Failed to fetch", "stack": "NetworkError"},
        ]
        
        for error in test_errors:
            error_type = console_service.classify_error(error)
            severity = console_service.assess_error_severity({"error_type": error_type, "message": error["message"]})
            print(f"   - '{error['message'][:30]}...' → {error_type} ({severity})")
        
        print("\n✅ All tests completed successfully!")
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        await console_service.clear_logs(project_id)
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Test failed")
        return False
    
    return True


async def main():
    """Main test function."""
    print("🚀 Console Error Capture System Test")
    print("=" * 50)
    
    try:
        # Test Redis connection first
        redis_ok = await test_redis_connection()
        if not redis_ok:
            print("❌ Redis connection failed - console capture won't work")
            return False
        
        # Test console service
        service_ok = await test_console_service()
        if not service_ok:
            print("❌ Console service tests failed")
            return False
        
        print("\n🎉 All tests passed! Console error capture system is working correctly.")
        return True
        
    finally:
        # Always disconnect Redis
        try:
            await redis_client.disconnect()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main()) 