"""
Course filters for the Intelligent LMS system.

This module provides advanced filtering capabilities for course searches.
"""

import django_filters
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Course, CourseTag, CourseRating

User = get_user_model()


class CourseFilter(django_filters.FilterSet):
    """
    Advanced filtering for courses with search and multi-criteria filtering.
    """
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Basic filters
    difficulty_level = django_filters.MultipleChoiceFilter(
        choices=Course.DIFFICULTY_LEVELS,
        field_name='difficulty_level',
        lookup_expr='in'
    )
    
    status = django_filters.MultipleChoiceFilter(
        choices=Course.STATUS_CHOICES,
        field_name='status',
        lookup_expr='in'
    )
    
    language = django_filters.CharFilter(
        field_name='language',
        lookup_expr='icontains'
    )
    
    # Instructor filter
    instructor = django_filters.CharFilter(
        method='filter_instructor',
        label='Instructor'
    )
    
    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    published_after = django_filters.DateTimeFilter(
        field_name='published_at',
        lookup_expr='gte'
    )
    
    published_before = django_filters.DateTimeFilter(
        field_name='published_at',
        lookup_expr='lte'
    )
    
    # Duration filters
    min_hours = django_filters.NumberFilter(
        field_name='estimated_hours',
        lookup_expr='gte'
    )
    
    max_hours = django_filters.NumberFilter(
        field_name='estimated_hours',
        lookup_expr='lte'
    )
    
    # Rating filters
    min_rating = django_filters.NumberFilter(
        field_name='average_rating',
        lookup_expr='gte'
    )
    
    # Enrollment filters
    min_enrollments = django_filters.NumberFilter(
        field_name='total_enrollments',
        lookup_expr='gte'
    )
    
    max_enrollments = django_filters.NumberFilter(
        field_name='total_enrollments',
        lookup_expr='lte'
    )
    
    # Tags filter
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=CourseTag.objects.all(),
        field_name='course_tags__tag',
        to_field_name='name',
        conjoined=False  # OR logic instead of AND
    )
    
    # Boolean filters
    has_certificate = django_filters.BooleanFilter(
        method='filter_has_certificate',
        label='Has Certificate'
    )
    
    is_free = django_filters.BooleanFilter(
        method='filter_is_free',
        label='Is Free'
    )
    
    has_prerequisites = django_filters.BooleanFilter(
        method='filter_has_prerequisites',
        label='Has Prerequisites'
    )
    
    # Enrollment status filter (for authenticated users)
    enrollment_status = django_filters.ChoiceFilter(
        choices=[
            ('enrolled', 'Enrolled'),
            ('completed', 'Completed'),
            ('dropped', 'Dropped'),
            ('not_enrolled', 'Not Enrolled')
        ],
        method='filter_enrollment_status',
        label='My Enrollment Status'
    )
    
    class Meta:
        model = Course
        fields = []
    
    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields including title, description, 
        instructor name, and tags.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(short_description__icontains=value) |
            Q(instructor__first_name__icontains=value) |
            Q(instructor__last_name__icontains=value) |
            Q(instructor__username__icontains=value) |
            Q(course_tags__tag__name__icontains=value) |
            Q(learning_objectives__icontains=value) |
            Q(modules__title__icontains=value) |
            Q(modules__lessons__title__icontains=value)
        ).distinct()
    
    def filter_instructor(self, queryset, name, value):
        """Filter by instructor name or username."""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(instructor__first_name__icontains=value) |
            Q(instructor__last_name__icontains=value) |
            Q(instructor__username__icontains=value)
        )
    
    def filter_has_certificate(self, queryset, name, value):
        """Filter courses that offer certificates."""
        if value is None:
            return queryset
        
        # This would depend on how certificates are configured
        # For now, assume courses with completion tracking offer certificates
        if value:
            return queryset.filter(
                modules__lessons__isnull=False
            ).distinct()
        else:
            return queryset.filter(
                modules__lessons__isnull=True
            )
    
    def filter_is_free(self, queryset, name, value):
        """Filter free/paid courses."""
        if value is None:
            return queryset
        
        # This would integrate with a pricing model
        # For now, assume all courses are free unless otherwise specified
        # This is a placeholder for future payment integration
        return queryset
    
    def filter_has_prerequisites(self, queryset, name, value):
        """Filter courses with or without prerequisites."""
        if value is None:
            return queryset
        
        if value:
            return queryset.filter(prerequisites__isnull=False).distinct()
        else:
            return queryset.filter(prerequisites__isnull=True)
    
    def filter_enrollment_status(self, queryset, name, value):
        """Filter by user's enrollment status."""
        request = self.request
        if not request or not request.user.is_authenticated:
            return queryset
        
        user = request.user
        
        if value == 'enrolled':
            return queryset.filter(
                enrollments__student=user,
                enrollments__status='enrolled',
                enrollments__is_active=True
            )
        elif value == 'completed':
            return queryset.filter(
                enrollments__student=user,
                enrollments__status='completed',
                enrollments__is_active=True
            )
        elif value == 'dropped':
            return queryset.filter(
                enrollments__student=user,
                enrollments__status='dropped'
            )
        elif value == 'not_enrolled':
            return queryset.exclude(
                enrollments__student=user,
                enrollments__is_active=True
            )
        
        return queryset


class CourseRatingFilter(django_filters.FilterSet):
    """Filter for course ratings and reviews."""
    
    rating = django_filters.NumberFilter(field_name='rating')
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    
    has_review = django_filters.BooleanFilter(
        method='filter_has_review',
        label='Has Review Text'
    )
    
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    is_approved = django_filters.BooleanFilter(field_name='is_approved')
    
    would_recommend = django_filters.BooleanFilter(field_name='would_recommend')
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = CourseRating
        fields = []
    
    def filter_has_review(self, queryset, name, value):
        """Filter ratings that have review text."""
        if value is None:
            return queryset
        
        if value:
            return queryset.exclude(Q(review='') | Q(review__isnull=True))
        else:
            return queryset.filter(Q(review='') | Q(review__isnull=True))
