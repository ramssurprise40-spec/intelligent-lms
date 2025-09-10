"""
URL patterns for authentication endpoints.
"""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout, name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User registration and profile
    path('register/', views.register_user, name='register'),
    path('profile/', views.user_profile, name='profile'),
    
    # Password management
    path('password/change/', views.change_password, name='change_password'),
    path('password/reset/', views.password_reset_request, name='password_reset'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    
    # Multi-factor authentication
    path('mfa/setup/', views.mfa_setup, name='mfa_setup'),
    path('mfa/enable/', views.mfa_enable, name='mfa_enable'),
    path('mfa/disable/', views.mfa_disable, name='mfa_disable'),
    path('mfa/verify/', views.mfa_verify, name='mfa_verify'),
    
    # Security endpoints
    path('security/events/', views.security_events, name='security_events'),
    
    # Social authentication
    path('social/', include('social_django.urls', namespace='social')),
    
    # OAuth2
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
