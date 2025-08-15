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

# Access development tools
# Adminer (Database UI): http://localhost:8080
# Redis Commander: http://localhost:8081
```

### Testing Commands

#### Backend Testing
```bash
# Run tests with specific markers
pytest modules/backend/tests -m unit -v
pytest modules/backend/tests -m integration -v
pytest modules/backend/tests -m "not slow" -v

# Run tests with detailed output
pytest modules/backend/tests -vv

# Run tests in parallel (install pytest-xdist first)
pytest modules/backend/tests -n auto
```

#### Frontend E2E Testing
```bash
cd modules/frontend

# Install Playwright browsers
bunx playwright install

# Run E2E tests with UI mode
bun run test:e2e:ui

# Run specific test file
bunx playwright test e2e/auth.spec.ts

# Run tests in headed mode
bunx playwright test --headed
```

### Security and Load Testing
```bash
# Security scanning for secrets
python -m modules.backend.services.file_security scan <file_path>

# Load testing with Locust
locust -f scripts/load_test.py --host http://localhost:8000
locust -f scripts/load_test.py --host http://localhost:8000 --users 100 --spawn-rate 10

# Backup production data
./scripts/backup/backup.sh
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
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection (defaults to localhost:6379)
- `ANTHROPIC_API_KEY`: Claude API access
- `JWT_SECRET`: Token signing key (generate with: `openssl rand -hex 32`)
- `ANTHROPIC_MODEL`: AI model selection (claude-4-opus-20250514 or claude-4-5-sonnet-20241022)
- `MAX_CONTAINERS_PER_USER`: Container limit (default: 5)
- `CONTAINER_MEMORY_LIMIT`: Memory per container (default: 2g)
- `USER_DAILY_COST_LIMIT`: Daily AI usage limit (default: $10.00)

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
2. Docker SDK integration (OrbStack has been replaced with standard Docker)
3. Each container gets unique port range (30000+)
4. Containers auto-cleanup after 1 hour idle

When handling file uploads or user content:
1. Use `FileUtils` for path validation and sanitization
2. Run `FileSecurityScanner` to detect secrets before processing
3. Check file extensions against blocked list
4. Validate file sizes against configured limits