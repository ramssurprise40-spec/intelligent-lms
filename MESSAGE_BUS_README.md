# Message Bus and Task Queue System

## Overview

The Intelligent LMS uses a hybrid message bus and task queue system combining **Celery** for Django backend tasks and **Dramatiq** for FastAPI microservices. This architecture provides robust, scalable background processing with Redis as the message broker.

## Architecture Components

### 🔄 Message Brokers
- **Redis**: Primary message broker and result backend
- **Multiple Redis Databases**: Separate databases for different purposes
  - DB 0: Celery broker and general tasks
  - DB 1: Django cache
  - DB 2: Session storage
  - DB 5: Dramatiq results backend

### 🏭 Task Queue Systems

#### Celery (Django Backend)
- **Purpose**: Django-specific tasks, database operations, user management
- **Queues**: 
  - `default`: General Django tasks
  - `user_tasks`: User-related operations
  - `course_tasks`: Course management
  - `assessment_tasks`: Assessment processing
  - `communication_tasks`: Email and notifications
  - `analytics_tasks`: Data analysis and reporting
  - `system_tasks`: Maintenance and cleanup
  - `high_priority`: Time-sensitive tasks
  - `low_priority`: Background analytics

#### Dramatiq (FastAPI Microservices)
- **Purpose**: AI processing, content generation, search indexing
- **Queues**:
  - `ai_content`: AI content generation
  - `ai_assessment`: AI-powered grading
  - `search`: Search indexing and queries
  - `file_processing`: File uploads and conversion
  - `notifications`: Real-time notifications

## 🚀 Deployment Options

### Local Development
```bash
# Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Start Celery workers
celery -A intelligent_lms worker -l info

# Start Celery Beat scheduler
celery -A intelligent_lms beat -l info

# Start Dramatiq workers
dramatiq tasks --processes 2 --threads 4

# Monitor with Flower
celery -A intelligent_lms flower
```

### Render.com Deployment
The system is fully configured for Render deployment with the `render.yml` configuration:

- **Managed Redis**: Automatic Redis instance with high availability
- **Separate Workers**: Dedicated worker services for different queue types
- **Auto-scaling**: Workers scale based on queue load
- **Monitoring**: Flower dashboard for task monitoring

## 📊 Task Examples

### User Management Tasks
```python
# Email verification
send_email_verification.delay(user_id, verification_url)

# Password reset
send_password_reset_email.delay(user_id, reset_url)

# User analytics
update_user_recommendations.delay()
```

### AI Content Tasks (Dramatiq)
```python
# Generate course summary
generate_course_summary.send(course_id, content, max_length=500)

# Content translation
generate_content_translations.send(course_id, content, ['es', 'fr', 'de'])

# Accessibility enhancement
enhance_content_accessibility.send(course_id, content, 'WCAG_AA')
```

### Communication Tasks
```python
# Bulk notifications
send_bulk_email_notifications.delay(user_emails, subject, message)

# Urgent alerts
send_urgent_notification.delay(user_id, title, message, ['email', 'push', 'sms'])

# Daily digest
send_daily_digest.delay('activity')
```

## 🔧 Configuration

### Django Settings (Celery)
```python
# Redis Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Task Configuration
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Task Routing
CELERY_TASK_ROUTES = {
    'apps.users.tasks.*': {'queue': 'user_tasks'},
    'apps.courses.tasks.*': {'queue': 'course_tasks'},
    'apps.communications.tasks.*': {'queue': 'communication_tasks'},
}
```

### Dramatiq Configuration (FastAPI)
```python
from shared.task_queue import get_task_decorator

# Get configured task decorator
ai_content_task = get_task_decorator('ai_content')

@ai_content_task
def process_content(content_data):
    # AI processing logic
    pass
```

## 📈 Monitoring and Management

### Built-in Monitoring Tools

#### Flower Dashboard
- **URL**: `http://localhost:5555` (local) or `https://flower-monitor.render.com`
- **Features**: Real-time task monitoring, worker statistics, task history
- **Authentication**: Basic auth (`admin:secure_password_2024`)

