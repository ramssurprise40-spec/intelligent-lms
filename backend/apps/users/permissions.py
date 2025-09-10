"""
Custom permissions for the Intelligent LMS users app.
"""

from rest_framework import permissions
from django.contrib.auth.models import AnonymousUser


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj == request.user


class IsStudentOrReadOnly(permissions.BasePermission):
    """
    Permission for students to only read content, with write access for instructors and admins.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        # Allow read access for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write access only for non-students
        return request.user.role != 'student'


class IsInstructorOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to instructors and admins.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
            
        return request.user.role in ['instructor', 'admin']


class IsAdminOnly(permissions.BasePermission):
    """
    Permission class that allows access only to admins.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False
            
        return request.user.role == 'admin'


class IsEnrolledInCourse(permissions.BasePermission):
    """
    Permission to check if user is enrolled in a specific course.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin and instructor can access any course
        if request.user.role in ['admin', 'instructor']:
            return True

        # Check if user is enrolled in the course
        from apps.courses.models import CourseEnrollment
        return CourseEnrollment.objects.filter(
            course=obj,
            student=request.user,
            is_active=True
        ).exists()


class IsCourseInstructorOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is the course instructor or admin.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin can access any course
        if request.user.role == 'admin':
            return True

        # Check if user is the course instructor
        return obj.instructor == request.user


class CanViewUserProfile(permissions.BasePermission):
    """
    Permission to view user profiles based on privacy settings.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin can view any profile
        if request.user.role == 'admin':
            return True

        # Users can view their own profile
        if obj == request.user:
            return True

        # Check privacy settings
        profile_privacy = getattr(obj.profile, 'privacy_level', 'private')
        
        if profile_privacy == 'public':
            return True
        elif profile_privacy == 'friends':
            # Check if users are connected/friends
            return self.are_connected(request.user, obj)
        else:  # private
            return False

    def are_connected(self, user1, user2):
        """
        Check if two users are connected (can be extended for friend system).
        For now, check if they share any courses.
        """
        from apps.courses.models import CourseEnrollment
        
        user1_courses = set(CourseEnrollment.objects.filter(
            student=user1, is_active=True
        ).values_list('course_id', flat=True))
        
        user2_courses = set(CourseEnrollment.objects.filter(
            student=user2, is_active=True
        ).values_list('course_id', flat=True))
        
        return bool(user1_courses & user2_courses)


class IsAssessmentOwnerOrInstructor(permissions.BasePermission):
    """
    Permission for assessment access - owner or course instructor.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin can access anything
        if request.user.role == 'admin':
            return True

        # Assessment creator can access
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True

        # Course instructor can access course assessments
        if hasattr(obj, 'course') and obj.course.instructor == request.user:
            return True

        # For submissions, check if user is the submitter or instructor
        if hasattr(obj, 'student'):
            if obj.student == request.user:
                return True
            # Check if current user is instructor of the course
            if hasattr(obj, 'assessment') and hasattr(obj.assessment, 'course'):
                return obj.assessment.course.instructor == request.user

        return False


class IsForumModeratorOrAdmin(permissions.BasePermission):
    """
    Permission for forum moderation capabilities.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return request.user.role in ['admin', 'instructor'] or \
               getattr(request.user.profile, 'is_forum_moderator', False)


class CanManageNotifications(permissions.BasePermission):
    """
    Permission to manage user notifications.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin can manage any notifications
        if request.user.role == 'admin':
            return True

        # Users can manage their own notifications
        return obj.user == request.user


class IsVerifiedUser(permissions.BasePermission):
    """
    Permission that requires email verification.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return getattr(request.user, 'is_verified', False)


class HasCompletedProfile(permissions.BasePermission):
    """
    Permission that requires completed user profile.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        return getattr(request.user.profile, 'is_profile_complete', False)


# Composite permissions
class IsInstructorOrAdminAndVerified(permissions.BasePermission):
    """
    Composite permission: Instructor/Admin AND verified email.
    """

    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            return False

        is_instructor_or_admin = request.user.role in ['instructor', 'admin']
        is_verified = getattr(request.user, 'is_verified', False)
        
        return is_instructor_or_admin and is_verified


class IsActiveStudentInCourse(permissions.BasePermission):
    """
    Permission to check if user is an active student in the course.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(request.user, AnonymousUser):
            return False

        # Admin and instructors can access
        if request.user.role in ['admin', 'instructor']:
            return True

        # Check if user is actively enrolled
        from apps.courses.models import CourseEnrollment
        try:
            enrollment = CourseEnrollment.objects.get(
                course=obj,
                student=request.user
            )
            return enrollment.is_active and enrollment.enrollment_status == 'enrolled'
        except CourseEnrollment.DoesNotExist:
            return False
