"""
Serializers for the communications app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Forum, ForumTopic, ForumPost, PostVote,
    DirectMessage, Announcement, AnnouncementView,
    ChatRoom, ChatRoomMembership, ChatMessage
)

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for nested representations.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'email']


class ForumSerializer(serializers.ModelSerializer):
    """
    Serializer for Forum model.
    """
    moderators = UserBasicSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Forum
        fields = [
            'id', 'course', 'course_title', 'title', 'description',
            'is_active', 'is_moderated', 'allow_anonymous_posts',
            'moderators', 'total_posts', 'total_topics',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_posts', 'total_topics', 'created_at', 'updated_at']


class ForumTopicSerializer(serializers.ModelSerializer):
    """
    Serializer for ForumTopic model.
    """
    author = UserBasicSerializer(read_only=True)
    last_post_by = UserBasicSerializer(read_only=True)
    forum_title = serializers.CharField(source='forum.title', read_only=True)
    
    class Meta:
        model = ForumTopic
        fields = [
            'id', 'forum', 'forum_title', 'title', 'author',
            'status', 'is_announcement', 'is_sticky',
            'view_count', 'post_count', 'created_at', 'updated_at',
            'last_post_at', 'last_post_by'
        ]
        read_only_fields = [
            'id', 'author', 'view_count', 'post_count',
            'created_at', 'updated_at', 'last_post_at', 'last_post_by'
        ]


class ForumPostSerializer(serializers.ModelSerializer):
    """
    Serializer for ForumPost model.
    """
    author = UserBasicSerializer(read_only=True)
    moderated_by = UserBasicSerializer(read_only=True)
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    vote_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumPost
        fields = [
            'id', 'topic', 'topic_title', 'author', 'content', 'status',
            'is_solution', 'post_number', 'upvotes', 'downvotes',
            'sentiment_score', 'toxicity_score', 'key_topics',
            'moderated_by', 'moderated_at', 'moderation_reason',
            'created_at', 'updated_at', 'vote_summary'
        ]
        read_only_fields = [
            'id', 'author', 'post_number', 'upvotes', 'downvotes',
            'sentiment_score', 'toxicity_score', 'key_topics',
            'moderated_by', 'moderated_at', 'created_at', 'updated_at'
        ]
    
    def get_vote_summary(self, obj):
        """Get voting summary for the post."""
        return {
            'total_votes': obj.upvotes + obj.downvotes,
            'score': obj.upvotes - obj.downvotes,
            'upvote_percentage': (obj.upvotes / max(obj.upvotes + obj.downvotes, 1)) * 100
        }


class PostVoteSerializer(serializers.ModelSerializer):
    """
    Serializer for PostVote model.
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = PostVote
        fields = ['id', 'post', 'user', 'vote_type', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class DirectMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for DirectMessage model.
    """
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    recipient_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DirectMessage
        fields = [
            'id', 'sender', 'recipient', 'recipient_id',
            'subject', 'content', 'status', 'priority',
            'parent_message', 'thread_id',
            'sent_at', 'delivered_at', 'read_at',
            'sender_archived', 'recipient_archived'
        ]
        read_only_fields = [
            'id', 'sender', 'status', 'thread_id',
            'sent_at', 'delivered_at', 'read_at',
            'sender_archived', 'recipient_archived'
        ]
    
    def create(self, validated_data):
        """Create message and set thread_id if it's a reply."""
        recipient_id = validated_data.pop('recipient_id')
        recipient = User.objects.get(id=recipient_id)
        validated_data['recipient'] = recipient
        
        message = super().create(validated_data)
        
        # Set thread_id for conversation threading
        if message.parent_message:
            message.thread_id = message.parent_message.thread_id or message.parent_message.id
        else:
            message.thread_id = message.id
        
        message.save()
        return message


class AnnouncementSerializer(serializers.ModelSerializer):
    """
    Serializer for Announcement model.
    """
    author = UserBasicSerializer(read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    target_users = UserBasicSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'announcement_type', 'priority',
            'course', 'course_title', 'target_users', 'target_roles',
            'author', 'is_published', 'publish_at', 'expires_at',
            'send_email', 'send_push', 'pin_to_top',
            'view_count', 'click_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'view_count', 'click_count', 'is_active',
            'created_at', 'updated_at'
        ]


class AnnouncementViewSerializer(serializers.ModelSerializer):
    """
    Serializer for AnnouncementView model.
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = AnnouncementView
        fields = ['id', 'announcement', 'user', 'viewed_at', 'ip_address', 'user_agent']
        read_only_fields = ['id', 'user', 'viewed_at']


class ChatRoomMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatRoomMembership model.
    """
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ChatRoomMembership
        fields = ['user', 'role', 'joined_at', 'last_read_at']
        read_only_fields = ['joined_at', 'last_read_at']


class ChatRoomSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatRoom model.
    """
    members = UserBasicSerializer(many=True, read_only=True)
    moderators = UserBasicSerializer(many=True, read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    membership_details = ChatRoomMembershipSerializer(
        source='chatroomMembership_set', many=True, read_only=True
    )
    member_count = serializers.SerializerMethodField()
    recent_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'description', 'room_type',
            'course', 'course_title', 'members', 'moderators',
            'membership_details', 'member_count',
            'is_active', 'is_private', 'max_members',
            'auto_moderate', 'sentiment_tracking',
            'recent_message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'members', 'moderators', 'member_count', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get current member count."""
        return obj.members.count()
    
    def get_recent_message(self, obj):
        """Get most recent message in chat room."""
        recent_message = obj.messages.filter(is_deleted=False).order_by('-sent_at').first()
        if recent_message:
            return {
                'id': str(recent_message.id),
                'sender': recent_message.sender.username,
                'content': recent_message.content[:50] + '...' if len(recent_message.content) > 50 else recent_message.content,
                'sent_at': recent_message.sent_at.isoformat()
            }
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model.
    """
    sender = UserBasicSerializer(read_only=True)
    parent_message = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'chat_room', 'sender', 'content', 'message_type',
            'parent_message', 'replies', 'sentiment_score', 'toxicity_score',
            'is_edited', 'is_deleted', 'sent_at', 'edited_at'
        ]
        read_only_fields = [
            'id', 'sender', 'sentiment_score', 'toxicity_score',
            'is_edited', 'sent_at', 'edited_at'
        ]
    
    def get_parent_message(self, obj):
        """Get parent message if this is a reply."""
        if obj.parent_message:
            return {
                'id': str(obj.parent_message.id),
                'sender': obj.parent_message.sender.username,
                'content': obj.parent_message.content[:30] + '...' if len(obj.parent_message.content) > 30 else obj.parent_message.content,
                'sent_at': obj.parent_message.sent_at.isoformat()
            }
        return None
    
    def get_replies(self, obj):
        """Get reply count for this message."""
        return obj.replies.filter(is_deleted=False).count()


class AIFeedbackSerializer(serializers.Serializer):
    """
    Serializer for AI feedback responses.
    """
    feedback_type = serializers.CharField(max_length=50)
    content = serializers.CharField()
    confidence_score = serializers.FloatField(min_value=0.0, max_value=1.0)
    suggestions = serializers.ListField(child=serializers.CharField(), required=False)
    metadata = serializers.JSONField(required=False)
    generated_at = serializers.DateTimeField(read_only=True)


class SentimentAnalysisSerializer(serializers.Serializer):
    """
    Serializer for sentiment analysis results.
    """
    sentiment_score = serializers.FloatField(min_value=-1.0, max_value=1.0)
    subjectivity = serializers.FloatField(min_value=0.0, max_value=1.0)
    emotional_indicators = serializers.ListField(child=serializers.CharField())
    key_topics = serializers.ListField(child=serializers.CharField())
    primary_tone = serializers.CharField(max_length=20)
    communication_style = serializers.CharField(max_length=20)
    analyzed_at = serializers.DateTimeField(read_only=True)


class EmailProcessingSerializer(serializers.Serializer):
    """
    Serializer for email processing requests.
    """
    email_content = serializers.CharField()
    sender_email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    
    # Response fields
    category = serializers.CharField(max_length=50, read_only=True)
    priority_level = serializers.CharField(max_length=20, read_only=True)
    sentiment_analysis = SentimentAnalysisSerializer(read_only=True)
    response_suggestions = serializers.ListField(
        child=serializers.JSONField(), read_only=True
    )
    action_items = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
    processed_at = serializers.DateTimeField(read_only=True)


class AutoModerationSerializer(serializers.Serializer):
    """
    Serializer for auto-moderation results.
    """
    content = serializers.CharField(write_only=True)
    
    # Response fields
    toxicity_score = serializers.FloatField(min_value=0.0, max_value=1.0, read_only=True)
    requires_moderation = serializers.BooleanField(read_only=True)
    flags = serializers.ListField(child=serializers.CharField(), read_only=True)
    confidence = serializers.FloatField(min_value=0.0, max_value=1.0, read_only=True)
    reason = serializers.CharField(allow_null=True, read_only=True)
    moderated_at = serializers.DateTimeField(read_only=True)


class ConversationHealthSerializer(serializers.Serializer):
    """
    Serializer for conversation health analysis.
    """
    conversation_id = serializers.CharField()
    time_window_hours = serializers.IntegerField(min_value=1, max_value=168, default=24)
    
    # Response fields
    total_messages = serializers.IntegerField(read_only=True)
    flagged_messages = serializers.IntegerField(read_only=True)
    average_toxicity = serializers.FloatField(read_only=True)
    conversation_health = serializers.CharField(read_only=True)
    recommendations = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
    flagged_content = serializers.ListField(
        child=serializers.JSONField(), read_only=True
    )
    analyzed_at = serializers.DateTimeField(read_only=True)
