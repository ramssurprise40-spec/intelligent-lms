"""
Analytics models for the Intelligent LMS system.
Includes learning analytics, performance tracking, and insights.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class LearningAnalytics(models.Model):
    """
    Comprehensive learning analytics for users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='learning_analytics')
    
    # Learning Metrics
    total_study_time = models.DurationField(null=True, blank=True)
    average_session_duration = models.DurationField(null=True, blank=True)
    total_logins = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    
    # Performance Metrics
    overall_completion_rate = models.FloatField(default=0.0)
    average_score = models.FloatField(default=0.0)
    improvement_rate = models.FloatField(default=0.0)
    consistency_score = models.FloatField(default=0.0)
    
    # Engagement Metrics
    forum_participation_rate = models.FloatField(default=0.0)
    resource_utilization_rate = models.FloatField(default=0.0)
    peer_interaction_score = models.FloatField(default=0.0)
    help_seeking_frequency = models.FloatField(default=0.0)
    
    # AI-Derived Insights
    learning_style_prediction = models.CharField(max_length=50, blank=True)
    difficulty_preference = models.CharField(max_length=20, blank=True)
    optimal_study_schedule = models.JSONField(default=dict, blank=True)
    predicted_outcomes = models.JSONField(default=dict, blank=True)
    
    # Risk Assessment
    dropout_risk_score = models.FloatField(null=True, blank=True)
    performance_risk_factors = models.JSONField(default=list, blank=True)
    recommended_interventions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_learninganalytics'
        
    def __str__(self):
        return f"Analytics for {self.user.username}"


class CourseAnalytics(models.Model):
    """
    Analytics data for individual courses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField('courses.Course', on_delete=models.CASCADE, related_name='course_analytics')
    
    # Enrollment Metrics
    total_enrollments = models.IntegerField(default=0)
    active_students = models.IntegerField(default=0)
    completion_rate = models.FloatField(default=0.0)
    dropout_rate = models.FloatField(default=0.0)
    retention_rate = models.FloatField(default=0.0)
    
    # Performance Metrics
    average_grade = models.FloatField(default=0.0)
    median_grade = models.FloatField(default=0.0)
    pass_rate = models.FloatField(default=0.0)
    average_completion_time = models.DurationField(null=True, blank=True)
    
    # Engagement Metrics
    average_session_duration = models.DurationField(null=True, blank=True)
    forum_activity_rate = models.FloatField(default=0.0)
    resource_access_rate = models.FloatField(default=0.0)
    peer_interaction_frequency = models.FloatField(default=0.0)
    
    # Content Analytics
    most_accessed_lessons = models.JSONField(default=list, blank=True)
    least_accessed_lessons = models.JSONField(default=list, blank=True)
    difficult_topics = models.JSONField(default=list, blank=True)
    popular_resources = models.JSONField(default=list, blank=True)
    
    # Satisfaction Metrics
    average_rating = models.FloatField(default=0.0)
    satisfaction_score = models.FloatField(default=0.0)
    net_promoter_score = models.FloatField(null=True, blank=True)
    
    # AI Insights
    learning_effectiveness_score = models.FloatField(null=True, blank=True)
    content_difficulty_analysis = models.JSONField(default=dict, blank=True)
    optimization_suggestions = models.JSONField(default=list, blank=True)
    
    # Timestamps
    last_calculated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_courseanalytics'
        
    def __str__(self):
        return f"Analytics for {self.course.title}"


class PerformanceReport(models.Model):
    """
    Periodic performance reports for users and courses.
    """
    REPORT_TYPES = [
        ('individual', 'Individual Student Report'),
        ('course', 'Course Report'),
        ('institutional', 'Institutional Report'),
        ('comparative', 'Comparative Report'),
    ]
    
    REPORT_PERIODS = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semester', 'Semester'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    period = models.CharField(max_length=20, choices=REPORT_PERIODS)
    
    # Scope
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='performance_reports')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='performance_reports')
    
    # Report data
    metrics = models.JSONField(default=dict)
    insights = models.JSONField(default=dict)
    recommendations = models.JSONField(default=list, blank=True)
    
    # Report metadata
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_reports')
    is_automated = models.BooleanField(default=True)
    
    # Date range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_performancereport'
        indexes = [
            models.Index(fields=['report_type', 'period']),
            models.Index(fields=['user', 'generated_at']),
            models.Index(fields=['course', 'generated_at']),
        ]
        
    def __str__(self):
        scope = self.user.username if self.user else (self.course.title if self.course else 'System')
        return f"{self.get_report_type_display()} - {scope} ({self.period})"


class PredictiveModel(models.Model):
    """
    Store AI/ML predictive models and their performance.
    """
    MODEL_TYPES = [
        ('dropout_prediction', 'Dropout Prediction'),
        ('performance_prediction', 'Performance Prediction'),
        ('completion_time', 'Completion Time Prediction'),
        ('difficulty_assessment', 'Difficulty Assessment'),
        ('recommendation', 'Content Recommendation'),
        ('engagement_prediction', 'Engagement Prediction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=30, choices=MODEL_TYPES)
    description = models.TextField(blank=True)
    
    # Model metadata
    version = models.CharField(max_length=20)
    algorithm = models.CharField(max_length=100)
    features = models.JSONField(default=list)
    hyperparameters = models.JSONField(default=dict, blank=True)
    
    # Performance metrics
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    
    # Model files and data
    model_path = models.CharField(max_length=500, blank=True)
    training_data_size = models.IntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_production = models.BooleanField(default=False)
    
    # Timestamps
    trained_at = models.DateTimeField()
    deployed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_predictivemodel'
        
    def __str__(self):
        return f"{self.name} v{self.version}"


class LearningPath(models.Model):
    """
    AI-generated learning paths for students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_paths')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Path metadata
    target_skills = models.JSONField(default=list)
    estimated_duration = models.DurationField()
    difficulty_level = models.CharField(max_length=20)
    
    # Path structure
    milestones = models.JSONField(default=list)  # Ordered list of milestones
    prerequisites = models.JSONField(default=list, blank=True)
    
    # Progress tracking
    current_milestone = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    
    # AI optimization
    personalization_factors = models.JSONField(default=dict, blank=True)
    adaptation_history = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_learningpath'
        
    def __str__(self):
        return f"{self.title} - {self.user.username}"
