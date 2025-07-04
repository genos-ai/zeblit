# AI Development Platform (Zeblit)

A browser-based AI development platform that enables users to build applications through natural language interactions with a team of specialized AI agents.

## 🚀 Overview

This platform provides a complete AI-powered development team in your browser:
- **6 Specialized AI Agents** working collaboratively
- **Isolated Development Containers** for each user
- **Real-time Code Generation** with live preview
- **Natural Language to Application** workflow

## 🤖 The AI Agent Team

1. **Development Manager** - Orchestrates and coordinates all agents
2. **Product Manager** - Translates requirements into user stories
3. **Data Analyst** - Designs database schemas and analytics
4. **Senior Engineer** - Writes core application code
5. **Architect** - Makes system design decisions
6. **Platform Engineer** - Handles deployment and infrastructure

## 🛠️ Tech Stack

### Frontend
- React 18.3.1 + TypeScript 5.6.3
- Vite build tool
- Monaco Editor (VS Code's editor)
- Tailwind CSS + shadcn/ui
- TanStack Query for state management

### Backend
- FastAPI (Python 3.11+)
- PostgreSQL 16 + SQLAlchemy
- Redis for real-time features
- Celery for background tasks

### AI & Container Platform
- Anthropic Claude (primary LLM)
- OrbStack for container management
- Docker → Kubernetes migration path

## 📚 Documentation

All documentation is in the `docs/` folder, numbered in recommended reading order:

1. `1. architecture-summary.md` - Start here for overview
2. `2. dev-platform-requirements.md` - Detailed requirements
3. `3. implementation-plan.md` - Step-by-step roadmap
4. [... and more]

## 🚦 Getting Started

### Prerequisites
- Node.js 20.18.1 LTS
- Python 3.11+
- PostgreSQL 16
- Redis 7+
- OrbStack (macOS) or Docker

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/zeblit.git
cd zeblit
```

2. Set up the backend:
```bash
cd src/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../../requirements-dev.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Configure environment variables:
```bash
# Copy example env files
cp env.example src/backend/.env
cp frontend/.env.example frontend/.env

# Edit with your API keys and configuration
```

5. Start the development servers:
```bash
# Terminal 1: Backend
cd src/backend
uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Redis
redis-server

# Terminal 4: PostgreSQL (if not running)
# Follow PostgreSQL setup for your OS
```

## 🏗️ Project Structure

```
zeblit/
├── src/
│   └── backend/      # FastAPI backend services
├── frontend/         # React frontend application
├── infrastructure/   # Docker and Kubernetes configs
├── shared/          # Shared types and contracts
├── docs/            # Comprehensive documentation
└── .cursorrules     # AI coding assistant rules
```

## 🔐 Security

- JWT-based authentication
- Container isolation for user code
- Comprehensive audit logging
- Input validation and sanitization
- Rate limiting on API endpoints

## 📊 Development Workflow

1. User describes what they want to build
2. Development Manager analyzes and delegates tasks
3. Agents work in parallel on separate Git branches
4. Real-time updates stream to the UI
5. Live preview updates as code is generated
6. Development Manager coordinates final merge

## 🧪 Testing

We follow Test-Driven Development (TDD) with:
- Unit tests (75% of tests)
- Integration tests (20%)
- End-to-end tests (5%)
- Target: >80% code coverage

Run tests:
```bash
# Backend tests
cd src/backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📈 Performance

- Redis for all real-time operations
- Smart LLM model selection (Sonnet for routine, Opus for complex)
- Container auto-sleep after 30 minutes
- Efficient WebSocket communication
- Database query optimization

## 🚀 Deployment

The platform follows a progressive deployment strategy:
1. **Phase 1**: Docker Compose (development)
2. **Phase 2**: Hybrid Docker/Kubernetes
3. **Phase 3**: Full Kubernetes
4. **Production**: Azure Kubernetes Service (AKS)

## 🤝 Contributing

Please read our contributing guidelines and follow the coding standards in `.cursorrules`.

## 📄 License

[License Type] - See LICENSE file for details

## 🔗 Links

- [Documentation](./docs)
- [API Specification](./shared/api-spec.yaml)
- [Architecture Diagrams](./docs/8.%20tech-architecture-diagram.mermaid)

---

Built with ❤️ by the Zeblit team 