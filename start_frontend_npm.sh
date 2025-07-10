#!/bin/bash

# Zeblit Frontend Startup Script (npm version)
# This script ensures the frontend starts with proper logging

echo "Starting Zeblit Frontend (using npm)..."
echo "Logs will be written to:"
echo "  - Build logs: logs/frontend/build.log"
echo "  - Runtime logs: logs/frontend/dev-server.log"
echo ""

# Ensure we're in the frontend directory
cd "$(dirname "$0")"

# Create log directories if they don't exist
mkdir -p ../logs/frontend

# Kill any existing frontend dev server
echo "Stopping any existing frontend processes..."
pkill -f "vite" 2>/dev/null

# Wait a moment for processes to clean up
sleep 2

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed or not in PATH"
    echo "Please install Node.js first"
    exit 1
fi

echo "Using npm version: $(npm --version)"
echo "Using node version: $(node --version)"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install 2>&1 | tee -a ../logs/frontend/install.log
fi

# Set environment variables
export VITE_LOG_LEVEL=info

# Start the frontend dev server with logging
echo "Starting frontend development server..."
echo "Server will be available at: http://localhost:5173"
echo ""

# Run the dev server and capture all output
npm run dev 2>&1 | while IFS= read -r line; do
    # Print to console
    echo "$line"
    
    # Also append to log file with timestamp
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $line" >> ../logs/frontend/dev-server.log
done

# Note: The above will capture all output including:
# - Vite build messages
# - HMR (Hot Module Replacement) updates
# - Error messages
# - Network requests (if Vite is configured for it) 