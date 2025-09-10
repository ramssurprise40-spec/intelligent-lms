"""
User models for the Intelligent LMS system.
Includes advanced user profiles, learning analytics, and personalization features.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    Extended user model with additional fields for the LMS.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Administrator'),
        ('teaching_assistant', 'Teaching Assistant'),
        ('content_creator', 'Content Creator'),
        ('institution_admin', 'Institution Admin'),
    ]
    
    LEARNING_STYLE_CHOICES = [
        ('visual', 'Visual'),
        ('auditory', 'Auditory'),
        ('kinesthetic', 'Kinesthetic'),
        ('reading_writing', 'Reading/Writing'),
        ('multimodal', 'Multimodal'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # Profile Information
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    # Learning Preferences
    learning_style = models.CharField(
        max_length=20, 
        choices=LEARNING_STYLE_CHOICES, 
        null=True, 
        blank=True
    )
    preferred_difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')],
        default='medium'
    )
    study_time_preference = models.CharField(
        max_length=20,
        choices=[
            ('morning', 'Morning'),
            ('afternoon', 'Afternoon'),
            ('evening', 'Evening'),
            ('night', 'Night'),
            ('flexible', 'Flexible')
        ],
        default='flexible'
    )
    
    # Privacy and Notifications
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    profile_visibility = models.CharField(
        max_length=10,
        choices=[('public', 'Public'), ('private', 'Private'), ('friends', 'Friends Only')],
        default='public'
    )
    
    # System fields
    is_verified = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # LMS specific fields
    student_id = models.CharField(max_length=20, blank=True, unique=True, null=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    major = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'users_user'
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_instructor(self):
        return self.role in ['instructor', 'teaching_assistant']
    
    @property
    def is_admin(self):
        return self.role in ['admin', 'institution_admin']


class UserProfile(models.Model):
    """
    Extended user profile with learning analytics and AI-generated insights.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Learning Analytics
    total_study_hours = models.FloatField(default=0.0)
    courses_completed = models.IntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ],
        default='beginner'
    )
    
    # Engagement Metrics
    login_streak = models.IntegerField(default=0)
    max_login_streak = models.IntegerField(default=0)
    forum_posts = models.IntegerField(default=0)
    forum_reputation = models.IntegerField(default=100)
    badges_earned = models.IntegerField(default=0)
    
    # AI-Generated Insights
    learning_path_recommendation = models.JSONField(default=dict, blank=True)
    strengths = models.JSONField(default=list, blank=True)  # AI-identified strengths
    improvement_areas = models.JSONField(default=list, blank=True)  # Areas for improvement
    predicted_success_rate = models.FloatField(null=True, blank=True)
    
    # Personalization Data
    content_preferences = models.JSONField(default=dict, blank=True)
    interaction_patterns = models.JSONField(default=dict, blank=True)
    optimal_study_schedule = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_analytics_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users_profile'
        
    def __str__(self):
        return f"Profile for {self.user.username}"
    
    def update_login_streak(self):
        """Update login streak based on current login."""
        now = timezone.now()
        if self.user.last_login and (now - self.user.last_login).days == 1:
            self.login_streak += 1
            if self.login_streak > self.max_login_streak:
                self.max_login_streak = self.login_streak
        elif self.user.last_login and (now - self.user.last_login).days > 1:
            self.login_streak = 1
        else:
            self.login_streak = 1
        self.save()


class UserActivity(models.Model):
    """
    Track user activities for analytics and personalization.
    """
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('course_view', 'Course View'),
        ('lesson_complete', 'Lesson Complete'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('assignment_submit', 'Assignment Submit'),
        ('forum_post', 'Forum Post'),
        ('resource_download', 'Resource Download'),
        ('search', 'Search'),
        ('interaction', 'Interaction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Context data
    object_id = models.CharField(max_length=100, null=True, blank=True)
    object_type = models.CharField(max_length=50, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional data (JSON field for flexibility)
    metadata = models.JSONField(default=dict, blank=True)
    duration = models.DurationField(null=True, blank=True)  # For timed activities
    
    class Meta:
        db_table = 'users_activity'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['activity_type', 'timestamp']),
            models.Index(fields=['session_id']),
        ]
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.timestamp}"


class UserNotification(models.Model):
    """
    User notifications with read status and preferences.
    """
    NOTIFICATION_TYPES = [
        ('system', 'System'),
        ('course', 'Course'),
        ('assignment', 'Assignment'),
        ('grade', 'Grade'),
        ('message', 'Message'),
        ('forum', 'Forum'),
        ('achievement', 'Achievement'),
        ('reminder', 'Reminder'),
        ('announcement', 'Announcement'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Links and actions
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery
    sent_via_email = models.BooleanField(default=False)
    sent_via_push = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users_notification'
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['priority', 'created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        read_status = "Read" if self.is_read else "Unread"
        return f"{self.title} - {self.user.username} ({read_status})"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# Signal handlers for profile creation
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when user is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
