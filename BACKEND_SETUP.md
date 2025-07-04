# Backend Setup Guide

## Requirements Files

This project includes three requirements files:

1. **`requirements.txt`** - All dependencies (development + production)
2. **`requirements-dev.txt`** - Development-only dependencies (includes requirements.txt)
3. **`requirements-prod.txt`** - Production-only dependencies

## Python Version

This project requires **Python 3.11+**

## Installation

### For Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install all development dependencies
pip install -r requirements-dev.txt
```

### For Production

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install production dependencies only
pip install -r requirements-prod.txt
```

## Key Dependencies

### Core Framework
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **SQLAlchemy 2.0** - ORM with async support
- **Pydantic** - Data validation

### AI/LLM Integrations
- **Anthropic** - Claude API integration
- **OpenAI** - GPT models (fallback)
- **Google GenerativeAI** - Gemini models (fallback)

### Infrastructure
- **Redis** - Caching, pub/sub, task queues
- **Celery** - Background task processing
- **PostgreSQL** - Primary database (via asyncpg)

### Development Tools
- **pytest** - Testing framework
- **black** - Code formatting
- **mypy** - Type checking
- **pre-commit** - Git hooks

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/ai_dev_platform

# Redis
REDIS_URL=redis://localhost:6379

# Security
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# AI/LLM APIs
ANTHROPIC_API_KEY=your-anthropic-api-key
OPENAI_API_KEY=your-openai-api-key
GOOGLE_API_KEY=your-google-api-key

# Email
RESEND_API_KEY=your-resend-api-key

# Container Management
DOCKER_HOST=unix:///var/run/docker.sock
ORBSTACK_SOCKET=/var/run/orbstack.sock

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Set up database
alembic upgrade head

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Format code
black .

# Type check
mypy .
```

## Docker Support

For containerized development:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
``` 