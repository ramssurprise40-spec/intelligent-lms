"""
Views for intelligent communication and feedback system.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import json
import logging

from .models import (
    Forum, ForumTopic, ForumPost, DirectMessage, 
    Announcement, ChatRoom, ChatMessage, PostVote
)
from .services import (
    AIFeedbackService, SentimentAnalysisService, 
    EmailProcessingService, AutoModerationService
)
from .serializers import (
    ForumSerializer, ForumTopicSerializer, ForumPostSerializer,
    DirectMessageSerializer, AnnouncementSerializer,
    ChatRoomSerializer, ChatMessageSerializer
)

logger = logging.getLogger(__name__)


class ForumViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing course forums with AI-enhanced features.
    """
    serializer_class = ForumSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Forum.objects.filter(
            course__enrollments__user=self.request.user,
            is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def sentiment_analysis(self, request, pk=None):
        """
        Get sentiment analysis for forum posts.
        """
        forum = self.get_object()
        sentiment_service = SentimentAnalysisService()
        
        # Analyze recent posts in the forum
        recent_posts = ForumPost.objects.filter(
            topic__forum=forum,
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).order_by('-created_at')[:100]
        
        sentiment_data = sentiment_service.analyze_forum_sentiment(recent_posts)
        
        return Response({
            'forum_id': str(forum.id),
            'sentiment_overview': sentiment_data,
            'analysis_date': timezone.now().isoformat()
        })
    
    @action(detail=True, methods=['post'])
    def generate_ai_summary(self, request, pk=None):
        """
        Generate AI summary of forum discussions.
        """
        forum = self.get_object()
        ai_service = AIFeedbackService()
        
        summary_data = ai_service.generate_forum_summary(forum.id)
        
        return Response({
            'forum_id': str(forum.id),
            'ai_summary': summary_data,
            'generated_at': timezone.now().isoformat()
        })


class ForumPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing forum posts with AI moderation.
    """
    serializer_class = ForumPostSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ForumPost.objects.filter(
            topic__forum__course__enrollments__user=self.request.user
        ).exclude(status='deleted')
    
    def perform_create(self, serializer):
        """
        Create post with AI moderation and sentiment analysis.
        """
        post = serializer.save(author=self.request.user)
        
        # Run AI analysis on the new post
        moderation_service = AutoModerationService()
        sentiment_service = SentimentAnalysisService()
        
        # Analyze content
        moderation_result = moderation_service.moderate_content(post.content)
        sentiment_result = sentiment_service.analyze_text(post.content)
        
        # Update post with AI analysis
        post.sentiment_score = sentiment_result.get('sentiment_score')
        post.toxicity_score = moderation_result.get('toxicity_score')
        post.key_topics = sentiment_result.get('key_topics', [])
        
        # Auto-moderate if necessary
        if moderation_result.get('requires_moderation'):
            post.status = 'moderated'
            post.moderation_reason = moderation_result.get('reason')
        
        post.save()
        
        # Notify moderators if flagged
        if post.status == 'moderated':
            self._notify_moderators(post, moderation_result)
    
    def _notify_moderators(self, post, moderation_result):
        """
        Notify forum moderators about flagged content.
        """
        # Implementation would send notifications to moderators
        logger.info(f"Post {post.id} flagged for moderation: {moderation_result.get('reason')}")
    
    @action(detail=True, methods=['post'])
    def generate_ai_response(self, request, pk=None):
        """
        Generate AI-suggested response to a forum post.
        """
        post = self.get_object()
        ai_service = AIFeedbackService()
        
        # Generate contextual response suggestions
        response_suggestions = ai_service.generate_response_suggestions(
            post.content, 
            post.topic.title,
            request.user
        )
        
        return Response({
            'post_id': str(post.id),
            'response_suggestions': response_suggestions,
            'generated_at': timezone.now().isoformat()
        })


class DirectMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for direct messaging with AI assistance.
    """
    serializer_class = DirectMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return DirectMessage.objects.filter(
            models.Q(sender=self.request.user) | models.Q(recipient=self.request.user)
        ).exclude(
            models.Q(sender_deleted=True, sender=self.request.user) |
            models.Q(recipient_deleted=True, recipient=self.request.user)
        )
    
    def perform_create(self, serializer):
        """
        Send message with AI assistance for tone and content.
        """
        message = serializer.save(sender=self.request.user)
        
        # Analyze message sentiment and suggest improvements
        ai_service = AIFeedbackService()
        sentiment_service = SentimentAnalysisService()
        
        # Analyze message tone
        tone_analysis = sentiment_service.analyze_communication_tone(message.content)
        
        # Generate response if this is a reply or needs assistance
        if message.parent_message:
            context = {
                'original_message': message.parent_message.content,
                'relationship': self._get_user_relationship(message.sender, message.recipient),
                'message_history': self._get_message_history(message.sender, message.recipient)
            }
            ai_suggestions = ai_service.suggest_message_improvements(message.content, context)
        
        logger.info(f"Message sent with AI analysis: {tone_analysis}")
    
    def _get_user_relationship(self, sender, recipient):
        """Determine relationship between users for context."""
        # Implementation would determine if users are instructor/student, peers, etc.
        return 'peer'  # Placeholder
    
    def _get_message_history(self, sender, recipient):
        """Get recent message history for context."""
        return DirectMessage.objects.filter(
            models.Q(sender=sender, recipient=recipient) |
            models.Q(sender=recipient, recipient=sender)
        ).order_by('-sent_at')[:5]
    
    @action(detail=False, methods=['post'])
    def ai_compose_assistance(self, request):
        """
        Get AI assistance for composing messages.
        """
        ai_service = AIFeedbackService()
        
        draft_content = request.data.get('draft_content', '')
        message_type = request.data.get('message_type', 'general')
        recipient_id = request.data.get('recipient_id')
        
        # Generate composition suggestions
        suggestions = ai_service.provide_composition_assistance(
            draft_content, message_type, recipient_id
        )
        
        return Response({
            'suggestions': suggestions,
            'generated_at': timezone.now().isoformat()
        })


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for real-time chat rooms with AI moderation.
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatRoom.objects.filter(
            members=self.request.user,
            is_active=True
        )
    
    @action(detail=True, methods=['get'])
    def real_time_sentiment(self, request, pk=None):
        """
        Get real-time sentiment analysis of chat room.
        """
        chat_room = self.get_object()
        sentiment_service = SentimentAnalysisService()
        
        # Analyze recent messages
        recent_messages = ChatMessage.objects.filter(
            chat_room=chat_room,
            sent_at__gte=timezone.now() - timezone.timedelta(hours=1),
            is_deleted=False
        ).order_by('-sent_at')[:50]
        
        sentiment_data = sentiment_service.analyze_chat_sentiment(recent_messages)
        
        return Response({
            'chat_room_id': str(chat_room.id),
            'real_time_sentiment': sentiment_data,
            'analysis_timestamp': timezone.now().isoformat()
        })
    
    @action(detail=True, methods=['post'])
    def moderate_conversation(self, request, pk=None):
        """
        Run AI moderation on chat conversation.
        """
        chat_room = self.get_object()
        moderation_service = AutoModerationService()
        
        time_window = request.data.get('time_window_hours', 24)
        messages = ChatMessage.objects.filter(
            chat_room=chat_room,
            sent_at__gte=timezone.now() - timezone.timedelta(hours=time_window)
        )
        
        moderation_results = moderation_service.moderate_chat_conversation(messages)
        
        return Response({
            'chat_room_id': str(chat_room.id),
            'moderation_results': moderation_results,
            'analyzed_at': timezone.now().isoformat()
        })


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def process_email_feedback(request):
    """
    Process incoming email and generate intelligent feedback.
    """
    try:
        data = json.loads(request.body)
        email_content = data.get('email_content')
        sender_email = data.get('sender_email')
        subject = data.get('subject')
        
        # Process email with AI
        email_service = EmailProcessingService()
        processing_result = email_service.process_incoming_email(
            email_content, sender_email, subject
        )
        
        return JsonResponse({
            'status': 'success',
            'processing_result': processing_result,
            'processed_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Email processing error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required
def generate_automated_response(request):
    """
    Generate automated response using AI.
    """
    try:
        data = json.loads(request.body)
        original_message = data.get('original_message')
        response_type = data.get('response_type', 'helpful')
        context = data.get('context', {})
        
        ai_service = AIFeedbackService()
        
        # Generate appropriate response
        automated_response = ai_service.generate_automated_response(
            original_message, response_type, context, request.user
        )
        
        return JsonResponse({
            'status': 'success',
            'automated_response': automated_response,
            'generated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Automated response generation error: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
