"""
URL configuration for the assessments app.

This module defines all URL patterns for assessment-related API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

app_name = 'assessments'

# Main router
router = DefaultRouter()
router.register(r'assessments', views.AssessmentViewSet, basename='assessment')

# Nested routers: assessments -> questions, submissions, rubric, peer-reviews
assessments_router = routers.NestedDefaultRouter(router, r'assessments', lookup='assessment')
assessments_router.register(r'questions', views.QuestionViewSet, basename='assessment-questions')
assessments_router.register(r'submissions', views.SubmissionViewSet, basename='assessment-submissions')
assessments_router.register(r'rubric', views.RubricViewSet, basename='assessment-rubric')
assessments_router.register(r'peer-reviews', views.PeerReviewViewSet, basename='assessment-peer-reviews')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(assessments_router.urls)),
    path('api/stats/', views.assessment_stats, name='assessment-stats'),
]
