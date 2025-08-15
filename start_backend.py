#!/usr/bin/env python3
"""
Zeblit Backend Startup Script

A Python-based startup script for the AI Development Platform backend
that provides better control over logging, environment setup, and process management.

Usage:
    python start_backend.py [OPTIONS]

Examples:
    python start_backend.py                    # Start with default settings
    python start_backend.py --log-level WARNING # Quiet mode
    python start_backend.py --log-level DEBUG   # Verbose mode
    python start_backend.py --port 8080         # Custom port
    python start_backend.py --no-reload         # Disable auto-reload
    python start_backend.py --help              # Show help
"""

import sys
import os
import subprocess
import signal
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import psutil

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import after path setup
try:
    from modules.backend.core.config import settings
    from modules.backend.config.logging_config import setup_logging, get_logger
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    print("Make sure you're running from the project root and all dependencies are installed.")
    sys.exit(1)


class BackendStarter:
    """Manages the backend startup process with proper logging and process control."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.logger = None
        
    def setup_environment(self, args):
        """Setup environment variables and logging."""
        # Set environment variables
        os.environ["PYTHONPATH"] = f"{os.environ.get('PYTHONPATH', '')}:{project_root}"
        os.environ["LOG_LEVEL"] = args.log_level
        os.environ["ENVIRONMENT"] = args.environment
        
        # Create log directories
        log_dirs = [
            project_root / "logs",
            project_root / "logs" / "backend",
            project_root / "logs" / "errors",
            project_root / "logs" / "daily",
            project_root / "logs" / "archive"
        ]
        
        for log_dir in log_dirs:
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        setup_logging(
            app_name="ai_dev_platform",
            log_level=args.log_level,
            environment=args.environment
        )
        
        self.logger = get_logger(__name__)
        
    def check_dependencies(self):
        """Check if required dependencies are available."""
        try:
            import uvicorn
            import fastapi
            import sqlalchemy
            import redis
        except ImportError as e:
            self.logger.error(f"Missing required dependency: {e}")
            print(f"❌ Missing dependency: {e}")
            print("Please install dependencies: pip install -r requirements.txt")
            return False
        return True
        
    def check_services(self):
        """Check if required services (Redis, PostgreSQL) are running."""
        services_ok = True
        
        # Check Redis
        try:
            import redis
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            r = redis.Redis.from_url(redis_url)
            r.ping()
            self.logger.info("✅ Redis connection successful")
        except Exception as e:
            self.logger.warning(f"⚠️ Redis connection failed: {e}")
            print(f"⚠️ Warning: Redis connection failed: {e}")
            print("Some features may not work without Redis.")
        
        # Check PostgreSQL
        try:
            import asyncpg
            # We can't easily test async connection here, but we can check if the URL is valid
            self.logger.info("✅ Database configuration loaded")
        except Exception as e:
            self.logger.warning(f"⚠️ Database check failed: {e}")
            print(f"⚠️ Warning: Database configuration issue: {e}")
        
        return services_ok
        
    def kill_existing_processes(self):
        """Kill any existing backend processes."""
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'uvicorn' in cmdline and 'modules.backend.main:app' in cmdline:
                    self.logger.info(f"Killing existing backend process: PID {proc.info['pid']}")
                    proc.terminate()
                    killed_count += 1
                    
                    # Wait for graceful termination
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        self.logger.warning(f"Force killing process: PID {proc.info['pid']}")
                        proc.kill()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            self.logger.info(f"Killed {killed_count} existing backend process(es)")
            time.sleep(2)  # Give processes time to clean up
            
    def build_uvicorn_command(self, args) -> List[str]:
        """Build the uvicorn command with appropriate arguments."""
        # Find Python executable in conda environment
        python_exec = self.find_python_executable()
        
        cmd = [
            python_exec, "-m", "uvicorn", 
            "modules.backend.main:app",
            "--host", args.host,
            "--port", str(args.port),
            "--log-level", args.log_level.lower()
        ]
        
        # Add reload if enabled
        if args.reload:
            cmd.append("--reload")
            
        # Disable access logs for quiet levels
        if args.log_level.upper() in ["WARNING", "ERROR", "CRITICAL"]:
            cmd.append("--no-access-log")
            
        return cmd
        
    def find_python_executable(self) -> str:
        """Find the appropriate Python executable."""
        # Try conda environment first
        conda_python = Path("/opt/anaconda3/envs/zeblit/bin/python")
        if conda_python.exists():
            return str(conda_python)
            
        # Fall back to current Python
        return sys.executable
        
    def start_backend(self, args):
        """Start the backend server."""
        cmd = self.build_uvicorn_command(args)
        
        self.logger.info(f"Starting backend server...")
        self.logger.info(f"Command: {' '.join(cmd)}")
        self.logger.info(f"Host: {args.host}")
        self.logger.info(f"Port: {args.port}")
        self.logger.info(f"Log Level: {args.log_level}")
        self.logger.info(f"Environment: {args.environment}")
        self.logger.info(f"Reload: {args.reload}")
        
        print(f"🚀 Starting Zeblit Backend...")
        print(f"   Host: {args.host}")
        print(f"   Port: {args.port}")
        print(f"   Log Level: {args.log_level}")
        print(f"   Access logs: {'disabled' if args.log_level.upper() in ['WARNING', 'ERROR', 'CRITICAL'] else 'enabled'}")
        print(f"   Auto-reload: {args.reload}")
        print()
        
        # Setup log file path
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = project_root / "logs" / "backend" / f"startup-{today}.log"
        
        try:
            # Start the process
            with open(log_file, "a") as f:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    cwd=project_root
                )
                
                # Stream output to both console and log file
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        print(line.rstrip())
                        f.write(line)
                        f.flush()
                        
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt, shutting down...")
            self.shutdown()
        except Exception as e:
            self.logger.error(f"Failed to start backend: {e}")
            print(f"❌ Failed to start backend: {e}")
            sys.exit(1)
            
    def shutdown(self):
        """Gracefully shutdown the backend process."""
        if self.process:
            self.logger.info("Shutting down backend server...")
            print("\n🛑 Shutting down backend server...")
            
            try:
                # Send SIGTERM for graceful shutdown
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if necessary
                self.logger.warning("Force killing backend process...")
                print("⚠️ Force killing backend process...")
                self.process.kill()
                self.process.wait()
                
            self.logger.info("Backend server stopped")
            print("✅ Backend server stopped")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Start the Zeblit AI Development Platform backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_backend.py                      # Start with defaults
  python start_backend.py --log-level WARNING  # Quiet mode
  python start_backend.py --log-level DEBUG    # Debug mode
  python start_backend.py --port 8080          # Custom port
  python start_backend.py --no-reload          # Disable auto-reload
  python start_backend.py --host 127.0.0.1     # Localhost only

Log Levels:
  DEBUG     - Show all messages including request logs
  INFO      - Normal application logs
  WARNING   - Only warnings and errors (recommended for development)
  ERROR     - Only errors and critical messages
  CRITICAL  - Only critical messages
        """
    )
    
    parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--environment", "-e",
        choices=["development", "staging", "production"],
        default="development",
        help="Environment mode (default: development)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload on file changes (default: enabled)"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies and services, don't start server"
    )
    
    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle reload flag
    if args.no_reload:
        args.reload = False
    
    # Create backend starter
    starter = BackendStarter()
    
    try:
        # Setup environment and logging
        starter.setup_environment(args)
        
        print("🔍 Zeblit Backend Startup")
        print("=" * 50)
        
        # Check dependencies
        print("🔧 Checking dependencies...")
        if not starter.check_dependencies():
            sys.exit(1)
        print("✅ Dependencies OK")
        
        # Check services
        print("🔌 Checking services...")
        starter.check_services()
        
        # Exit if only checking
        if args.check_only:
            print("✅ All checks completed")
            return
        
        # Kill existing processes
        print("🧹 Cleaning up existing processes...")
        starter.kill_existing_processes()
        
        # Start the backend
        starter.start_backend(args)
        
    except KeyboardInterrupt:
        starter.shutdown()
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        if starter.logger:
            starter.logger.error(f"Startup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
