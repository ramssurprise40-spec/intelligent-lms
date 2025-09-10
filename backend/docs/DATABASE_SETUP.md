# Database Setup and Configuration

This document provides comprehensive information about the database setup, models, migrations, and configuration for the Intelligent LMS system.

## Overview

The Intelligent LMS uses a hybrid approach for database management:
- **PostgreSQL with pgvector** for production environments (with vector similarity search capabilities)
- **SQLite** as a fallback for development environments
- **Connection pooling** for production performance optimization
- **Comprehensive model relationships** across all system components

## Database Architecture

### Core Applications and Models

#### 1. Users App (`apps.users`)
- **User Model**: Custom user model with roles (admin, instructor, student)
- **Profile Model**: Extended user profiles with additional metadata
- **Enrollment Model**: Student course enrollments with progress tracking

#### 2. Courses App (`apps.courses`)
- **Course Model**: Course information, metadata, and instructor assignments
- **CourseModule Model**: Course content organization into modules
- **Lesson Model**: Individual lessons within modules
- **CourseTag Model**: Categorization and tagging system
- **CourseTagging Model**: Many-to-many relationship for course tags
- **Progress Models**: Student progress tracking

#### 3. Assessments App (`apps.assessments`)
- **Assessment Model**: Quizzes, assignments, and exams
- **Question Model**: Individual assessment questions
- **AssessmentSubmission Model**: Student submissions
- **QuestionResponse Model**: Individual question responses
- **GradingRubric Model**: Detailed grading criteria
- **PeerReview Model**: Peer review assignments

#### 4. Communications App (`apps.communications`)
- **Forum Model**: Course discussion forums
- **ForumTopic Model**: Discussion topics/threads
- **ForumPost Model**: Individual forum posts
- **DirectMessage Model**: Private messaging between users
- **Announcement Model**: Course and system announcements
- **ChatRoom Model**: Real-time chat functionality

## Database Configuration

### Environment-Based Configuration

The system supports multiple database configurations based on the environment:

```python
# Development (SQLite fallback)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Production (PostgreSQL with pooling)
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 15,
        }
    }
}
```

### Required Environment Variables

For production PostgreSQL setup:

```bash
# Database Configuration
DATABASE_NAME=intelligent_lms
DATABASE_USER=lms_user
DATABASE_PASSWORD=your_secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_SSL_MODE=require

# Connection Pooling
DATABASE_MAX_CONNS=20
DATABASE_MIN_CONNS=5
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=7200

# Environment
DJANGO_ENV=production
```

## Required Dependencies

### Core Database Dependencies
```bash
pip install psycopg2-binary  # PostgreSQL adapter
pip install pgvector        # Vector similarity search
pip install django-extensions  # Additional model utilities
pip install dj-database-url    # Database URL parsing
```

### Optional Production Dependencies
```bash
pip install dj-db-conn-pool    # Connection pooling
pip install django-prometheus  # Database metrics
```

## Database Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your database configuration:
```bash
cp .env.example .env
# Edit .env with your database settings
```

### 3. Run Migrations
```bash
# Create migrations for all apps
python manage.py makemigrations users courses assessments communications

# Apply migrations
python manage.py migrate
```

### 4. Initialize Database
```bash
# Initialize database with sample data
python manage.py init_db

# Test database models (optional)
python manage.py test_models --verbose
```

### 5. Create Superuser (optional)
```bash
python manage.py createsuperuser
```

## PostgreSQL Setup

### Install PostgreSQL with pgvector

#### Ubuntu/Debian:
```bash
# Install PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Install pgvector extension
sudo apt-get install postgresql-14-pgvector
```

#### macOS (using Homebrew):
```bash
# Install PostgreSQL
brew install postgresql

# Install pgvector
brew install pgvector
```

#### Docker:
```bash
# Run PostgreSQL with pgvector
docker run -d \
  --name intelligent-lms-postgres \
  -e POSTGRES_USER=lms_user \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=intelligent_lms \
  -p 5432:5432 \
  ankane/pgvector
```

### Database Setup Commands

```sql
-- Create database and user
CREATE DATABASE intelligent_lms;
CREATE USER lms_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE intelligent_lms TO lms_user;

-- Connect to the database and enable extensions
\c intelligent_lms;
CREATE EXTENSION IF NOT EXISTS pgvector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gin;
```

## Management Commands

### Database Initialization
```bash
# Full initialization with all sample data
python manage.py init_db

# Initialize without specific components
python manage.py init_db --skip-users
python manage.py init_db --skip-courses
python manage.py init_db --skip-assessments
```

### Model Testing
```bash
# Basic model tests
python manage.py test_models

# Verbose output with detailed information
python manage.py test_models --verbose

# Include complex query performance tests
python manage.py test_models --verbose --test-queries
```

### Database Utilities
```bash
# Check database health
python manage.py shell -c "
from config.database_pool import check_database_health
print(check_database_health())
"

# Get connection pool statistics
python manage.py shell -c "
from config.database_pool import get_pool_statistics
print(get_pool_statistics())
"
```

## Performance Optimization

