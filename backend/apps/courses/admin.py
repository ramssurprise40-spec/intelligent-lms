"""
Django admin configuration for course models.

This module provides administrative interfaces for managing courses,
modules, lessons, enrollments, and related data.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django.utils import timezone

from .models import (
    Course, CourseModule, Lesson, CourseEnrollment, LessonProgress,
    CourseRating, CourseTag, CourseTagging, CourseWaitlist,
    CourseCertificate, LessonContent, CourseAnalytics, CourseAnnouncement
)


class CourseTaggingInline(admin.TabularInline):
    """Inline admin for course tags."""
    model = CourseTagging
    extra = 1
    autocomplete_fields = ['tag']


class CourseModuleInline(admin.StackedInline):
    """Inline admin for course modules."""
    model = CourseModule
    extra = 0
    fields = ['title', 'description', 'order', 'estimated_hours', 'is_required', 'unlock_date']
    ordering = ['order']


class CourseEnrollmentInline(admin.TabularInline):
    """Inline admin for course enrollments."""
    model = CourseEnrollment
    extra = 0
    readonly_fields = ['enrolled_at', 'progress_percentage', 'lessons_completed']
    fields = ['student', 'status', 'enrolled_at', 'progress_percentage', 'lessons_completed']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model."""
    list_display = [
        'title', 'instructor', 'status', 'difficulty_level',
        'total_enrollments', 'average_rating', 'created_at'
    ]
    list_filter = [
        'status', 'difficulty_level', 'language', 'created_at',
        'published_at', 'instructor'
    ]
    search_fields = ['title', 'description', 'instructor__username']
    readonly_fields = [
        'slug', 'total_enrollments', 'average_rating', 'completion_rate',
        'ai_summary', 'auto_generated_tags', 'difficulty_analysis',
        'created_at', 'updated_at', 'published_at'
    ]
    filter_horizontal = ['prerequisites', 'teaching_assistants']
    inlines = [CourseTaggingInline, CourseModuleInline, CourseEnrollmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'instructor', 'teaching_assistants')
        }),
        ('Content', {
            'fields': ('description', 'short_description', 'learning_objectives')
        }),
        ('Settings', {
            'fields': (
                'difficulty_level', 'status', 'language', 'estimated_hours',
                'prerequisites'
            )
        }),
        ('Enrollment', {
            'fields': (
                'start_date', 'end_date', 'enrollment_start', 'enrollment_end',
                'max_students'
            )
        }),
        ('Media', {
            'fields': ('thumbnail', 'trailer_video')
        }),
        ('AI Generated Data', {
            'fields': ('ai_summary', 'auto_generated_tags', 'difficulty_analysis'),
            'classes': ['collapse']
        }),
        ('Statistics', {
            'fields': ('total_enrollments', 'average_rating', 'completion_rate'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ['collapse']
        })
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('instructor')
    
    actions = ['publish_courses', 'unpublish_courses']
    
    def publish_courses(self, request, queryset):
        """Publish selected courses."""
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} courses published successfully.')
    publish_courses.short_description = 'Publish selected courses'
    
    def unpublish_courses(self, request, queryset):
        """Unpublish selected courses."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} courses unpublished successfully.')
    unpublish_courses.short_description = 'Unpublish selected courses'


class LessonInline(admin.StackedInline):
    """Inline admin for lessons."""
    model = Lesson
    extra = 0
    fields = [
        'title', 'slug', 'lesson_type', 'order', 'estimated_minutes',
        'is_free', 'is_required'
    ]
    ordering = ['order']


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    """Admin interface for CourseModule model."""
    list_display = ['title', 'course', 'order', 'estimated_hours', 'is_required']
    list_filter = ['is_required', 'course__status', 'course__instructor']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['difficulty_score', 'completion_time_prediction', 'created_at', 'updated_at']
    inlines = [LessonInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Settings', {
            'fields': ('estimated_hours', 'is_required', 'unlock_date')
        }),
        ('AI Analysis', {
            'fields': ('difficulty_score', 'completion_time_prediction'),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )


class LessonContentInline(admin.StackedInline):
    """Inline admin for lesson content versions."""
    model = LessonContent
    extra = 0
    readonly_fields = ['version', 'auto_transcript', 'auto_summary', 'key_concepts']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin interface for Lesson model."""
    list_display = [
        'title', 'module', 'lesson_type', 'order',
        'estimated_minutes', 'is_free', 'is_required'
    ]
    list_filter = ['lesson_type', 'is_free', 'is_required', 'module__course']
    search_fields = ['title', 'content', 'module__title']
    readonly_fields = [
        'slug', 'auto_transcript', 'generated_summary', 'key_concepts',
        'difficulty_rating', 'view_count', 'average_completion_time',
        'completion_rate', 'created_at', 'updated_at'
    ]
    inlines = [LessonContentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'slug', 'content')
        }),
        ('Settings', {
            'fields': (
                'lesson_type', 'order', 'estimated_minutes',
                'is_free', 'is_required'
            )
        }),
        ('Media', {
            'fields': ('video_url', 'video_duration', 'external_url')
        }),
        ('AI Generated Data', {
            'fields': ('auto_transcript', 'generated_summary', 'key_concepts'),
            'classes': ['collapse']
        }),
        ('Analytics', {
            'fields': (
                'difficulty_rating', 'view_count', 'average_completion_time',
                'completion_rate'
            ),
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for CourseEnrollment model."""
    list_display = [
        'student', 'course', 'status', 'progress_percentage',
        'enrolled_at', 'completed_at'
    ]
    list_filter = [
        'status', 'is_active', 'enrolled_at', 'course__status',
        'certificate_issued'
    ]
    search_fields = ['student__username', 'course__title']
    readonly_fields = [
        'progress_percentage', 'lessons_completed', 'predicted_completion_date',
        'risk_score', 'enrolled_at'
    ]
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('student', 'course', 'status', 'is_active')
        }),
        ('Progress', {
            'fields': (
                'progress_percentage', 'lessons_completed', 'total_study_time',
                'current_grade', 'final_grade'
            )
        }),
        ('AI Predictions', {
            'fields': (
                'predicted_completion_date', 'risk_score',
                'personalized_recommendations'
            ),
            'classes': ['collapse']
        }),
        ('Certificates', {
            'fields': ('certificate_issued', 'certificate_issued_at')
        }),
        ('Timestamps', {
            'fields': ('enrolled_at', 'completed_at', 'dropped_at', 'updated_at'),
            'classes': ['collapse']
        })
    )


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """Admin interface for LessonProgress model."""
    list_display = [
        'enrollment', 'lesson', 'is_completed',
        'completion_percentage', 'time_spent'
    ]
    list_filter = ['is_completed', 'first_accessed', 'completed_at']
    search_fields = [
        'enrollment__student__username', 'lesson__title',
        'enrollment__course__title'
    ]
    readonly_fields = ['first_accessed', 'access_count', 'engagement_score']


@admin.register(CourseRating)
class CourseRatingAdmin(admin.ModelAdmin):
    """Admin interface for CourseRating model."""
    list_display = [
        'course', 'student', 'rating', 'would_recommend',
        'is_approved', 'is_featured', 'created_at'
    ]
    list_filter = [
        'rating', 'would_recommend', 'is_approved', 'is_featured',
        'created_at', 'course'
    ]
    search_fields = ['course__title', 'student__username', 'review']
    readonly_fields = ['sentiment_score', 'key_topics']
    
    actions = ['approve_ratings', 'feature_ratings']
    
    def approve_ratings(self, request, queryset):
        """Approve selected ratings."""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} ratings approved successfully.')
    approve_ratings.short_description = 'Approve selected ratings'
    
    def feature_ratings(self, request, queryset):
        """Feature selected ratings."""
        updated = queryset.filter(is_approved=True).update(is_featured=True)
        self.message_user(request, f'{updated} ratings featured successfully.')
    feature_ratings.short_description = 'Feature selected ratings'


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    """Admin interface for CourseTag model."""
    list_display = ['name', 'slug', 'usage_count', 'color']
    search_fields = ['name', 'description']
    readonly_fields = ['slug', 'usage_count']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CourseWaitlist)
class CourseWaitlistAdmin(admin.ModelAdmin):
    """Admin interface for CourseWaitlist model."""
    list_display = [
        'student', 'course', 'status', 'position',
        'priority_score', 'created_at'
    ]
    list_filter = ['status', 'notification_sent', 'created_at']
    search_fields = ['student__username', 'course__title']
    readonly_fields = ['position', 'priority_score']


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    """Admin interface for CourseCertificate model."""
    list_display = [
        'certificate_number', 'enrollment', 'certificate_type',
        'issued_at', 'is_valid'
    ]
    list_filter = ['certificate_type', 'issued_at', 'expires_at', 'is_valid']
    search_fields = [
        'certificate_number', 'enrollment__student__username',
        'enrollment__course__title', 'verification_code'
    ]
    readonly_fields = ['certificate_number', 'verification_code', 'issued_at']


@admin.register(CourseAnnouncement)
class CourseAnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for CourseAnnouncement model."""
    list_display = [
        'title', 'course', 'priority', 'is_published',
        'publish_at', 'author'
    ]
    list_filter = [
        'priority', 'is_published', 'send_email', 'send_push_notification',
        'publish_at', 'course'
    ]
    search_fields = ['title', 'content', 'course__title']
    readonly_fields = ['author']
    
    def save_model(self, request, obj, form, change):
        """Set author to current user when creating."""
        if not change:  # Only set author when creating
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    """Admin interface for CourseAnalytics model."""
    list_display = [
        'course', 'metric_type', 'metric_name',
        'metric_value', 'date', 'period_type'
    ]
    list_filter = ['metric_type', 'period_type', 'date', 'course']
    search_fields = ['course__title', 'metric_name']
    readonly_fields = ['created_at']


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    """Admin interface for LessonContent model."""
    list_display = [
        'lesson', 'content_type', 'title', 'version',
        'is_current', 'created_by'
    ]
    list_filter = [
        'content_type', 'is_current', 'language',
        'created_at', 'lesson__module__course'
    ]
    search_fields = ['title', 'content', 'lesson__title']
    readonly_fields = [
        'version', 'auto_transcript', 'auto_summary',
        'key_concepts', 'difficulty_score'
    ]
