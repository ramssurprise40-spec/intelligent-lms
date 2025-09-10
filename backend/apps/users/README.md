# Users App - Authentication System

## Overview

The Users app provides comprehensive authentication and user management functionality for the Intelligent LMS system. It supports multiple authentication methods, role-based access control, user profiles, and activity tracking.

## Features

### Authentication Methods
- **JWT Authentication**: Primary authentication method using access/refresh tokens
- **OAuth2 Authentication**: For third-party application integration
- **Social Authentication**: Login via Google, Facebook, GitHub, etc.
- **Session Authentication**: Traditional session-based authentication

### User Models

#### User
Extended Django User model with:
- UUID primary key
- Role-based permissions (student, instructor, admin, etc.)
- Profile information (avatar, bio, preferences)
- Learning preferences and study patterns
- Email verification and security features

#### UserProfile
Analytics and personalization data:
- Study statistics and progress tracking
- AI-powered learning recommendations
- Skill assessments and improvement areas
- Forum activity and reputation

#### UserActivity
Comprehensive activity logging:
- Login/logout tracking
- Course interaction history
- Learning analytics data
- Session management

#### UserNotification
Multi-channel notification system:
- Email and push notifications
- Priority-based delivery
- Action-based notifications
- Read/unread status tracking

## API Endpoints

### Authentication
- `POST /api/v1/users/auth/login/` - JWT login
- `POST /api/v1/users/auth/refresh/` - Refresh JWT token
- `POST /api/v1/users/auth/logout/` - Logout and blacklist token
- `POST /api/v1/users/auth/register/` - User registration
- `GET /api/v1/users/auth/verify-email/{uid}/{token}/` - Email verification

### Password Management
- `POST /api/v1/users/auth/password-reset/` - Request password reset
- `POST /api/v1/users/auth/reset-password/{uid}/{token}/` - Confirm password reset
- `POST /api/v1/users/auth/password-change/` - Change password (authenticated)

### User Profile
- `GET/PUT /api/v1/users/profile/` - User profile management
- `GET/PUT /api/v1/users/preferences/` - User preferences
- `GET /api/v1/users/me/` - Current user info

### Social Authentication
- `POST /api/v1/users/auth/social/{backend}/` - Social login

## Permissions System

### Built-in Permission Classes
- `IsOwnerOrReadOnly` - Object owners can edit, others read-only
- `IsInstructorOrAdmin` - Instructor/admin only access
- `IsStudentOrReadOnly` - Students read-only, others write
- `IsEnrolledInCourse` - Course enrollment required
- `IsVerifiedUser` - Email verification required
- `HasCompletedProfile` - Complete profile required

### Role-Based Access
- **Student**: Basic learning access, course enrollment
- **Instructor**: Course management, student oversight
- **Admin**: Full system access
- **Teaching Assistant**: Limited instructor privileges
- **Content Creator**: Content development access

## Configuration

### Required Settings
```python
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
    'rest_framework_simplejwt',
    'oauth2_provider',
    'social_django',
    'drf_yasg',
    'apps.users',
]

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### JWT Settings
JWT tokens are configured for secure authentication with:
- Access token lifetime: 15 minutes
- Refresh token lifetime: 7 days
- Token blacklisting support
- Automatic token refresh

### Email Configuration
Email templates are provided for:
- Account verification
- Password reset
- Notification delivery

## Usage Examples

### User Registration
```python
POST /api/v1/users/auth/register/
{
    "username": "student123",
    "email": "student@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
}
```

### JWT Login
```python
POST /api/v1/users/auth/login/
{
    "username": "student123",
    "password": "securepassword123"
}

Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "username": "student123",
        "email": "student@example.com",
        "role": "student"
    }
}
```

### Profile Update
```python
PUT /api/v1/users/profile/
Authorization: Bearer {access_token}
{
    "bio": "Computer Science student passionate about AI",
    "timezone": "America/New_York",
    "learning_style": "visual",
    "email_notifications": true
}
```

## Security Features

- **Password Validation**: Strong password requirements
- **Email Verification**: Required for account activation
- **Rate Limiting**: Protection against brute force attacks
- **Session Security**: IP tracking and session management
- **Token Security**: JWT blacklisting and refresh rotation
- **CSRF Protection**: Cross-site request forgery prevention

## Analytics Integration

The user system provides comprehensive analytics:
- Learning behavior tracking
- Performance metrics
- Engagement analytics
- Personalization data for AI recommendations

## Testing

Run tests with:
```bash
python manage.py test apps.users
```

## Development

To extend the user system:
1. Add new fields to User or UserProfile models
2. Create migrations: `python manage.py makemigrations users`
3. Apply migrations: `python manage.py migrate`
4. Update serializers and views as needed
5. Add appropriate permissions and tests

## Support

For issues or questions regarding the authentication system, please refer to the project documentation or contact the development team.
