# API Reference Documentation

## 📋 Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Course Management](#course-management)
- [Communications](#communications)
- [Analytics](#analytics)
- [AI Services](#ai-services)
- [Error Handling](#error-handling)

## 🔐 Authentication

### Base URL
```
Production: https://your-app.onrender.com/api/
Development: http://localhost:8000/api/
```

### Authentication Methods
- **JWT Tokens**: Bearer token in Authorization header
- **OAuth2**: Social login support (Google, GitHub, etc.)
- **Session Authentication**: For web interface

### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }
}
```

### Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 👤 User Management

### Get User Profile
```http
GET /api/users/profile/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "student",
  "profile": {
    "bio": "Computer Science student",
    "avatar": "https://example.com/avatar.jpg",
    "preferences": {
      "language": "en",
      "timezone": "UTC",
      "notifications": true
    }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Update User Profile
```http
PUT /api/users/profile/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "profile": {
    "bio": "Updated bio",
    "preferences": {
      "notifications": false
    }
  }
}
```

## 📚 Course Management

### List Courses
```http
GET /api/courses/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `search`: Search term
- `category`: Course category
- `level`: Difficulty level
- `instructor`: Instructor ID
- `page`: Page number
- `limit`: Items per page

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/courses/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Introduction to Machine Learning",
      "description": "Learn the basics of ML",
      "instructor": {
        "id": 2,
        "name": "Dr. Jane Smith",
        "avatar": "https://example.com/instructor.jpg"
      },
      "category": "Technology",
      "level": "beginner",
      "duration": 12,
      "modules_count": 8,
      "students_count": 150,
      "rating": 4.8,
      "price": 99.99,
      "thumbnail": "https://example.com/course-thumb.jpg",
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### Get Course Details
```http
GET /api/courses/{course_id}/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "id": 1,
  "title": "Introduction to Machine Learning",
  "description": "Comprehensive ML course...",
  "instructor": {
    "id": 2,
    "name": "Dr. Jane Smith",
    "bio": "PhD in Computer Science...",
    "avatar": "https://example.com/instructor.jpg"
  },
  "modules": [
    {
      "id": 1,
      "title": "Module 1: ML Fundamentals",
      "description": "Introduction to core concepts",
      "order": 1,
      "duration": 90,
      "lessons": [
        {
          "id": 1,
          "title": "What is Machine Learning?",
          "type": "video",
          "duration": 15,
          "content_url": "https://example.com/lesson1.mp4",
          "completed": false
        }
      ]
    }
  ],
  "assessments": [
    {
      "id": 1,
      "title": "Module 1 Quiz",
      "type": "quiz",
      "questions_count": 10,
      "time_limit": 30,
      "attempts_allowed": 3
    }
  ],
  "enrollment": {
    "enrolled_at": "2024-01-15T10:30:00Z",
    "progress": 25.5,
    "last_accessed": "2024-01-20T14:20:00Z"
  }
}
```

### Enroll in Course
```http
POST /api/courses/{course_id}/enroll/
Authorization: Bearer {access_token}
```

### Update Progress
```http
POST /api/courses/{course_id}/lessons/{lesson_id}/complete/
Authorization: Bearer {access_token}
```

## 💬 Communications

### Get Messages
```http
GET /api/communications/messages/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `thread_id`: Conversation thread
- `recipient`: Recipient user ID
- `search`: Search in messages
- `page`: Page number

### Send Message
```http
POST /api/communications/messages/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "recipient": 2,
  "subject": "Question about assignment",
  "content": "I have a question about the ML assignment...",
  "message_type": "direct",
  "attachments": [
    {
      "name": "assignment.pdf",
      "url": "https://example.com/file.pdf"
    }
  ]
}
```

### Forum Posts
```http
GET /api/communications/forums/{forum_id}/posts/
Authorization: Bearer {access_token}
```

```http
POST /api/communications/forums/{forum_id}/posts/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "title": "Help with Neural Networks",
  "content": "I'm struggling with backpropagation...",
  "tags": ["neural-networks", "help"]
}
```

## 📊 Analytics

### Learning Analytics
```http
GET /api/analytics/learning-progress/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "overall_progress": 65.5,
  "courses_enrolled": 3,
  "courses_completed": 1,
  "total_study_time": 2450,
  "weekly_activity": [
    {"week": "2024-W03", "hours": 12.5, "progress": 8.2},
    {"week": "2024-W04", "hours": 15.0, "progress": 12.1}
  ],
  "performance_metrics": {
    "average_quiz_score": 87.5,
    "assignment_completion_rate": 92.3,
    "engagement_score": 8.4
  }
}
```

### Course Analytics (Instructors only)
```http
GET /api/analytics/courses/{course_id}/
Authorization: Bearer {access_token}
```

### Generate Report
```http
POST /api/analytics/reports/generate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "report_type": "learning_progress",
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "filters": {
    "course_ids": [1, 2],
    "include_details": true
  },
  "format": "pdf"
}
```

## 🤖 AI Services

### AI Search
```http
POST /api/ai/search/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "explain neural networks backpropagation",
  "context": "course_materials",
  "filters": {
    "course_ids": [1, 2],
    "content_types": ["video", "document"]
  },
  "include_ai_answer": true
}
```

**Response:**
```json
{
  "query": "explain neural networks backpropagation",
  "results": [
    {
      "id": "content_123",
      "title": "Backpropagation in Neural Networks",
      "content_type": "video",
      "course": "Introduction to Deep Learning",
      "relevance_score": 0.95,
      "url": "https://example.com/lesson-backprop.mp4",
      "timestamp": 45.2,
      "summary": "Explains the mathematical foundation..."
    }
  ],
  "ai_answer": {
    "content": "Backpropagation is a fundamental algorithm...",
    "confidence": 0.92,
    "sources": ["content_123", "content_456"],
    "follow_up_questions": [
      "How does gradient descent work?",
      "What are common backpropagation challenges?"
    ]
  },
  "total_results": 15,
  "processing_time": 0.85
}
```

### AI Feedback
```http
POST /api/ai/feedback/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content": "Neural networks are machine learning models...",
  "context": {
    "assignment_id": 123,
    "course_id": 1,
    "question": "Explain neural networks"
  },
  "feedback_type": "detailed"
}
```

### Content Generation
```http
POST /api/ai/generate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "content_type": "quiz_questions",
  "topic": "Machine Learning Basics",
  "parameters": {
    "difficulty": "intermediate",
    "count": 5,
    "question_types": ["multiple_choice", "short_answer"]
  },
  "context": {
    "course_id": 1,
    "module_id": 2
  }
}
```

## 🚨 Error Handling

### HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **429**: Rate Limited
- **500**: Internal Server Error

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "This field is required"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Common Error Codes
- `AUTHENTICATION_FAILED`: Invalid credentials
- `PERMISSION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource not found
- `RATE_LIMITED`: Too many requests
- `AI_SERVICE_ERROR`: AI service unavailable

## 📱 Rate Limiting

### Limits
- **Authentication**: 10 requests/minute
- **General API**: 100 requests/minute
- **AI Services**: 20 requests/minute
- **File Upload**: 5 requests/minute

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1642248600
```

## 🔍 Pagination

### Request
```
GET /api/courses/?page=2&limit=20
```

### Response
```json
{
  "count": 150,
  "next": "http://api.example.com/courses/?page=3&limit=20",
  "previous": "http://api.example.com/courses/?page=1&limit=20",
  "results": [...]
}
```

## 🌐 WebSocket Endpoints

### Real-time Chat
```
ws://localhost:8000/ws/chat/{room_id}/
```

### Live Updates
```
ws://localhost:8000/ws/updates/{user_id}/
```

### Notifications
```
ws://localhost:8000/ws/notifications/{user_id}/
```

---

**📚 For more detailed information, check our [Development Guide](DEVELOPMENT.md)**
