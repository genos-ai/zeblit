# Zeblit CLI Quick Start

This guide demonstrates the basic workflow with the Zeblit CLI client.

## Installation

```bash
# Install the CLI
cd clients/zeblit-cli
pip install -e .
```

## Authentication

```bash
# First time: authenticate with your API key
zeblit auth login

# Check status
zeblit auth status
```

## Create Your First Project

```bash
# Create a new project
zeblit create my-first-app --template=python-web

# List your projects
zeblit list

# Check project status
zeblit status
```

## Chat with Agents

```bash
# Ask the Dev Manager for help
zeblit chat "What should I build first?"

# Get specific advice
zeblit chat "Create a simple REST API with FastAPI"

# Direct communication with specific agents
zeblit chat --agent Engineer "How do I structure my code?"

# View chat history
zeblit chat history
```

## Container Management

```bash
# Start the development environment
zeblit container start

# Check container status
zeblit container status

# Execute commands
zeblit run "python --version"
zeblit run "pip install fastapi uvicorn"

# View logs
zeblit logs
```

## File Management

```bash
# View project structure
zeblit files tree

# List files in a directory
zeblit files list /workspace

# Upload local files
zeblit files upload ./app.py /workspace/app.py
zeblit files upload ./requirements.txt /workspace/

# Download files
zeblit files download /workspace/output.log ./

# Edit files (download, edit, upload)
zeblit files edit /workspace/main.py
```

## Real-time Console

```bash
# Stream live output from the container
zeblit console

# View console history
zeblit console history

# In another terminal, run commands to see live output
zeblit run "python app.py"
```

## Example Workflow

Here's a complete example workflow:

```bash
# 1. Setup
zeblit auth login
zeblit create todo-api --template=python-web

# 2. Development
zeblit chat "Create a FastAPI todo application with SQLite"
zeblit container start
zeblit run "pip install -r requirements.txt"

# 3. Real-time development
# Terminal 1: Live console
zeblit console

# Terminal 2: Development commands
zeblit run "python main.py"
zeblit chat "Add user authentication to the API"
zeblit files tree

# 4. File management
zeblit files download /workspace/main.py ./
# Edit locally, then:
zeblit files upload ./main.py /workspace/

# 5. Testing
zeblit run "pytest tests/"
zeblit chat "The tests are failing, can you help fix them?"
```

## Key Benefits

1. **Backend-First**: All logic handled by Zeblit backend
2. **Thin Client**: CLI just translates commands to API calls
3. **Real-time**: Live streaming of output and agent responses
4. **Multi-Agent**: Chat with specialized AI agents
5. **Isolated Environments**: Each project runs in its own container
6. **Cross-Platform**: Works on macOS, Linux, Windows

## Next Steps

- Try different project templates
- Explore direct agent communication
- Set up scheduled tasks (coming soon)
- Build your own applications with Zeblit's help!

The CLI demonstrates how easy it is to build clients for the Zeblit platform when following a backend-first architecture.
