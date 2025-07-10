#!/bin/bash

# Zeblit Frontend Startup Script
# This script ensures the frontend starts with proper logging

echo "Starting Zeblit Frontend..."
echo "Logs will be written to:"
echo "  - Build logs: logs/frontend/build.log"
echo "  - Runtime logs: logs/frontend/dev-server.log"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Change to the frontend directory
cd "$SCRIPT_DIR/frontend"

# Create log directories if they don't exist
mkdir -p "$SCRIPT_DIR/logs/frontend"

# Kill any existing frontend dev server
echo "Stopping any existing frontend processes..."
pkill -f "vite" 2>/dev/null

# Wait a moment for processes to clean up
sleep 2

# Try to find bun in multiple locations
BUN_PATH=""
if [ -f "$HOME/.bun/bin/bun" ]; then
    BUN_PATH="$HOME/.bun/bin/bun"
elif command -v bun >/dev/null 2>&1; then
    BUN_PATH="bun"
elif [ -f "/usr/local/bin/bun" ]; then
    BUN_PATH="/usr/local/bin/bun"
fi

# Check if bun is available
if [ -z "$BUN_PATH" ]; then
    echo "Error: Bun is not installed or not found"
    echo "Please install Bun first: curl -fsSL https://bun.sh/install | bash"
    echo "Or ensure it's in your PATH"
    exit 1
fi

echo "Using Bun version: $($BUN_PATH --version)"

# Set environment variables
export VITE_LOG_LEVEL=info

# Start the frontend dev server with logging
echo "Starting frontend development server..."
echo "Server will be available at: http://localhost:5173"
echo ""

# Run the dev server and capture all output
$BUN_PATH run dev 2>&1 | while IFS= read -r line; do
    # Print to console
    echo "$line"
    
    # Also append to log file with timestamp
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line" >> "$SCRIPT_DIR/logs/frontend/dev-server.log"
done

# Note: The above will capture all output including:
# - Vite build messages
# - HMR (Hot Module Replacement) updates
# - Error messages
# - Network requests (if Vite is configured for it) 