# Authentication and Authorization System

This document provides comprehensive information about the authentication and authorization system implemented for the Intelligent LMS.

## Overview

The authentication system provides comprehensive security features including:

- **JWT-based Authentication**: Secure token-based authentication with access and refresh tokens
- **Role-based Access Control**: Fine-grained permissions for admin, instructor, and student roles
- **Multi-Factor Authentication (MFA)**: TOTP-based 2FA with backup codes
- **Social Authentication**: OAuth2 integration with Google, Microsoft, and GitHub
- **Advanced Security Features**: Account lockout, suspicious activity detection, and security monitoring
- **Password Policies**: Configurable password strength requirements and history tracking
- **Session Management**: Secure session handling with hijacking detection

## Architecture

### Components

1. **Models** (`authentication/models.py`)
   - `UserMFA`: Multi-factor authentication settings
   - `LoginAttempt`: Login attempt tracking for security monitoring
   - `AccountLockout`: Account lockout management
   - `SecurityEvent`: Security event logging and auditing

2. **Permissions** (`authentication/permissions.py`)
   - Role-based permission classes
   - Object-level permissions
   - Custom decorators for view protection

3. **Middleware** (`authentication/middleware.py`)
   - Security monitoring middleware
   - Session security checks
   - Rate limiting
   - Content Security Policy headers

4. **API Views** (`authentication/views.py`)
   - Login/logout endpoints
   - User registration
   - Password management
   - MFA setup and verification
   - User profile management

5. **Utilities** (`authentication/utils.py`)
   - Security helper functions
   - Password validation
   - Email notifications
   - Device fingerprinting

## API Endpoints

### Authentication

#### Login
```
POST /api/v1/auth/login/
```

**Request:**
```json
{
    "username": "user@example.com",
    "password": "securepassword"
}
```

**Response (Success):**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "role": "student"
    }
}
```

**Response (MFA Required):**
```json
{
    "mfa_required": true,
    "message": "Multi-factor authentication required",
    "temp_token": "abc123...",
    "user_id": 1
}
```

#### MFA Verification
```
POST /api/v1/auth/mfa/verify/
```

**Request:**
```json
{
    "temp_token": "abc123...",
    "mfa_token": "123456",
    "user_id": 1
}
```

#### User Registration
```
POST /api/v1/auth/register/
```

**Request:**
```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "StrongPassword123!",
    "password_confirm": "StrongPassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
}
```

#### Logout
```
POST /api/v1/auth/logout/
```

**Request:**
```json
{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Password Management

#### Change Password
```
POST /api/v1/auth/password/change/
```

**Request:**
```json
{
    "old_password": "oldpassword",
    "new_password": "NewStrongPassword123!",
    "new_password_confirm": "NewStrongPassword123!"
}
```

#### Password Reset Request
```
POST /api/v1/auth/password/reset/
```

**Request:**
```json
{
    "email": "user@example.com"
}
```

#### Password Reset Confirmation
```
POST /api/v1/auth/password/reset/confirm/
```

**Request:**
```json
{
    "uid": "base64-encoded-user-id",
    "token": "password-reset-token",
    "new_password": "NewStrongPassword123!",
    "new_password_confirm": "NewStrongPassword123!"
}
```

### Multi-Factor Authentication

#### Setup MFA
```
GET /api/v1/auth/mfa/setup/
```

**Response:**
```json
{
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "secret_key": "JBSWY3DPEHPK3PXP",
    "backup_codes": [
        "1234-5678",
        "9ABC-DEFG",
        ...
    ]
}
```

#### Enable MFA
```
POST /api/v1/auth/mfa/enable/
```

**Request:**
```json
{
    "token": "123456"
}
```

#### Disable MFA
```
POST /api/v1/auth/mfa/disable/
```

**Request:**
```json
{
    "password": "currentpassword"
}
```

### User Profile

#### Get User Profile
```
GET /api/v1/auth/profile/
```

**Response:**
```json
{
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student",
        "is_verified": true,
        "last_login": "2024-01-15T10:30:00Z",
        "date_joined": "2024-01-01T09:00:00Z"
    },
    "security": {
        "mfa_enabled": true,
        "recent_logins": [
            {
                "ip_address": "192.168.1.100",
                "attempted_at": "2024-01-15T10:30:00Z",
                "user_agent": "Mozilla/5.0..."
            }
        ]
    }
}
```

#### Get Security Events
```
GET /api/v1/auth/security/events/
```

**Response:**
```json
{
    "events": [
        {
            "event_type": "Successful Login",
            "description": "User logged in successfully",
            "risk_level": "Low",
            "ip_address": "192.168.1.100",
            "occurred_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

## Permissions System

### Permission Classes

#### Basic Role Permissions
- `IsAdminUser`: Admin users only
- `IsInstructorUser`: Instructors and admins
- `IsStudentUser`: Students only

#### Object-Level Permissions
- `IsOwnerOrInstructor`: Resource owners or instructors
- `IsCourseInstructor`: Course instructor access
- `IsEnrolledStudent`: Enrolled students only

#### Functional Permissions
- `CanManageUsers`: User management operations
- `CanManageCourses`: Course management operations
- `CanGradeAssessments`: Assessment grading
- `CanViewAnalytics`: Analytics viewing

### Permission Decorators

```python
from authentication.permissions import admin_required, instructor_required

@admin_required
def admin_view(request):
    # Only admin users can access
    pass

@instructor_required
def instructor_view(request):
    # Instructors and admins can access
    pass

@role_required('admin', 'instructor')
def multi_role_view(request):
    # Multiple roles allowed
    pass

@course_enrollment_required
def enrolled_student_view(request, course_id):
    # Students must be enrolled in the course
    pass

@mfa_required
def sensitive_view(request):
    # MFA verification required
    pass
```

## Security Features

### Account Security

#### Account Lockout
- Automatic lockout after 5 failed login attempts
- Lockout duration: 30 minutes (configurable)
- IP-based tracking
- Manual unlock by administrators

#### Password Policies
- Minimum length: 8 characters
- Must contain uppercase, lowercase, digits, and symbols
- Cannot reuse last 5 passwords
- Password expiry: 90 days (configurable)

#### Suspicious Activity Detection
- New device/location detection
- Unusual login patterns
- Automatic security alerts
- Email notifications

### Session Security

#### Session Management
- Secure session cookies
- Session timeout: 1 hour
- Session hijacking detection
- Concurrent session limits

#### Device Tracking
- Device fingerprinting
- Trusted device management
- Session monitoring
- Remote logout capability

### Multi-Factor Authentication

#### TOTP Support
- Time-based one-time passwords
- 30-second validity window
- QR code setup
- Backup codes for recovery

#### Recovery Options
- 10 single-use backup codes
- Email-based account recovery
- Administrative override

## Configuration

### Django Settings

```python
# Authentication backends
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.microsoft.MicrosoftOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
]

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Security Settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPT_TIMEOUT = 300  # 5 minutes
ACCOUNT_LOCKOUT_TIME = 1800  # 30 minutes

