"""
API views for social and collaborative features.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import (
    StudyGroup, StudyGroupMembership, PeerConnection,
    CollaborationSession, PeerReview, ProjectGroup,
    ProjectGroupMembership, SocialInteraction, LearningCircle,
    SkillExchange, MentorshipRelationship
)
from .serializers import (
    StudyGroupSerializer, PeerConnectionSerializer, CollaborationSessionSerializer,
    PeerReviewSerializer, ProjectGroupSerializer, SocialInteractionSerializer,
    LearningCircleSerializer, SkillExchangeSerializer, MentorshipRelationshipSerializer
)


class StudyGroupViewSet(viewsets.ModelViewSet):
    serializer_class = StudyGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyGroup.objects.filter(members=self.request.user)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        group = self.get_object()
        return Response({
            'group_id': str(group.id),
            'member_count': group.members.count(),
            'members': [m.username for m in group.members.all()]
        })


class PeerConnectionViewSet(viewsets.ModelViewSet):
    serializer_class = PeerConnectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PeerConnection.objects.filter(from_user=self.request.user)


class CollaborationSessionViewSet(viewsets.ModelViewSet):
    serializer_class = CollaborationSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CollaborationSession.objects.filter(participants=self.request.user)


class PeerReviewViewSet(viewsets.ModelViewSet):
    serializer_class = PeerReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PeerReview.objects.filter(reviewer=self.request.user)


class ProjectGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectGroupSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectGroup.objects.filter(members=self.request.user)


class SocialInteractionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SocialInteractionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SocialInteraction.objects.filter(from_user=self.request.user)


class LearningCircleViewSet(viewsets.ModelViewSet):
    serializer_class = LearningCircleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LearningCircle.objects.filter(members=self.request.user)


class SkillExchangeViewSet(viewsets.ModelViewSet):
    serializer_class = SkillExchangeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SkillExchange.objects.filter(
            models.Q(creator=self.request.user) | models.Q(participants=self.request.user)
        ).distinct()


class MentorshipRelationshipViewSet(viewsets.ModelViewSet):
    serializer_class = MentorshipRelationshipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MentorshipRelationship.objects.filter(
            models.Q(mentor=self.request.user) | models.Q(mentee=self.request.user)
        )
