"""
Course API views for the Intelligent LMS system.

This module provides comprehensive API endpoints for course management,
enrollment, content delivery, progress tracking, and analytics.
"""

from rest_framework import status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView
)
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum, F
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.http import Http404
from django.conf import settings
import logging

from authentication.permissions import (
    IsInstructorUser, IsOwnerOrInstructor, ReadOnlyOrOwner
)
from django.utils.decorators import method_decorator
from functools import wraps

# Rate limiting decorator (placeholder - can be replaced with django-ratelimit)
def rate_limit(key=None, rate=None, methods=None):
    """Simple rate limiting decorator placeholder."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # In production, implement actual rate limiting here
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Create missing permission classes
class IsInstructorOrReadOnly(permissions.BasePermission):
    """Permission for instructors to write, others to read only."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        if user.is_staff:
            return True
        
        # Check if user is instructor based on role or object relationship
        if hasattr(user, 'role') and user.role == 'instructor':
            return True
        
        if hasattr(obj, 'instructor') and obj.instructor == user:
            return True
        
        return False

class IsStudentOrInstructor(permissions.BasePermission):
    """Permission for students and instructors."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        
        if hasattr(user, 'role') and user.role in ['student', 'instructor']:
            return True
        
        return True  # Allow authenticated users by default

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission for owners to write, others to read only."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        if hasattr(obj, 'student') and obj.student == request.user:
            return True
        if hasattr(obj, 'instructor') and obj.instructor == request.user:
            return True
        
        return False

from .models import (
    Course, CourseModule, Lesson, CourseEnrollment, LessonProgress,
    CourseRating, CourseTag, CourseTagging, CourseWaitlist, 
    CourseCertificate, LessonContent, CourseAnalytics, CourseAnnouncement
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer, CourseCreateUpdateSerializer,
    CourseModuleSerializer, LessonSerializer, CourseEnrollmentSerializer,
    LessonProgressSerializer, CourseRatingSerializer, CourseTagSerializer,
    CourseWaitlistSerializer, CourseCertificateSerializer, LessonContentSerializer,
    CourseAnalyticsSerializer, CourseAnnouncementSerializer, CourseSearchSerializer
)
from .filters import CourseFilter
from .permissions import IsEnrolledOrInstructor

User = get_user_model()
logger = logging.getLogger(__name__)


class CourseViewSet(ModelViewSet):
    """
    ViewSet for managing courses with full CRUD operations.
    
    Provides endpoints for:
    - List/search courses with filtering
    - Retrieve course details
    - Create, update, delete courses (instructors only)
    - Enroll/unenroll from courses
    - Rate and review courses
    """
    queryset = Course.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'instructor__username']
    ordering_fields = ['title', 'created_at', 'average_rating', 'total_enrollments']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Add performance optimizations
        queryset = queryset.select_related('instructor').prefetch_related(
            'course_tags__tag',
            'modules__lessons',
            'enrollments',
            'ratings'
        )
        
        # Filter based on user permissions
        if self.action == 'list':
            # Show only published courses for non-instructors
            if not self.request.user.is_authenticated or not self.request.user.is_staff:
                queryset = queryset.filter(status='published')
        
        return queryset
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsInstructorOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    @rate_limit(key='enroll', rate='10/h', methods=['POST'])
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll a student in the course."""
        course = self.get_object()
        
        # Check if already enrolled
        existing_enrollment = CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            is_active=True
        ).first()
        
        if existing_enrollment:
            return Response(
                {'error': 'You are already enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if enrollment is allowed
        if not course.can_enroll:
            # Check if waitlist is available
            if course.max_students and course.total_enrollments >= course.max_students:
                return self._add_to_waitlist(course, request.user)
            
            return Response(
                {'error': 'Enrollment is not currently available for this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create enrollment
        with transaction.atomic():
            enrollment = CourseEnrollment.objects.create(
                student=request.user,
                course=course,
                status='enrolled'
            )
            
            # Create lesson progress records
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    LessonProgress.objects.create(
                        enrollment=enrollment,
                        lesson=lesson
                    )
        
        serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
        logger.info(f"User {request.user.username} enrolled in course {course.title}")
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _add_to_waitlist(self, course, user):
        """Add user to course waitlist."""
        waitlist_entry, created = CourseWaitlist.objects.get_or_create(
            course=course,
            student=user,
            defaults={'status': 'waiting'}
        )
        
        if created:
            serializer = CourseWaitlistSerializer(waitlist_entry)
            return Response({
                'message': 'Added to waitlist. You will be notified when a spot becomes available.',
                'waitlist': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {'error': 'You are already on the waitlist for this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unenroll(self, request, pk=None):
        """Unenroll a student from the course."""
        course = self.get_object()
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=request.user,
                course=course,
                is_active=True
            )
            enrollment.status = 'dropped'
            enrollment.dropped_at = timezone.now()
            enrollment.is_active = False
            enrollment.save()
            
            logger.info(f"User {request.user.username} unenrolled from course {course.title}")
            
            return Response({'message': 'Successfully unenrolled from course.'})
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @rate_limit(key='rating', rate='5/h', methods=['POST'])
    @action(detail=True, methods=['post'], permission_classes=[IsEnrolledOrInstructor])
    def rate(self, request, pk=None):
        """Rate and review a course."""
        course = self.get_object()
        
        # Check if user has already rated this course
        existing_rating = CourseRating.objects.filter(
            course=course,
            student=request.user
        ).first()
        
        serializer = CourseRatingSerializer(
            existing_rating,
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            if existing_rating:
                serializer.save()
                message = 'Rating updated successfully.'
            else:
                serializer.save(course=course)
                message = 'Rating submitted successfully.'
            
            return Response({
                'message': message,
                'rating': serializer.data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_progress(self, request, pk=None):
        """Get user's progress in the course."""
        course = self.get_object()
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=request.user,
                course=course,
                is_active=True
            )
            serializer = CourseEnrollmentSerializer(enrollment, context={'request': request})
            return Response(serializer.data)
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get course analytics (instructors only)."""
        course = self.get_object()
        
        # Check if user is the instructor
        if course.instructor != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get analytics data
        analytics_data = {
            'total_enrollments': course.total_enrollments,
            'active_enrollments': course.enrollments.filter(is_active=True).count(),
            'completion_rate': course.completion_rate,
            'average_rating': course.average_rating,
            'total_ratings': course.ratings.count(),
            'enrollment_trend': self._get_enrollment_trend(course),
            'completion_by_module': self._get_module_completion_stats(course),
            'student_engagement': self._get_engagement_stats(course),
            'rating_distribution': self._get_rating_distribution(course)
        }
        
        return Response(analytics_data)
    
    def _get_enrollment_trend(self, course):
        """Get enrollment trend over time."""
        from django.db.models import TruncDate
        
        trend_data = course.enrollments.extra(
            select={'date': 'DATE(enrolled_at)'}
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return list(trend_data)
    
    def _get_module_completion_stats(self, course):
        """Get completion statistics by module."""
        stats = []
        for module in course.modules.all():
            total_lessons = module.lessons.count()
            if total_lessons > 0:
                completion_data = LessonProgress.objects.filter(
                    lesson__module=module
                ).aggregate(
                    total_attempts=Count('id'),
                    completed=Count('id', filter=Q(is_completed=True))
                )
                
                completion_rate = (completion_data['completed'] / completion_data['total_attempts']) * 100 if completion_data['total_attempts'] > 0 else 0
                
                stats.append({
                    'module_id': module.id,
                    'module_title': module.title,
                    'total_lessons': total_lessons,
                    'completion_rate': round(completion_rate, 2)
                })
        
        return stats
    
    def _get_engagement_stats(self, course):
        """Get student engagement statistics."""
        enrollments = course.enrollments.filter(is_active=True)
        
        if not enrollments.exists():
            return {}
        
        avg_time_spent = enrollments.aggregate(
            avg_time=Avg('total_study_time')
        )['avg_time'] or 0
        
        progress_distribution = enrollments.values('progress_percentage').annotate(
            count=Count('id')
        ).order_by('progress_percentage')
        
        return {
            'average_study_time_hours': round(avg_time_spent / 3600, 2) if avg_time_spent else 0,
            'progress_distribution': list(progress_distribution)
        }
    
    def _get_rating_distribution(self, course):
        """Get rating distribution."""
        ratings = course.ratings.values('rating').annotate(
            count=Count('id')
        ).order_by('rating')
        
        distribution = {str(i): 0 for i in range(1, 6)}
        for rating in ratings:
            distribution[str(rating['rating'])] = rating['count']
        
        return distribution


class CourseModuleViewSet(ModelViewSet):
    """ViewSet for managing course modules."""
    serializer_class = CourseModuleSerializer
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_queryset(self):
        """Filter modules by course."""
        course_id = self.kwargs.get('course_pk')
        if course_id:
            return CourseModule.objects.filter(course_id=course_id).order_by('order')
        return CourseModule.objects.all()
    
    def perform_create(self, serializer):
        """Set course when creating a module."""
        course_id = self.kwargs.get('course_pk')
        if course_id:
            serializer.save(course_id=course_id)


class LessonViewSet(ModelViewSet):
    """ViewSet for managing lessons."""
    serializer_class = LessonSerializer
    permission_classes = [IsInstructorOrReadOnly]
    
    def get_queryset(self):
        """Filter lessons by module."""
        module_id = self.kwargs.get('module_pk')
        if module_id:
            return Lesson.objects.filter(module_id=module_id).order_by('order')
        return Lesson.objects.all()
    
    def perform_create(self, serializer):
        """Set module when creating a lesson."""
        module_id = self.kwargs.get('module_pk')
        if module_id:
            serializer.save(module_id=module_id)
    
    @action(detail=True, methods=['post'], permission_classes=[IsEnrolledOrInstructor])
    def mark_complete(self, request, pk=None):
        """Mark a lesson as complete."""
        lesson = self.get_object()
        
        try:
            # Find the user's enrollment
            enrollment = CourseEnrollment.objects.get(
                student=request.user,
                course=lesson.module.course,
                is_active=True
            )
            
            # Get or create lesson progress
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson,
                defaults={'completion_percentage': 100}
            )
            
            if not progress.is_completed:
                progress.is_completed = True
                progress.completion_percentage = 100
                progress.completed_at = timezone.now()
                progress.save()
                
                # Update enrollment progress
                enrollment.update_progress()
                
                return Response({
                    'message': 'Lesson marked as complete.',
                    'progress': LessonProgressSerializer(progress).data
                })
            else:
                return Response({
                    'message': 'Lesson already completed.',
                    'progress': LessonProgressSerializer(progress).data
                })
                
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsEnrolledOrInstructor])
    def update_progress(self, request, pk=None):
        """Update lesson progress."""
        lesson = self.get_object()
        completion_percentage = request.data.get('completion_percentage', 0)
        time_spent = request.data.get('time_spent', 0)
        
        try:
            enrollment = CourseEnrollment.objects.get(
                student=request.user,
                course=lesson.module.course,
                is_active=True
            )
            
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson
            )
            
            # Update progress
            progress.completion_percentage = max(progress.completion_percentage, completion_percentage)
            progress.time_spent = F('time_spent') + time_spent
            progress.last_accessed = timezone.now()
            
            if completion_percentage >= 100 and not progress.is_completed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
            
            progress.save()
            progress.refresh_from_db()
            
            # Update enrollment progress
            enrollment.update_progress()
            
            return Response(LessonProgressSerializer(progress).data)
            
        except CourseEnrollment.DoesNotExist:
            return Response(
                {'error': 'You are not enrolled in this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MyEnrollmentsView(ListAPIView):
    """List user's course enrollments."""
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['enrolled_at', 'progress_percentage', 'status']
    ordering = ['-enrolled_at']
    
    def get_queryset(self):
        """Get current user's enrollments."""
        return CourseEnrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).select_related('course', 'course__instructor')


class CourseTagViewSet(ReadOnlyModelViewSet):
    """ViewSet for course tags."""
    queryset = CourseTag.objects.all()
    serializer_class = CourseTagSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'usage_count']
    ordering = ['name']


class CourseWaitlistViewSet(ModelViewSet):
    """ViewSet for course waitlist management."""
    serializer_class = CourseWaitlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's waitlist entries or course waitlist (for instructors)."""
        if self.request.user.is_staff or hasattr(self.request.user, 'instructor_courses'):
            # Allow instructors to see their course waitlists
            return CourseWaitlist.objects.all()
        return CourseWaitlist.objects.filter(student=self.request.user)
    
    @action(detail=True, methods=['post'])
    def remove(self, request, pk=None):
        """Remove user from waitlist."""
        waitlist_entry = self.get_object()
        
        if waitlist_entry.student != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        waitlist_entry.delete()
        return Response({'message': 'Removed from waitlist successfully.'})


class CourseCertificateViewSet(ReadOnlyModelViewSet):
    """ViewSet for course certificates."""
    serializer_class = CourseCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Get user's certificates."""
        return CourseCertificate.objects.filter(
            enrollment__student=self.request.user
        ).select_related('enrollment__course', 'enrollment__student')


class CourseAnnouncementViewSet(ModelViewSet):
    """ViewSet for course announcements."""
    serializer_class = CourseAnnouncementSerializer
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter announcements by course."""
        course_id = self.kwargs.get('course_pk')
        if course_id:
            queryset = CourseAnnouncement.objects.filter(course_id=course_id)
            
            # Only show published announcements to students
            if not self.request.user.is_staff:
                queryset = queryset.filter(
                    is_published=True,
                    publish_at__lte=timezone.now()
                )
                
                # Filter by expiration
                queryset = queryset.filter(
                    Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
                )
            
            return queryset
        return CourseAnnouncement.objects.none()
    
    def perform_create(self, serializer):
        """Set course when creating an announcement."""
        course_id = self.kwargs.get('course_pk')
        if course_id:
            serializer.save(course_id=course_id)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def course_search(request):
    """Advanced course search with filtering and analytics."""
    serializer = CourseSearchSerializer(data=request.query_params)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    queryset = Course.objects.filter(status='published')
    
    # Apply filters
    if data.get('q'):
        queryset = queryset.filter(
            Q(title__icontains=data['q']) |
            Q(description__icontains=data['q']) |
            Q(instructor__username__icontains=data['q'])
        )
    
    if data.get('difficulty_level'):
        queryset = queryset.filter(difficulty_level__in=data['difficulty_level'])
    
    if data.get('tags'):
        queryset = queryset.filter(
            course_tags__tag__name__in=data['tags']
        ).distinct()
    
    if data.get('instructor'):
        queryset = queryset.filter(instructor__username__icontains=data['instructor'])
    
    if data.get('min_rating'):
        queryset = queryset.filter(average_rating__gte=data['min_rating'])
    
    if data.get('max_hours'):
        queryset = queryset.filter(estimated_hours__lte=data['max_hours'])
    
    if data.get('language'):
        queryset = queryset.filter(language__icontains=data['language'])
    
    # Apply ordering
    ordering = data.get('ordering', '-created_at')
    queryset = queryset.order_by(ordering)
    
    # Paginate results
    from rest_framework.pagination import PageNumberPagination
    
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = CourseListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = CourseListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics for the current user."""
    user = request.user
    
    # Student dashboard
    if not user.is_staff and not hasattr(user, 'instructor_courses'):
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            is_active=True
        )
        
        stats = {
            'total_enrollments': enrollments.count(),
            'completed_courses': enrollments.filter(status='completed').count(),
            'in_progress_courses': enrollments.filter(status='enrolled').count(),
            'total_study_time': sum(e.total_study_time for e in enrollments) / 3600,  # Convert to hours
            'certificates_earned': CourseCertificate.objects.filter(
                enrollment__student=user
            ).count(),
            'recent_progress': enrollments.order_by('-enrolled_at')[:5]
        }
        
        # Serialize recent progress
        stats['recent_progress'] = CourseEnrollmentSerializer(
            stats['recent_progress'],
            many=True,
            context={'request': request}
        ).data
        
    # Instructor dashboard
    else:
        courses = Course.objects.filter(instructor=user)
        
        stats = {
            'total_courses': courses.count(),
            'published_courses': courses.filter(status='published').count(),
            'draft_courses': courses.filter(status='draft').count(),
            'total_students': CourseEnrollment.objects.filter(
                course__instructor=user,
                is_active=True
            ).count(),
            'total_revenue': 0,  # Would integrate with payment system
            'average_rating': courses.aggregate(
                avg=Avg('average_rating')
            )['avg'] or 0,
            'recent_enrollments': CourseEnrollment.objects.filter(
                course__instructor=user
            ).order_by('-enrolled_at')[:10]
        }
        
        # Serialize recent enrollments
        stats['recent_enrollments'] = CourseEnrollmentSerializer(
            stats['recent_enrollments'],
            many=True,
            context={'request': request}
        ).data
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@rate_limit(key='certificate', rate='5/d', methods=['POST'])
def generate_certificate(request, enrollment_id):
    """Generate a certificate for completed course."""
    try:
        enrollment = CourseEnrollment.objects.get(
            id=enrollment_id,
            student=request.user,
            status='completed'
        )
        
        if enrollment.certificate_issued:
            return Response(
                {'error': 'Certificate already issued for this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create certificate
        certificate = CourseCertificate.objects.create(
            enrollment=enrollment,
            certificate_type='completion',
            minimum_score=enrollment.final_grade or 0
        )
        
        # Mark certificate as issued in enrollment
        enrollment.certificate_issued = True
        enrollment.certificate_issued_at = timezone.now()
        enrollment.save()
        
        logger.info(f"Certificate generated for user {request.user.username} - course {enrollment.course.title}")
        
        serializer = CourseCertificateSerializer(certificate, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except CourseEnrollment.DoesNotExist:
        return Response(
            {'error': 'Enrollment not found or course not completed.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error generating certificate: {str(e)}")
        return Response(
            {'error': 'Error generating certificate. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
