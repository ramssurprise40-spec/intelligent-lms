"""
Assessment API views for the Intelligent LMS system.

This module provides endpoints for managing assessments, questions,
submissions, grading, peer reviews, and analytics.
"""

from rest_framework import status, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.db import transaction
from django.contrib.auth import get_user_model
import logging

from authentication.permissions import (
    IsInstructorUser, IsOwnerOrInstructor, ReadOnlyOrOwner
)
from apps.courses.permissions import IsEnrolledOrInstructor

from .models import (
    Assessment, Question, AssessmentSubmission, QuestionResponse,
    GradingRubric, PeerReview, AssessmentAnalytics
)
from .serializers import (
    AssessmentListSerializer, AssessmentDetailSerializer, AssessmentCreateUpdateSerializer,
    QuestionSerializer, AssessmentSubmissionSerializer, SubmissionCreateSerializer,
    GradeSubmissionSerializer, GradingRubricSerializer, PeerReviewSerializer,
    AssessmentAnalyticsSerializer, AssessmentStatsSerializer
)

User = get_user_model()
logger = logging.getLogger(__name__)


class AssessmentViewSet(ModelViewSet):
    """ViewSet for managing assessments with CRUD and custom actions."""
    queryset = Assessment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assessment_type', 'status', 'course']
    search_fields = ['title', 'description', 'course__title']
    ordering_fields = ['created_at', 'due_date', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return AssessmentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AssessmentCreateUpdateSerializer
        return AssessmentDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related('course', 'creator').prefetch_related('questions')
        user = self.request.user
        if user.is_staff:
            return qs
        # Instructors see their course assessments; students see published
        return qs.filter(Q(course__instructor=user) | Q(status='published')).distinct()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def publish(self, request, pk=None):
        assessment = self.get_object()
        if request.user != assessment.course.instructor and not request.user.is_staff:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        assessment.status = 'published'
        assessment.published_at = timezone.now()
        assessment.save()
        return Response({'message': 'Assessment published.'})

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_submissions(self, request, pk=None):
        assessment = self.get_object()
        submissions = assessment.submissions.filter(student=request.user).order_by('-attempt_number')
        return Response(AssessmentSubmissionSerializer(submissions, many=True).data)


class QuestionViewSet(ModelViewSet):
    """Manage questions for an assessment."""
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        assessment_id = self.kwargs.get('assessment_pk')
        return Question.objects.filter(assessment_id=assessment_id).order_by('order')

    def perform_create(self, serializer):
        assessment_id = self.kwargs.get('assessment_pk')
        serializer.save(assessment_id=assessment_id)


class SubmissionViewSet(ModelViewSet):
    """Create and view submissions for an assessment."""
    serializer_class = AssessmentSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrolledOrInstructor]

    def get_queryset(self):
        assessment_id = self.kwargs.get('assessment_pk')
        qs = AssessmentSubmission.objects.filter(assessment_id=assessment_id)
        # Students see only their own submissions
        if not self.request.user.is_staff and self.request.user != self.get_assessment().course.instructor:
            qs = qs.filter(student=self.request.user)
        return qs

    def get_assessment(self):
        return Assessment.objects.get(id=self.kwargs.get('assessment_pk'))

    def create(self, request, *args, **kwargs):
        assessment = self.get_assessment()
        serializer = SubmissionCreateSerializer(data=request.data, context={'request': request, 'assessment': assessment})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        return Response(AssessmentSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit(self, request, assessment_pk=None, pk=None):
        submission = self.get_object()
        if submission.student != request.user and not request.user.is_staff:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        submission.submit()
        return Response({'message': 'Submission marked as submitted.'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOwnerOrInstructor])
    def grade(self, request, assessment_pk=None, pk=None):
        submission = self.get_object()
        serializer = GradeSubmissionSerializer(submission, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AssessmentSubmissionSerializer(submission).data)


class RubricViewSet(ModelViewSet):
    """Manage grading rubrics for assessments."""
    serializer_class = GradingRubricSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GradingRubric.objects.filter(assessment_id=self.kwargs.get('assessment_pk'))

    def perform_create(self, serializer):
        serializer.save(assessment_id=self.kwargs.get('assessment_pk'))


class PeerReviewViewSet(ModelViewSet):
    """Manage peer reviews for submissions."""
    serializer_class = PeerReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PeerReview.objects.filter(assessment_id=self.kwargs.get('assessment_pk'))

    def perform_create(self, serializer):
        serializer.save(assessment_id=self.kwargs.get('assessment_pk'), reviewer=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def assessment_stats(request):
    """Return dashboard stats for assessments for current user."""
    user = request.user
    if user.is_staff or hasattr(user, 'instructor_courses'):
        assessments = Assessment.objects.filter(Q(creator=user) | Q(course__instructor=user))
        total_assessments = assessments.count()
        published_assessments = assessments.filter(status='published').count()
        draft_assessments = assessments.filter(status='draft').count()
        subs = AssessmentSubmission.objects.filter(assessment__in=assessments)
        total_submissions = subs.count()
        pending_grading = subs.filter(status='submitted').count()
        average_score = subs.aggregate(avg=Avg('score'))['avg'] or 0
        recent_submissions = subs.order_by('-submitted_at')[:10]
    else:
        # Student stats
        assessments = Assessment.objects.filter(status='published')
        subs = AssessmentSubmission.objects.filter(student=user)
        total_assessments = assessments.count()
        published_assessments = total_assessments
        draft_assessments = 0
        total_submissions = subs.count()
        pending_grading = subs.filter(status='submitted').count()
        average_score = subs.aggregate(avg=Avg('score'))['avg'] or 0
        recent_submissions = subs.order_by('-submitted_at')[:10]

    data = {
        'total_assessments': total_assessments,
        'published_assessments': published_assessments,
        'draft_assessments': draft_assessments,
        'total_submissions': total_submissions,
        'pending_grading': pending_grading,
        'average_score': average_score,
        'recent_submissions': AssessmentSubmissionSerializer(recent_submissions, many=True).data
    }
    return Response(data)
