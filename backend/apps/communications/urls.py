"""
URL configuration for communications app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'forums', views.ForumViewSet, basename='forum')
router.register(r'forum-posts', views.ForumPostViewSet, basename='forumpost')
router.register(r'direct-messages', views.DirectMessageViewSet, basename='directmessage')
router.register(r'chat-rooms', views.ChatRoomViewSet, basename='chatroom')

app_name = 'communications'

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
    
    # Additional API endpoints
    path('api/email/process/', views.process_email_feedback, name='process_email'),
    path('api/responses/generate/', views.generate_automated_response, name='generate_response'),
    
    # WebSocket endpoints would be defined in routing.py for Django Channels
    # path('ws/chat/', include('communications.routing')),
]
