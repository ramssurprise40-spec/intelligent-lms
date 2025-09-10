"""
Assessment models for the Intelligent LMS system.
Includes quizzes, assignments, submissions, and AI-powered grading.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class Assessment(models.Model):
    """
    Base assessment model for quizzes, assignments, and exams.
    """
    ASSESSMENT_TYPES = [
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
        ('project', 'Project'),
        ('peer_review', 'Peer Review'),
        ('discussion', 'Discussion'),
        ('survey', 'Survey'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    GRADING_METHODS = [
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
        ('hybrid', 'Hybrid (AI + Manual)'),
        ('peer', 'Peer Grading'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Assessment properties
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    grading_method = models.CharField(max_length=20, choices=GRADING_METHODS, default='automatic')
    
    # Timing
    available_from = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    time_limit_minutes = models.IntegerField(null=True, blank=True)
    
    # Grading
    max_score = models.FloatField(default=100.0)
    passing_score = models.FloatField(null=True, blank=True)
    weight = models.FloatField(default=1.0)  # Weight in course grade
    
    # Attempts
    max_attempts = models.IntegerField(default=1)
    allow_late_submission = models.BooleanField(default=False)
    late_penalty_percent = models.FloatField(default=0.0)
    
    # AI Features
    auto_generate_feedback = models.BooleanField(default=True)
    plagiarism_check = models.BooleanField(default=True)
    difficulty_analysis = models.JSONField(default=dict, blank=True)
    
    # Relations
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='assessments')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assessments')
    
    # Instructions and resources
    instructions = models.TextField(blank=True)
    resources = models.JSONField(default=list, blank=True)
    rubric = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'assessments_assessment'
        indexes = [
            models.Index(fields=['course', 'status']),
            models.Index(fields=['assessment_type', 'status']),
            models.Index(fields=['due_date', 'status']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_available(self):
        """Check if assessment is currently available."""
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        return self.status == 'published'
    
    @property
    def is_past_due(self):
        """Check if assessment is past due date."""
        if not self.due_date:
            return False
        return timezone.now() > self.due_date
    
    @property
    def can_submit(self):
        """Check if new submissions are allowed."""
        if not self.is_available:
            return False
        if self.is_past_due and not self.allow_late_submission:
            return False
        return True


class Question(models.Model):
    """
    Individual questions within assessments.
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('fill_blank', 'Fill in the Blank'),
        ('matching', 'Matching'),
        ('ordering', 'Ordering'),
        ('file_upload', 'File Upload'),
        ('code', 'Code'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    
    # Question content
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    order = models.PositiveIntegerField(default=0)
    
    # Scoring
    points = models.FloatField(default=1.0)
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    
    # Question data (flexible JSON field)
    question_data = models.JSONField(default=dict, blank=True)  # Choices, correct answers, etc.
    
    # AI features
    auto_generated = models.BooleanField(default=False)
    topics = models.JSONField(default=list, blank=True)
    learning_objectives = models.JSONField(default=list, blank=True)
    
    # Analytics
    average_score = models.FloatField(null=True, blank=True)
    answer_distribution = models.JSONField(default=dict, blank=True)
    discrimination_index = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments_question'
        ordering = ['assessment', 'order']
        
    def __str__(self):
        return f"{self.assessment.title} - Q{self.order}: {self.question_text[:50]}..."


class AssessmentSubmission(models.Model):
    """
    Student submissions for assessments.
    """
    SUBMISSION_STATUS = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('returned', 'Returned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assessment_submissions')
    
    # Submission details
    attempt_number = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=SUBMISSION_STATUS, default='in_progress')
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    time_spent = models.DurationField(null=True, blank=True)
    
    # Grading
    score = models.FloatField(null=True, blank=True)
    percentage = models.FloatField(null=True, blank=True)
    grade = models.CharField(max_length=10, blank=True)
    
    # AI Analysis
    plagiarism_score = models.FloatField(null=True, blank=True)
    plagiarism_sources = models.JSONField(default=list, blank=True)
    ai_feedback = models.TextField(blank=True)
    learning_gaps = models.JSONField(default=list, blank=True)
    
    # Feedback
    instructor_feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    
    # Flags
    is_late = models.BooleanField(default=False)
    needs_review = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'assessments_submission'
        unique_together = ['assessment', 'student', 'attempt_number']
        indexes = [
            models.Index(fields=['student', 'submitted_at']),
            models.Index(fields=['assessment', 'status']),
            models.Index(fields=['graded_by', 'graded_at']),
        ]
        ordering = ['-submitted_at']
        
    def __str__(self):
        return f"{self.student.username} - {self.assessment.title} (Attempt {self.attempt_number})"
    
    def calculate_grade(self):
        """Calculate final grade based on score and late penalties."""
        if self.score is None:
            return None
            
        final_score = self.score
        
        # Apply late penalty if applicable
        if self.is_late and self.assessment.late_penalty_percent > 0:
            penalty = final_score * (self.assessment.late_penalty_percent / 100)
            final_score = max(0, final_score - penalty)
        
        # Calculate percentage
        if self.assessment.max_score > 0:
            self.percentage = (final_score / self.assessment.max_score) * 100
        
        return final_score
    
    def submit(self):
        """Mark submission as submitted."""
        if self.status == 'in_progress':
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            
            # Check if late
            if self.assessment.due_date and self.submitted_at > self.assessment.due_date:
                self.is_late = True
            
            # Calculate time spent
            if self.started_at:
                self.time_spent = self.submitted_at - self.started_at
            
            self.save()


