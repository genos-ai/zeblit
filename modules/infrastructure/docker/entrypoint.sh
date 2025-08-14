#!/bin/bash
# Entrypoint script for AI Development Platform containers

# Set up workspace permissions
sudo chown -R developer:developer /workspace 2>/dev/null || true

# Create common directories
mkdir -p /workspace/{src,tests,docs,config}

# Initialize git if not already initialized
if [ ! -d "/workspace/.git" ]; then
    git init /workspace
    git config --global user.email "developer@ai-platform.local"
    git config --global user.name "AI Developer"
    git config --global init.defaultBranch main
fi

# Create a welcome file if workspace is empty
if [ -z "$(ls -A /workspace)" ]; then
    cat > /workspace/README.md << EOF
# Welcome to AI Development Platform

Your development environment is ready! 🚀

## Quick Start

### Python Project
\`\`\`bash
# Create a new FastAPI app
pip install fastapi uvicorn
echo "from fastapi import FastAPI; app = FastAPI(); @app.get('/'); def read_root(): return {'Hello': 'World'}" > main.py
uvicorn main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### Node.js Project
\`\`\`bash
# Create a new Vite + React app
npm create vite@latest my-app -- --template react-ts
cd my-app
npm install
npm run dev -- --host 0.0.0.0
\`\`\`

## Available Tools
- Python 3.12 with FastAPI, Django, Flask
- Node.js 20.x with TypeScript, Vite, React
- Git, curl, wget, vim, nano
- And much more!

## Environment Variables
- PROJECT_ID: $PROJECT_ID
- USER_ID: $USER_ID
- WORKSPACE: $WORKSPACE

Happy coding! 💻
EOF
fi

# Print welcome message
echo "🚀 AI Development Platform Container Started!"
echo "📁 Workspace: /workspace"
echo "👤 User: $(whoami)"
echo "🐍 Python: $(python --version)"
echo "📦 Node.js: $(node --version)"
echo "💻 Ready for development!"
echo ""

# Execute the command passed to the container
exec "$@" 