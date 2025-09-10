"""
Authentication middleware for enhanced security features.

This module provides middleware classes for authentication monitoring,
session management, and security event logging.
"""

import time
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from .models import LoginAttempt, AccountLockout, SecurityEvent, UserSession
from .utils import get_client_ip, get_user_agent_info, log_security_event


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware for security monitoring and event logging.
    """
    
    def process_request(self, request):
        """Process incoming request for security monitoring."""
        # Store request start time for performance monitoring
        request._security_start_time = time.time()
        
        # Get client IP and user agent
        request._client_ip = get_client_ip(request)
        request._user_agent_info = get_user_agent_info(request)
        
        # Check for suspicious patterns
        self._check_suspicious_patterns(request)
        
        return None
    
    def process_response(self, request, response):
        """Process response for security logging."""
        # Log security events if needed
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check for permission denied responses
            if response.status_code == 403:
                log_security_event(
                    user=request.user,
                    event_type='permission_denied',
                    description=f'Access denied to {request.path}',
                    ip_address=getattr(request, '_client_ip', None),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    risk_level='medium'
                )
        
        return response
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious request patterns."""
        ip = getattr(request, '_client_ip', None)
        if not ip:
            return
        
        # Check request rate from IP
        cache_key = f"suspicious_ip_{ip}"
        request_count = cache.get(cache_key, 0)
        
        # If too many requests from same IP
        if request_count > 100:  # Configurable threshold
            log_security_event(
                event_type='suspicious_activity',
                description=f'High request rate from IP {ip}',
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                risk_level='high'
            )
        
        # Increment counter
        cache.set(cache_key, request_count + 1, 300)  # 5 minute window


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for enhanced session security.
    """
    
    def process_request(self, request):
        """Check session security."""
        if not request.user.is_authenticated:
            return None
        
        # Check session timeout
        if self._is_session_expired(request):
            logout(request)
            return JsonResponse({
                'error': 'Session expired',
                'message': 'Your session has expired. Please log in again.'
            }, status=401)
        
        # Update last activity
        request.session['last_activity'] = timezone.now().timestamp()
        
        # Check for session hijacking
        if self._detect_session_hijacking(request):
            logout(request)
            log_security_event(
                user=request.user,
                event_type='suspicious_activity',
                description='Possible session hijacking detected',
                ip_address=getattr(request, '_client_ip', None),
                risk_level='critical'
            )
            return JsonResponse({
                'error': 'Security violation',
                'message': 'Session security violation detected.'
            }, status=403)
        
        return None
    
    def _is_session_expired(self, request):
        """Check if session has expired."""
        last_activity = request.session.get('last_activity')
        if not last_activity:
            return False
        
        timeout = getattr(settings, 'SESSION_COOKIE_AGE', 3600)
        return (timezone.now().timestamp() - last_activity) > timeout
    
    def _detect_session_hijacking(self, request):
        """Detect possible session hijacking."""
        # Check if IP address changed
        session_ip = request.session.get('client_ip')
        current_ip = getattr(request, '_client_ip', None)
        
        if session_ip and session_ip != current_ip:
            # IP changed - possible hijacking
            return True
        
        # Store current IP in session
        request.session['client_ip'] = current_ip
        
        # Check if user agent changed significantly
        session_ua = request.session.get('user_agent')
        current_ua = request.META.get('HTTP_USER_AGENT', '')
        
        if session_ua and session_ua != current_ua:
            # User agent changed - possible hijacking
            return True
        
        # Store current user agent
        request.session['user_agent'] = current_ua
        
        return False


class AccountLockoutMiddleware(MiddlewareMixin):
    """
    Middleware to check for account lockouts.
    """
    
    def process_request(self, request):
        """Check if user account is locked out."""
        if request.path_info.startswith('/auth/login/'):
            return None  # Don't check on login page
        
        if not request.user.is_authenticated:
            return None
        
        # Check for active lockouts
        active_lockout = AccountLockout.objects.filter(
            user=request.user,
            is_active=True,
            locked_until__gt=timezone.now()
        ).first()
        
        if active_lockout:
            logout(request)
            return JsonResponse({
                'error': 'Account locked',
                'message': f'Account is locked until {active_lockout.locked_until}',
                'locked_until': active_lockout.locked_until.isoformat()
            }, status=403)
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware for request rate limiting.
    """
    
    def process_request(self, request):
        """Apply rate limiting."""
        # Skip rate limiting for certain paths
        skip_paths = ['/static/', '/media/', '/health/']
        if any(request.path_info.startswith(path) for path in skip_paths):
            return None
        
        ip = getattr(request, '_client_ip', None)
        if not ip:
            return None
        
        # Different rate limits for different endpoints
        rate_limits = {
            '/auth/login/': (5, 300),  # 5 requests per 5 minutes
            '/auth/register/': (3, 300),  # 3 requests per 5 minutes
            '/auth/password-reset/': (3, 900),  # 3 requests per 15 minutes
            'default': (100, 60)  # 100 requests per minute for other endpoints
        }
        
        # Get rate limit for current path
        limit, window = rate_limits.get('default')
        for path, (path_limit, path_window) in rate_limits.items():
            if request.path_info.startswith(path):
                limit, window = path_limit, path_window
                break
        
        # Check rate limit
        cache_key = f"rate_limit_{ip}_{request.path_info}"
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            log_security_event(
                event_type='suspicious_activity',
                description=f'Rate limit exceeded for {request.path_info}',
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                risk_level='medium'
            )
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, status=429)
        
        # Increment counter
        cache.set(cache_key, current_count + 1, window)
        
        return None


class MFAMiddleware(MiddlewareMixin):
    """
    Middleware to enforce multi-factor authentication.
    """
    
    def process_request(self, request):
        """Check MFA requirements."""
        if not request.user.is_authenticated:
            return None
        
        # Skip MFA check for certain paths
        skip_paths = [
            '/auth/mfa/',
            '/auth/logout/',
            '/static/',
            '/media/'
        ]
        if any(request.path_info.startswith(path) for path in skip_paths):
            return None
        
        # Check if user has MFA enabled
        if hasattr(request.user, 'mfa') and request.user.mfa.is_enabled:
            # Check if MFA is verified for this session
            if not request.session.get('mfa_verified', False):
                return JsonResponse({
                    'error': 'MFA required',
                    'message': 'Multi-factor authentication required',
                    'mfa_required': True
                }, status=401)
        
        return None


class UserSessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user sessions for security monitoring.
    """
    
    def process_request(self, request):
        """Track user session information."""
        if not request.user.is_authenticated:
            return None
        
        session_key = request.session.session_key
        if not session_key:
            return None
        
        # Update or create session tracking
        user_agent_info = getattr(request, '_user_agent_info', {})
        
        user_session, created = UserSession.objects.get_or_create(
            user=request.user,
            session_key=session_key,
            defaults={
                'ip_address': getattr(request, '_client_ip', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'device_type': user_agent_info.get('device_type', ''),
                'browser': user_agent_info.get('browser', ''),
                'os': user_agent_info.get('os', ''),
                'expires_at': timezone.now() + timezone.timedelta(
                    seconds=getattr(settings, 'SESSION_COOKIE_AGE', 3600)
                )
            }
        )
        
        if not created:
            # Update last activity
            user_session.last_activity = timezone.now()
            user_session.save(update_fields=['last_activity'])
        
        return None


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Middleware to add Content Security Policy headers.
    """
    
    def process_response(self, request, response):
        """Add CSP headers to response."""
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )
        
        response['Content-Security-Policy'] = csp_policy
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
