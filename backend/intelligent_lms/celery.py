"""
Celery configuration for Intelligent LMS

This module contains the Celery application setup for handling background tasks,
scheduled jobs, and inter-service communication in the Intelligent LMS.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intelligent_lms.settings')

app = Celery('intelligent_lms')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Task routing configuration
app.conf.task_routes = {
    # AI Content Tasks
    'apps.courses.tasks.generate_course_summary': {'queue': 'ai_content'},
    'apps.courses.tasks.generate_learning_objectives': {'queue': 'ai_content'},
    'apps.courses.tasks.extract_content_from_file': {'queue': 'ai_content'},
    'apps.courses.tasks.generate_course_glossary': {'queue': 'ai_content'},
    
    # AI Assessment Tasks
    'apps.assessments.tasks.generate_quiz_from_content': {'queue': 'ai_assessment'},
    'apps.assessments.tasks.grade_assignment_ai': {'queue': 'ai_assessment'},
    'apps.assessments.tasks.analyze_student_performance': {'queue': 'ai_assessment'},
    
    # AI Communication Tasks
    'apps.communications.tasks.draft_email_response': {'queue': 'ai_communication'},
    'apps.communications.tasks.analyze_email_sentiment': {'queue': 'ai_communication'},
    'apps.communications.tasks.categorize_messages': {'queue': 'ai_communication'},
    'apps.communications.tasks.send_bulk_notifications': {'queue': 'communication'},
    
    # Search and Analytics Tasks
    'apps.analytics.tasks.update_search_index': {'queue': 'search'},
    'apps.analytics.tasks.generate_student_insights': {'queue': 'analytics'},
    'apps.analytics.tasks.process_learning_analytics': {'queue': 'analytics'},
    
    # File Processing Tasks
    'apps.files.tasks.process_uploaded_file': {'queue': 'file_processing'},
    'apps.files.tasks.generate_file_preview': {'queue': 'file_processing'},
    'apps.files.tasks.convert_document': {'queue': 'file_processing'},
    
    # System Tasks
    'apps.users.tasks.cleanup_expired_sessions': {'queue': 'system'},
    'apps.courses.tasks.backup_course_data': {'queue': 'system'},
}

# Queue configuration
app.conf.task_create_missing_queues = True
app.conf.task_default_queue = 'default'
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'ai_content': {
        'exchange': 'ai_content',
        'routing_key': 'ai_content',
    },
    'ai_assessment': {
        'exchange': 'ai_assessment',
        'routing_key': 'ai_assessment',
    },
    'ai_communication': {
        'exchange': 'ai_communication',
        'routing_key': 'ai_communication',
    },
    'search': {
        'exchange': 'search',
        'routing_key': 'search',
    },
    'analytics': {
        'exchange': 'analytics',
        'routing_key': 'analytics',
    },
    'file_processing': {
        'exchange': 'file_processing',
        'routing_key': 'file_processing',
    },
    'communication': {
        'exchange': 'communication',
        'routing_key': 'communication',
    },
    'system': {
        'exchange': 'system',
        'routing_key': 'system',
    },
}

# Task result configuration
app.conf.result_expires = 3600  # Results expire after 1 hour
app.conf.result_persistent = True

# Task execution configuration
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Worker configuration
app.conf.worker_max_tasks_per_child = 1000
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_concurrency = 4

# Task retry configuration
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Monitoring and logging
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery functionality."""
    print(f'Request: {self.request!r}')
    return 'Debug task completed successfully!'

# Periodic tasks configuration using Celery Beat
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Daily tasks
    'cleanup-expired-sessions': {
        'task': 'apps.users.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2:00 AM
        'options': {'queue': 'system'}
    },
    
    'backup-course-data': {
        'task': 'apps.courses.tasks.backup_course_data',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3:00 AM
        'options': {'queue': 'system'}
    },
    
    'update-search-index': {
        'task': 'apps.analytics.tasks.update_search_index',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'search'}
    },
    
    # Weekly tasks
    'generate-weekly-analytics': {
        'task': 'apps.analytics.tasks.generate_weekly_report',
        'schedule': crontab(day_of_week=1, hour=4, minute=0),  # Monday at 4:00 AM
        'options': {'queue': 'analytics'}
    },
    
    # Hourly tasks
    'process-pending-notifications': {
        'task': 'apps.communications.tasks.process_pending_notifications',
        'schedule': crontab(minute=0),  # Every hour
        'options': {'queue': 'communication'}
    },
}
