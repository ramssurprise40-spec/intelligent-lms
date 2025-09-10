"""
Utility functions for authentication and security.

This module provides helper functions for IP detection, user agent parsing,
security logging, and password validation.
"""

import re
import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache
import user_agents


User = get_user_model()


def get_client_ip(request):
    """
    Get the real IP address of the client.
    """
    # Check for forwarded headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip


def get_user_agent_info(request):
    """
    Parse user agent string to extract device and browser information.
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        user_agent = user_agents.parse(user_agent_string)
        
        return {
            'device_type': 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop',
            'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
            'os': f"{user_agent.os.family} {user_agent.os.version_string}",
            'is_bot': user_agent.is_bot,
        }
    except Exception:
        return {
            'device_type': 'unknown',
            'browser': 'unknown',
            'os': 'unknown',
            'is_bot': False,
        }


def log_security_event(user=None, event_type=None, description=None, 
                      ip_address=None, user_agent=None, risk_level='low', 
                      metadata=None):
    """
    Log a security event.
    """
    from .models import SecurityEvent
    
    SecurityEvent.objects.create(
        user=user,
        event_type=event_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent or '',
        risk_level=risk_level,
        metadata=metadata or {}
    )


def track_login_attempt(username, ip_address, user_agent, status, 
                       failure_reason=None, user=None):
    """
    Track login attempts for security monitoring.
    """
    from .models import LoginAttempt
    
    LoginAttempt.objects.create(
        user=user,
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        failure_reason=failure_reason or ''
    )


def check_account_lockout(user, ip_address):
    """
    Check if account should be locked out due to failed login attempts.
    """
    from .models import LoginAttempt, AccountLockout
    
    # Get recent failed attempts
    recent_attempts = LoginAttempt.objects.filter(
        user=user,
        status='failed',
        attempted_at__gte=timezone.now() - timedelta(
            seconds=getattr(settings, 'LOGIN_ATTEMPT_TIMEOUT', 300)
        )
    ).count()
    
    max_attempts = getattr(settings, 'MAX_LOGIN_ATTEMPTS', 5)
    
    if recent_attempts >= max_attempts:
        # Lock the account
        lockout_time = getattr(settings, 'ACCOUNT_LOCKOUT_TIME', 1800)  # 30 minutes
        locked_until = timezone.now() + timedelta(seconds=lockout_time)
        
        AccountLockout.objects.create(
            user=user,
            ip_address=ip_address,
            failed_attempts=recent_attempts,
            locked_until=locked_until
        )
        
        log_security_event(
            user=user,
            event_type='account_locked',
            description=f'Account locked due to {recent_attempts} failed login attempts',
            ip_address=ip_address,
            risk_level='high'
        )
        
        return True
    
    return False


def is_account_locked(user):
    """
    Check if user account is currently locked.
    """
    from .models import AccountLockout
    
    active_lockout = AccountLockout.objects.filter(
        user=user,
        is_active=True,
        locked_until__gt=timezone.now()
    ).first()
    
    return active_lockout is not None


def validate_password_strength(password, user=None):
    """
    Validate password strength based on configured policies.
    """
    errors = []
    
    # Check minimum length
    min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
    if len(password) < min_length:
        errors.append(f'Password must be at least {min_length} characters long.')
    
    # Check for uppercase letters
    if getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True):
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter.')
    
    # Check for lowercase letters
    if getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True):
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter.')
    
    # Check for digits
    if getattr(settings, 'PASSWORD_REQUIRE_DIGITS', True):
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one digit.')
    
    # Check for symbols
    if getattr(settings, 'PASSWORD_REQUIRE_SYMBOLS', True):
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character.')
    
    # Check against user information (if provided)
    if user:
        user_info = [
            user.username.lower(),
            user.first_name.lower(),
            user.last_name.lower(),
            user.email.lower().split('@')[0]
        ]
        
        for info in user_info:
            if info and len(info) > 2 and info in password.lower():
                errors.append('Password must not contain personal information.')
                break
    
    # Check against common passwords
    common_passwords = [
        'password', '123456', 'password123', 'admin', 'qwerty',
        'letmein', 'welcome', 'monkey', '1234567890'
    ]
    
    if password.lower() in common_passwords:
        errors.append('Password is too common. Please choose a more secure password.')
    
    return errors


def check_password_history(user, password):
    """
    Check if password was used recently.
    """
    from .models import PasswordHistory
    
    # Hash the password to compare with history
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Check against recent passwords
    history_length = getattr(settings, 'PASSWORD_HISTORY_LENGTH', 5)
    recent_passwords = PasswordHistory.objects.filter(
        user=user
    ).order_by('-created_at')[:history_length]
    
    for history_entry in recent_passwords:
        if history_entry.password_hash == password_hash:
            return True  # Password was used before
    
    return False


def save_password_history(user, password):
    """
    Save password to user's password history.
    """
    from .models import PasswordHistory
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    PasswordHistory.objects.create(
        user=user,
        password_hash=password_hash
    )
    
    # Clean up old password history
    history_length = getattr(settings, 'PASSWORD_HISTORY_LENGTH', 5)
    old_entries = PasswordHistory.objects.filter(
        user=user
    ).order_by('-created_at')[history_length:]
    
    for entry in old_entries:
        entry.delete()


def generate_secure_token(length=32):
    """
    Generate a cryptographically secure random token.
    """
    return secrets.token_urlsafe(length)


def generate_backup_codes(count=10):
    """
    Generate backup codes for MFA.
    """
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        # Format as XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    
    return codes


def send_security_notification(user, event_type, context=None):
    """
    Send security notification email to user.
    """
    if not user.email:
        return False
    
    context = context or {}
    context.update({
        'user': user,
        'site_name': 'Intelligent LMS',
        'timestamp': timezone.now(),
    })
    
    email_templates = {
        'login_success': {
            'subject': 'New login to your account',
            'template': 'authentication/emails/login_success.html'
        },
        'password_changed': {
            'subject': 'Your password was changed',
            'template': 'authentication/emails/password_changed.html'
        },
        'account_locked': {
            'subject': 'Your account has been locked',
            'template': 'authentication/emails/account_locked.html'
        },
        'mfa_enabled': {
            'subject': 'Two-factor authentication enabled',
            'template': 'authentication/emails/mfa_enabled.html'
        },
        'suspicious_activity': {
            'subject': 'Suspicious activity detected',
            'template': 'authentication/emails/suspicious_activity.html'
        }
    }
    
    if event_type not in email_templates:
        return False
    
    template_info = email_templates[event_type]
    
    try:
        # Render email content
        html_content = render_to_string(template_info['template'], context)
        
        # Send email
        send_mail(
            subject=template_info['subject'],
            message='',  # Plain text version can be added
            html_message=html_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        # Log the error but don't raise it
        log_security_event(
            user=user,
            event_type='email_failed',
            description=f'Failed to send security notification: {str(e)}',
            risk_level='low'
        )
        return False


def get_geolocation_info(ip_address):
    """
    Get geolocation information for an IP address.
    This is a stub - you would integrate with a geolocation service.
    """
    # For now, return empty data
    # In production, you might use services like:
    # - MaxMind GeoIP
    # - ipstack.com
    # - ipapi.co
    
    return {
        'country': '',
        'city': '',
        'region': '',
        'timezone': ''
    }


def clean_expired_sessions():
    """
    Clean up expired user sessions.
    """
    from .models import UserSession
    
    expired_sessions = UserSession.objects.filter(
        expires_at__lt=timezone.now()
    )
    
    count = expired_sessions.count()
    expired_sessions.update(is_active=False)
    
    return count


def clean_old_login_attempts():
    """
    Clean up old login attempts.
    """
    from .models import LoginAttempt
    
    # Keep login attempts for 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    old_attempts = LoginAttempt.objects.filter(
        attempted_at__lt=cutoff_date
    )
    
    count = old_attempts.count()
    old_attempts.delete()
    
    return count


def clean_old_security_events():
    """
    Clean up old security events.
    """
    from .models import SecurityEvent
    
    # Keep security events for 90 days
    cutoff_date = timezone.now() - timedelta(days=90)
    old_events = SecurityEvent.objects.filter(
        occurred_at__lt=cutoff_date,
        risk_level__in=['low', 'medium']  # Keep high and critical events longer
    )
    
    count = old_events.count()
    old_events.delete()
    
    return count


def is_suspicious_login(user, ip_address, user_agent):
    """
    Check if login attempt appears suspicious.
    """
    from .models import LoginAttempt
    
    # Check for recent successful logins from different locations
    recent_logins = LoginAttempt.objects.filter(
        user=user,
        status='success',
        attempted_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-attempted_at')[:10]
    
    if recent_logins:
        # Check if IP address is significantly different
        recent_ips = {login.ip_address for login in recent_logins}
        if ip_address not in recent_ips and len(recent_ips) > 0:
            # New IP address - might be suspicious
            return True
        
        # Check if user agent is significantly different
        recent_agents = {login.user_agent for login in recent_logins}
        if user_agent not in recent_agents and len(recent_agents) > 0:
            # Check for major differences in user agent
            current_info = get_user_agent_info({'META': {'HTTP_USER_AGENT': user_agent}})
            for agent in recent_agents:
                agent_info = get_user_agent_info({'META': {'HTTP_USER_AGENT': agent}})
                if (current_info['device_type'] != agent_info['device_type'] or
                    current_info['os'].split()[0] != agent_info['os'].split()[0]):
                    return True
    
    return False


def create_mfa_qr_code(user):
    """
    Create QR code for MFA setup.
    """
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        # Get or create MFA settings
        mfa, created = user.mfa.get_or_create()
        
        if not mfa.secret_key:
            mfa.generate_secret_key()
        
        # Generate QR code
        qr_code_url = mfa.get_qr_code_url()
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_code_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for easy display
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'qr_code': f'data:image/png;base64,{img_str}',
            'secret_key': mfa.secret_key,
            'backup_codes': mfa.generate_backup_codes()
        }
        
    except ImportError:
        # qrcode not available
        return None


def verify_recaptcha(recaptcha_response):
    """
    Verify reCAPTCHA response.
    This is a stub - implement based on your reCAPTCHA configuration.
    """
    # For now, return True
    # In production, you would verify with Google's reCAPTCHA API
    return True
