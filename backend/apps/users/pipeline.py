"""
Social authentication pipeline for custom user creation.

This module provides pipeline functions for social authentication
to handle user creation and profile updates.
"""

from django.contrib.auth import get_user_model
from authentication.utils import log_security_event, get_client_ip

User = get_user_model()


def create_user_profile(strategy, details, backend, user=None, *args, **kwargs):
    """
    Create or update user profile after social authentication.
    """
    if user:
        # User already exists, update profile
        updated = False
        
        # Update basic information if not already set
        if not user.first_name and details.get('first_name'):
            user.first_name = details['first_name']
            updated = True
            
        if not user.last_name and details.get('last_name'):
            user.last_name = details['last_name']
            updated = True
            
        # Set default role if not set
        if not user.role:
            user.role = 'student'  # Default role for social auth users
            updated = True
        
        # Mark as verified since they authenticated via social provider
        if not user.is_verified:
            user.is_verified = True
            updated = True
        
        if updated:
            user.save()
            
            # Log security event
            request = strategy.request
            log_security_event(
                user=user,
                event_type='profile_updated',
                description=f'Profile updated via {backend.name} authentication',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                risk_level='low'
            )
    
    return {'user': user}


def associate_by_email(strategy, details, backend, user=None, *args, **kwargs):
    """
    Associate social account with existing user by email.
    """
    if user:
        return None
    
    email = details.get('email')
    if not email:
        return None
    
    try:
        # Try to find existing user with this email
        existing_user = User.objects.get(email=email)
        
        # Log security event
        request = strategy.request
        log_security_event(
            user=existing_user,
            event_type='social_account_linked',
            description=f'Social account linked via {backend.name}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='medium'
        )
        
        return {'user': existing_user}
        
    except User.DoesNotExist:
        return None


def prevent_duplicate_emails(strategy, details, backend, user=None, *args, **kwargs):
    """
    Prevent creation of users with duplicate emails.
    """
    if user:
        return None
    
    email = details.get('email')
    if not email:
        return None
    
    # Check if user already exists with this email
    if User.objects.filter(email=email).exists():
        # Redirect to login page with message
        return strategy.redirect('/auth/login/?message=email_exists')
    
    return None


def require_email(strategy, details, backend, user=None, *args, **kwargs):
    """
    Require email for social authentication.
    """
    if user:
        return None
    
    email = details.get('email')
    if not email:
        # Redirect to complete profile page
        return strategy.redirect('/auth/complete-profile/')
    
    return None


def set_user_role(strategy, details, backend, user=None, *args, **kwargs):
    """
    Set appropriate user role based on social auth provider.
    """
    if not user:
        return None
    
    # Set role based on provider or domain
    email = details.get('email', '')
    domain = email.split('@')[1] if '@' in email else ''
    
    # Default role
    if not user.role:
        # You can customize this logic based on your requirements
        if domain in ['university.edu', 'school.edu']:  # Educational domains
            user.role = 'instructor'
        else:
            user.role = 'student'
        user.save()
    
    return None


def log_social_login(strategy, details, backend, user=None, *args, **kwargs):
    """
    Log social authentication attempt.
    """
    if user:
        request = strategy.request
        log_security_event(
            user=user,
            event_type='login_success',
            description=f'Social login via {backend.name}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='low',
            metadata={
                'provider': backend.name,
                'social_auth': True
            }
        )
    
    return None
