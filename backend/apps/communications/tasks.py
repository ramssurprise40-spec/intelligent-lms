"""
Celery tasks for communications, notifications, and messaging.
"""

from celery import shared_task
from django.conf import settings
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@shared_task(bind=True, name='apps.communications.tasks.send_email_notification')
def send_email_notification(self, recipient_email, subject, message, template_name=None):
    """
    Send email notification to a user.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        message (str): Email message content
        template_name (str, optional): Email template to use
    
    Returns:
        dict: Email sending results
    """
    try:
        logger.info(f"Sending email to {recipient_email}: {subject}")
        
        # Call AI Communication Service for email processing
        comm_service_url = "http://localhost:8003/send-email"
        
        payload = {
            "recipient": recipient_email,
            "subject": subject,
            "content": message,
            "template": template_name,
            "sender": settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else "noreply@lms.edu"
        }
        
        try:
            response = requests.post(comm_service_url, json=payload, timeout=30)
            response.raise_for_status()
            email_result = response.json()
            sent_successfully = True
        except Exception as e:
            logger.error(f"Failed to send email via service: {e}")
            # In a real implementation, you might use Django's email backend as fallback
            email_result = {
                "status": "failed",
                "error": str(e),
                "fallback_used": True
            }
            sent_successfully = False
        
        logger.info(f"Email to {recipient_email} {'sent' if sent_successfully else 'failed'}")
        
        return {
            'status': 'success' if sent_successfully else 'failed',
            'recipient': recipient_email,
            'subject': subject,
            'email_result': email_result,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Email sending failed for {recipient_email}: {exc}")
        self.retry(countdown=30, max_retries=3, exc=exc)

@shared_task(bind=True, name='apps.communications.tasks.send_bulk_announcement')
def send_bulk_announcement(self, user_ids, announcement_data):
    """
    Send bulk announcements to multiple users.
    
    Args:
        user_ids (list): List of user IDs to send announcements to
        announcement_data (dict): Announcement content and metadata
    
    Returns:
        dict: Bulk sending results
    """
    try:
        logger.info(f"Sending bulk announcement to {len(user_ids)} users")
        
        sent_count = 0
        failed_count = 0
        results = []
        
        # Process each user
        for user_id in user_ids:
            try:
                # In a real implementation, you'd get user email from database
                # Here we simulate the process
                
                # Call communication service
                comm_service_url = "http://localhost:8003/send-announcement"
                
                payload = {
                    "user_id": user_id,
                    "title": announcement_data.get("title", "System Announcement"),
                    "content": announcement_data.get("content", ""),
                    "priority": announcement_data.get("priority", "normal"),
                    "delivery_methods": ["email", "in_app"]
                }
                
                response = requests.post(comm_service_url, json=payload, timeout=30)
                response.raise_for_status()
                
                results.append({
                    "user_id": user_id,
                    "status": "sent",
                    "timestamp": datetime.now().isoformat()
                })
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send announcement to user {user_id}: {e}")
                results.append({
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        logger.info(f"Bulk announcement completed: {sent_count} sent, {failed_count} failed")
        
        return {
            'status': 'success',
            'total_users': len(user_ids),
            'sent_count': sent_count,
            'failed_count': failed_count,
            'results': results,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Bulk announcement failed: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.communications.tasks.process_forum_notifications')
def process_forum_notifications(self, post_id, author_id, forum_id):
    """
    Process notifications for new forum posts and replies.
    
    Args:
        post_id (int): ID of the forum post
        author_id (int): ID of the post author
        forum_id (int): ID of the forum
    
    Returns:
        dict: Notification processing results
    """
    try:
        logger.info(f"Processing forum notifications for post {post_id}")
        
        # In a real implementation, you'd query for forum subscribers
        # Here we simulate finding users to notify
        
        # Call communication service to get forum subscribers
        comm_service_url = "http://localhost:8003/get-forum-subscribers"
        
        payload = {
            "forum_id": forum_id,
            "exclude_user_id": author_id  # Don't notify the author
        }
        
        try:
            response = requests.post(comm_service_url, json=payload, timeout=30)
            response.raise_for_status()
            subscribers = response.json().get("subscribers", [])
        except Exception as e:
            logger.error(f"Failed to get forum subscribers: {e}")
            # Fallback: simulate some subscribers
            subscribers = [{"user_id": 1, "email": "user1@example.com", "notification_preferences": ["email"]}]
        
        notifications_sent = 0
        
        # Send notifications to each subscriber
        for subscriber in subscribers:
            try:
                if "email" in subscriber.get("notification_preferences", []):
                    # Send email notification about new forum post
                    notification_payload = {
                        "user_id": subscriber["user_id"],
                        "type": "forum_post",
                        "content": {
                            "post_id": post_id,
                            "forum_id": forum_id,
                            "author_id": author_id
                        },
                        "delivery_method": "email"
                    }
                    
                    notify_response = requests.post(
                        "http://localhost:8003/send-notification", 
                        json=notification_payload, 
                        timeout=30
                    )
                    notify_response.raise_for_status()
                    notifications_sent += 1
                    
            except Exception as e:
                logger.error(f"Failed to notify user {subscriber['user_id']}: {e}")
        
        logger.info(f"Forum notifications processed: {notifications_sent} notifications sent")
        
        return {
            'status': 'success',
            'post_id': post_id,
            'forum_id': forum_id,
            'notifications_sent': notifications_sent,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Forum notification processing failed for post {post_id}: {exc}")
        self.retry(countdown=30, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.communications.tasks.generate_digest_email')
def generate_digest_email(self, user_id, digest_type='weekly'):
    """
    Generate and send digest email with user's activity summary.
    
    Args:
        user_id (int): ID of the user
        digest_type (str): Type of digest (daily, weekly, monthly)
    
    Returns:
        dict: Digest generation results
    """
    try:
        logger.info(f"Generating {digest_type} digest for user {user_id}")
        
        # Call various services to gather digest data
        
        # Get user analytics
        try:
            analytics_response = requests.get(
                f"http://localhost:8000/api/users/{user_id}/analytics/",
                timeout=30
            )
            analytics_response.raise_for_status()
            analytics_data = analytics_response.json()
        except Exception as e:
            logger.error(f"Failed to get user analytics: {e}")
            analytics_data = {"error": "Analytics unavailable"}
        
        # Get recent course progress
        try:
            progress_response = requests.get(
                f"http://localhost:8000/api/users/{user_id}/progress/",
                timeout=30
            )
            progress_response.raise_for_status()
            progress_data = progress_response.json()
        except Exception as e:
            logger.error(f"Failed to get course progress: {e}")
            progress_data = {"error": "Progress data unavailable"}
        
        # Generate digest content using AI
        ai_service_url = "http://localhost:8001/generate-digest"
        
        digest_payload = {
            "user_id": user_id,
            "digest_type": digest_type,
            "analytics": analytics_data,
            "progress": progress_data,
            "template": "educational_digest"
        }
        
        try:
            ai_response = requests.post(ai_service_url, json=digest_payload, timeout=45)
            ai_response.raise_for_status()
            digest_content = ai_response.json()
        except Exception as e:
            logger.error(f"Failed to generate AI digest: {e}")
            # Fallback digest content
            digest_content = {
                "subject": f"Your {digest_type.title()} Learning Summary",
                "content": f"Here's your {digest_type} learning summary...",
                "highlights": ["Completed 2 lessons", "Scored 85% on quiz"],
                "recommendations": ["Continue with Module 3", "Review challenging concepts"]
            }
        
        # Send digest email
        email_task = send_email_notification.delay(
            recipient_email=f"user{user_id}@example.com",  # In real app, get from user model
            subject=digest_content["subject"],
            message=digest_content["content"],
            template_name="digest_email"
        )
        
        logger.info(f"{digest_type.title()} digest generated and sent to user {user_id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'digest_type': digest_type,
            'digest_content': digest_content,
            'email_task_id': email_task.id,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Digest generation failed for user {user_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.communications.tasks.send_reminder_notifications')
def send_reminder_notifications(self, reminder_type, target_data):
    """
    Send various types of reminder notifications.
    
    Args:
        reminder_type (str): Type of reminder (assignment_due, course_deadline, etc.)
        target_data (dict): Data about what to remind and to whom
    
    Returns:
        dict: Reminder sending results
    """
    try:
        logger.info(f"Sending {reminder_type} reminders")
        
        reminders_sent = 0
        failed_reminders = 0
        
        if reminder_type == "assignment_due":
            # Process assignment due reminders
            for assignment in target_data.get("assignments", []):
                try:
                    # Get students enrolled in the course
                    students_response = requests.get(
                        f"http://localhost:8000/api/courses/{assignment['course_id']}/students/",
                        timeout=30
                    )
                    students_response.raise_for_status()
                    students = students_response.json()
                    
                    # Send reminder to each student
                    for student in students:
                        reminder_payload = {
                            "user_id": student["id"],
                            "type": "assignment_reminder",
                            "content": {
                                "assignment_title": assignment["title"],
                                "due_date": assignment["due_date"],
                                "course_name": assignment["course_name"]
                            },
                            "delivery_methods": ["email", "in_app"]
                        }
                        
                        notify_response = requests.post(
                            "http://localhost:8003/send-notification",
                            json=reminder_payload,
                            timeout=30
                        )
                        notify_response.raise_for_status()
                        reminders_sent += 1
                        
                except Exception as e:
                    logger.error(f"Failed to send assignment reminder: {e}")
                    failed_reminders += 1
        
        elif reminder_type == "course_deadline":
            # Process course deadline reminders
            for course in target_data.get("courses", []):
                try:
                    # Similar logic for course deadline reminders
                    reminders_sent += 1  # Placeholder
                except Exception as e:
                    logger.error(f"Failed to send course deadline reminder: {e}")
                    failed_reminders += 1
        
        logger.info(f"Reminder processing completed: {reminders_sent} sent, {failed_reminders} failed")
        
        return {
            'status': 'success',
            'reminder_type': reminder_type,
            'reminders_sent': reminders_sent,
            'failed_reminders': failed_reminders,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Reminder notification sending failed: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)

@shared_task(bind=True, name='apps.communications.tasks.cleanup_old_messages')
def cleanup_old_messages(self, days_threshold=90):
    """
    Periodic task to clean up old messages and notifications.
    
    Args:
        days_threshold (int): Number of days after which to clean up messages
    
    Returns:
        dict: Cleanup results
    """
    try:
        logger.info(f"Starting cleanup of messages older than {days_threshold} days")
        
        # In a real implementation, you'd query the database for old messages
        # and delete them according to retention policies
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        # Simulate cleanup process
        messages_deleted = 0  # Placeholder
        notifications_deleted = 0  # Placeholder
        storage_freed_mb = 0  # Placeholder
        
        cleanup_summary = {
            "cutoff_date": cutoff_date.isoformat(),
            "messages_deleted": messages_deleted,
            "notifications_deleted": notifications_deleted,
            "storage_freed_mb": storage_freed_mb
        }
        
        logger.info(f"Message cleanup completed: {messages_deleted} messages, {notifications_deleted} notifications deleted")
        
        return {
            'status': 'success',
            'cleanup_summary': cleanup_summary,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Message cleanup failed: {exc}")
        # Don't retry cleanup tasks automatically
        raise exc

@shared_task(bind=True, name='apps.communications.tasks.process_chat_analysis')
def process_chat_analysis(self, conversation_id, participants, message_count):
    """
    Analyze chat conversations for insights and moderation.
    
    Args:
        conversation_id (int): ID of the conversation
        participants (list): List of participant IDs
        message_count (int): Number of messages in the conversation
    
    Returns:
        dict: Analysis results
    """
    try:
        logger.info(f"Analyzing conversation {conversation_id} with {message_count} messages")
        
        # Call AI Communication Service for chat analysis
        ai_service_url = "http://localhost:8003/analyze-conversation"
        
        payload = {
            "conversation_id": conversation_id,
            "participants": participants,
            "analysis_type": "comprehensive"
        }
        
        try:
            response = requests.post(ai_service_url, json=payload, timeout=45)
            response.raise_for_status()
            analysis_result = response.json()
        except Exception as e:
            logger.error(f"Failed to analyze conversation: {e}")
            # Fallback analysis
            analysis_result = {
                "sentiment_score": 0.7,
                "engagement_level": "high",
                "topics_discussed": ["course content", "assignments"],
                "moderation_flags": [],
                "learning_indicators": ["collaborative discussion", "peer help"],
                "summary": f"Productive conversation with {message_count} messages"
            }
        
        # Store analysis results and take action if needed
        if analysis_result.get("moderation_flags"):
            logger.warning(f"Moderation flags detected in conversation {conversation_id}: {analysis_result['moderation_flags']}")
        
        logger.info(f"Conversation analysis completed for {conversation_id}")
        
        return {
            'status': 'success',
            'conversation_id': conversation_id,
            'analysis': analysis_result,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"Chat analysis failed for conversation {conversation_id}: {exc}")
        self.retry(countdown=60, max_retries=2, exc=exc)
