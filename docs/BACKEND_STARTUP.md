# Backend Startup Guide

The Zeblit AI Development Platform provides both shell and Python startup scripts for maximum flexibility.

## Python Startup Script (Recommended)

### Quick Start

```bash
# Start with clean output (recommended for development)
python start_backend.py --log-level WARNING

# Start with normal logging
python start_backend.py

# Start with full debug output
python start_backend.py --log-level DEBUG
```

### Features

✅ **Smart Dependency Checking** - Validates all required packages before startup  
✅ **Service Health Checks** - Tests Redis and PostgreSQL connections  
✅ **Process Management** - Automatically kills existing backend processes  
✅ **Intelligent Logging** - Configures appropriate log levels and output  
✅ **Environment Setup** - Properly configures Python path and environment variables  
✅ **Graceful Shutdown** - Handles Ctrl+C with proper cleanup  

### Command Line Options

```bash
python start_backend.py [OPTIONS]

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}  Set logging level
  --host HOST                                      Host to bind (default: 0.0.0.0)
  --port PORT                                      Port to bind (default: 8000)
  --environment {development,staging,production}   Environment mode
  --reload / --no-reload                          Auto-reload on changes
  --check-only                                    Only check deps, don't start
  --help                                          Show help
```

### Log Levels Explained

| Level | Output | Use Case |
|-------|--------|----------|
| `DEBUG` | All messages including request logs | Deep debugging |
| `INFO` | Normal application logs | Default development |
| `WARNING` | Only warnings and errors | **Recommended for daily dev** |
| `ERROR` | Only errors and critical | Production monitoring |
| `CRITICAL` | Only critical messages | Emergency situations |

### Examples

```bash
# Daily development (clean output)
python start_backend.py --log-level WARNING

# Custom port
python start_backend.py --port 8080

# Production-like mode
python start_backend.py --environment production --no-reload

# Check everything without starting
python start_backend.py --check-only

# Full debugging
python start_backend.py --log-level DEBUG

# Localhost only
python start_backend.py --host 127.0.0.1
```

## Shell Script (Legacy)

The original shell script is still available:

```bash
# Quick start
./start_backend.sh WARNING

# Or with environment variable
LOG_LEVEL=WARNING ./start_backend.sh
```

## Recommended Workflow

1. **Daily Development**: `python start_backend.py --log-level WARNING`
2. **Debugging Issues**: `python start_backend.py --log-level DEBUG`  
3. **Testing Changes**: `python start_backend.py --log-level INFO`
4. **Health Check**: `python start_backend.py --check-only`

## Output Examples

### WARNING Level (Recommended)
```
🚀 Starting Zeblit Backend...
   Host: 0.0.0.0
   Port: 8000
   Log Level: WARNING
   Access logs: disabled
   Auto-reload: True

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### DEBUG Level (Verbose)
```
🚀 Starting Zeblit Backend...
   [Same as above plus all request logs]

2025-08-15T04:00:04.656062Z [debug] request_started client_host=127.0.0.1 method=GET path=/health
2025-08-15T04:00:04.656062Z [debug] request_completed duration_ms=1.23 status_code=200
```

## Troubleshooting

### Common Issues

1. **"Missing dependency"** - Run `pip install -r requirements.txt`
2. **"Redis connection failed"** - Start Redis: `brew services start redis`
3. **"Database connection failed"** - Check PostgreSQL is running
4. **"Port already in use"** - Script automatically kills existing processes

### Health Check

```bash
# Verify everything is working
python start_backend.py --check-only
```

This will check dependencies and services without starting the server.
