#!/bin/bash

# Zeblit Backend Startup Script
# This script ensures the backend starts with proper logging configuration
#
# Usage: ./start_backend.sh [LOG_LEVEL]
# Examples:
#   ./start_backend.sh WARNING    # Only warnings and errors
#   ./start_backend.sh ERROR      # Only errors
#   ./start_backend.sh DEBUG      # All debug information
#   ./start_backend.sh            # Uses INFO (default)

# Accept log level as first argument
if [ $# -gt 0 ]; then
    LOG_LEVEL="$1"
    echo "Using command line log level: $LOG_LEVEL"
fi

echo "Starting Zeblit Backend..."
echo "Logs will be written to:"
echo "  - Main logs: logs/backend/"
echo "  - Error logs: logs/errors/"
echo "  - Daily logs: logs/daily/"
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")"

# Create log directories if they don't exist
mkdir -p logs/backend logs/errors logs/daily logs/archive

# Kill any existing backend processes
echo "Stopping any existing backend processes..."
pkill -f "uvicorn modules.backend.main:app" 2>/dev/null

# Wait a moment for processes to clean up
sleep 2

# Use conda environment Python explicitly
PYTHON_EXEC="/opt/anaconda3/envs/zeblit/bin/python"

# Verify Python path
echo "Using Python: $PYTHON_EXEC"

# Export environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export ENVIRONMENT="${ENVIRONMENT:-development}"

# Convert log level to lowercase using tr (more portable)
LOG_LEVEL_LOWER=$(echo "$LOG_LEVEL" | tr '[:upper:]' '[:lower:]')

# Start the backend
echo "Starting backend server with log level: $LOG_LEVEL"
$PYTHON_EXEC -m uvicorn modules.backend.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level "$LOG_LEVEL_LOWER" \
    2>&1 | tee -a logs/backend/startup-$(date +%Y-%m-%d).log

# The tee command will:
# 1. Display output in the terminal
# 2. Also append to a startup log file 