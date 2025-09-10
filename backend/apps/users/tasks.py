"""
Celery tasks for user management, analytics, and personalization.
"""

from celery import shared_task
from django.conf import settings
import logging
import requests
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='apps.users.tasks.generate_user_analytics')
def generate_user_analytics(self, user_id, period_days=30):
    """
    Generate comprehensive analytics for a user's learning activity.
    
    Args:
        user_id (int): ID of the user
        period_days (int): Number of days to analyze (default: 30)
    
    Returns:
        dict: User analytics including learning progress, engagement metrics
    """
    try:
        logger.info(f"Generating analytics for user {user_id} over {period_days} days")
        
        # In a real implementation, you'd query the database for user activity
        # For now, we'll simulate analytics data
        
        analytics_data = {
            "user_id": user_id,
            "period_days": period_days,
            "learning_metrics": {
                "courses_enrolled": 3,
                "courses_completed": 1,
                "total_study_time_hours": 25.5,
                "average_session_duration": "45 minutes",
                "login_frequency": 4.2,  # logins per week
                "streak_days": 12
            },
            "performance_metrics": {
                "average_quiz_score": 85.7,
                "assignments_submitted": 8,
                "assignments_completed_on_time": 7,
                "improvement_rate": 0.15,  # 15% improvement
                "mastery_level": "Intermediate"
            },
            "engagement_metrics": {
                "forum_posts": 5,
                "questions_asked": 3,
                "peer_interactions": 12,
                "resources_accessed": 45,
                "badges_earned": 2
            },
            "learning_path": {
                "current_objectives": ["Complete Module 3", "Master Python Basics"],
                "recommended_next_steps": ["Advanced Python", "Data Structures"],
                "difficulty_areas": ["Algorithm Complexity", "OOP Concepts"],
                "strength_areas": ["Basic Syntax", "Control Structures"]
            }
        }
        
        logger.info(f"Analytics generated for user {user_id}: {analytics_data['learning_metrics']['total_study_time_hours']} hours studied")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'analytics': analytics_data,
            'generated_at': datetime.now().isoformat(),
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Analytics generation failed for user {user_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.users.tasks.send_personalized_recommendations')
def send_personalized_recommendations(self, user_id):
    """
    Generate and send personalized learning recommendations to a user.
    
    Args:
        user_id (int): ID of the user
    
    Returns:
        dict: Recommendation results
    """
    try:
        logger.info(f"Generating personalized recommendations for user {user_id}")
        
        # Call AI services to generate recommendations
        ai_service_url = "http://localhost:8001/recommend"
        
        payload = {
            "user_id": user_id,
            "recommendation_types": ["courses", "resources", "study_schedule"],
            "max_recommendations": 5
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            recommendations = response.json()
        except Exception as e:
            logger.error(f"Failed to call AI recommendation service: {e}")
            # Fallback recommendations
            recommendations = {
                "courses": [
                    {"title": "Advanced Python Programming", "relevance_score": 0.9},
                    {"title": "Data Science Fundamentals", "relevance_score": 0.8}
                ],
                "resources": [
                    {"title": "Python Best Practices Guide", "type": "article"},
                    {"title": "Interactive Python Exercises", "type": "practice"}
                ],
                "study_schedule": {
                    "optimal_study_time": "evenings",
                    "recommended_session_length": 45,
                    "suggested_frequency": "daily"
                }
            }
        
        # Send recommendations via communication service
        comm_service_url = "http://localhost:8003/send-notification"
        
        notification_payload = {
            "user_id": user_id,
            "type": "recommendations",
            "content": recommendations,
            "delivery_method": "email"
        }
        
        try:
            comm_response = requests.post(comm_service_url, json=notification_payload, timeout=30)
            comm_response.raise_for_status()
            notification_sent = True
        except Exception as e:
            logger.error(f"Failed to send recommendations notification: {e}")
            notification_sent = False
        
        logger.info(f"Recommendations generated and sent to user {user_id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommendations': recommendations,
            'notification_sent': notification_sent,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Recommendation generation failed for user {user_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.users.tasks.update_user_profile')
def update_user_profile(self, user_id, profile_updates):
    """
    Update user profile with additional computed data.
    
    Args:
        user_id (int): ID of the user
        profile_updates (dict): Profile data to update
    
    Returns:
        dict: Update results
    """
    try:
        logger.info(f"Updating profile for user {user_id}")
        
        # In a real implementation, you'd update the user model
        # Here we simulate the update process
        
        updated_fields = []
        for field, value in profile_updates.items():
            # Simulate field validation and update
            updated_fields.append(field)
        
        # Generate additional computed profile data
        computed_data = {
            "learning_style": "Visual/Kinesthetic",
            "skill_level": "Intermediate",
            "preferred_difficulty": "Medium",
            "estimated_graduation": "2024-12-15",
            "completion_rate": 0.78
        }
        
        logger.info(f"Profile updated for user {user_id}: {len(updated_fields)} fields")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'updated_fields': updated_fields,
            'computed_data': computed_data,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Profile update failed for user {user_id}: {exc}")
        self.retry(countdown=30, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.users.tasks.process_user_feedback')
def process_user_feedback(self, feedback_id, user_id, feedback_type, content):
    """
    Process and analyze user feedback for system improvements.
    
    Args:
        feedback_id (int): ID of the feedback
        user_id (int): ID of the user who provided feedback
        feedback_type (str): Type of feedback (bug, suggestion, complaint, etc.)
        content (str): Feedback content
    
    Returns:
        dict: Processing results
    """
    try:
        logger.info(f"Processing feedback {feedback_id} from user {user_id}")
        
        # Analyze feedback sentiment and content
        ai_service_url = "http://localhost:8001/analyze-feedback"
        
        payload = {
            "feedback_content": content,
            "feedback_type": feedback_type,
            "user_context": {"user_id": user_id}
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=30)
            response.raise_for_status()
            analysis = response.json()
        except Exception as e:
            logger.error(f"Failed to analyze feedback: {e}")
            # Fallback analysis
            analysis = {
                "sentiment": "neutral",
                "category": feedback_type,
                "priority": "medium",
                "key_topics": ["user experience", "system performance"],
                "suggested_actions": ["Review UI design", "Optimize response times"]
            }
        
        # Store analysis results and create action items if needed
        if analysis.get('priority') == 'high':
            # Create high-priority ticket for immediate attention
            logger.warning(f"High priority feedback detected: {feedback_id}")
        
        logger.info(f"Feedback {feedback_id} processed with sentiment: {analysis['sentiment']}")
        
        return {
            'status': 'success',
            'feedback_id': feedback_id,
            'user_id': user_id,
            'analysis': analysis,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Feedback processing failed for feedback {feedback_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.users.tasks.cleanup_inactive_users')
def cleanup_inactive_users(self, days_threshold=365):
    """
    Periodic task to clean up inactive user accounts and associated data.
    
    Args:
        days_threshold (int): Number of days of inactivity before cleanup (default: 365)
    
    Returns:
        dict: Cleanup results
    """
    try:
        logger.info(f"Starting cleanup of users inactive for more than {days_threshold} days")
        
        # In a real implementation, you'd query for inactive users
        # and handle data cleanup according to privacy policies
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # Simulate cleanup process
        inactive_users_found = 0  # Placeholder
        users_archived = 0
        data_anonymized = 0
        
        cleanup_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "inactive_users_found": inactive_users_found,
            "users_archived": users_archived,
            "data_anonymized": data_anonymized,
            "total_storage_freed_mb": 0  # Placeholder
        }
        
        logger.info(f"User cleanup completed: {users_archived} users archived, {data_anonymized} records anonymized")
        
        return {
            'status': 'success',
            'cleanup_summary': cleanup_summary,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"User cleanup failed: {exc}")
        # Don't retry cleanup tasks automatically to avoid data issues
        raise exc

@shared_task(bind=True, name='apps.users.tasks.generate_learning_path')
def generate_learning_path(self, user_id, target_skills, timeline_months=6):
    """
    Generate a personalized learning path for a user based on their goals.
    
    Args:
        user_id (int): ID of the user
        target_skills (list): List of skills the user wants to learn
        timeline_months (int): Desired timeline in months
    
    Returns:
        dict: Generated learning path
    """
    try:
        logger.info(f"Generating learning path for user {user_id} with {len(target_skills)} target skills")
        
        # Call AI Content Service to generate learning path
        ai_service_url = "http://localhost:8001/generate-learning-path"
        
        payload = {
            "user_id": user_id,
            "target_skills": target_skills,
            "timeline_months": timeline_months,
            "learning_style": "adaptive"  # Could be derived from user profile
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=45)
            response.raise_for_status()
            learning_path = response.json()
        except Exception as e:
            logger.error(f"Failed to generate learning path: {e}")
            # Fallback learning path
            learning_path = {
                "total_duration_months": timeline_months,
                "phases": [
                    {
                        "phase": 1,
                        "title": "Foundation Building",
                        "duration_weeks": 4,
                        "courses": ["Introduction to Programming", "Basic Algorithms"],
                        "skills_covered": target_skills[:2] if target_skills else ["Programming Basics"]
                    },
                    {
                        "phase": 2,
                        "title": "Skill Development", 
                        "duration_weeks": 8,
                        "courses": ["Intermediate Programming", "Data Structures"],
                        "skills_covered": target_skills[2:4] if len(target_skills) > 2 else ["Advanced Programming"]
                    }
                ],
                "milestones": [
                    {"week": 4, "title": "Complete Foundation", "requirements": ["Pass all quizzes"]},
                    {"week": 12, "title": "Intermediate Proficiency", "requirements": ["Complete projects"]}
                ],
                "estimated_study_hours_per_week": 8
            }
        
        logger.info(f"Learning path generated for user {user_id}: {learning_path['total_duration_months']} months")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'learning_path': learning_path,
            'target_skills': target_skills,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Learning path generation failed for user {user_id}: {exc}")
        self.retry(countdown=60, max_retries=3, exc=exc)
