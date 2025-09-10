"""
URL configuration for the courses app.

This module defines all URL patterns for course-related API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

app_name = 'courses'

# Main router for top-level resources
router = DefaultRouter()

# Course-related endpoints
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'tags', views.CourseTagViewSet, basename='coursetag')
router.register(r'waitlist', views.CourseWaitlistViewSet, basename='waitlist')
router.register(r'certificates', views.CourseCertificateViewSet, basename='certificate')

# Nested routers for course sub-resources
courses_router = routers.NestedDefaultRouter(router, r'courses', lookup='course')
courses_router.register(r'modules', views.CourseModuleViewSet, basename='course-modules')
courses_router.register(r'announcements', views.CourseAnnouncementViewSet, basename='course-announcements')

# Nested router for module sub-resources
modules_router = routers.NestedDefaultRouter(courses_router, r'modules', lookup='module')
modules_router.register(r'lessons', views.LessonViewSet, basename='module-lessons')

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(courses_router.urls)),
    path('api/', include(modules_router.urls)),
    
    # Custom function-based views
    path('api/search/', views.course_search, name='course-search'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/my-enrollments/', views.MyEnrollmentsView.as_view(), name='my-enrollments'),
    path('api/generate-certificate/<uuid:enrollment_id>/', views.generate_certificate, name='generate-certificate'),
]

# Additional URL patterns can be added for specific endpoints
# that don't fit the REST pattern or need custom routing
