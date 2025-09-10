"""
Role-based permissions system for the Intelligent LMS.

This module provides custom permission classes and decorators for
implementing fine-grained access control based on user roles and
specific permissions.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps


class IsAdminUser(BasePermission):
    """
    Permission class for admin users only.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )


class IsInstructorUser(BasePermission):
    """
    Permission class for instructor users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['instructor', 'admin']
        )


class IsStudentUser(BasePermission):
    """
    Permission class for student users.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'student'
        )


class IsOwnerOrInstructor(BasePermission):
    """
    Permission class that allows access to owners or instructors.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin':
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if user is an instructor for course-related objects
        if hasattr(obj, 'course') and hasattr(obj.course, 'instructor'):
            return obj.course.instructor == request.user
        
        # Check if object itself has instructor relationship
        if hasattr(obj, 'instructor') and obj.instructor == request.user:
            return True
        
        return False


class IsCourseInstructor(BasePermission):
    """
    Permission class for course instructors.
    """
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin':
            return True
        
        # Check if user is the course instructor
        if hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        elif hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        
        return False


class IsEnrolledStudent(BasePermission):
    """
    Permission class for enrolled students.
    """
    def has_object_permission(self, request, view, obj):
        # Admin and instructor users have access
        if request.user.role in ['admin', 'instructor']:
            return True
        
        # Check if student is enrolled in the course
        if hasattr(obj, 'course'):
            return obj.course.enrollments.filter(
                student=request.user, 
                is_active=True
            ).exists()
        
        return False


class CanManageUsers(BasePermission):
    """
    Permission class for user management operations.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )


class CanManageCourses(BasePermission):
    """
    Permission class for course management operations.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'instructor']
        )


class CanGradeAssessments(BasePermission):
    """
    Permission class for assessment grading operations.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'instructor']
        )
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.role == 'admin':
            return True
        
        # Check if instructor owns the assessment or course
        if hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        elif hasattr(obj, 'assessment') and hasattr(obj.assessment, 'course'):
            return obj.assessment.course.instructor == request.user
        
        return False


class CanViewAnalytics(BasePermission):
    """
    Permission class for analytics viewing.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['admin', 'instructor']
        )


class ReadOnlyOrOwner(BasePermission):
    """
    Permission class that allows read-only access to all, 
    but write access only to owners.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


# Decorator-based permissions
def admin_required(function):
    """
    Decorator that requires admin role.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            raise PermissionDenied("Admin access required.")
        return function(request, *args, **kwargs)
    return wrapper


def instructor_required(function):
    """
    Decorator that requires instructor or admin role.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['instructor', 'admin']:
            raise PermissionDenied("Instructor access required.")
        return function(request, *args, **kwargs)
    return wrapper


def student_required(function):
    """
    Decorator that requires student role.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            raise PermissionDenied("Student access required.")
        return function(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator that requires specific roles.
    
    Usage: @role_required('admin', 'instructor')
    """
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated or request.user.role not in allowed_roles:
                raise PermissionDenied(f"Access denied. Required roles: {', '.join(allowed_roles)}")
            return function(request, *args, **kwargs)
        return wrapper
    return decorator


def course_enrollment_required(function):
    """
    Decorator that requires course enrollment for students.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        # Admin and instructors have access
        if request.user.role in ['admin', 'instructor']:
            return function(request, *args, **kwargs)
        
        # For students, check enrollment
        course_id = kwargs.get('course_id') or request.GET.get('course_id')
        if not course_id:
            raise PermissionDenied("Course enrollment required.")
        
        from apps.courses.models import Enrollment
        if not Enrollment.objects.filter(
            student=request.user, 
            course_id=course_id, 
            is_active=True
        ).exists():
            raise PermissionDenied("You must be enrolled in this course.")
        
        return function(request, *args, **kwargs)
    return wrapper


def mfa_required(function):
    """
    Decorator that requires multi-factor authentication.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        # Check if MFA is enabled and verified
        if hasattr(request.user, 'mfa') and request.user.mfa.is_enabled:
            # Check if current session has MFA verification
            if not request.session.get('mfa_verified', False):
                raise PermissionDenied("Multi-factor authentication required.")
        
        return function(request, *args, **kwargs)
    return wrapper


def rate_limit_required(rate='5/m'):
    """
    Decorator that applies rate limiting.
    
    Usage: @rate_limit_required('10/m')  # 10 requests per minute
    """
    def decorator(function):
        from django_ratelimit.decorators import ratelimit
        return ratelimit(key='user', rate=rate, method='POST')(function)
    return decorator


# Permission checking utilities
class PermissionChecker:
    """
    Utility class for checking permissions in views and templates.
    """
    
    @staticmethod
    def can_manage_user(user, target_user):
        """Check if user can manage another user."""
        if user.role == 'admin':
            return True
        return False
    
    @staticmethod
    def can_manage_course(user, course):
        """Check if user can manage a course."""
        if user.role == 'admin':
            return True
        if user.role == 'instructor' and course.instructor == user:
            return True
        return False
    
    @staticmethod
    def can_view_course(user, course):
        """Check if user can view a course."""
        if user.role in ['admin', 'instructor']:
            return True
        if user.role == 'student':
            return course.enrollments.filter(
                student=user, 
                is_active=True
            ).exists()
        return False
    
    @staticmethod
    def can_submit_assessment(user, assessment):
        """Check if user can submit an assessment."""
        if user.role != 'student':
            return False
        
        # Check course enrollment
        if not assessment.course.enrollments.filter(
            student=user, 
            is_active=True
        ).exists():
            return False
        
        # Check if assessment is available
        if not assessment.can_submit:
            return False
        
        # Check attempt limits
        submitted_attempts = assessment.submissions.filter(
            student=user,
            status__in=['submitted', 'graded']
        ).count()
        
        return submitted_attempts < assessment.max_attempts
    
    @staticmethod
    def can_grade_assessment(user, assessment):
        """Check if user can grade an assessment."""
        if user.role == 'admin':
            return True
        if user.role == 'instructor' and assessment.course.instructor == user:
            return True
        return False
    
    @staticmethod
    def can_view_analytics(user, course=None):
        """Check if user can view analytics."""
        if user.role == 'admin':
            return True
        if user.role == 'instructor':
            if course is None or course.instructor == user:
                return True
        return False


# Custom authentication backend
class RoleBasedAuthBackend:
    """
    Custom authentication backend that considers user roles.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.backends import ModelBackend
        
        User = get_user_model()
        backend = ModelBackend()
        
        user = backend.authenticate(request, username=username, password=password, **kwargs)
        
        if user and user.is_authenticated:
            # Additional role-based checks can be added here
            if not user.is_active:
                return None
            
            # Check account lockout
            if hasattr(user, 'lockouts'):
                active_lockout = user.lockouts.filter(
                    is_active=True,
                    locked_until__gt=timezone.now()
                ).first()
                if active_lockout:
                    return None
        
        return user
    
    def get_user(self, user_id):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.backends import ModelBackend
        
        backend = ModelBackend()
        return backend.get_user(user_id)
