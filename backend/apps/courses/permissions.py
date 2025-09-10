"""
Course-specific permissions for the Intelligent LMS system.

This module provides custom permission classes for course-related operations.
"""

from rest_framework import permissions
from django.contrib.auth import get_user_model
from .models import CourseEnrollment

User = get_user_model()


class IsEnrolledOrInstructor(permissions.BasePermission):
    """
    Permission that allows access only to enrolled students or course instructors.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is enrolled in the course or is the instructor.
        
        This works for different object types:
        - Course: Check if user is instructor or enrolled
        - Lesson: Check if user is enrolled in the course containing this lesson
        - Module: Check if user is enrolled in the course containing this module
        """
        user = request.user
        
        # Staff users have access to everything
        if user.is_staff:
            return True
        
        # Determine the course based on the object type
        if hasattr(obj, 'instructor'):  # Course object
            course = obj
        elif hasattr(obj, 'course'):  # Module object
            course = obj.course
        elif hasattr(obj, 'module'):  # Lesson object
            course = obj.module.course
        elif hasattr(obj, 'enrollment') and hasattr(obj.enrollment, 'course'):  # Progress objects
            course = obj.enrollment.course
        else:
            return False
        
        # Check if user is the instructor
        if course.instructor == user:
            return True
        
        # Check if user is enrolled
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=course,
                is_active=True
            )
            return True
        except CourseEnrollment.DoesNotExist:
            return False


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to anyone, but write access only to instructors.
    """
    
    def has_permission(self, request, view):
        """Allow read access to anyone, write access to authenticated users."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Allow read access to anyone, write access only to course instructor."""
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        
        # Staff users have full access
        if user.is_staff:
            return True
        
        # Determine the course and check instructor status
        if hasattr(obj, 'instructor'):  # Course object
            return obj.instructor == user
        elif hasattr(obj, 'course'):  # Module object
            return obj.course.instructor == user
        elif hasattr(obj, 'module'):  # Lesson object
            return obj.module.course.instructor == user
        elif hasattr(obj, 'enrollment'):  # Progress objects
            return obj.enrollment.course.instructor == user
        
        return False


class IsOwnerOrInstructor(permissions.BasePermission):
    """
    Permission that allows access to object owners or course instructors.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Allow access to owners or instructors."""
        user = request.user
        
        # Staff users have access to everything
        if user.is_staff:
            return True
        
        # Check if user owns the object
        if hasattr(obj, 'student') and obj.student == user:
            return True
        elif hasattr(obj, 'user') and obj.user == user:
            return True
        
        # Check if user is the course instructor
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'enrollment'):
            course = obj.enrollment.course
        elif hasattr(obj, 'lesson') and hasattr(obj.lesson, 'module'):
            course = obj.lesson.module.course
        
        if course and course.instructor == user:
            return True
        
        return False


class CanEnrollPermission(permissions.BasePermission):
    """
    Permission to check if a user can enroll in a course.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can enroll in the course."""
        user = request.user
        course = obj
        
        # Check if already enrolled
        if CourseEnrollment.objects.filter(
            student=user,
            course=course,
            is_active=True
        ).exists():
            return False
        
        # Check if enrollment is currently open
        if not course.can_enroll:
            return False
        
        return True


class CanRateCoursePermission(permissions.BasePermission):
    """
    Permission to check if a user can rate a course.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can rate the course."""
        user = request.user
        course = obj
        
        # Instructors cannot rate their own courses
        if course.instructor == user:
            return False
        
        # User must be enrolled or have completed the course
        try:
            enrollment = CourseEnrollment.objects.get(
                student=user,
                course=course
            )
            # Allow rating if enrolled or completed
            return enrollment.status in ['enrolled', 'completed']
        except CourseEnrollment.DoesNotExist:
            return False


class IsCourseInstructorOrReadOnly(permissions.BasePermission):
    """
    Permission for course-specific instructor access.
    """
    
    def has_permission(self, request, view):
        """Allow read access to anyone, write access to authenticated users."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the specific course instructor."""
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        
        # Staff users have full access
        if user.is_staff:
            return True
        
        # Get the course from different object types
        if hasattr(obj, 'instructor'):  # Course
            return obj.instructor == user
        elif hasattr(obj, 'course'):  # Module, Announcement, etc.
            return obj.course.instructor == user
        elif hasattr(obj, 'module'):  # Lesson
            return obj.module.course.instructor == user
        
        return False


class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Permission that allows read access to anyone, write access to students only.
    """
    
    def has_permission(self, request, view):
        """Allow read access to anyone, write access to authenticated non-staff users."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and not request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        """Allow read access to anyone, write access to students who own the object."""
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        user = request.user
        
        # Check if user owns the object (for ratings, progress, etc.)
        if hasattr(obj, 'student') and obj.student == user:
            return True
        
        return False


class IsEnrolledStudent(permissions.BasePermission):
    """
    Permission that allows access only to students enrolled in the specific course.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is enrolled as a student."""
        user = request.user
        
        # Staff users have access
        if user.is_staff:
            return True
        
        # Get course from object
        course = None
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'enrollment'):
            course = obj.enrollment.course
        elif hasattr(obj, 'lesson'):
            course = obj.lesson.module.course
        
        if not course:
            return False
        
        # Check enrollment
        return CourseEnrollment.objects.filter(
            student=user,
            course=course,
            is_active=True,
            status__in=['enrolled', 'completed']
        ).exists()


class CanManageCertificate(permissions.BasePermission):
    """
    Permission for certificate management.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user can manage the certificate."""
        user = request.user
        
        # Staff users can manage all certificates
        if user.is_staff:
            return True
        
        # Students can view their own certificates
        if hasattr(obj, 'enrollment') and obj.enrollment.student == user:
            return request.method in permissions.SAFE_METHODS
        
        # Instructors can view certificates for their courses
        if hasattr(obj, 'enrollment') and obj.enrollment.course.instructor == user:
            return True
        
        return False
