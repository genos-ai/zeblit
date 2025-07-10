# Authentication Flow Documentation

## Overview

The Zeblit platform uses JWT (JSON Web Token) based authentication with access and refresh tokens. The authentication system is built with FastAPI on the backend and React Context API on the frontend.

## Authentication Endpoints

### 1. User Registration
**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "role": "user",
  "id": "uuid",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00"
}
```

### 2. User Login
**Endpoint**: `POST /api/v1/auth/login`

**Request**: Form data (OAuth2 compatible)
```
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

**Response**:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 3. Get Current User
**Endpoint**: `GET /api/v1/users/me`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "is_active": true,
  "role": "user",
  "id": "uuid",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00",
  "last_login": "2025-01-01T00:00:00",
  "login_count": 0,
  "preferences": {},
  "monthly_token_limit": 1000000,
  "monthly_cost_limit": 100.0
}
```

### 4. Refresh Token
**Endpoint**: `POST /api/v1/auth/refresh`

**Request Body**:
```json
{
  "refresh_token": "eyJhbGc..."
}
```

**Response**: Same as login response

### 5. Change Password
**Endpoint**: `POST /api/v1/auth/change-password`

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

## Frontend Implementation

### AuthContext
Located at `frontend/src/contexts/AuthContext.tsx`

Provides:
- `user`: Current user object or null
- `isAuthenticated`: Boolean indicating auth status
- `isLoading`: Boolean for loading state
- `login(email, password)`: Login function
- `logout()`: Logout function
- `checkAuth()`: Verify current authentication

### Authentication Flow

1. **Initial Load**:
   - AuthContext checks for stored JWT token in localStorage
   - If token exists, calls `/users/me` to validate and get user data
   - If invalid, clears token and redirects to login

2. **Login Process**:
   - User submits email/password on login page
   - Frontend sends POST to `/auth/login` with form data
   - Backend validates credentials and returns JWT tokens
   - Frontend stores access token in localStorage
   - Frontend fetches user data from `/users/me`
   - User is redirected to dashboard

3. **Protected Routes**:
   - Routes wrapped in ProtectedRoute component
   - Checks `isAuthenticated` from AuthContext
   - Redirects to login if not authenticated

4. **API Requests**:
   - API client automatically includes JWT token in Authorization header
   - If 401 response, user is logged out and redirected to login

5. **Logout**:
   - Clears tokens from localStorage
   - Resets user state in AuthContext
   - Redirects to login page

## Security Considerations

1. **Token Storage**:
   - Access tokens stored in localStorage (convenient but vulnerable to XSS)
   - Consider httpOnly cookies for production

2. **Token Expiration**:
   - Access tokens expire in 30 minutes
   - Refresh tokens expire in 7 days
   - Implement auto-refresh logic for seamless UX

3. **Password Security**:
   - Passwords hashed with bcrypt
   - Minimum password requirements should be enforced
   - Rate limiting on login attempts recommended

4. **CORS Configuration**:
   - Currently allows localhost origins
   - Restrict to specific domains in production

## Default Test Users

For development, the seed script creates:

1. **Regular User**:
   - Email: `user@zeblit.com`
   - Password: `password123`
   - Role: `user`

2. **Admin User**:
   - Email: `admin@zeblit.com`
   - Password: `admin123`
   - Role: `admin`

## Common Issues and Solutions

### Issue: 404 on `/auth/me`
**Solution**: The correct endpoint is `/users/me`, not `/auth/me`

### Issue: Login returns 401
**Possible Causes**:
- Incorrect credentials
- User account is inactive
- Token has expired

### Issue: CORS errors
**Solution**: Ensure frontend URL is in ALLOWED_ORIGINS in backend .env

### Issue: Token not included in requests
**Solution**: Check that API client is properly configured to read from localStorage

## Future Improvements

1. **OAuth2 Social Login**: Add Google, GitHub authentication
2. **Two-Factor Authentication**: Implement TOTP-based 2FA
3. **Session Management**: Allow users to view/revoke active sessions
4. **Password Reset**: Implement email-based password reset flow
5. **Remember Me**: Extended refresh token lifetime option
6. **Rate Limiting**: Prevent brute force attacks
7. **Audit Logging**: Track all authentication events 