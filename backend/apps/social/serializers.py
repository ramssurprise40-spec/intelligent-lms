"""
Serializers for social and collaborative app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    StudyGroup, StudyGroupMembership, PeerConnection,
    CollaborationSession, PeerReview, ProjectGroup,
    ProjectGroupMembership, SocialInteraction, LearningCircle,
    SkillExchange, MentorshipRelationship
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class StudyGroupMembershipSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = StudyGroupMembership
        fields = ['user', 'role', 'contribution_score', 'last_activity', 'joined_at']
        read_only_fields = ['last_activity', 'joined_at']


class StudyGroupSerializer(serializers.ModelSerializer):
    members = UserBasicSerializer(many=True, read_only=True)
    creator = UserBasicSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            'id', 'name', 'description', 'course', 'status', 'is_private', 'max_members',
            'members', 'creator', 'member_count', 'matching_criteria', 'compatibility_scores',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'member_count', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()


class PeerConnectionSerializer(serializers.ModelSerializer):
    from_user = UserBasicSerializer(read_only=True)
    to_user = UserBasicSerializer(read_only=True)

    class Meta:
        model = PeerConnection
        fields = [
            'id', 'from_user', 'to_user', 'connection_type', 'strength_score',
            'interaction_frequency', 'is_active', 'is_mutual', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'from_user', 'created_at', 'updated_at']


class CollaborationSessionSerializer(serializers.ModelSerializer):
    organizer = UserBasicSerializer(read_only=True)
    participants = UserBasicSerializer(many=True, read_only=True)

    class Meta:
        model = CollaborationSession
        fields = [
            'id', 'title', 'description', 'session_type', 'participants', 'organizer',
            'course', 'related_lesson', 'related_assessment', 'scheduled_at',
            'duration_minutes', 'location', 'effectiveness_score', 'collaboration_quality',
            'learning_outcomes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organizer', 'created_at', 'updated_at']


class PeerReviewSerializer(serializers.ModelSerializer):
    reviewer = UserBasicSerializer(read_only=True)
    reviewee = UserBasicSerializer(read_only=True)

    class Meta:
        model = PeerReview
        fields = [
            'id', 'title', 'description', 'reviewer', 'reviewee', 'feedback_type', 'status',
            'course', 'assignment', 'overall_rating', 'written_feedback', 'rubric_scores',
            'suggestions', 'ai_analysis', 'feedback_quality_score', 'assigned_at', 'due_date', 'completed_at'
        ]
        read_only_fields = ['id', 'reviewer', 'assigned_at', 'completed_at']


class ProjectGroupMembershipSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)

    class Meta:
        model = ProjectGroupMembership
        fields = [
            'user', 'role', 'contribution_percentage', 'tasks_assigned', 'tasks_completed',
            'peer_rating', 'last_activity', 'total_contributions', 'joined_at'
        ]
        read_only_fields = ['last_activity', 'joined_at']


class ProjectGroupSerializer(serializers.ModelSerializer):
    members = UserBasicSerializer(many=True, read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = ProjectGroup
        fields = [
            'id', 'name', 'description', 'course', 'assignment', 'assignment_title',
            'members', 'member_count', 'status', 'max_members', 'is_self_selected',
            'progress_percentage', 'milestones_completed', 'current_milestone',
            'collaboration_effectiveness', 'risk_factors', 'success_predictors',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'member_count', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.count()


class SocialInteractionSerializer(serializers.ModelSerializer):
    from_user = UserBasicSerializer(read_only=True)
    to_user = UserBasicSerializer(read_only=True)

    class Meta:
        model = SocialInteraction
        fields = [
            'id', 'from_user', 'to_user', 'interaction_type', 'content_summary',
            'course', 'related_object_type', 'related_object_id',
            'sentiment_score', 'engagement_level', 'learning_value',
            'duration_minutes', 'participants_count', 'created_at'
        ]
        read_only_fields = ['id', 'from_user', 'created_at']


class LearningCircleSerializer(serializers.ModelSerializer):
    facilitator = UserBasicSerializer(read_only=True)
    members = UserBasicSerializer(many=True, read_only=True)

    class Meta:
        model = LearningCircle
        fields = [
            'id', 'name', 'description', 'circle_type', 'status', 'members', 'facilitator',
            'max_members', 'is_public', 'meeting_frequency', 'learning_objectives',
            'success_metrics', 'recommended_participants', 'compatibility_matrix',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SkillExchangeSerializer(serializers.ModelSerializer):
    creator = UserBasicSerializer(read_only=True)
    participants = UserBasicSerializer(many=True, read_only=True)

    class Meta:
        model = SkillExchange
        fields = [
            'id', 'title', 'description', 'exchange_type', 'status', 'creator', 'participants',
            'skills_offered', 'skills_requested', 'proficiency_level', 'potential_matches',
            'match_score', 'preferred_format', 'time_commitment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']


class MentorshipRelationshipSerializer(serializers.ModelSerializer):
    mentor = UserBasicSerializer(read_only=True)
    mentee = UserBasicSerializer(read_only=True)

    class Meta:
        model = MentorshipRelationship
        fields = [
            'id', 'mentor', 'mentee', 'mentorship_type', 'status', 'learning_goals',
            'progress_milestones', 'success_metrics', 'meeting_frequency', 'next_meeting',
            'total_meetings', 'relationship_effectiveness', 'compatibility_score',
            'progress_assessment', 'started_at', 'ended_at', 'updated_at'
        ]
        read_only_fields = ['id', 'started_at', 'ended_at', 'updated_at']