class QuestionResponse(models.Model):
    """
    Individual question responses within submissions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(AssessmentSubmission, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    
    # Response data
    response_data = models.JSONField(default=dict)  # Flexible storage for different response types
    response_text = models.TextField(blank=True)  # For text-based responses
    
    # Grading
    score = models.FloatField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    
    # AI Analysis
    ai_score = models.FloatField(null=True, blank=True)
    ai_feedback = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    
    # Manual grading
    manual_score = models.FloatField(null=True, blank=True)
    manual_feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timestamps
    answered_at = models.DateTimeField(auto_now_add=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'assessments_response'
        unique_together = ['submission', 'question']
        
    def __str__(self):
        return f"{self.submission.student.username} - Q{self.question.order}"
    
    def auto_grade(self):
        """Automatically grade the response based on question type."""
        if self.question.question_type == 'multiple_choice':
            correct_answer = self.question.question_data.get('correct_answer')
            student_answer = self.response_data.get('selected_choice')
            
            if correct_answer == student_answer:
                self.score = self.question.points
                self.is_correct = True
            else:
                self.score = 0
                self.is_correct = False
                
        elif self.question.question_type == 'true_false':
            correct_answer = self.question.question_data.get('correct_answer')
            student_answer = self.response_data.get('answer')
            
            if correct_answer == student_answer:
                self.score = self.question.points
                self.is_correct = True
            else:
                self.score = 0
                self.is_correct = False
        
        # For other question types, AI grading would be triggered
        # This would be handled by Celery tasks
        
        self.save()


class GradingRubric(models.Model):
    """
    Detailed grading rubrics for assessments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='rubric_detail')
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Rubric structure (JSON)
    criteria = models.JSONField(default=list)  # List of criteria with levels and points
    total_points = models.FloatField()
    
    # AI features
    ai_assisted = models.BooleanField(default=True)
    consistency_check = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments_rubric'
        
    def __str__(self):
        return f"Rubric for {self.assessment.title}"


class PeerReview(models.Model):
    """
    Peer review assignments and submissions.
    """
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='peer_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='peer_reviews_given')
    reviewed_submission = models.ForeignKey(AssessmentSubmission, on_delete=models.CASCADE, related_name='peer_reviews')
    
    # Review details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    
    # Detailed ratings (JSON structure based on rubric)
    detailed_ratings = models.JSONField(default=dict, blank=True)
    
    # Quality assessment (how good is this peer review)
    review_quality_score = models.FloatField(null=True, blank=True)
    
    # Timestamps
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'assessments_peer_review'
        unique_together = ['reviewer', 'reviewed_submission']
        
    def __str__(self):
        return f"{self.reviewer.username} reviewing {self.reviewed_submission.student.username}"


class AssessmentAnalytics(models.Model):
    """
    Analytics and insights for assessments.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.OneToOneField(Assessment, on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    total_submissions = models.IntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)
    median_score = models.FloatField(null=True, blank=True)
    pass_rate = models.FloatField(null=True, blank=True)
    
    # Time analytics
    average_completion_time = models.DurationField(null=True, blank=True)
    median_completion_time = models.DurationField(null=True, blank=True)
    
    # Question analytics
    question_analytics = models.JSONField(default=dict, blank=True)
    difficult_questions = models.JSONField(default=list, blank=True)
    
    # Insights
    learning_gaps_identified = models.JSONField(default=list, blank=True)
    improvement_suggestions = models.JSONField(default=list, blank=True)
    
    # Last updated
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assessments_analytics'
        
    def __str__(self):
        return f"Analytics for {self.assessment.title}"
