"""
Course API serializers for the Intelligent LMS system.

This module provides serializers for course management, enrollment,
content delivery, and analytics.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Course, CourseModule, Lesson, CourseEnrollment, LessonProgress,
    CourseRating, CourseTag, CourseTagging, CourseWaitlist, 
    CourseCertificate, LessonContent, CourseAnalytics, CourseAnnouncement
)

User = get_user_model()


class CourseTagSerializer(serializers.ModelSerializer):
    """Serializer for course tags."""
    
    class Meta:
        model = CourseTag
        fields = ['id', 'name', 'slug', 'description', 'color', 'usage_count']
        read_only_fields = ['id', 'usage_count']


class CourseTaggingSerializer(serializers.ModelSerializer):
    """Serializer for course tagging relationships."""
    tag = CourseTagSerializer(read_only=True)
    
    class Meta:
        model = CourseTagging
        fields = ['tag', 'relevance_score']


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for course contexts."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class LessonContentSerializer(serializers.ModelSerializer):
    """Serializer for lesson content versions."""
    created_by = UserSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonContent
        fields = [
            'id', 'content_type', 'title', 'content', 'file', 'file_url',
            'file_size', 'file_type', 'version', 'is_current', 'change_notes',
            'duration', 'language', 'accessibility_features', 'auto_transcript',
            'auto_summary', 'key_concepts', 'difficulty_score', 'created_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'version', 'auto_transcript', 'auto_summary', 'key_concepts',
            'difficulty_score', 'created_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        """Get the file URL if file exists."""
        if obj.file:
            return self.context['request'].build_absolute_uri(obj.file.url)
        return None


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress tracking."""
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'is_completed', 'completion_percentage', 'time_spent',
            'first_accessed', 'last_accessed', 'completed_at', 'access_count',
            'engagement_score', 'difficulty_rating', 'notes'
        ]
        read_only_fields = ['id', 'first_accessed', 'access_count']


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for course lessons."""
    current_content = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'content', 'lesson_type', 'order',
            'video_url', 'video_duration', 'external_url', 'estimated_minutes',
            'is_free', 'is_required', 'auto_transcript', 'key_concepts',
            'generated_summary', 'difficulty_rating', 'view_count',
            'average_completion_time', 'completion_rate', 'current_content',
            'user_progress', 'course_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'auto_transcript', 'generated_summary', 'difficulty_rating',
            'view_count', 'average_completion_time', 'completion_rate',
            'current_content', 'user_progress', 'course_id', 'created_at', 'updated_at'
        ]
    
    def get_current_content(self, obj):
        """Get the current version of lesson content."""
        current_content = obj.content_versions.filter(is_current=True).first()
        if current_content:
            return LessonContentSerializer(current_content, context=self.context).data
        return None
    
    def get_user_progress(self, obj):
        """Get user's progress for this lesson."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                # Find enrollment first
                enrollment = CourseEnrollment.objects.get(
                    student=request.user,
                    course=obj.module.course,
                    is_active=True
                )
                progress = LessonProgress.objects.get(
                    enrollment=enrollment,
                    lesson=obj
                )
                return LessonProgressSerializer(progress).data
            except (CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                pass
        return None
    
    def get_course_id(self, obj):
        """Get the course ID for this lesson."""
        return str(obj.module.course.id)


class CourseModuleSerializer(serializers.ModelSerializer):
    """Serializer for course modules."""
    lessons = LessonSerializer(many=True, read_only=True)
    lesson_count = serializers.SerializerMethodField()
    estimated_completion_time = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = [
            'id', 'title', 'description', 'order', 'estimated_hours',
            'is_required', 'unlock_date', 'difficulty_score',
            'completion_time_prediction', 'lessons', 'lesson_count',
            'estimated_completion_time', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'difficulty_score', 'completion_time_prediction',
            'lesson_count', 'estimated_completion_time', 'created_at', 'updated_at'
        ]
    
    def get_lesson_count(self, obj):
        """Get the number of lessons in this module."""
        return obj.lessons.count()
    
    def get_estimated_completion_time(self, obj):
        """Get estimated time to complete all lessons."""
        total_minutes = obj.lessons.aggregate(
            total=serializers.models.Sum('estimated_minutes')
        )['total'] or 0
        return total_minutes


class CourseRatingSerializer(serializers.ModelSerializer):
    """Serializer for course ratings and reviews."""
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = CourseRating
        fields = [
            'id', 'rating', 'review', 'content_quality', 'instructor_rating',
            'difficulty_rating', 'would_recommend', 'sentiment_score',
            'key_topics', 'is_approved', 'is_featured', 'student',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'sentiment_score', 'key_topics', 'is_approved',
            'is_featured', 'student', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create a new course rating."""
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments."""
    student = UserSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_progress_count = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'status', 'enrolled_at', 'completed_at', 'dropped_at',
            'progress_percentage', 'lessons_completed', 'total_study_time',
            'current_grade', 'final_grade', 'predicted_completion_date',
            'risk_score', 'personalized_recommendations', 'is_active',
            'certificate_issued', 'certificate_issued_at', 'student',
            'course_title', 'lesson_progress_count', 'certificate'
        ]
        read_only_fields = [
            'id', 'enrolled_at', 'progress_percentage', 'lessons_completed',
            'predicted_completion_date', 'risk_score', 'personalized_recommendations',
            'certificate_issued', 'certificate_issued_at', 'student',
            'course_title', 'lesson_progress_count', 'certificate'
        ]
    
    def get_lesson_progress_count(self, obj):
        """Get lesson progress statistics."""
        progress = obj.lesson_progress.aggregate(
            total=serializers.models.Count('id'),
            completed=serializers.models.Count('id', filter=serializers.models.Q(is_completed=True))
        )
        return {
            'total': progress['total'] or 0,
            'completed': progress['completed'] or 0
        }
    
    def get_certificate(self, obj):
        """Get certificate information if exists."""
        if hasattr(obj, 'certificate'):
            return {
                'certificate_number': obj.certificate.certificate_number,
                'certificate_type': obj.certificate.certificate_type,
                'issued_at': obj.certificate.issued_at,
                'verification_code': obj.certificate.verification_code
            }
        return None


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list view."""
    instructor = UserSerializer(read_only=True)
    tags = serializers.SerializerMethodField()
    enrollment_status = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'short_description', 'instructor',
            'difficulty_level', 'status', 'language', 'estimated_hours',
            'thumbnail', 'thumbnail_url', 'total_enrollments', 'average_rating',
            'completion_rate', 'tags', 'enrollment_status', 'created_at',
            'published_at'
        ]
        read_only_fields = [
            'id', 'total_enrollments', 'average_rating', 'completion_rate',
            'tags', 'enrollment_status', 'thumbnail_url', 'created_at', 'published_at'
        ]
    
    def get_tags(self, obj):
        """Get course tags."""
        return [tagging.tag.name for tagging in obj.course_tags.all()[:5]]
    
    def get_enrollment_status(self, obj):
        """Get user's enrollment status for this course."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(
                    student=request.user,
                    is_active=True
                )
                return enrollment.status
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_thumbnail_url(self, obj):
        """Get the thumbnail URL."""
        if obj.thumbnail:
            return self.context['request'].build_absolute_uri(obj.thumbnail.url)
        return None


class CourseDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed course view."""
    instructor = UserSerializer(read_only=True)
    teaching_assistants = UserSerializer(many=True, read_only=True)
    modules = CourseModuleSerializer(many=True, read_only=True)
    tags = CourseTaggingSerializer(source='course_tags', many=True, read_only=True)
    prerequisites = CourseListSerializer(many=True, read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    recent_ratings = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'instructor', 'teaching_assistants', 'difficulty_level',
            'status', 'language', 'start_date', 'end_date',
            'enrollment_start', 'enrollment_end', 'max_students',
            'estimated_hours', 'prerequisites', 'thumbnail', 'thumbnail_url',
            'trailer_video', 'ai_summary', 'learning_objectives',
            'auto_generated_tags', 'difficulty_analysis', 'total_enrollments',
            'average_rating', 'completion_rate', 'modules', 'tags',
            'enrollment_status', 'user_rating', 'recent_ratings',
            'can_enroll', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'ai_summary', 'auto_generated_tags', 'difficulty_analysis',
            'total_enrollments', 'average_rating', 'completion_rate',
            'enrollment_status', 'user_rating', 'recent_ratings',
            'thumbnail_url', 'can_enroll', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_enrollment_status(self, obj):
        """Get user's enrollment status."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                enrollment = obj.enrollments.get(
                    student=request.user,
                    is_active=True
                )
                return CourseEnrollmentSerializer(enrollment, context=self.context).data
            except CourseEnrollment.DoesNotExist:
                pass
        return None
    
    def get_user_rating(self, obj):
        """Get user's rating for this course."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                rating = obj.ratings.get(student=request.user)
                return CourseRatingSerializer(rating).data
            except CourseRating.DoesNotExist:
                pass
        return None
    
    def get_recent_ratings(self, obj):
        """Get recent course ratings."""
        recent_ratings = obj.ratings.filter(
            is_approved=True
        ).order_by('-created_at')[:5]
        return CourseRatingSerializer(recent_ratings, many=True).data
    
    def get_thumbnail_url(self, obj):
        """Get the thumbnail URL."""
        if obj.thumbnail:
            return self.context['request'].build_absolute_uri(obj.thumbnail.url)
        return None
    
    def get_can_enroll(self, obj):
        """Check if user can enroll in this course."""
        return obj.can_enroll


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating courses."""
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Course
        fields = [
            'title', 'slug', 'description', 'short_description',
            'difficulty_level', 'status', 'language', 'start_date',
            'end_date', 'enrollment_start', 'enrollment_end',
            'max_students', 'estimated_hours', 'prerequisites',
            'thumbnail', 'trailer_video', 'learning_objectives', 'tags'
        ]
    
    def create(self, validated_data):
        """Create a new course."""
        tags_data = validated_data.pop('tags', [])
        validated_data['instructor'] = self.context['request'].user
        course = super().create(validated_data)
        
        # Handle tags
        self._handle_tags(course, tags_data)
        
        return course
    
    def update(self, instance, validated_data):
        """Update an existing course."""
        tags_data = validated_data.pop('tags', None)
        course = super().update(instance, validated_data)
        
        if tags_data is not None:
            # Clear existing tags and add new ones
            course.course_tags.all().delete()
            self._handle_tags(course, tags_data)
        
        return course
    
    def _handle_tags(self, course, tags_data):
        """Handle course tags creation and assignment."""
        for tag_name in tags_data:
            tag, created = CourseTag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name.lower().replace(' ', '-')}
            )
            CourseTagging.objects.get_or_create(
                course=course,
                tag=tag,
                defaults={'relevance_score': 1.0}
            )


