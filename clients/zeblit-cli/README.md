# Zeblit CLI Client

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Overview

The Zeblit CLI is a lightweight command-line client for the Zeblit AI Development Platform. It demonstrates the backend-first architecture by consuming the unified API with zero business logic in the client.

## Features

- **Authentication**: API key-based authentication
- **Project Management**: Create, list, select, and manage projects
- **Agent Interaction**: Chat with AI agents through the DevManager
- **File Operations**: Upload, download, and manage project files
- **Real-time Console**: Stream container output and logs
- **Container Management**: Execute commands in isolated environments
- **Scheduling**: Manage scheduled tasks (future)

## Installation

```bash
# Install the CLI
pip install -e .

# Or install from requirements
pip install -r requirements.txt
```

## Quick Start

```bash
# Authenticate with your API key
zeblit auth login

# Create a new project
zeblit create my-app --template=python-web

# Chat with the Dev Manager
zeblit chat "Build a todo API with FastAPI"

# Execute commands in the project container
zeblit run "python main.py"

# View real-time logs
zeblit console

# Upload files
zeblit files upload ./local-file.py /workspace/file.py

# Download files
zeblit files download /workspace/output.log ./output.log
```

## Commands Reference

### Authentication
- `zeblit auth login` - Authenticate with API key
- `zeblit auth logout` - Clear stored credentials
- `zeblit auth status` - Check authentication status

### Project Management
- `zeblit create <name>` - Create a new project
- `zeblit list` - List your projects
- `zeblit use <project-id>` - Set active project
- `zeblit delete <project-id>` - Delete a project
- `zeblit status` - Show current project status

### Development
- `zeblit chat <message>` - Send message to Dev Manager
- `zeblit run <command>` - Execute command in container
- `zeblit console` - Stream real-time console output
- `zeblit logs` - View recent logs

### File Management
- `zeblit files list [path]` - List files in project
- `zeblit files tree` - Show complete file tree
- `zeblit files upload <local> <remote>` - Upload file
- `zeblit files download <remote> <local>` - Download file
- `zeblit files edit <path>` - Edit file (opens in $EDITOR)

### Container Management
- `zeblit container start` - Start project container
- `zeblit container stop` - Stop project container
- `zeblit container status` - Check container status

## Configuration

The CLI stores configuration in `~/.zeblit/config.json`:

```json
{
  "api_base_url": "http://localhost:8000/api/v1",
  "api_key": "zbl_...",
  "current_project_id": "uuid",
  "preferences": {
    "default_editor": "vim",
    "color_output": true,
    "auto_sync_files": true
  }
}
```

## Architecture

The CLI is designed as a **thin client** with these principles:

1. **Zero Business Logic**: All logic handled by backend API
2. **Stateless**: Only stores API keys and current project
3. **Real-time**: Uses WebSockets for live updates
4. **Offline Capable**: Caches recent data when possible
5. **Cross-Platform**: Works on macOS, Linux, Windows

## Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 src/
black src/
mypy src/

# Build distribution
python setup.py sdist bdist_wheel
```

## Backend Compatibility

This CLI is compatible with Zeblit Backend API v1.0+. It uses:

- **Authentication**: API Keys with Bearer token format
- **Real-time**: WebSocket connections for console streaming
- **File Transfer**: REST API for file upload/download
- **Agent Communication**: Unified chat API with DevManager routing

## Error Handling

The CLI provides user-friendly error messages and suggests solutions:

```bash
$ zeblit chat "hello"
Error: No active project selected
Suggestion: Run 'zeblit use <project-id>' or 'zeblit create <name>' first

$ zeblit run "python app.py"
Error: Container not running
Suggestion: Run 'zeblit container start' first
```

## New Features (Phase 3 Complete!)

### 🚀 Enhanced Performance
- **Progress Bars**: Beautiful progress indicators for file uploads and long operations
- **Offline Caching**: Smart caching with configurable TTL for improved performance
- **Tab Completion**: Full shell completion for commands, project IDs, and file paths

### 🔧 Developer Experience
- **Better Error Handling**: User-friendly error messages with actionable suggestions
- **Real-time Console**: WebSocket-based console streaming with live updates
- **Cache Management**: Built-in cache statistics and management commands

### 📊 Additional Commands

```bash
# Enhanced console streaming
zeblit console stream --project <id>
zeblit console history --lines 200
zeblit console clear

# Cache management
zeblit cache --stats
zeblit cache --clear
zeblit cache --cleanup

# Shell completion setup
zeblit setup-completion

# Enhanced project info
zeblit project info <project-id>

# API key management
zeblit auth keys list
zeblit auth keys create --name "laptop" --expires-in-days 30
zeblit auth keys revoke <key-id>
Suggestion: Run 'zeblit container start' first
```

## Examples

### Complete Workflow
```bash
# Start fresh
zeblit auth login
zeblit create my-todo-app --template=python-web
zeblit chat "Create a FastAPI todo application with SQLite database"
zeblit run "pip install -r requirements.txt"
zeblit run "python main.py"
zeblit console  # Watch the app start
```

### File Management
```bash
# Upload local development files
zeblit files upload ./src/ /workspace/src/
zeblit files upload ./requirements.txt /workspace/
zeblit files tree  # Verify upload

# Make changes and download results
zeblit chat "Add user authentication to the todo app"
zeblit files download /workspace/src/ ./updated-src/
```

### Container Management
```bash
# Check what's running
zeblit container status
zeblit logs

# Restart fresh environment
zeblit container stop
zeblit container start
zeblit run "python --version"  # Verify environment
```

This CLI demonstrates how easy it is to build clients for the Zeblit platform when using a backend-first architecture!
