"""
Course models for the Intelligent LMS system.
Includes courses, lessons, content, enrollments, and AI-powered features.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()


class Course(models.Model):
    """
    Main course model with AI-enhanced features.
    """
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
        ('private', 'Private'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Course metadata
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    teaching_assistants = models.ManyToManyField(
        User, 
        related_name='courses_assisted', 
        blank=True
    )
    
    # Course properties
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    language = models.CharField(max_length=10, default='en')
    
    # Timing and capacity
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    enrollment_start = models.DateTimeField(null=True, blank=True)
    enrollment_end = models.DateTimeField(null=True, blank=True)
    max_students = models.IntegerField(null=True, blank=True)
    
    # Course structure
    estimated_hours = models.IntegerField(help_text="Estimated completion time in hours")
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    # Multimedia
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    trailer_video = models.URLField(blank=True)
    
    # AI-Generated Content
    ai_summary = models.TextField(blank=True, help_text="AI-generated course summary")
    learning_objectives = models.JSONField(default=list, blank=True)
    auto_generated_tags = models.JSONField(default=list, blank=True)
    difficulty_analysis = models.JSONField(default=dict, blank=True)
    
    # Analytics
    total_enrollments = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    completion_rate = models.FloatField(default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'courses_course'
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['instructor', 'created_at']),
            models.Index(fields=['difficulty_level', 'status']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    @property
    def is_enrollment_open(self):
        """Check if enrollment is currently open."""
        now = timezone.now()
        if self.enrollment_start and now < self.enrollment_start:
            return False
        if self.enrollment_end and now > self.enrollment_end:
            return False
        return True
    
    @property
    def current_enrollment_count(self):
        """Get current number of enrolled students."""
        return self.enrollments.filter(is_active=True).count()
    
    @property
    def can_enroll(self):
        """Check if new students can enroll."""
        if not self.is_enrollment_open:
            return False
        if self.max_students and self.current_enrollment_count >= self.max_students:
            return False
        return True


class CourseModule(models.Model):
    """
    Course modules/chapters for organizing content.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Module properties
    estimated_hours = models.FloatField(default=1.0)
    is_required = models.BooleanField(default=True)
    unlock_date = models.DateTimeField(null=True, blank=True)
    
    # AI insights
    difficulty_score = models.FloatField(null=True, blank=True)
    completion_time_prediction = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_module'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Lesson(models.Model):
    """
    Individual lessons within course modules.
    """
    LESSON_TYPES = [
        ('video', 'Video'),
        ('text', 'Text/Article'),
        ('interactive', 'Interactive Content'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('discussion', 'Discussion'),
        ('live_session', 'Live Session'),
        ('external_link', 'External Link'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250)
    
    # Content
    content = models.TextField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPES)
    order = models.PositiveIntegerField(default=0)
    
    # Media and resources
    video_url = models.URLField(blank=True)
    video_duration = models.DurationField(null=True, blank=True)
    external_url = models.URLField(blank=True)
    
    # Lesson properties
    estimated_minutes = models.IntegerField(default=10)
    is_free = models.BooleanField(default=False)
    is_required = models.BooleanField(default=True)
    
    # AI-Enhanced features
    auto_transcript = models.TextField(blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    generated_summary = models.TextField(blank=True)
    difficulty_rating = models.FloatField(null=True, blank=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    average_completion_time = models.DurationField(null=True, blank=True)
    completion_rate = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lesson'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
        
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    @property
    def course(self):
        return self.module.course


class CourseEnrollment(models.Model):
    """
    Track student enrollments in courses.
    """
    ENROLLMENT_STATUS = [
        ('enrolled', 'Enrolled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('suspended', 'Suspended'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    # Enrollment details
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='enrolled')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    dropped_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.FloatField(default=0.0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    lessons_completed = models.IntegerField(default=0)
    total_study_time = models.DurationField(null=True, blank=True)
    
    # Performance
    current_grade = models.FloatField(null=True, blank=True)
    final_grade = models.FloatField(null=True, blank=True)
    
    # AI Predictions and recommendations
    predicted_completion_date = models.DateTimeField(null=True, blank=True)
    risk_score = models.FloatField(null=True, blank=True)  # Risk of dropping out
    personalized_recommendations = models.JSONField(default=list, blank=True)
    
    # Flags
    is_active = models.BooleanField(default=True)
    certificate_issued = models.BooleanField(default=False)
    certificate_issued_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'courses_enrollment'
        unique_together = ['student', 'course']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'enrolled_at']),
            models.Index(fields=['status', 'enrolled_at']),
        ]
        
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    def calculate_progress(self):
        """Calculate and update progress percentage."""
        total_lessons = self.course.modules.aggregate(
            total=models.Count('lessons')
        )['total'] or 0
        
        if total_lessons > 0:
            completed_lessons = LessonProgress.objects.filter(
                enrollment=self,
                is_completed=True
            ).count()
            self.progress_percentage = (completed_lessons / total_lessons) * 100
            self.lessons_completed = completed_lessons
        else:
            self.progress_percentage = 0.0
            self.lessons_completed = 0
        
        self.save()
        return self.progress_percentage


class LessonProgress(models.Model):
    """
    Track individual lesson progress for students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    
    # Progress details
    is_completed = models.BooleanField(default=False)
    completion_percentage = models.FloatField(default=0.0)
    time_spent = models.DurationField(null=True, blank=True)
    
    # Interaction data
    first_accessed = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    access_count = models.IntegerField(default=0)
    
    # Learning analytics
    engagement_score = models.FloatField(null=True, blank=True)
    difficulty_rating = models.FloatField(null=True, blank=True)  # Student's perceived difficulty
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lesson_progress'
        unique_together = ['enrollment', 'lesson']
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
            models.Index(fields=['lesson', 'completed_at']),
        ]
        
    def __str__(self):
        status = "✓" if self.is_completed else f"{self.completion_percentage:.0f}%"
        return f"{self.enrollment.student.username} - {self.lesson.title} ({status})"
    
    def mark_as_accessed(self):
        """Update access tracking."""
        now = timezone.now()
        if not self.first_accessed:
            self.first_accessed = now
        self.last_accessed = now
        self.access_count += 1
        self.save()
    
    def mark_as_completed(self):
        """Mark lesson as completed."""
        if not self.is_completed:
            self.is_completed = True
            self.completion_percentage = 100.0
            self.completed_at = timezone.now()
            self.save()
            
            # Update enrollment progress
            self.enrollment.calculate_progress()


class CourseRating(models.Model):
    """
    Course ratings and reviews from students.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ratings')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_ratings')
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, null=True)
    
    # Rating details
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    
    # Specific ratings
    content_quality = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True)
    instructor_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True)
    difficulty_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True)
    would_recommend = models.BooleanField(null=True)
    
    # AI analysis
    sentiment_score = models.FloatField(null=True, blank=True)
    key_topics = models.JSONField(default=list, blank=True)
    
    # Status
    is_approved = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_rating'
        unique_together = ['course', 'student']
        indexes = [
            models.Index(fields=['course', 'rating']),
            models.Index(fields=['is_approved', 'created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.course.title} - {self.rating}/5 by {self.student.username}"


class CourseTag(models.Model):
    """
    Tags for course categorization and discovery.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    is_ai_generated = models.BooleanField(default=False)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses_tag'
        ordering = ['name']
        
    def __str__(self):
        return self.name


class CourseTagging(models.Model):
    """
    Many-to-many relationship between courses and tags.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tags')
    tag = models.ForeignKey(CourseTag, on_delete=models.CASCADE, related_name='tagged_courses')
    relevance_score = models.FloatField(default=1.0)  # AI-determined relevance
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses_tagging'
        unique_together = ['course', 'tag']
        
    def __str__(self):
        return f"{self.course.title} - {self.tag.name}"


class CourseWaitlist(models.Model):
    """
    Waitlist for courses that are at capacity.
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('enrolled', 'Enrolled'),
        ('expired', 'Expired'),
        ('removed', 'Removed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='waitlist')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='waitlist_entries')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    position = models.PositiveIntegerField()
    priority_score = models.FloatField(default=1.0)  # For prioritizing waitlist
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_waitlist'
        unique_together = ['course', 'student']
        indexes = [
            models.Index(fields=['course', 'status', 'position']),
            models.Index(fields=['student', 'created_at']),
        ]
        ordering = ['course', 'position']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} (#{self.position})"


class CourseCertificate(models.Model):
    """
    Certificates for course completion.
    """
    CERTIFICATE_TYPES = [
        ('completion', 'Completion Certificate'),
        ('achievement', 'Achievement Certificate'),
        ('participation', 'Participation Certificate'),
        ('excellence', 'Certificate of Excellence'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, related_name='certificate')
    
    # Certificate details
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES, default='completion')
    certificate_number = models.CharField(max_length=50, unique=True)
    
    # Requirements
    minimum_score = models.FloatField(default=70.0)
    required_modules = models.JSONField(default=list, blank=True)
    
    # Certificate data
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # File storage
    certificate_pdf = models.FileField(upload_to='certificates/', null=True, blank=True)
    certificate_template = models.CharField(max_length=100, default='default')
    
    # Verification
    verification_code = models.CharField(max_length=32, unique=True)
    is_valid = models.BooleanField(default=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # Additional certificate data
    
    class Meta:
        db_table = 'courses_certificate'
        indexes = [
            models.Index(fields=['certificate_number']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['issued_at']),
        ]
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"Certificate for {self.enrollment.student.username} - {self.enrollment.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_number:
            # Generate unique certificate number
            import secrets
            self.certificate_number = f"CERT-{timezone.now().year}-{secrets.token_hex(6).upper()}"
        
        if not self.verification_code:
            import secrets
            self.verification_code = secrets.token_hex(16)
        
        super().save(*args, **kwargs)


class LessonContent(models.Model):
    """
    Versioned content for lessons.
    """
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('html', 'HTML Content'),
        ('markdown', 'Markdown Content'),
        ('video', 'Video Content'),
        ('audio', 'Audio Content'),
        ('document', 'Document'),
        ('presentation', 'Presentation'),
        ('interactive', 'Interactive Content'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='content_versions')
    
    # Content details
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    
    # File storage
    file = models.FileField(upload_to='lesson_content/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=100, blank=True)
    
    # Versioning
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    change_notes = models.TextField(blank=True)
    
    # Metadata
    duration = models.DurationField(null=True, blank=True)
    language = models.CharField(max_length=10, default='en')
    accessibility_features = models.JSONField(default=dict, blank=True)
    
    # AI-generated metadata
    auto_transcript = models.TextField(blank=True)
    auto_summary = models.TextField(blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    difficulty_score = models.FloatField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_content')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_lesson_content'
        indexes = [
            models.Index(fields=['lesson', 'version']),
            models.Index(fields=['lesson', 'is_current']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['lesson', '-version']
        unique_together = ['lesson', 'version']
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        if not self.pk and self.is_current:
            # Mark all other versions as not current
            LessonContent.objects.filter(
                lesson=self.lesson,
                is_current=True
            ).update(is_current=False)
            
            # Set version number
            last_version = LessonContent.objects.filter(
                lesson=self.lesson
            ).aggregate(max_version=models.Max('version'))['max_version']
            self.version = (last_version or 0) + 1
        
        super().save(*args, **kwargs)


class CourseAnalytics(models.Model):
    """
    Course analytics and performance metrics.
    """
    METRIC_TYPES = [
        ('enrollment', 'Enrollment Metrics'),
        ('engagement', 'Engagement Metrics'),
        ('completion', 'Completion Metrics'),
        ('performance', 'Performance Metrics'),
        ('satisfaction', 'Satisfaction Metrics'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='analytics')
    
    # Metric details
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    
    # Time period
    date = models.DateField()
    period_type = models.CharField(max_length=20, default='daily')  # daily, weekly, monthly
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courses_analytics'
        indexes = [
            models.Index(fields=['course', 'metric_type', 'date']),
            models.Index(fields=['metric_type', 'date']),
            models.Index(fields=['date']),
        ]
        ordering = ['course', 'metric_type', '-date']
        unique_together = ['course', 'metric_type', 'metric_name', 'date']
    
    def __str__(self):
        return f"{self.course.title} - {self.metric_name}: {self.metric_value} ({self.date})"


class CourseAnnouncement(models.Model):
    """
    Course announcements from instructors.
    """
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_announcements')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_announcements')
    
    # Announcement content
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    
    # Targeting
    target_all_students = models.BooleanField(default=True)
    target_students = models.ManyToManyField(User, blank=True, related_name='course_targeted_announcements')
    
    # Publishing
    is_published = models.BooleanField(default=True)
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    send_email = models.BooleanField(default=True)
    send_push_notification = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses_announcement'
        indexes = [
            models.Index(fields=['course', '-created_at']),
            models.Index(fields=['is_published', 'publish_at']),
            models.Index(fields=['priority', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_active(self):
        """Check if announcement is currently active."""
        now = timezone.now()
        if self.publish_at and now < self.publish_at:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return self.is_published
