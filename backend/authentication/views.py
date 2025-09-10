"""
Authentication API views.

This module provides API endpoints for user authentication, registration,
password management, and multi-factor authentication.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from .models import UserMFA, LoginAttempt, SecurityEvent, AccountLockout
from .utils import (
    get_client_ip, get_user_agent_info, track_login_attempt, 
    check_account_lockout, is_account_locked, log_security_event,
    validate_password_strength, send_security_notification,
    is_suspicious_login, create_mfa_qr_code
)

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def login_user(request):
    """
    User login endpoint with enhanced security.
    """
    username = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Check rate limiting
    cache_key = f"login_attempts_{ip_address}"
    attempts = cache.get(cache_key, 0)
    if attempts >= 10:  # 10 attempts per hour
        return Response({
            'error': 'Too many login attempts. Please try again later.'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # Try to authenticate
    user = authenticate(request, username=username, password=password)
    
    if user:
        # Check if account is locked
        if is_account_locked(user):
            return Response({
                'error': 'Account is locked. Please contact support.'
            }, status=status.HTTP_423_LOCKED)
        
        # Check if login is suspicious
        if is_suspicious_login(user, ip_address, user_agent):
            log_security_event(
                user=user,
                event_type='suspicious_activity',
                description='Suspicious login detected',
                ip_address=ip_address,
                user_agent=user_agent,
                risk_level='medium'
            )
            
            send_security_notification(user, 'suspicious_activity', {
                'ip_address': ip_address,
                'location': 'Unknown'
            })
        
        # Track successful login
        track_login_attempt(username, ip_address, user_agent, 'success', user=user)
        
        # Log security event
        log_security_event(
            user=user,
            event_type='login_success',
            description='User logged in successfully',
            ip_address=ip_address,
            user_agent=user_agent,
            risk_level='low'
        )
        
        # Clear login attempts cache
        cache.delete(cache_key)
        
        # Check if MFA is enabled
        if hasattr(user, 'mfa') and user.mfa.is_enabled:
            # Generate temporary token for MFA
            temp_token = default_token_generator.make_token(user)
            cache.set(f"mfa_temp_token_{user.id}", temp_token, 300)  # 5 minutes
            
            return Response({
                'mfa_required': True,
                'message': 'Multi-factor authentication required',
                'temp_token': temp_token,
                'user_id': user.id
            })
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    else:
        # Failed login
        track_login_attempt(
            username, ip_address, user_agent, 'failed', 
            failure_reason='Invalid credentials'
        )
        
        # Increment attempts counter
        cache.set(cache_key, attempts + 1, 3600)  # 1 hour
        
        # Check for account lockout
        try:
            user_obj = User.objects.get(username=username)
            if check_account_lockout(user_obj, ip_address):
                return Response({
                    'error': 'Account has been locked due to multiple failed login attempts.'
                }, status=status.HTTP_423_LOCKED)
        except User.DoesNotExist:
            pass
        
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_verify(request):
    """
    Verify MFA token and complete login.
    """
    temp_token = request.data.get('temp_token')
    mfa_token = request.data.get('mfa_token')
    user_id = request.data.get('user_id')
    
    if not all([temp_token, mfa_token, user_id]):
        return Response({
            'error': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id)
        
        # Verify temp token
        cached_token = cache.get(f"mfa_temp_token_{user.id}")
        if not cached_token or cached_token != temp_token:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify MFA token
        mfa = user.mfa
        if mfa.verify_totp(mfa_token) or mfa.use_backup_code(mfa_token):
            # Clear temp token
            cache.delete(f"mfa_temp_token_{user.id}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Mark MFA as verified in session
            request.session['mfa_verified'] = True
            
            # Log successful MFA
            log_security_event(
                user=user,
                event_type='login_success',
                description='MFA verification successful',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                risk_level='low'
            )
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role
                }
            })
        else:
            track_login_attempt(
                user.username, get_client_ip(request),
                request.META.get('HTTP_USER_AGENT', ''),
                'mfa_failed', failure_reason='Invalid MFA token'
            )
            
            return Response({
                'error': 'Invalid MFA token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (User.DoesNotExist, UserMFA.DoesNotExist):
        return Response({
            'error': 'Invalid request'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout endpoint.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        # Clear MFA verification
        request.session.pop('mfa_verified', None)
        
        # Log security event
        log_security_event(
            user=request.user,
            event_type='logout',
            description='User logged out',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='low'
        )
        
        return Response({
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        return Response({
            'error': 'Logout failed'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST')
def register_user(request):
    """
    User registration endpoint.
    """
    from .serializers import UserRegistrationSerializer
    
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        # Validate password strength
        password = serializer.validated_data['password']
        password_errors = validate_password_strength(password)
        
        if password_errors:
            return Response({
                'password_errors': password_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        user = serializer.save()
        
        # Log security event
        log_security_event(
            user=user,
            event_type='user_registered',
            description='New user registered',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='low'
        )
        
        return Response({
            'message': 'User registered successfully',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password endpoint.
    """
    from .serializers import ChangePasswordSerializer
    
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        # Verify old password
        if not user.check_password(old_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password strength
        password_errors = validate_password_strength(new_password, user)
        if password_errors:
            return Response({
                'password_errors': password_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Change password
        user.set_password(new_password)
        user.save()
        
        # Log security event
        log_security_event(
            user=user,
            event_type='password_change',
            description='User changed password',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='medium'
        )
        
        return Response({
            'message': 'Password changed successfully'
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/h', method='POST')
def password_reset_request(request):
    """
    Request password reset endpoint.
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Store token in cache for security
        cache.set(f"password_reset_{user.id}", token, 3600)  # 1 hour
        
        # Log security event
        log_security_event(
            user=user,
            event_type='password_reset',
            description='Password reset requested',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='medium'
        )
        
    except User.DoesNotExist:
        # Don't reveal if email exists or not
        pass
    
    return Response({
        'message': 'If the email exists, a password reset link has been sent.'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    Confirm password reset endpoint.
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([uid, token, new_password]):
        return Response({
            'error': 'All fields are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        # Verify token
        cached_token = cache.get(f"password_reset_{user.id}")
        if not cached_token or cached_token != token:
            return Response({
                'error': 'Invalid or expired token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        password_errors = validate_password_strength(new_password, user)
        if password_errors:
            return Response({
                'password_errors': password_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Clear reset token
        cache.delete(f"password_reset_{user.id}")
        
        # Log security event
        log_security_event(
            user=user,
            event_type='password_reset',
            description='Password was reset',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='high'
        )
        
        return Response({
            'message': 'Password reset successfully'
        })
        
    except (User.DoesNotExist, ValueError):
        return Response({
            'error': 'Invalid reset link'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mfa_setup(request):
    """
    Set up multi-factor authentication.
    """
    user = request.user
    
    # Get or create MFA settings
    mfa, created = UserMFA.objects.get_or_create(user=user)
    
    if mfa.is_enabled:
        return Response({
            'error': 'MFA is already enabled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate QR code
    qr_data = create_mfa_qr_code(user)
    
    if not qr_data:
        return Response({
            'error': 'Unable to generate QR code'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'qr_code': qr_data['qr_code'],
        'secret_key': qr_data['secret_key'],
        'backup_codes': qr_data['backup_codes']
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mfa_enable(request):
    """
    Enable multi-factor authentication.
    """
    user = request.user
    token = request.data.get('token')
    
    if not token:
        return Response({
            'error': 'TOTP token is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        mfa = user.mfa
        
        # Verify token
        if mfa.verify_totp(token):
            mfa.is_enabled = True
            mfa.save()
            
            # Log security event
            log_security_event(
                user=user,
                event_type='mfa_enabled',
                description='Multi-factor authentication enabled',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                risk_level='low'
            )
            
            return Response({
                'message': 'MFA enabled successfully'
            })
        else:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except UserMFA.DoesNotExist:
        return Response({
            'error': 'MFA not set up'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mfa_disable(request):
    """
    Disable multi-factor authentication.
    """
    user = request.user
    password = request.data.get('password')
    
    if not password or not user.check_password(password):
        return Response({
            'error': 'Current password is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        mfa = user.mfa
        mfa.is_enabled = False
        mfa.secret_key = ''
        mfa.backup_codes = []
        mfa.save()
        
        # Log security event
        log_security_event(
            user=user,
            event_type='mfa_disabled',
            description='Multi-factor authentication disabled',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            risk_level='medium'
        )
        
        return Response({
            'message': 'MFA disabled successfully'
        })
        
    except UserMFA.DoesNotExist:
        return Response({
            'error': 'MFA not enabled'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile.
    """
    user = request.user
    
    # Get MFA status
    mfa_enabled = hasattr(user, 'mfa') and user.mfa.is_enabled
    
    # Get recent login attempts
    recent_logins = LoginAttempt.objects.filter(
        user=user,
        status='success'
    ).order_by('-attempted_at')[:5]
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_verified': user.is_verified,
            'last_login': user.last_login,
            'date_joined': user.date_joined,
        },
        'security': {
            'mfa_enabled': mfa_enabled,
            'recent_logins': [
                {
                    'ip_address': login.ip_address,
                    'attempted_at': login.attempted_at,
                    'user_agent': login.user_agent[:100] + '...' if len(login.user_agent) > 100 else login.user_agent
                }
                for login in recent_logins
            ]
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def security_events(request):
    """
    Get user's security events.
    """
    events = SecurityEvent.objects.filter(
        user=request.user
    ).order_by('-occurred_at')[:50]
    
    return Response({
        'events': [
            {
                'event_type': event.get_event_type_display(),
                'description': event.description,
                'risk_level': event.get_risk_level_display(),
                'ip_address': event.ip_address,
                'occurred_at': event.occurred_at,
            }
            for event in events
        ]
    })