class CourseWaitlistSerializer(serializers.ModelSerializer):
    """Serializer for course waitlist entries."""
    student = UserSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = CourseWaitlist
        fields = [
            'id', 'status', 'position', 'priority_score',
            'notification_sent', 'expires_at', 'student',
            'course_title', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'position', 'priority_score', 'notification_sent',
            'student', 'course_title', 'created_at', 'updated_at'
        ]


class CourseCertificateSerializer(serializers.ModelSerializer):
    """Serializer for course certificates."""
    student_name = serializers.CharField(source='enrollment.student.get_full_name', read_only=True)
    course_title = serializers.CharField(source='enrollment.course.title', read_only=True)
    certificate_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCertificate
        fields = [
            'id', 'certificate_type', 'certificate_number',
            'minimum_score', 'required_modules', 'issued_at',
            'expires_at', 'certificate_pdf', 'certificate_url',
            'certificate_template', 'verification_code', 'is_valid',
            'metadata', 'student_name', 'course_title'
        ]
        read_only_fields = [
            'id', 'certificate_number', 'issued_at', 'verification_code',
            'student_name', 'course_title', 'certificate_url'
        ]
    
    def get_certificate_url(self, obj):
        """Get the certificate PDF URL."""
        if obj.certificate_pdf:
            return self.context['request'].build_absolute_uri(obj.certificate_pdf.url)
        return None


class CourseAnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for course announcements."""
    author = UserSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = CourseAnnouncement
        fields = [
            'id', 'title', 'content', 'priority', 'target_all_students',
            'target_students', 'is_published', 'publish_at', 'expires_at',
            'send_email', 'send_push_notification', 'author',
            'course_title', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'course_title', 'is_active',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create a new course announcement."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class CourseAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for course analytics data."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = CourseAnalytics
        fields = [
            'id', 'metric_type', 'metric_name', 'metric_value',
            'date', 'period_type', 'metadata', 'course_title', 'created_at'
        ]
        read_only_fields = ['id', 'course_title', 'created_at']


class CourseSearchSerializer(serializers.Serializer):
    """Serializer for course search parameters."""
    q = serializers.CharField(required=False, allow_blank=True)
    difficulty_level = serializers.MultipleChoiceField(
        choices=Course.DIFFICULTY_LEVELS,
        required=False,
        allow_empty=True
    )
    status = serializers.MultipleChoiceField(
        choices=Course.STATUS_CHOICES,
        required=False,
        allow_empty=True
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    instructor = serializers.CharField(required=False, allow_blank=True)
    min_rating = serializers.FloatField(min_value=0, max_value=5, required=False)
    max_hours = serializers.IntegerField(min_value=1, required=False)
    has_certificate = serializers.BooleanField(required=False)
    is_free = serializers.BooleanField(required=False)
    language = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        choices=[
            'title', '-title', 'created_at', '-created_at',
            'average_rating', '-average_rating', 'total_enrollments',
            '-total_enrollments', 'difficulty_level', '-difficulty_level'
        ],
        required=False,
        default='-created_at'
    )
