"""
Security and compliance middleware for the Intelligent LMS.
Handles audit logging, data encryption, privacy controls, and GDPR compliance.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from .models import AuditLog, SecurityEvent, DataProcessingLog, GDPRRequest
from .services import EncryptionService, GDPRService

User = get_user_model()
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to all responses.
    """
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' wss: https:",
            "media-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        
        security_headers = {
            'Content-Security-Policy': '; '.join(csp_directives),
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        }
        
        # Add headers if not already present
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
        
        return response


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive audit logging.
    Logs all API requests, responses, and user actions for compliance.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.encryption_service = EncryptionService()
    
    def process_request(self, request: HttpRequest) -> None:
        """Process request and prepare audit data."""
        # Start timing
        request._audit_start_time = time.time()
        request._audit_id = str(uuid.uuid4())
        
        # Store request data for logging
        request._audit_data = {
            'audit_id': request._audit_id,
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self._get_client_ip(request),
            'timestamp': timezone.now(),
            'session_key': request.session.session_key if hasattr(request, 'session') else None,
        }
        
        # Add user info if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            request._audit_data.update({
                'user_id': request.user.id,
                'username': request.user.username,
                'user_type': self._get_user_type(request.user),
            })
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log the completed request/response cycle."""
        if not hasattr(request, '_audit_data'):
            return response
        
        try:
            # Calculate response time
            response_time = (time.time() - request._audit_start_time) * 1000  # ms
            
            # Prepare audit log data
            audit_data = request._audit_data.copy()
            audit_data.update({
                'status_code': response.status_code,
                'response_time_ms': round(response_time, 2),
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
            })
            
            # Add request body for POST/PUT/PATCH (with PII filtering)
            if request.method in ['POST', 'PUT', 'PATCH']:
                audit_data['request_data'] = self._sanitize_request_data(request)
            
            # Add query parameters
            if request.GET:
                audit_data['query_params'] = dict(request.GET)
            
            # Determine if this is a sensitive operation
            is_sensitive = self._is_sensitive_operation(request)
            
            # Create audit log entry
            self._create_audit_log(audit_data, is_sensitive)
            
            # Log security events if applicable
            self._check_security_events(request, response, audit_data)
            
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _get_user_type(self, user) -> str:
        """Determine user type for audit purposes."""
        if user.is_superuser:
            return 'admin'
        elif user.is_staff:
            return 'staff'
        elif hasattr(user, 'instructor_profile'):
            return 'instructor'
        else:
            return 'student'
    
    def _sanitize_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Sanitize request data to remove PII and sensitive information."""
        try:
            if hasattr(request, 'body') and request.body:
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = dict(request.POST)
            
            # Fields that should be completely redacted
            sensitive_fields = {
                'password', 'password_confirmation', 'token', 'secret',
                'api_key', 'credit_card', 'ssn', 'social_security'
            }
            
            # Fields that should be partially redacted (show first/last chars)
            pii_fields = {
                'email', 'phone', 'address', 'birth_date'
            }
            
            return self._recursive_sanitize(data, sensitive_fields, pii_fields)
            
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {'_sanitized': 'Unable to parse request data'}
    
    def _recursive_sanitize(self, data: Any, sensitive_fields: set, pii_fields: set) -> Any:
        """Recursively sanitize data structure."""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(field in key_lower for field in sensitive_fields):
                    sanitized[key] = '[REDACTED]'
                elif any(field in key_lower for field in pii_fields):
                    sanitized[key] = self._partial_redact(str(value))
                else:
                    sanitized[key] = self._recursive_sanitize(value, sensitive_fields, pii_fields)
            return sanitized
        elif isinstance(data, list):
            return [self._recursive_sanitize(item, sensitive_fields, pii_fields) for item in data]
        else:
            return data
    
    def _partial_redact(self, value: str) -> str:
        """Partially redact a string value (show first and last 2 chars)."""
        if len(value) <= 4:
            return '*' * len(value)
        return value[:2] + '*' * (len(value) - 4) + value[-2:]
    
    def _is_sensitive_operation(self, request: HttpRequest) -> bool:
        """Determine if this is a sensitive operation requiring enhanced logging."""
        sensitive_paths = [
            '/admin/', '/api/users/', '/api/auth/', '/api/payment/',
            '/api/grades/', '/api/analytics/'
        ]
        
        sensitive_methods = ['DELETE', 'PUT', 'PATCH']
        
        return (
            any(path in request.path for path in sensitive_paths) or
            request.method in sensitive_methods or
            (hasattr(request, 'user') and request.user.is_staff)
        )
    
    def _create_audit_log(self, audit_data: Dict[str, Any], is_sensitive: bool) -> None:
        """Create audit log entry in database."""
        try:
            # Encrypt sensitive data if required
            if is_sensitive and hasattr(settings, 'AUDIT_ENCRYPTION_ENABLED') and settings.AUDIT_ENCRYPTION_ENABLED:
                encrypted_data = self.encryption_service.encrypt_data(audit_data)
                audit_data = {'encrypted': True, 'data': encrypted_data}
            
            AuditLog.objects.create(
                audit_id=audit_data['audit_id'],
                user_id=audit_data.get('user_id'),
                action=f"{audit_data['method']} {audit_data['path']}",
                resource_type='api_request',
                resource_id=audit_data['path'],
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
                request_data=audit_data,
                status_code=audit_data['status_code'],
                is_sensitive=is_sensitive,
                timestamp=audit_data['timestamp']
            )
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    def _check_security_events(self, request: HttpRequest, response: HttpResponse, audit_data: Dict) -> None:
        """Check for potential security events and log them."""
        # Failed authentication attempts
        if response.status_code == 401 and 'auth' in request.path:
            self._log_security_event('FAILED_AUTH', request, audit_data)
        
        # Multiple failed attempts from same IP
        if response.status_code == 401:
            self._check_brute_force_attempt(request, audit_data)
        
        # Admin access
        if request.path.startswith('/admin/') and hasattr(request, 'user') and request.user.is_authenticated:
            self._log_security_event('ADMIN_ACCESS', request, audit_data)
        
        # Suspicious user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(bot in user_agent for bot in ['bot', 'crawler', 'spider']) and not request.path.startswith('/api/'):
            self._log_security_event('SUSPICIOUS_USER_AGENT', request, audit_data)
    
    def _log_security_event(self, event_type: str, request: HttpRequest, audit_data: Dict) -> None:
        """Log a security event."""
        try:
            SecurityEvent.objects.create(
                event_type=event_type,
                user_id=audit_data.get('user_id'),
                ip_address=audit_data['ip_address'],
                user_agent=audit_data['user_agent'],
                path=audit_data['path'],
                details=audit_data,
                severity='medium',
                timestamp=audit_data['timestamp']
            )
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _check_brute_force_attempt(self, request: HttpRequest, audit_data: Dict) -> None:
        """Check for brute force attempts."""
        ip_address = audit_data['ip_address']
        cache_key = f"failed_auth:{ip_address}"
        
        # Get current count
        failed_count = cache.get(cache_key, 0)
        failed_count += 1
        
        # Store with 1 hour expiry
        cache.set(cache_key, failed_count, 3600)
        
        # Log if threshold exceeded
        if failed_count >= 5:
            self._log_security_event('BRUTE_FORCE_ATTEMPT', request, audit_data)


