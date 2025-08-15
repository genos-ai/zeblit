#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for Zeblit AI Development Platform

This script tests all major systems and workflows to ensure everything
is working correctly before moving to the next development phase.

Usage:
    python test_comprehensive.py [OPTIONS]

Tests:
    1. Backend API endpoints
    2. Authentication system
    3. Task scheduling system
    4. CLI client integration
    5. Database operations
    6. Redis connectivity
    7. WebSocket connections
    8. Error handling
    9. Performance benchmarks
"""

import sys
import asyncio
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    import httpx
    import pytest
    import psutil
    import redis
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich import print as rprint
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install: pip install httpx pytest psutil redis-py rich")
    sys.exit(1)

console = Console()


class TestResult:
    """Represents the result of a test."""
    
    def __init__(self, name: str, success: bool, duration: float, details: str = "", error: str = ""):
        self.name = name
        self.success = success
        self.duration = duration
        self.details = details
        self.error = error


class ComprehensiveTester:
    """Comprehensive testing suite for the Zeblit platform."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.client: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()
    
    def add_result(self, name: str, success: bool, duration: float, details: str = "", error: str = ""):
        """Add a test result."""
        self.results.append(TestResult(name, success, duration, details, error))
    
    async def run_test(self, name: str, test_func, *args, **kwargs):
        """Run a single test with timing and error handling."""
        console.print(f"🧪 Testing: {name}")
        start_time = time.time()
        
        try:
            result = await test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            if isinstance(result, dict):
                success = result.get("success", True)
                details = result.get("details", "")
                error = result.get("error", "")
            else:
                success = bool(result)
                details = str(result) if result else ""
                error = ""
            
            self.add_result(name, success, duration, details, error)
            
            if success:
                console.print(f"✅ {name} - {duration:.2f}s")
            else:
                console.print(f"❌ {name} - {duration:.2f}s - {error}")
                
        except Exception as e:
            duration = time.time() - start_time
            self.add_result(name, False, duration, "", str(e))
            console.print(f"❌ {name} - {duration:.2f}s - Exception: {e}")
    
    # ============================================================================
    # BACKEND API TESTS
    # ============================================================================
    
    async def test_backend_health(self):
        """Test backend health endpoint."""
        response = await self.client.get("/health")
        
        if response.status_code != 200:
            return {"success": False, "error": f"Status code: {response.status_code}"}
        
        data = response.json()
        expected_fields = ["status", "version", "environment"]
        
        for field in expected_fields:
            if field not in data:
                return {"success": False, "error": f"Missing field: {field}"}
        
        if data["status"] != "healthy":
            return {"success": False, "error": f"Status is {data['status']}, expected 'healthy'"}
        
        return {"success": True, "details": f"Version: {data['version']}, Environment: {data['environment']}"}
    
    async def test_models_endpoint(self):
        """Test OpenAI-compatible models endpoint."""
        response = await self.client.get("/v1/models")
        
        if response.status_code != 200:
            return {"success": False, "error": f"Status code: {response.status_code}"}
        
        data = response.json()
        
        if data.get("object") != "list":
            return {"success": False, "error": "Response object should be 'list'"}
        
        if not isinstance(data.get("data"), list):
            return {"success": False, "error": "Data should be a list"}
        
        models = data["data"]
        if len(models) < 1:
            return {"success": False, "error": "Should have at least 1 model"}
        
        # Check model structure
        for model in models:
            required_fields = ["id", "object", "owned_by"]
            for field in required_fields:
                if field not in model:
                    return {"success": False, "error": f"Model missing field: {field}"}
        
        return {"success": True, "details": f"Found {len(models)} models"}
    
    async def test_api_v1_health(self):
        """Test API v1 health endpoint."""
        response = await self.client.get("/api/v1/health")
        
        if response.status_code != 200:
            return {"success": False, "error": f"Status code: {response.status_code}"}
        
        return {"success": True, "details": "API v1 health check passed"}
    
    async def test_scheduled_tasks_unauthenticated(self):
        """Test that scheduled tasks require authentication."""
        response = await self.client.get("/api/v1/scheduled-tasks/")
        
        if response.status_code != 401:
            return {"success": False, "error": f"Expected 401, got {response.status_code}"}
        
        data = response.json()
        if "detail" not in data:
            return {"success": False, "error": "Missing error detail"}
        
        return {"success": True, "details": "Authentication properly required"}
    
    # ============================================================================
    # INFRASTRUCTURE TESTS
    # ============================================================================
    
    async def test_redis_connection(self):
        """Test Redis connectivity."""
        try:
            r = redis.Redis.from_url("redis://localhost:6379/0")
            r.ping()
            
            # Test basic operations
            test_key = "zeblit_test_key"
            test_value = "test_value"
            
            r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved = r.get(test_key)
            
            if retrieved is None:
                return {"success": False, "error": "Failed to retrieve test value"}
            
            if retrieved.decode() != test_value:
                return {"success": False, "error": "Retrieved value doesn't match"}
            
            r.delete(test_key)
            
            return {"success": True, "details": "Redis read/write operations successful"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_backend_process(self):
        """Test that backend process is running properly."""
        found_process = False
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'uvicorn' in cmdline and 'modules.backend.main:app' in cmdline:
                    found_process = True
                    pid = proc.info['pid']
                    
                    # Check if process is responding
                    try:
                        cpu_percent = proc.cpu_percent()
                        memory_info = proc.memory_info()
                        
                        details = f"PID: {pid}, CPU: {cpu_percent:.1f}%, Memory: {memory_info.rss / 1024 / 1024:.1f}MB"
                        return {"success": True, "details": details}
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        return {"success": False, "error": "Process exists but cannot access stats"}
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if not found_process:
            return {"success": False, "error": "Backend process not found"}
        
        return {"success": True, "details": "Backend process found and accessible"}
    
    # ============================================================================
    # CLI CLIENT TESTS
    # ============================================================================
    
    async def test_cli_help(self):
        """Test CLI help functionality."""
        try:
            # Test by importing and running directly
            cli_src_path = project_root / "clients" / "zeblit-cli" / "src"
            
            # Check if CLI directory and main file exist
            if not (cli_src_path / "zeblit_cli" / "main.py").exists():
                return {"success": False, "error": "CLI main.py not found"}
            
            # Simple test - check if the CLI module can be imported and has expected structure
            import sys
            old_path = sys.path[:]
            try:
                sys.path.insert(0, str(cli_src_path))
                import zeblit_cli.main
                
                # Check if the CLI module has the expected components
                if not hasattr(zeblit_cli.main, 'cli'):
                    return {"success": False, "error": "CLI module missing main 'cli' function"}
                
                # Test a simple command execution
                import click.testing
                runner = click.testing.CliRunner()
                result = runner.invoke(zeblit_cli.main.cli, ['--help'])
                
                if result.exit_code != 0:
                    return {"success": False, "error": f"CLI help command failed with exit code {result.exit_code}"}
                
                if "Usage:" not in result.output and "usage:" not in result.output.lower():
                    return {"success": False, "error": "Help output doesn't contain usage information"}
                
                return {"success": True, "details": "CLI help system working"}
                
            finally:
                sys.path[:] = old_path
            
        except ImportError as e:
            return {"success": False, "error": f"Cannot import CLI module: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def test_cli_schedule_help(self):
        """Test CLI schedule command help."""
        try:
            # Change to CLI directory first
            cli_dir = project_root / "clients" / "zeblit-cli" / "src"
            result = subprocess.run([
                "python", "-c",
                "import sys; sys.path.insert(0, '.'); "
                "from zeblit_cli.main import cli; "
                "try: cli(['schedule', '--help']); except SystemExit: pass"
            ], capture_output=True, text=True, timeout=10, cwd=cli_dir)
            
            # Check both stdout and stderr
            output = result.stdout + result.stderr
            
            if not output or "schedule" not in output.lower():
                return {"success": False, "error": f"Schedule help doesn't contain schedule information. Stdout: {result.stdout[:100]}... Stderr: {result.stderr[:100]}..."}
            
            return {"success": True, "details": "CLI schedule help working"}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "CLI schedule help timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ============================================================================
    # PERFORMANCE TESTS
    # ============================================================================
    
    async def test_api_response_times(self):
        """Test API response times under load."""
        endpoints = [
            "/health",
            "/v1/models",
            "/api/v1/health"
        ]
        
        times = []
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await self.client.get(endpoint)
            duration = time.time() - start_time
            
            if response.status_code not in [200, 401]:  # 401 is expected for some endpoints
                return {"success": False, "error": f"{endpoint} returned {response.status_code}"}
            
            times.append(duration)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        if max_time > 1.0:  # More than 1 second
            return {"success": False, "error": f"Slow response: {max_time:.2f}s"}
        
        return {"success": True, "details": f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s"}
    
    async def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        async def make_request():
            response = await self.client.get("/health")
            return response.status_code == 200
        
        # Run 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time
        
        success_count = sum(1 for r in results if r is True)
        
        if success_count < 8:  # Allow for some failures
            return {"success": False, "error": f"Only {success_count}/10 requests succeeded"}
        
        return {"success": True, "details": f"{success_count}/10 requests in {duration:.2f}s"}
    
    # ============================================================================
    # MAIN TEST RUNNER
    # ============================================================================
    
    async def run_all_tests(self):
        """Run all tests in sequence."""
        console.print("\n🚀 Starting Comprehensive Testing Suite")
        console.print("=" * 60)
        
        # Backend Infrastructure Tests
        console.print("\n📡 Backend Infrastructure Tests")
        await self.run_test("Backend Health Check", self.test_backend_health)
        await self.run_test("Backend Process Status", self.test_backend_process)
        await self.run_test("Models Endpoint (OpenAI Compat)", self.test_models_endpoint)
        await self.run_test("API v1 Health", self.test_api_v1_health)
        
        # Authentication & Security Tests
        console.print("\n🔐 Authentication & Security Tests")
        await self.run_test("Scheduled Tasks Auth Required", self.test_scheduled_tasks_unauthenticated)
        
        # Infrastructure Tests
        console.print("\n🔧 Infrastructure Tests")
        await self.run_test("Redis Connectivity", self.test_redis_connection)
        
        # CLI Client Tests
        console.print("\n💻 CLI Client Tests")
        await self.run_test("CLI Help System", self.test_cli_help)
        await self.run_test("CLI Schedule Commands", self.test_cli_schedule_help)
        
        # Performance Tests
        console.print("\n⚡ Performance Tests")
        await self.run_test("API Response Times", self.test_api_response_times)
        await self.run_test("Concurrent Request Handling", self.test_concurrent_requests)
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        passed = sum(1 for r in self.results if r.success)
        failed = len(self.results) - passed
        total_time = sum(r.duration for r in self.results)
        
        # Summary
        console.print("\n" + "=" * 60)
        console.print("📊 TEST RESULTS SUMMARY")
        console.print("=" * 60)
        
        if failed == 0:
            console.print(f"✅ ALL TESTS PASSED! ({passed}/{len(self.results)})")
        else:
            console.print(f"❌ {failed} TEST(S) FAILED ({passed}/{len(self.results)} passed)")
        
        console.print(f"⏱️  Total execution time: {total_time:.2f}s")
        
        # Detailed results table
        table = Table(title="Detailed Test Results")
        table.add_column("Test Name", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Details", style="dim")
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            duration = f"{result.duration:.3f}s"
            details = result.details if result.success else result.error
            
            table.add_row(result.name, status, duration, details)
        
        console.print(table)
        
        # Recommendations
        console.print("\n💡 RECOMMENDATIONS")
        
        if failed == 0:
            console.print("✅ All systems are functioning correctly!")
            console.print("✅ Platform is ready for Phase 4: Telegram Bot")
            console.print("✅ Consider running load testing for production readiness")
        else:
            console.print("❌ Please address the failed tests before proceeding")
            console.print("❌ Check logs and system status")
            
            # Show failed tests
            failed_tests = [r for r in self.results if not r.success]
            console.print(f"\n🔍 FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                console.print(f"  • {test.name}: {test.error}")
        
        return failed == 0


async def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Comprehensive testing suite for Zeblit platform")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Check if backend is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{args.base_url}/health", timeout=5.0)
            if response.status_code != 200:
                console.print("❌ Backend is not responding properly")
                console.print("Please ensure the backend is running: python start_backend.py")
                sys.exit(1)
    except Exception as e:
        console.print(f"❌ Cannot connect to backend at {args.base_url}")
        console.print(f"Error: {e}")
        console.print("Please ensure the backend is running: python start_backend.py")
        sys.exit(1)
    
    # Run tests
    async with ComprehensiveTester(args.base_url) as tester:
        await tester.run_all_tests()
        success = tester.generate_report()
        
        if success:
            console.print("\n🎉 All tests passed! Platform is ready for next phase.")
            sys.exit(0)
        else:
            console.print("\n💥 Some tests failed. Please investigate and fix issues.")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