# Password Policy
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SYMBOLS = True
PASSWORD_HISTORY_LENGTH = 5

# MFA Settings
MFA_ENABLED = True
MFA_TOTP_ISSUER = 'Intelligent LMS'
```

### Environment Variables

```bash
# Social Authentication
GOOGLE_OAUTH2_KEY=your-google-client-id
GOOGLE_OAUTH2_SECRET=your-google-client-secret
MICROSOFT_OAUTH2_KEY=your-microsoft-client-id
MICROSOFT_OAUTH2_SECRET=your-microsoft-client-secret
GITHUB_KEY=your-github-client-id
GITHUB_SECRET=your-github-client-secret

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@intelligent-lms.edu

# Security
SECRET_KEY=your-secret-key
DJANGO_ENV=production
```

## Social Authentication Setup

### Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth2 credentials
5. Add authorized redirect URIs:
   - `http://localhost:8000/auth/complete/google-oauth2/` (development)
   - `https://your-domain.com/auth/complete/google-oauth2/` (production)

### Microsoft OAuth2

1. Go to [Azure App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Create a new app registration
3. Add redirect URIs:
   - `http://localhost:8000/auth/complete/microsoft-oauth2/`
   - `https://your-domain.com/auth/complete/microsoft-oauth2/`

### GitHub OAuth2

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App
3. Set authorization callback URL:
   - `http://localhost:8000/auth/complete/github/`
   - `https://your-domain.com/auth/complete/github/`

## Management Commands

### Clean up old authentication data
```bash
python manage.py cleanup_auth
python manage.py cleanup_auth --dry-run
python manage.py cleanup_auth --days-login-attempts 30 --days-security-events 90
```

### Initialize database with authentication data
```bash
python manage.py init_db
```

## Monitoring and Logging

### Security Events

All security-related events are logged to the `SecurityEvent` model:

- Login success/failure
- Password changes
- MFA enable/disable
- Account lockouts
- Suspicious activity

### Login Attempts

All login attempts are tracked in the `LoginAttempt` model:

- Successful logins
- Failed login attempts
- IP address and user agent
- Geographic information (if available)

### Metrics and Analytics

- Login success/failure rates
- Account lockout statistics
- MFA adoption rates
- Security event trends
- Device and browser analytics

## Security Best Practices

### For Developers

1. Always use HTTPS in production
2. Keep dependencies updated
3. Use strong JWT secrets
4. Implement proper CORS policies
5. Enable security headers
6. Monitor security events regularly

### For Administrators

1. Enable MFA for all admin accounts
2. Regularly review security events
3. Monitor failed login attempts
4. Keep user roles and permissions updated
5. Implement backup and recovery procedures

### For Users

1. Use strong, unique passwords
2. Enable MFA when available
3. Log out from shared devices
4. Report suspicious activity
5. Keep recovery information updated

## Troubleshooting

### Common Issues

#### JWT Token Expired
```json
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": "access",
            "message": "Token is invalid or expired"
        }
    ]
}
```

**Solution:** Use the refresh token to get a new access token.

#### Account Locked
```json
{
    "error": "Account is locked. Please contact support.",
    "locked_until": "2024-01-15T11:00:00Z"
}
```

**Solution:** Wait for lockout period to expire or contact administrator.

#### MFA Setup Issues
- Ensure system time is synchronized
- Check TOTP app configuration
- Verify backup codes are saved securely

#### Social Authentication Errors
- Check OAuth2 credentials
- Verify redirect URIs
- Ensure social apps are properly configured

### Debug Mode

Enable debug logging for authentication:

```python
LOGGING = {
    'loggers': {
        'authentication': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Performance Considerations

### Database Optimization

- Index on frequently queried fields
- Regular cleanup of old data
- Connection pooling for high load
- Read replicas for analytics

### Caching

- Cache user permissions
- Store session data in Redis
- Cache social auth tokens
- Rate limiting with cache backend

### Monitoring

- Track authentication response times
- Monitor database query performance
- Set up alerting for security events
- Regular performance testing

---

For additional support or questions about the authentication system, please refer to the project documentation or contact the development team.
