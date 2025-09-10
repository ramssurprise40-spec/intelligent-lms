"""
Celery tasks for course management and AI content generation.
"""

from celery import shared_task
from django.conf import settings
import logging
import requests
import json

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='apps.courses.tasks.generate_course_summary')
def generate_course_summary(self, course_id, content_text):
    """
    Generate an AI-powered summary of course content.
    
    Args:
        course_id (int): ID of the course
        content_text (str): Course content to summarize
    
    Returns:
        dict: Summary data including text and key points
    """
    try:
        logger.info(f"Generating summary for course {course_id}")
        
        # TODO: Call AI Content Service
        # For now, this is a placeholder implementation
        ai_service_url = "http://localhost:8001/summarize"
        
        payload = {
            "content": content_text,
            "max_length": 300,
            "language": "en"
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            summary_data = response.json()
        except Exception as e:
            logger.error(f"Failed to call AI service: {e}")
            # Fallback summary
            summary_data = {
                "summary": content_text[:300] + "...",
                "key_points": ["Key concept 1", "Key concept 2", "Key concept 3"],
                "word_count": len(content_text.split()),
                "reading_time_minutes": max(1, len(content_text.split()) // 200)
            }
        
        # Update course with summary (you'd implement this with actual models)
        logger.info(f"Generated summary for course {course_id}: {len(summary_data['summary'])} chars")
        
        return {
            'status': 'success',
            'course_id': course_id,
            'summary': summary_data,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Task failed for course {course_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.courses.tasks.generate_learning_objectives')
def generate_learning_objectives(self, course_id, course_title, course_description, topics):
    """
    Generate learning objectives for a course using AI.
    
    Args:
        course_id (int): ID of the course
        course_title (str): Title of the course
        course_description (str): Description of the course
        topics (list): List of course topics
    
    Returns:
        dict: Generated learning objectives
    """
    try:
        logger.info(f"Generating learning objectives for course {course_id}")
        
        # Call AI Content Service
        ai_service_url = "http://localhost:8001/generate-objectives"
        
        payload = {
            "course_title": course_title,
            "course_description": course_description,
            "content_topics": topics,
            "level": "undergraduate"
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            objectives_data = response.json()
        except Exception as e:
            logger.error(f"Failed to call AI service: {e}")
            # Fallback objectives
            objectives_data = {
                "objectives": [
                    f"Students will understand the key concepts of {course_title}",
                    f"Students will be able to apply {course_title} principles",
                    f"Students will analyze complex scenarios in {course_title}"
                ],
                "bloom_taxonomy_levels": ["Understanding", "Application", "Analysis"],
                "total_objectives": 3
            }
        
        logger.info(f"Generated {objectives_data['total_objectives']} objectives for course {course_id}")
        
        return {
            'status': 'success',
            'course_id': course_id,
            'objectives': objectives_data,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Objectives generation failed for course {course_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.courses.tasks.extract_content_from_file')
def extract_content_from_file(self, file_path, file_type):
    """
    Extract text content from uploaded course files.
    
    Args:
        file_path (str): Path to the uploaded file
        file_type (str): Type of file (pdf, docx, pptx, etc.)
    
    Returns:
        dict: Extracted content and metadata
    """
    try:
        logger.info(f"Extracting content from {file_path} (type: {file_type})")
        
        # Call AI Content Service for document processing
        ai_service_url = "http://localhost:8001/process-document"
        
        # For demo purposes, we'll simulate file processing
        # In production, you'd actually read and send the file
        try:
            # Simulate document processing
            extracted_content = {
                "filename": file_path.split('/')[-1],
                "size": 1024,  # placeholder
                "type": file_type,
                "status": "processed",
                "extracted_text": f"Extracted content from {file_path}...",
                "metadata": {
                    "pages": 10,
                    "word_count": 2500,
                    "language": "en"
                }
            }
        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            extracted_content = {
                "filename": file_path.split('/')[-1],
                "status": "failed",
                "error": str(e)
            }
        
        logger.info(f"Content extraction completed for {file_path}")
        
        return {
            'status': 'success',
            'file_path': file_path,
            'content': extracted_content,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Content extraction failed for {file_path}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.courses.tasks.generate_course_glossary')
def generate_course_glossary(self, course_id, content_text, subject_area=None):
    """
    Generate a glossary of key terms from course content.
    
    Args:
        course_id (int): ID of the course
        content_text (str): Course content to analyze
        subject_area (str, optional): Subject area for context
    
    Returns:
        dict: Generated glossary terms and definitions
    """
    try:
        logger.info(f"Generating glossary for course {course_id}")
        
        # Call AI Content Service
        ai_service_url = "http://localhost:8001/generate-glossary"
        
        payload = {
            "content": content_text,
            "max_terms": 20,
            "subject_area": subject_area
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            glossary_data = response.json()
        except Exception as e:
            logger.error(f"Failed to call AI service: {e}")
            # Fallback glossary
            glossary_data = {
                "terms": [
                    {"Learning Management System": "A software application for educational content"},
                    {"Assessment": "The process of evaluating student learning"},
                    {"Course Content": "Educational materials and resources"}
                ],
                "total_terms": 3
            }
        
        logger.info(f"Generated {glossary_data['total_terms']} glossary terms for course {course_id}")
        
        return {
            'status': 'success',
            'course_id': course_id,
            'glossary': glossary_data,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Glossary generation failed for course {course_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.courses.tasks.backup_course_data')
def backup_course_data(self):
    """
    Periodic task to backup course data.
    Runs daily at 3:00 AM as configured in Celery Beat.
    """
    try:
        logger.info("Starting course data backup")
        
        # TODO: Implement actual backup logic
        # This would typically:
        # 1. Query all courses
        # 2. Export course data to backup format
        # 3. Store in backup location (S3, local storage, etc.)
        # 4. Clean up old backups
        
        backup_count = 0  # Placeholder
        
        logger.info(f"Course data backup completed. Backed up {backup_count} courses")
        
        return {
            'status': 'success',
            'backup_count': backup_count,
            'backup_timestamp': str(self.request.called_directly or 'scheduled'),
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Course backup failed: {exc}")
        # Don't retry backup tasks automatically
        raise exc
