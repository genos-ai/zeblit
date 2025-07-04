# AI Development Platform - Project Status for Cursor AI

## 🚨 CRITICAL FEATURE: Console & Error Capture

**This is absolutely critical for AI debugging!** The platform MUST capture ALL JavaScript errors and console logs in real-time so AI agents can see and debug them (like Replit does). See `docs/13. console-error-capture-implementation.md` for detailed implementation guide.

## 🎯 Project Context

You are working on **Zeblit**, an AI-powered development platform similar to Replit where users can build applications using natural language interactions with 6 specialized AI agents.

## 📁 Current Project State

### Created Files
- ✅ `.cursorrules` - Comprehensive coding guidelines and project context
- ✅ `README.md` - Project overview and getting started guide
- ✅ `.gitignore` - Version control ignore patterns
- ✅ This status file
- ✅ `requirements.txt` - All Python dependencies
- ✅ `requirements-dev.txt` - Development dependencies
- ✅ `requirements-prod.txt` - Production dependencies
- ✅ `BACKEND_SETUP.md` - Backend installation guide
- ✅ `env.example` - Environment variables template

### Documentation (in `docs/` folder)
All documentation files have been numbered (1-12) in recommended reading order:
1. Architecture summary
2. Requirements
3. Implementation plan
4. Database documentation
5. Database schema (Python)
6. Frontend components (TypeScript)
7. Testing strategy
8. Tech architecture diagram
9. Data flow diagram
10. Container architecture
11. Original PDF plan
12. Reference TDD from another project

## 🚀 Next Steps (Phase 1 - Core Platform)

### Backend Setup (Priority 1) ✅ COMPLETED
```bash
# Backend structure (created)
src/backend/
├── api/           # FastAPI routes ✅
├── agents/        # AI agent implementations ✅
├── services/      # Business logic ✅
├── models/        # SQLAlchemy models ✅
├── schemas/       # Pydantic schemas ✅
├── core/          # Core utilities ✅
├── tests/         # Test files ✅
└── main.py        # FastAPI app ✅
```

### Frontend Setup (Priority 2)
```bash
# Create frontend structure
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── lib/
│   ├── store/
│   └── types/
└── package.json
```

### Infrastructure Setup (Priority 3)
```bash
# Create infrastructure
infrastructure/
├── docker/
├── kubernetes/
└── docker-compose.yml
```

## 🔑 Key Technical Decisions

1. **Backend**: FastAPI (Python) - async, fast, modern
2. **Frontend**: React + TypeScript + Vite + shadcn/ui
3. **Database**: PostgreSQL + SQLAlchemy + Alembic
4. **Real-time**: Redis pub/sub + WebSockets
5. **AI**: Direct Anthropic Claude API (no frameworks)
6. **Containers**: OrbStack for dev, Kubernetes for prod

## 💡 Implementation Tips

1. Start with Phase 1 from the implementation plan
2. Follow TDD - write tests first
3. Use the repository pattern for data access
4. Implement authentication early
5. Set up Docker Compose for local development
6. Create a single working agent before implementing all 6

## 🎨 UI Layout Reference
```
┌────────────────────────────────────────┐
│ Header (Logo, User, Settings)          │
├─────────┬────────────────┬─────────────┤
│ Agent   │ Code Editor    │ App Preview │
│ Chat    │ (Monaco)       │ (iframe)    │
├─────────┴────────────────┴─────────────┤
│ Agent Tabs: [Dev][PM][Data][Eng][Arch] │
└────────────────────────────────────────┘
```

## 🔐 Environment Variables Needed

Create `.env` files with:
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY` (fallback)
- `RESEND_API_KEY`

## 📝 Current Phase

**Phase 1: Core Platform (Months 1-3)**
- [ ] Project setup and structure
- [ ] Database models and migrations
- [ ] Authentication system
- [ ] Basic API endpoints
- [ ] Container management with OrbStack
- [ ] Basic UI with Monaco editor
- [ ] Single agent proof of concept

## 🆘 Quick Commands

```bash
# Backend development
cd src/backend
python -m venv venv
source venv/bin/activate
pip install fastapi sqlalchemy alembic redis celery
uvicorn main:app --reload

# Frontend development
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm run dev

# Docker services
docker-compose up -d postgres redis

# Database migrations
alembic init alembic
alembic revision -m "Initial models"
alembic upgrade head
```

## 📚 Remember

- Check `.cursorrules` for coding standards
- Read docs in numbered order for context
- This is a complex project - implement incrementally
- Test everything - aim for >80% coverage
- Security and performance are critical
- User experience should feel magical
- **Always check `IMPLEMENTATION_CHECKLIST.md` before starting work**
- **Update the implementation plan after completing tasks**

---

**Note to Cursor AI**: This project is just starting. Begin with Phase 1 tasks from the implementation plan and follow the TDD approach outlined in the testing strategy. Always reference and update the implementation plan to track progress. 