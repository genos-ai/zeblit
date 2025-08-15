# Zeblit Development Debugging Guide

## Overview

This guide covers debugging techniques for developing the Zeblit platform itself (not for end-users debugging their apps).

## Frontend Debugging

### 1. Browser Developer Tools

The most powerful debugging tool is already in your browser:

- **Console**: All our logs appear here with color coding
- **Network Tab**: Monitor API calls to the backend
- **React DevTools**: Inspect component state and props
- **Sources Tab**: Set breakpoints in TypeScript code

### 2. Our Built-in Logging System

We have a comprehensive logger at `frontend/src/lib/logger.ts`:

```typescript
// Use it anywhere in the frontend
import { logger } from '@/lib/logger'

logger.debug('Component rendered', { props, state })
logger.info('API call successful', { response })
logger.warn('Deprecated method used', { method: 'oldMethod' })
logger.error('Failed to load data', { error })
```

### 3. VS Code/Cursor Debugging

Use the launch configurations in `.vscode/launch.json`:

1. **Start Frontend Debug Session**:
   - Press F5 and select "Frontend: React"
   - Sets breakpoints in VS Code
   - Chrome opens with debugging enabled

2. **Debug Frontend Tests**:
   - Press F5 and select "Frontend: Debug Tests"
   - Debug Vitest tests with breakpoints

### 4. React Error Boundaries

Our ErrorBoundary component catches all React errors:
- Displays error details in development
- Logs full stack traces
- Shows component tree where error occurred

### 5. API Client Debugging

Every API request/response is logged:
```typescript
// Check the Network tab or console for:
// [API] Request: GET /api/v1/projects
// [API] Response: 200 OK (45ms)
```

## Backend Debugging

### 1. Structured Logging

All backend modules use structured logging:

```python
import structlog
logger = structlog.get_logger(__name__)

# Use throughout your code
logger.info("Processing request", user_id=user.id, project_id=project_id)
logger.error("Database error", error=str(e), query=query)
```

### 2. Debug Utilities

Use our debug module at `src/backend/core/debug.py`:

```python
from src.backend.core.debug import debug_print, timer, DebugContext

# Pretty print any data
debug_print("User Data", user_dict)

# Time function execution
@timer
async def slow_operation():
    # Automatically logs execution time
    pass

# Debug specific code blocks
with DebugContext("Processing user data"):
    # Shows execution time and variable changes
    result = process_data(user_data)
```

### 3. VS Code/Cursor Backend Debugging

1. **Start Backend Debug Session**:
   - Press F5 and select "Backend: FastAPI"
   - Set breakpoints in Python code
   - Step through request handling

2. **Debug Backend Tests**:
   - Press F5 and select "Backend: Debug Tests"
   - Debug pytest with breakpoints

### 4. Request Tracking

Every request has a unique ID for tracing:
```
2025-01-09 10:15:23 [INFO] request_started request_id=abc-123 method=GET path=/api/v1/projects
2025-01-09 10:15:23 [ERROR] Database error request_id=abc-123 error="Connection timeout"
2025-01-09 10:15:23 [INFO] request_completed request_id=abc-123 status_code=500 duration_ms=45
```

### 5. Database Query Debugging

Enable SQL echo in development:
```python
# In your .env file
DATABASE_ECHO=true

# See all SQL queries in logs
```

## Full Stack Debugging

### 1. Simultaneous Frontend + Backend

Use the compound launch configuration:
1. Press F5 and select "Full Stack: Frontend + Backend"
2. Both debuggers start simultaneously
3. Set breakpoints in both frontend and backend

### 2. Tracing Requests End-to-End

1. Frontend logs the request with a unique ID
2. Backend receives and logs with same request ID
3. Follow the request through the entire stack

### 3. Common Issues and Solutions

#### CORS Errors
- Check backend CORS middleware configuration
- Ensure frontend uses correct API URL

#### Authentication Failures
- Check JWT token in browser DevTools > Application > Local Storage
- Verify token expiry time
- Check backend auth middleware logs

#### WebSocket Connection Issues
- Check browser console for connection errors
- Verify WebSocket URL matches backend
- Check Redis is running for pub/sub

## Log Files

### Backend Logs
```bash
# Main application log
tail -f logs/backend/zeblit_db_$(date +%Y-%m-%d).log

# Error-only log
tail -f logs/errors/errors_$(date +%Y-%m-%d).log

# Follow logs with highlighting
tail -f logs/backend/*.log | grep -E "(ERROR|WARN)" --color
```

### Frontend Logs
- Development: Browser console
- Production: Would be sent to backend for storage

## Performance Debugging

### Frontend Performance
1. React DevTools Profiler tab
2. Chrome Performance tab
3. Our logger tracks component render times

### Backend Performance
1. Use the `@timer` decorator on slow functions
2. Check request duration in logs
3. Use Python profiler for detailed analysis:
   ```bash
   python -m cProfile -s cumulative src/backend/main.py
   ```

## Quick Debugging Commands

```bash
# Check if backend is running
curl http://localhost:8000/api/v1/health

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@zeblit.com&password=password123"

# Watch backend logs
tail -f logs/backend/*.log | jq '.'

# Check Redis
redis-cli ping

# Check PostgreSQL
psql -U postgres -d zeblit_db -c "SELECT COUNT(*) FROM users;"
```

## IDE Setup

### VS Code/Cursor Extensions
- Python (Microsoft)
- Pylance
- ES7+ React/Redux/React-Native snippets
- Tailwind CSS IntelliSense
- Error Lens (shows errors inline)
- GitLens

### Settings for Better Debugging
```json
{
  "editor.fontSize": 14,
  "debug.console.fontSize": 13,
  "debug.showBreakpointsInOverviewRuler": true,
  "debug.inlineValues": "on",
  "python.testing.pytestEnabled": true,
  "typescript.updateImportsOnFileMove.enabled": "always"
}
```

## Best Practices

1. **Always check logs first** - Most issues are visible in logs
2. **Use structured logging** - Include context in log messages
3. **Set strategic breakpoints** - Not too many, focus on problem areas
4. **Use debug utilities** - Our debug module has helpful tools
5. **Keep console clean** - Remove debug prints before committing
6. **Test error paths** - Deliberately cause errors to test handling

## Debugging Checklist

When something isn't working:

- [ ] Check browser console for JavaScript errors
- [ ] Check network tab for failed API calls
- [ ] Check backend logs for Python errors
- [ ] Verify services are running (PostgreSQL, Redis)
- [ ] Check environment variables are set correctly
- [ ] Try in incognito mode (rules out extensions/cache)
- [ ] Set breakpoints at the start of the problematic flow
- [ ] Use git bisect if the issue appeared recently

Remember: Our comprehensive logging system means most debugging can be done by reading logs rather than stepping through code! 