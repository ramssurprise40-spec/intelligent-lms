"""
File models for the Intelligent LMS system.
Includes file management, processing, and analytics.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import os

User = get_user_model()


class File(models.Model):
    """
    Base file model for all uploaded files.
    """
    FILE_TYPES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('archive', 'Archive'),
        ('code', 'Code'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
        ('quarantined', 'Quarantined'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # File details
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()  # Size in bytes
    mime_type = models.CharField(max_length=100)
    file_extension = models.CharField(max_length=10)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    
    # Upload details
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    upload_session_id = models.CharField(max_length=100, blank=True)
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    processing_progress = models.IntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True)
    
    # File metadata
    checksum = models.CharField(max_length=64, blank=True)  # SHA-256
    metadata = models.JSONField(default=dict, blank=True)
    
    # Access and security
    is_public = models.BooleanField(default=False)
    access_level = models.CharField(
        max_length=20,
        choices=[
            ('public', 'Public'),
            ('course', 'Course Members'),
            ('group', 'Group Members'),
            ('private', 'Private'),
        ],
        default='private'
    )
    
    # Analytics
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files_file'
        indexes = [
            models.Index(fields=['uploaded_by', '-created_at']),
            models.Index(fields=['file_type', 'status']),
            models.Index(fields=['checksum']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return self.original_filename
    
    @property
    def filename(self):
        return os.path.basename(self.original_filename)
    
    @property
    def size_human_readable(self):
        """Return file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


class CourseFile(models.Model):
    """
    Associate files with courses and lessons.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='course_associations')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='files')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    
    # File context
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # Availability
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'files_coursefile'
        ordering = ['course', 'lesson', 'order']
        
    def __str__(self):
        return f"{self.file.original_filename} - {self.course.title}"


class FileProcessingTask(models.Model):
    """
    Track file processing tasks and results.
    """
    TASK_TYPES = [
        ('virus_scan', 'Virus Scan'),
        ('thumbnail_generation', 'Thumbnail Generation'),
        ('text_extraction', 'Text Extraction'),
        ('metadata_extraction', 'Metadata Extraction'),
        ('video_processing', 'Video Processing'),
        ('image_optimization', 'Image Optimization'),
        ('document_conversion', 'Document Conversion'),
    ]
    
    TASK_STATUS = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='processing_tasks')
    task_type = models.CharField(max_length=30, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=TASK_STATUS, default='pending')
    
    # Task details
    celery_task_id = models.CharField(max_length=100, blank=True)
    progress = models.IntegerField(default=0)
    
    # Results
    result = models.JSONField(default=dict, blank=True)
    error_details = models.TextField(blank=True)
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'files_processingtask'
        indexes = [
            models.Index(fields=['file', 'task_type']),
            models.Index(fields=['status', 'created_at']),
        ]
        
    def __str__(self):
        return f"{self.get_task_type_display()} for {self.file.original_filename}"


class FileVersion(models.Model):
    """
    Track file versions and history.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    # Version details
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    checksum = models.CharField(max_length=64)
    
    # Change information
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_versions')
    change_summary = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'files_fileversion'
        unique_together = ['file', 'version_number']
        ordering = ['file', '-version_number']
        
    def __str__(self):
        return f"{self.file.original_filename} v{self.version_number}"


class FileAccess(models.Model):
    """
    Track file access for analytics and security.
    """
    ACCESS_TYPES = [
        ('download', 'Download'),
        ('view', 'View'),
        ('preview', 'Preview'),
        ('stream', 'Stream'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='file_accesses')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    
    # Context
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Technical details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # Analytics
    duration = models.DurationField(null=True, blank=True)  # For streaming/viewing
    bytes_transferred = models.BigIntegerField(null=True, blank=True)
    
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'files_fileaccess'
        indexes = [
            models.Index(fields=['file', '-accessed_at']),
            models.Index(fields=['user', '-accessed_at']),
            models.Index(fields=['course', '-accessed_at']),
        ]
        ordering = ['-accessed_at']
        
    def __str__(self):
        return f"{self.user.username} {self.get_access_type_display()} {self.file.original_filename}"


class FileShare(models.Model):
    """
    Share files with specific users or groups.
    """
    SHARE_TYPES = [
        ('direct', 'Direct Share'),
        ('link', 'Share Link'),
        ('public_link', 'Public Link'),
    ]
    
    PERMISSION_LEVELS = [
        ('view', 'View Only'),
        ('download', 'View & Download'),
        ('edit', 'View, Download & Edit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_files')
    
    # Share details
    share_type = models.CharField(max_length=20, choices=SHARE_TYPES)
    permission_level = models.CharField(max_length=10, choices=PERMISSION_LEVELS, default='view')
    
    # Recipients (for direct shares)
    shared_with = models.ManyToManyField(User, related_name='received_file_shares', blank=True)
    
    # Link sharing
    share_token = models.CharField(max_length=100, unique=True, blank=True)
    password_protected = models.BooleanField(default=False)
    access_count = models.IntegerField(default=0)
    max_access_count = models.IntegerField(null=True, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'files_fileshare'
        
    def __str__(self):
        return f"Share: {self.file.original_filename} by {self.shared_by.username}"
    
    @property
    def is_expired(self):
        """Check if share link has expired."""
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        if self.max_access_count and self.access_count >= self.max_access_count:
            return True
        return False
