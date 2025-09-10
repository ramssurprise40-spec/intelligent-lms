# Course Management System

This module provides comprehensive course management functionality for the Intelligent LMS, including course creation, enrollment, progress tracking, and analytics.

## Features

### Core Models
- **Course**: Main course entity with instructor management, enrollment controls, and AI-powered features
- **CourseModule**: Organize course content into logical modules with prerequisites
- **Lesson**: Individual learning units with multiple content types and progress tracking
- **CourseEnrollment**: Track student enrollments with advanced progress analytics
- **LessonProgress**: Detailed progress tracking for each lesson
- **CourseRating**: Student reviews and ratings with sentiment analysis
- **CourseCertificate**: Automated certificate generation for course completion
- **CourseWaitlist**: Manage course capacity with intelligent waitlist system
- **CourseAnalytics**: Comprehensive analytics and reporting

### API Features
- **RESTful API**: Complete CRUD operations for all course-related entities
- **Advanced Filtering**: Comprehensive search and filtering capabilities
- **Nested Resources**: Structured API for courses → modules → lessons
- **Progress Tracking**: Real-time progress updates and analytics
- **Certificate Generation**: Automated certificate issuance
- **Dashboard Analytics**: Instructor and student dashboard statistics
- **Rate Limiting**: Prevent abuse of enrollment and rating endpoints

### Smart Features
- **AI Content Analysis**: Automatic difficulty analysis and content summarization
- **Predictive Analytics**: Completion predictions and risk scoring
- **Personalized Recommendations**: AI-driven course and content suggestions
- **Intelligent Waitlist**: Priority-based waitlist management
- **Content Versioning**: Track lesson content changes over time

## Installation

### 1. Install Dependencies

```bash
# Core dependencies should already be installed
pip install django-filter
pip install djangorestframework-nested
```

### 2. Update Django Settings

Add the courses app to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_filters',
    'rest_framework',
    'apps.courses',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

### 3. Run Migrations

```bash
python manage.py makemigrations courses
python manage.py migrate
```

### 4. Include Course URLs

Add course URLs to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('courses/', include('apps.courses.urls')),
]
```

## API Endpoints

### Courses
- `GET /courses/api/courses/` - List courses with filtering
- `GET /courses/api/courses/{id}/` - Retrieve course details
- `POST /courses/api/courses/` - Create course (instructors only)
- `PUT /courses/api/courses/{id}/` - Update course (instructors only)
- `DELETE /courses/api/courses/{id}/` - Delete course (instructors only)
- `POST /courses/api/courses/{id}/enroll/` - Enroll in course
- `POST /courses/api/courses/{id}/unenroll/` - Unenroll from course
- `POST /courses/api/courses/{id}/rate/` - Rate course
- `GET /courses/api/courses/{id}/my_progress/` - Get user's progress
- `GET /courses/api/courses/{id}/analytics/` - Get course analytics (instructors)

### Modules & Lessons
- `GET /courses/api/courses/{course_id}/modules/` - List course modules
- `POST /courses/api/courses/{course_id}/modules/` - Create module
- `GET /courses/api/courses/{course_id}/modules/{module_id}/lessons/` - List module lessons
- `POST /courses/api/courses/{course_id}/modules/{module_id}/lessons/` - Create lesson
- `POST /courses/api/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/mark_complete/` - Mark lesson complete
- `POST /courses/api/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/update_progress/` - Update lesson progress

### Additional Endpoints
- `GET /courses/api/search/` - Advanced course search
- `GET /courses/api/my-enrollments/` - User's enrollments
- `GET /courses/api/dashboard/stats/` - Dashboard statistics
- `POST /courses/api/generate-certificate/{enrollment_id}/` - Generate certificate
- `GET /courses/api/tags/` - Course tags
- `GET /courses/api/certificates/` - User certificates
- `GET /courses/api/waitlist/` - Waitlist entries

## Usage Examples

### Creating a Course

```python
import requests

course_data = {
    "title": "Introduction to Machine Learning",
    "description": "Learn the fundamentals of machine learning",
    "short_description": "ML basics for beginners",
    "difficulty_level": "beginner",
    "language": "English",
    "estimated_hours": 40,
    "tags": ["machine-learning", "python", "ai"]
}

response = requests.post('/courses/api/courses/', json=course_data)
```

### Enrolling in a Course

```python
response = requests.post(f'/courses/api/courses/{course_id}/enroll/')
```

### Tracking Progress

```python
progress_data = {
    "completion_percentage": 75,
    "time_spent": 3600  # seconds
}

response = requests.post(
    f'/courses/api/courses/{course_id}/modules/{module_id}/lessons/{lesson_id}/update_progress/',
    json=progress_data
)
```

### Searching Courses

```python
params = {
    "q": "python programming",
    "difficulty_level": ["beginner", "intermediate"],
    "min_rating": 4.0,
    "tags": ["python", "programming"]
}

response = requests.get('/courses/api/search/', params=params)
```

## Permissions

The system uses role-based permissions:

- **Anonymous users**: Can view published courses
- **Students**: Can enroll, view content, track progress, rate courses
- **Instructors**: Can create and manage their courses, view analytics
- **Staff/Admin**: Full access to all functionality

## Advanced Features

### AI Integration

The system includes placeholders for AI-powered features:
- Automatic content analysis and difficulty scoring
- Personalized learning recommendations
- Risk prediction for student dropouts
- Sentiment analysis for course reviews

### Analytics

Comprehensive analytics tracking includes:
- Enrollment trends and patterns
- Student engagement metrics
- Completion rates by module/lesson
- Rating and review analysis
- Revenue tracking (with payment integration)

### Scalability

The system is designed for scalability with:
- Efficient database queries with select_related/prefetch_related
- Proper indexing on frequently queried fields
- Pagination for large datasets
- Rate limiting to prevent abuse
- Caching-ready serializer structure

## Next Steps

1. **Payment Integration**: Add pricing models and payment processing
2. **Video Processing**: Integrate with video hosting services
3. **Real-time Features**: Add WebSocket support for live progress updates
4. **Mobile API**: Optimize endpoints for mobile applications
5. **AI Enhancement**: Implement actual machine learning models for predictions
6. **Notifications**: Add email and push notification systems
7. **Forum Integration**: Connect with discussion forums
8. **Assessment System**: Integrate with quiz and assignment modules

## Testing

Run the course tests:

```bash
python manage.py test apps.courses
```

## Contributing

When adding new features:
1. Update the models with appropriate fields and methods
2. Create/update serializers for API representation
3. Add/modify views for business logic
4. Update URL configurations
5. Add admin interfaces for management
6. Write comprehensive tests
7. Update documentation

The course system serves as the foundation for the entire learning management system and integrates with other modules like assessments, communications, and analytics.
