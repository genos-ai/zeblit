# Zeblit AI Development Platform - Quick Development Setup

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (via conda)
- Node.js & Bun
- PostgreSQL 15+
- Redis 8+

### Setup Steps

1. **Clone and Setup Environment**
```bash
git clone <repo>
cd zeblit
conda activate zeblit
```

2. **Install Dependencies**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && bun install && cd ..
```

3. **Environment Configuration**
```bash
# Copy example env file
cp env.example .env

# Edit .env with your settings
# NOTE: All environment variables should be in the root .env file only
# Do NOT create separate .env files in subdirectories (e.g., frontend/.env)
# The frontend will automatically load VITE_* variables from the root .env
```

4. **Database Setup**
```bash
# Create database
createdb zeblit_db

# Run migrations
cd src/backend && alembic upgrade head && cd ../..

# Seed default data
python src/backend/seed_data.py --verbose
```

5. **Start Services**
```bash
# Terminal 1: Backend
python -m uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend && bun run dev
```

## 🔑 Default Login Credentials

After running the seed script:
- **Regular User**: `user@zeblit.com` / `password123`
- **Admin User**: `admin@zeblit.com` / `admin123`

## 📁 Project Structure
```
zeblit/
├── .env                    # All environment variables (root only!)
├── src/backend/           # FastAPI backend
├── frontend/              # React frontend (no .env here)
├── logs/                  # Application logs
└── docs/                  # Documentation
```

## 🛠️ Common Commands

### Backend
```bash
# Run backend
python -m uvicorn src.backend.main:app --reload

# Run tests
pytest src/backend/tests/

# Create new migration
cd src/backend && alembic revision --autogenerate -m "description"

# Check logs
tail -f logs/backend/zeblit_db_$(date +%Y-%m-%d).log
```

### Frontend
```bash
# Start dev server
cd frontend && bun run dev

# Build for production
cd frontend && bun run build

# Run tests
cd frontend && bun test
```

### Database
```bash
# Access PostgreSQL
psql -U postgres -d zeblit_db

# Reset database
dropdb zeblit_db && createdb zeblit_db
cd src/backend && alembic upgrade head
```

## 🐛 Troubleshooting

### Backend Issues
- **Import errors**: Make sure you're in the project root
- **Database connection**: Check PostgreSQL is running
- **Redis connection**: Check Redis is running with `redis-cli ping`

### Frontend Issues
- **API connection**: Verify backend is running on port 8000
- **Environment variables**: Check root .env has VITE_* variables
- **WebSocket errors**: Ensure VITE_WS_URL is set correctly

### Environment Variables
- **All env vars in root .env**: Never create .env files in subdirectories
- **Frontend vars**: Must start with `VITE_` to be exposed to browser
- **Missing vars**: Check against env.example for required variables

## 📝 Environment Variables

Key variables in root `.env`:
```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user@localhost:5432/zeblit_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key

# Frontend (VITE_ prefix required)
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws

# Email (for development)
EMAIL_VALIDATION_SKIP_DELIVERABILITY=true
```

## 🔍 Debugging

### VS Code/Cursor
- Press F5 and select debug configuration
- Breakpoints work in both frontend and backend

### Logs
- Backend: `logs/backend/zeblit_db_*.log`
- Frontend: Browser console + `logs/frontend/`
- Errors: `logs/errors/errors_*.log`

## 🚀 Next Steps
1. Login with default credentials
2. Create a new project
3. Start coding with AI assistance! 