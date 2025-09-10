"""
Authentication models for enhanced security features.

This module provides models for multi-factor authentication, login tracking,
password history, and other security-related functionality.
"""

import secrets
import pyotp
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

User = get_user_model()


class UserMFA(models.Model):
    """
    Multi-Factor Authentication settings for users.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='mfa')
    
    # TOTP (Time-based One-Time Password) settings
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)
    
    # Recovery options
    recovery_email = models.EmailField(blank=True)
    recovery_phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')]
    )
    
    # Settings
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user_mfa'
        verbose_name = 'User MFA'
        verbose_name_plural = 'User MFA Settings'
    
    def __str__(self):
        return f"{self.user.username} - MFA {'Enabled' if self.is_enabled else 'Disabled'}"
    
    def generate_secret_key(self):
        """Generate a new secret key for TOTP."""
        self.secret_key = pyotp.random_base32()
        self.save()
        return self.secret_key
    
    def get_qr_code_url(self):
        """Get QR code URL for TOTP setup."""
        if not self.secret_key:
            self.generate_secret_key()
        
        totp_uri = pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=self.user.email,
            issuer_name="Intelligent LMS"
        )
        return totp_uri
    
    def verify_totp(self, token):
        """Verify TOTP token."""
        if not self.secret_key:
            return False
        
        totp = pyotp.TOTP(self.secret_key)
        if totp.verify(token):
            self.last_used = timezone.now()
            self.save()
            return True
        return False
    
    def generate_backup_codes(self):
        """Generate backup codes for account recovery."""
        codes = []
        for _ in range(10):  # Generate 10 backup codes
            code = secrets.token_hex(4).upper()  # 8-character hex code
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes
    
    def use_backup_code(self, code):
        """Use a backup code for authentication."""
        if code.upper() in self.backup_codes:
            self.backup_codes.remove(code.upper())
            self.save()
            return True
        return False


class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring.
    """
    STATUS_CHOICES = [
        ('success', 'Successful'),
        ('failed', 'Failed'),
        ('blocked', 'Blocked'),
        ('mfa_required', 'MFA Required'),
        ('mfa_failed', 'MFA Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='login_attempts')
    username = models.CharField(max_length=150)  # Store attempted username even if user doesn't exist
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Attempt details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    # Location data (optional)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_login_attempt'
        indexes = [
            models.Index(fields=['user', '-attempted_at']),
            models.Index(fields=['ip_address', '-attempted_at']),
            models.Index(fields=['status', '-attempted_at']),
        ]
        ordering = ['-attempted_at']
    
    def __str__(self):
        return f"{self.username} - {self.status} - {self.attempted_at}"


class AccountLockout(models.Model):
    """
    Track account lockouts due to failed login attempts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lockouts')
    ip_address = models.GenericIPAddressField()
    
    # Lockout details
    failed_attempts = models.PositiveIntegerField()
    locked_at = models.DateTimeField(auto_now_add=True)
    locked_until = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    unlocked_at = models.DateTimeField(null=True, blank=True)
    unlocked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='unlocked_accounts'
    )
    
    class Meta:
        db_table = 'auth_account_lockout'
        indexes = [
            models.Index(fields=['user', '-locked_at']),
            models.Index(fields=['is_active', 'locked_until']),
        ]
        ordering = ['-locked_at']
    
    def __str__(self):
        return f"{self.user.username} locked until {self.locked_until}"
    
    @property
    def is_locked(self):
        """Check if the account is currently locked."""
        return self.is_active and timezone.now() < self.locked_until
    
    def unlock(self, unlocked_by=None):
        """Manually unlock the account."""
        self.is_active = False
        self.unlocked_at = timezone.now()
        self.unlocked_by = unlocked_by
        self.save()


class SecurityEvent(models.Model):
    """
    Log security-related events for monitoring and auditing.
    """
    EVENT_TYPES = [
        ('login_success', 'Successful Login'),
        ('login_failed', 'Failed Login'),
        ('logout', 'Logout'),
        ('password_change', 'Password Changed'),
        ('password_reset', 'Password Reset'),
        ('mfa_enabled', 'MFA Enabled'),
        ('mfa_disabled', 'MFA Disabled'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('permission_denied', 'Permission Denied'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='security_events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low')
    
    # Event details
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    occurred_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_security_event'
        indexes = [
            models.Index(fields=['user', '-occurred_at']),
            models.Index(fields=['event_type', '-occurred_at']),
            models.Index(fields=['risk_level', '-occurred_at']),
        ]
        ordering = ['-occurred_at']
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} - {self.occurred_at}"


class UserSession(models.Model):
    """
    Track user sessions for security and analytics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    
    # Session details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Location data (optional)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Session tracking
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    # Flags
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user_session'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active', 'expires_at']),
        ]
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.created_at}"
    
    @property
    def is_session_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at
    
    def expire_session(self):
        """Manually expire the session."""
        self.is_active = False
        self.is_expired = True
        self.save()