#### Django Management Command
```bash
# Queue status
python manage.py monitor_tasks --action status --format table

# System health check
python manage.py monitor_tasks --action health --format summary

# Performance analysis
python manage.py monitor_tasks --action performance --format json

# Watch mode (continuous monitoring)
python manage.py monitor_tasks --action status --watch --interval 5

# Worker statistics
python manage.py monitor_tasks --action workers

# Purge queue (with confirmation)
python manage.py monitor_tasks --action purge --queue low_priority

# Cancel specific task
python manage.py monitor_tasks --action cancel --task-id abc123
```

### Programmatic Monitoring
```python
from intelligent_lms.task_monitor import get_system_status, get_performance_report

# Get comprehensive system status
status = get_system_status()

# Generate performance report
report = get_performance_report()

# Health check
health_checker = TaskHealthChecker()
health_status = health_checker.check_system_health()
```

## ⚡ Performance Optimization

### Queue Configuration Best Practices

1. **Separate Workers by Task Type**
   - CPU-intensive tasks: Dedicated workers with fewer processes
   - I/O-bound tasks: More concurrent processes
   - Memory-intensive tasks: Separate workers with memory limits

2. **Priority Queues**
   - `high_priority`: User-facing operations (email verification, password reset)
   - `default`: Regular operations
   - `low_priority`: Analytics and background tasks

3. **Retry Strategies**
   - Exponential backoff for transient failures
   - Different retry limits for different task types
   - Dead letter queues for failed tasks

### Scaling Guidelines

#### Horizontal Scaling (Render)
```yaml
# render.yml scaling configuration
plan: standard  # Auto-scales based on load
```

#### Vertical Scaling
```python
# Worker configuration
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### High Queue Backlog
```bash
# Check queue status
python manage.py monitor_tasks --action status

# Identify bottlenecks
python manage.py monitor_tasks --action performance

# Scale workers (Render auto-scales)
# Or increase worker concurrency locally
```

#### Memory Issues
```python
# Configure worker memory limits
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Restart workers after 100 tasks
CELERY_RESULT_EXPIRES = 3600  # Expire results after 1 hour
```

#### Failed Tasks
```bash
# Monitor failed tasks
python manage.py monitor_tasks --action health

# Check Flower dashboard for detailed error logs
```

### Health Check Endpoints

#### Django Backend
```python
# /health/ endpoint
def health_check(request):
    from intelligent_lms.task_monitor import get_system_status
    status = get_system_status()
    return JsonResponse(status)
```

#### FastAPI Microservices
```python
# /health endpoint
@app.get("/health")
def health_check():
    from shared.task_queue import check_broker_health
    return check_broker_health()
```

## 📋 Task Queue Status

### Current Implementation Status
✅ **Completed Components**:
- Redis message broker configuration
- Celery integration with Django
- Dramatiq integration with FastAPI
- Task routing and queue configuration
- Monitoring and management tools
- Example tasks for all major features
- Render.com deployment configuration
- Comprehensive documentation

### Next Steps
1. **Production Deployment**: Deploy to Render with managed Redis
2. **Monitoring Setup**: Configure alerts and dashboards
3. **Load Testing**: Test system under realistic loads
4. **Optimization**: Fine-tune worker configurations based on usage patterns

## 🔐 Security Considerations

### Message Queue Security
- Redis authentication enabled in production
- TLS encryption for Redis connections
- Task payload validation and sanitization
- Rate limiting for task submissions

### Access Control
- Flower dashboard authentication
- API endpoint protection
- Worker process isolation
- Resource limits and quotas

## 📚 Additional Resources

- [Celery Documentation](https://docs.celeryproject.org/)
- [Dramatiq Documentation](https://dramatiq.io/)
- [Redis Documentation](https://redis.io/documentation)
- [Render Deployment Guide](https://render.com/docs)

## 🤝 Contributing

When adding new tasks:
1. Choose appropriate queue based on task characteristics
2. Implement proper error handling and retries
3. Add monitoring and logging
4. Update documentation
5. Test in both local and production environments

---

This message bus and task queue system provides the foundation for scalable, reliable background processing in the Intelligent LMS. The hybrid approach leverages the strengths of both Celery and Dramatiq while maintaining operational simplicity.
