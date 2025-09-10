"""
URL configuration for users app authentication and user management.
"""

from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # JWT Authentication
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    
    # User Registration and Verification
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),
    path('auth/verify-email/<str:uidb64>/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('auth/resend-verification/', views.resend_verification_email, name='resend_verification'),
    
    # Password Management
    path('auth/password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('auth/reset-password/<str:uidb64>/<str:token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # User Profile and Preferences
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('preferences/', views.UserPreferencesView.as_view(), name='user_preferences'),
    path('me/', views.user_me, name='user_me'),
    
    # Social Authentication
    path('auth/social/<str:backend>/', views.SocialAuthView.as_view(), name='social_auth'),
    
    # OAuth2 Provider URLs (for third-party applications)
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    
    # Social Auth URLs (for third-party login providers)
    path('auth/', include('social_django.urls', namespace='social')),
]