class GDPRComplianceMiddleware(MiddlewareMixin):
    """
    Middleware to handle GDPR compliance requirements.
    Tracks data processing activities and manages consent.
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.gdpr_service = GDPRService()
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Process GDPR requirements for incoming requests."""
        # Handle GDPR data subject requests
        if request.path.startswith('/api/gdpr/'):
            return self._handle_gdpr_request(request)
        
        # Track data processing for EU users
        if self._is_eu_user(request):
            self._track_data_processing(request)
        
        # Check consent requirements
        if self._requires_consent(request):
            consent_status = self._check_consent(request)
            if not consent_status:
                return self._consent_required_response()
        
        return None
    
    def _handle_gdpr_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Handle GDPR data subject requests."""
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        if request.method == 'GET' and 'export' in request.path:
            # Data export request
            data = self.gdpr_service.export_user_data(request.user.id)
            return JsonResponse({'data': data, 'format': 'json'})
        
        elif request.method == 'POST' and 'delete' in request.path:
            # Data deletion request
            self.gdpr_service.request_data_deletion(request.user.id)
            return JsonResponse({'message': 'Data deletion request submitted'})
        
        elif request.method == 'GET' and 'processing' in request.path:
            # Data processing activities
            activities = self.gdpr_service.get_processing_activities(request.user.id)
            return JsonResponse({'processing_activities': activities})
        
        return None
    
    def _is_eu_user(self, request: HttpRequest) -> bool:
        """Determine if user is from EU based on various indicators."""
        # Check GeoIP (would need actual GeoIP service)
        # For now, use simple heuristics
        
        # Check Accept-Language header for EU languages
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        eu_languages = ['de', 'fr', 'es', 'it', 'nl', 'pl', 'sv', 'da', 'fi']
        
        if any(lang in accept_language.lower() for lang in eu_languages):
            return True
        
        # Check timezone (if available)
        # This would be more accurate with proper GeoIP
        
        return False
    
    def _track_data_processing(self, request: HttpRequest) -> None:
        """Track data processing activities for GDPR compliance."""
        if not request.user.is_authenticated:
            return
        
        processing_purposes = self._determine_processing_purposes(request)
        
        for purpose in processing_purposes:
            DataProcessingLog.objects.create(
                user_id=request.user.id,
                processing_purpose=purpose,
                data_categories=self._determine_data_categories(request, purpose),
                legal_basis='legitimate_interest',  # Default, should be determined properly
                retention_period=self._get_retention_period(purpose),
                timestamp=timezone.now()
            )
    
    def _determine_processing_purposes(self, request: HttpRequest) -> list:
        """Determine data processing purposes based on request."""
        purposes = []
        
        if '/api/courses/' in request.path:
            purposes.append('educational_service')
        elif '/api/analytics/' in request.path:
            purposes.append('performance_analytics')
        elif '/api/communications/' in request.path:
            purposes.append('communication')
        elif '/api/social/' in request.path:
            purposes.append('social_features')
        else:
            purposes.append('service_provision')
        
        return purposes
    
    def _determine_data_categories(self, request: HttpRequest, purpose: str) -> list:
        """Determine what categories of data are being processed."""
        categories = ['basic_profile']  # Always include basic profile
        
        if purpose == 'educational_service':
            categories.extend(['academic_performance', 'learning_progress'])
        elif purpose == 'performance_analytics':
            categories.extend(['usage_data', 'performance_metrics'])
        elif purpose == 'communication':
            categories.extend(['communication_data', 'interaction_history'])
        
        return categories
    
    def _get_retention_period(self, purpose: str) -> int:
        """Get retention period in days for different purposes."""
        retention_periods = {
            'educational_service': 2555,  # 7 years
            'performance_analytics': 1095,  # 3 years
            'communication': 365,  # 1 year
            'social_features': 730,  # 2 years
            'service_provision': 365,  # 1 year
        }
        return retention_periods.get(purpose, 365)
    
    def _requires_consent(self, request: HttpRequest) -> bool:
        """Check if the request requires explicit consent."""
        # Analytics and tracking require consent
        consent_required_paths = [
            '/api/analytics/tracking/',
            '/api/recommendations/',
            '/api/ai/personalization/'
        ]
        
        return any(path in request.path for path in consent_required_paths)
    
    def _check_consent(self, request: HttpRequest) -> bool:
        """Check if user has given consent for data processing."""
        if not request.user.is_authenticated:
            return False
        
        # Check if user has active consent
        # This would be stored in user profile or separate consent model
        return getattr(request.user, 'gdpr_consent_given', False)
    
    def _consent_required_response(self) -> JsonResponse:
        """Return response indicating consent is required."""
        return JsonResponse({
            'error': 'Consent required',
            'message': 'This operation requires your explicit consent for data processing.',
            'consent_url': '/privacy/consent/',
            'required_consents': ['analytics', 'personalization']
        }, status=403)


class RateLimitingMiddleware(MiddlewareMixin):
    """
    Middleware for rate limiting to prevent abuse and ensure fair usage.
    """
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Apply rate limiting based on user and endpoint."""
        # Skip rate limiting for static files and health checks
        if request.path.startswith('/static/') or request.path == '/health/':
            return None
        
        # Determine rate limit key
        if request.user.is_authenticated:
            rate_key = f"rate_limit:user:{request.user.id}"
            limit = self._get_user_rate_limit(request.user)
        else:
            rate_key = f"rate_limit:ip:{self._get_client_ip(request)}"
            limit = self._get_anonymous_rate_limit()
        
        # Apply endpoint-specific limits
        endpoint_limit = self._get_endpoint_rate_limit(request.path)
        if endpoint_limit:
            endpoint_key = f"{rate_key}:endpoint:{request.path}"
            if not self._check_rate_limit(endpoint_key, endpoint_limit):
                return self._rate_limit_response(endpoint_limit)
        
        # Apply general rate limit
        if not self._check_rate_limit(rate_key, limit):
            return self._rate_limit_response(limit)
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    def _get_user_rate_limit(self, user) -> Dict[str, int]:
        """Get rate limit for authenticated user."""
        if user.is_staff:
            return {'requests': 1000, 'window': 3600}  # 1000 req/hour for staff
        else:
            return {'requests': 300, 'window': 3600}   # 300 req/hour for users
    
    def _get_anonymous_rate_limit(self) -> Dict[str, int]:
        """Get rate limit for anonymous users."""
        return {'requests': 100, 'window': 3600}  # 100 req/hour for anonymous
    
    def _get_endpoint_rate_limit(self, path: str) -> Optional[Dict[str, int]]:
        """Get endpoint-specific rate limits."""
        endpoint_limits = {
            '/api/auth/login/': {'requests': 5, 'window': 300},  # 5 login attempts per 5 min
            '/api/ai/': {'requests': 50, 'window': 3600},        # 50 AI requests per hour
            '/api/search/': {'requests': 100, 'window': 3600},   # 100 searches per hour
        }
        
        for endpoint, limit in endpoint_limits.items():
            if path.startswith(endpoint):
                return limit
        
        return None
    
    def _check_rate_limit(self, key: str, limit: Dict[str, int]) -> bool:
        """Check if request is within rate limit."""
        current = cache.get(key, 0)
        if current >= limit['requests']:
            return False
        
        cache.set(key, current + 1, limit['window'])
        return True
    
    def _rate_limit_response(self, limit: Dict[str, int]) -> JsonResponse:
        """Return rate limit exceeded response."""
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'message': f"Too many requests. Limit: {limit['requests']} requests per {limit['window']} seconds.",
            'retry_after': limit['window']
        }, status=429)
