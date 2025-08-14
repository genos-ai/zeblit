# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zeblit is an AI-powered development platform similar to Replit where users build applications through natural language interactions with 6 specialized AI agents. Each user gets an isolated development container with full IDE capabilities.

## Development Commands

### Backend (Python FastAPI)
```bash
# Start backend with logging
./start_backend.sh
# Or manually:
python -m uvicorn modules.backend.main:app --reload --host 0.0.0.0 --port 8000

# Run tests with coverage
pytest modules/backend/tests -v --cov=modules.backend --cov-fail-under=80

# Run specific test
pytest modules/backend/tests/test_auth.py::TestAuth::test_login -v

# Database migrations
cd modules/backend
alembic upgrade head        # Apply migrations
alembic revision --autogenerate -m "description"  # Create new migration

# Seed initial data
python -m modules.backend.seed_data

# Linting and formatting
black modules/backend/      # Format code
flake8 modules/backend/     # Lint code
mypy modules/backend/       # Type checking
```

### Frontend (React TypeScript)
```bash
# Start frontend with Bun
./start_frontend_bun.sh
# Or manually:
cd modules/frontend
bun install
bun run dev

# Build for production
bun run build

# Linting and type checking
bun run lint
bun run build  # TypeScript check happens during build

# E2E tests
bun run test:e2e           # Run all E2E tests
bun run test:e2e:ui        # Open Playwright UI
bun run test:e2e:debug     # Debug mode
```

### Docker Development
```bash
# Start all services (from modules/infrastructure/docker/)
docker-compose up -d

# Start with dev profile (includes Adminer, Redis Commander)
docker-compose --profile dev up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend-dev

# Reset everything
docker-compose down -v  # Remove volumes too
```

## Architecture Overview

### Directory Structure After Reorganization
```
zeblit/
├── modules/
│   ├── backend/          # Python FastAPI backend
│   │   ├── agents/       # 6 AI agents (dev_manager, product_manager, etc.)
│   │   ├── api/v1/       # REST endpoints
│   │   ├── services/     # Business logic layer
│   │   ├── repositories/ # Data access layer
│   │   ├── core/         # Auth, config, database, WebSocket manager
│   │   └── main.py       # FastAPI app entry point
│   ├── frontend/         # React TypeScript frontend
│   │   └── src/
│   │       ├── components/  # UI components (CodeEditor, Terminal, etc.)
│   │       ├── pages/       # Route pages
│   │       └── lib/         # API client, WebSocket client
│   └── infrastructure/   # Docker and Kubernetes configs
├── docs/                 # Comprehensive documentation
└── scripts/              # Utility scripts
```

### Key Architectural Patterns

#### Backend Architecture
- **Layered Architecture**: Controller (API) → Service → Repository → Database
- **Dependency Injection**: FastAPI's `Depends()` for managing dependencies
- **Async Throughout**: All database operations, API calls, and WebSocket handling use async/await
- **WebSocket Manager**: Centralized WebSocket connection management in `core/websocket_manager.py`
- **Redis Pub/Sub**: Agent communication through Redis message bus

#### AI Agent System
Each agent inherits from `BaseAgent` and implements:
```python
async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]
async def collaborate(self, other_agent: str, message: Dict[str, Any])
```

Agents communicate via Redis pub/sub channels:
- `agent:{agent_id}:tasks` - Task queue
- `agent:{agent_id}:messages` - Inter-agent messages
- `project:{project_id}:updates` - Real-time updates

#### Frontend Architecture
- **Context Providers**: AuthContext and WebSocketContext for global state
- **Monaco Editor Integration**: Full VS Code editing experience
- **Real-time Updates**: WebSocket connection for live agent communication
- **API Client**: Axios with interceptors for auth and error handling

### Database Schema
PostgreSQL with these main tables:
- `users` - User accounts with JWT auth
- `projects` - User projects
- `containers` - Docker container instances
- `agents` - AI agent instances
- `conversations` - Agent conversation history
- `tasks` - Agent task queue
- `git_branches` - Git branch tracking per agent

### External Integrations
- **Anthropic Claude API**: Primary LLM (Claude 4 Sonnet/Opus)
- **Docker API**: Container management via Docker SDK
- **GitPython**: Git operations within containers
- **OrbStack**: Development container runtime (macOS)

### WebSocket Event Types
```typescript
// Frontend subscribes to these events
type WebSocketEvent = 
  | { type: 'agent.message', data: AgentMessage }
  | { type: 'agent.status', data: AgentStatus }
  | { type: 'file.update', data: FileUpdate }
  | { type: 'terminal.output', data: TerminalOutput }
  | { type: 'container.status', data: ContainerStatus }
```

### Authentication Flow
1. User registers/logs in → JWT token issued
2. Token stored in localStorage and added to all API requests
3. WebSocket connection authenticated with token in query params
4. Container access validated per user/project

### Testing Strategy
- **Backend**: pytest with 80% minimum coverage, async fixtures
- **Frontend**: Playwright E2E tests for critical user flows
- **Load Testing**: Locust for API performance testing

### Environment Variables
Key variables (see `config/env.example`):
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `ANTHROPIC_API_KEY`: Claude API access
- `JWT_SECRET`: Token signing key
- `ORBSTACK_API_URL`: Container management API

### Common Development Patterns

When adding a new API endpoint:
1. Define Pydantic schema in `schemas/`
2. Create service method in `services/`
3. Add repository method if needed in `repositories/`
4. Create endpoint in `api/v1/endpoints/`
5. Add frontend API client method in `lib/api-client.ts`
6. Update relevant React components

When modifying AI agents:
1. Agents are in `modules/backend/agents/`
2. Each agent has specific prompt templates
3. Test with mock LLM responses first
4. Monitor token usage via `cost_tracking` service

When working with containers:
1. Container service handles lifecycle in `services/container.py`
2. OrbStack client in `core/orbstack_client.py`
3. Each container gets unique port range (30000+)
4. Containers auto-cleanup after 1 hour idle