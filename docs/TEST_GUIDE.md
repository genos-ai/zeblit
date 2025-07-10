# Zeblit Platform - Development Testing Guide

## 🚀 Services Running

✅ **Backend API**: http://localhost:8000
✅ **Frontend**: http://localhost:5173
✅ **API Documentation**: http://localhost:8000/api/docs

## 🧪 Quick Tests to Try

### 1. Test the Login Flow
1. Open http://localhost:5173 in your browser
2. You should see the login page
3. Use these test credentials:
   - **Regular User**: `user@zeblit.com` / `password123`
   - **Admin User**: `admin@zeblit.com` / `admin123`

### 2. Test Project Creation
1. After logging in, click "New Project"
2. Follow the 3-step wizard:
   - Select a template (e.g., "Web Application")
   - Enter project details
   - Review and create

### 3. Test the IDE Interface
1. Click on a project to open it
2. You'll see:
   - **Code Editor** (Monaco) in the center
   - **File Explorer** on the left
   - **Terminal** at the bottom
   - **Preview** on the right
   - **Agent Chat** panel

### 4. Test WebSocket Connection
1. Open the browser console (F12)
2. Look for "WebSocket connected" message
3. Any actions should show real-time updates

### 5. Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/v1/health/health

# Login (get JWT token)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@zeblit.com", "password": "password123"}'

# Get current user (with token)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 6. Test Console Logging
1. Open browser DevTools (F12)
2. Go to Console tab
3. All actions are logged with details
4. Errors are captured automatically

## 🔍 Things to Check

### Frontend Features
- [ ] Login/Logout works
- [ ] Registration page accessible
- [ ] Dashboard shows projects
- [ ] New project wizard completes
- [ ] Monaco editor loads
- [ ] File explorer shows files
- [ ] Terminal accepts commands
- [ ] WebSocket connects

### Backend Features
- [ ] API docs load at /api/docs
- [ ] Authentication works
- [ ] Projects can be created
- [ ] WebSocket connections work
- [ ] Database queries succeed
- [ ] Redis is caching

## 🐛 Common Issues

### Backend Won't Start
- Check PostgreSQL is running: `pg_isready`
- Check Redis is running: `redis-cli ping`
- Check port 8000 is free: `lsof -i :8000`

### Frontend Won't Start
- Check port 5173 is free: `lsof -i :5173`
- Try: `cd frontend && bun install`

### Can't Login
- Check backend is running
- Verify seed data was loaded
- Check CORS settings in .env

## 📊 Monitoring

### Check Logs
```bash
# Backend logs
tail -f logs/backend/app.log

# Frontend console
# Open browser DevTools > Console

# Database queries
tail -f logs/backend/app.log | grep "database"
```

### Performance
- Backend adds `X-Process-Time` header to all responses
- Slow requests (>3s) are logged as warnings
- Check browser Network tab for API response times

## 🎯 Next Steps

1. **Create a Project**: Test the full project creation flow
2. **Write Code**: Use the Monaco editor to write some code
3. **Test Agent Chat**: Try chatting with AI agents (when integrated)
4. **File Operations**: Create, edit, delete files
5. **Terminal Commands**: Run commands in the terminal

## 🚦 Status Check Commands

```bash
# Check all services
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:5173 -o /dev/null -w "%{http_code}\n"

# Check database
psql -U zeblit -d zeblit -c "SELECT COUNT(*) FROM users;"

# Check Redis
redis-cli ping

# Check running processes
ps aux | grep -E "uvicorn|vite" | grep -v grep
```

---

**Happy Testing!** 🎉

If you encounter any issues, check the logs in the `logs/` directory or the browser console for detailed error messages. 