### Indexes

The system includes optimized indexes for common queries:

```sql
-- User activity indexes
CREATE INDEX users_user_last_login_idx ON users_user (last_login DESC);
CREATE INDEX users_user_role_active_idx ON users_user (role, is_active);

-- Course search and filtering
CREATE INDEX courses_course_status_created_idx ON courses_course (status, created_at DESC);
CREATE INDEX courses_course_instructor_status_idx ON courses_course (instructor_id, status);

-- Assessment performance
CREATE INDEX assessments_submission_student_submitted_idx ON assessments_submission (student_id, submitted_at DESC);
CREATE INDEX assessments_assessment_course_type_idx ON assessments_assessment (course_id, assessment_type);
```

### Connection Pooling

For production environments, connection pooling is automatically configured:

- **Pool Size**: 10 connections (configurable)
- **Max Overflow**: 15 additional connections
- **Connection Recycling**: Every 2 hours
- **Pool Timeout**: 30 seconds

### Query Optimization

The models use optimized query patterns:
- `select_related()` for foreign key relationships
- `prefetch_related()` for many-to-many and reverse foreign key relationships
- Database-level constraints for data integrity
- Efficient indexing strategies

## Data Models Summary

### Key Relationships

```
User (1) ←→ (M) Course [instructor]
User (M) ←→ (M) Course [enrollments]
Course (1) ←→ (M) CourseModule
CourseModule (1) ←→ (M) Lesson
Course (1) ←→ (M) Assessment
Assessment (1) ←→ (M) Question
User (M) ←→ (M) AssessmentSubmission
Course (1) ←→ (M) Forum
Forum (1) ←→ (M) ForumTopic
ForumTopic (1) ←→ (M) ForumPost
User (M) ←→ (M) DirectMessage [sender/recipient]
```

### Model Field Summary

#### User Model Fields
- Basic: `username`, `email`, `first_name`, `last_name`
- Role: `role` (admin/instructor/student)
- Profile: `bio`, `avatar`, `timezone`, `language`
- Academic: `student_id`, `graduation_year`, `specialization`
- Status: `is_active`, `is_verified`, `is_staff`

#### Course Model Fields
- Basic: `title`, `slug`, `description`, `short_description`
- Academic: `instructor`, `difficulty_level`, `estimated_hours`
- Content: `learning_objectives`, `prerequisites`, `language`
- Status: `status`, `is_featured`, `enrollment_limit`
- Metadata: `created_at`, `updated_at`, `published_at`

#### Assessment Model Fields
- Basic: `title`, `description`, `assessment_type`
- Grading: `max_score`, `passing_score`, `grading_method`
- Timing: `available_from`, `due_date`, `time_limit_minutes`
- Attempts: `max_attempts`, `allow_late_submission`
- AI: `auto_generate_feedback`, `plagiarism_check`

## Troubleshooting

### Common Issues

#### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate --fake users zero
python manage.py migrate --fake courses zero
python manage.py migrate --fake assessments zero
python manage.py migrate --fake communications zero

# Recreate migrations
python manage.py makemigrations
python manage.py migrate
```

#### PostgreSQL Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check pgvector extension
psql -U lms_user -d intelligent_lms -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

#### Performance Issues
```bash
# Check slow queries
tail -f logs/slow_queries.log

# Monitor database connections
python manage.py shell -c "
from config.database_pool import check_database_health, get_pool_statistics
print('Health:', check_database_health())
print('Pool Stats:', get_pool_statistics())
"
```

### Database Maintenance

#### Regular Maintenance Tasks
```bash
# PostgreSQL vacuum and analyze
psql -U lms_user -d intelligent_lms -c "VACUUM ANALYZE;"

# Update table statistics
psql -U lms_user -d intelligent_lms -c "ANALYZE;"

# Check database size
psql -U lms_user -d intelligent_lms -c "
SELECT pg_size_pretty(pg_database_size('intelligent_lms')) AS db_size;
"
```

## Security Considerations

### Database Security
- Use strong passwords for database users
- Enable SSL/TLS for database connections
- Implement connection limits and timeouts
- Regular security updates for PostgreSQL
- Database-level user permissions and roles

### Application Security
- SQL injection prevention through Django ORM
- Parameter validation and sanitization
- Database connection encryption
- Audit logging for sensitive operations

## Monitoring and Logging

### Database Logging
- Query logging for performance analysis
- Slow query detection and logging
- Connection pool monitoring
- Error tracking and alerting

### Metrics Collection
- Database connection metrics
- Query performance metrics
- Table size and growth tracking
- Index usage statistics

## Backup and Recovery

### Backup Strategy
```bash
# Full database backup
pg_dump -U lms_user -h localhost intelligent_lms > backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -U lms_user -h localhost intelligent_lms | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
psql -U lms_user -h localhost intelligent_lms < backup_20231215.sql
```

### Automated Backups
Consider implementing automated backup solutions:
- Daily incremental backups
- Weekly full backups
- Off-site backup storage
- Backup verification procedures

---

For additional support or questions about the database setup, please refer to the project documentation or contact the development team.
