"""
Authentication serializers for API endpoints.

This module provides serializers for user authentication, registration,
and security-related operations.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserMFA

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user information.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'is_verified': self.user.is_verified,
        }
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def validate_password(self, value):
        """Validate password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate_email(self, value):
        """Check if email is already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create new user."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords do not match.")
        return attrs
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if email exists."""
        if not User.objects.filter(email=value).exists():
            # Don't reveal if email exists or not for security
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        return attrs
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class MFASetupSerializer(serializers.ModelSerializer):
    """
    Serializer for MFA setup.
    """
    class Meta:
        model = UserMFA
        fields = ['recovery_email', 'recovery_phone']


class MFAVerifySerializer(serializers.Serializer):
    """
    Serializer for MFA token verification.
    """
    token = serializers.CharField(required=True, min_length=6, max_length=8)
    
    def validate_token(self, value):
        """Validate token format."""
        # Remove spaces and convert to uppercase for backup codes
        value = value.replace(' ', '').replace('-', '').upper()
        
        # Check if it's a 6-digit TOTP token or 8-character backup code
        if not (value.isdigit() and len(value) == 6) and not (len(value) == 8):
            raise serializers.ValidationError("Invalid token format.")
        
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    mfa_enabled = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'is_verified', 'last_login', 'date_joined',
            'mfa_enabled'
        ]
        read_only_fields = ['id', 'username', 'last_login', 'date_joined']
    
    def get_mfa_enabled(self, obj):
        """Get MFA status."""
        return hasattr(obj, 'mfa') and obj.mfa.is_enabled


class SecurityEventSerializer(serializers.Serializer):
    """
    Serializer for security events.
    """
    event_type = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    risk_level = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    occurred_at = serializers.DateTimeField(read_only=True)


class LoginAttemptSerializer(serializers.Serializer):
    """
    Serializer for login attempts.
    """
    ip_address = serializers.IPAddressField(read_only=True)
    status = serializers.CharField(read_only=True)
    attempted_at = serializers.DateTimeField(read_only=True)
    user_agent = serializers.CharField(read_only=True)


class UserSecuritySerializer(serializers.Serializer):
    """
    Serializer for user security information.
    """
    mfa_enabled = serializers.BooleanField(read_only=True)
    recent_logins = LoginAttemptSerializer(many=True, read_only=True)
    security_events = SecurityEventSerializer(many=True, read_only=True)


class SocialAuthSerializer(serializers.Serializer):
    """
    Serializer for social authentication.
    """
    provider = serializers.ChoiceField(choices=['google', 'microsoft', 'github'])
    access_token = serializers.CharField(required=True)
    
    def validate_provider(self, value):
        """Validate social auth provider."""
        allowed_providers = ['google', 'microsoft', 'github']
        if value not in allowed_providers:
            raise serializers.ValidationError(f"Provider must be one of: {', '.join(allowed_providers)}")
        return value


class APITokenSerializer(serializers.Serializer):
    """
    Serializer for API token management.
    """
    name = serializers.CharField(required=True, max_length=100)
    scopes = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        default=list
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_name(self, value):
        """Validate token name."""
        user = self.context['request'].user
        if user.api_tokens.filter(name=value, is_active=True).exists():
            raise serializers.ValidationError("A token with this name already exists.")
        return value


class DeviceInfoSerializer(serializers.Serializer):
    """
    Serializer for device information.
    """
    device_type = serializers.CharField(read_only=True)
    browser = serializers.CharField(read_only=True)
    os = serializers.CharField(read_only=True)
    ip_address = serializers.IPAddressField(read_only=True)
    location = serializers.CharField(read_only=True)
    last_used = serializers.DateTimeField(read_only=True)


class AccountSecuritySettingsSerializer(serializers.Serializer):
    """
    Serializer for account security settings.
    """
    email_notifications = serializers.BooleanField(default=True)
    login_alerts = serializers.BooleanField(default=True)
    suspicious_activity_alerts = serializers.BooleanField(default=True)
    password_change_alerts = serializers.BooleanField(default=True)
    session_management = serializers.BooleanField(default=True)
    
    def update(self, instance, validated_data):
        """Update user security settings."""
        # This would update user preferences stored in a separate model
        # For now, we'll just return the validated data
        return validated_data


class LoginSessionSerializer(serializers.Serializer):
    """
    Serializer for active login sessions.
    """
    session_id = serializers.CharField(read_only=True)
    device_info = DeviceInfoSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)
    is_current = serializers.BooleanField(read_only=True)


class AccountLockoutSerializer(serializers.Serializer):
    """
    Serializer for account lockout information.
    """
    is_locked = serializers.BooleanField(read_only=True)
    locked_until = serializers.DateTimeField(read_only=True, allow_null=True)
    failed_attempts = serializers.IntegerField(read_only=True)
    lockout_reason = serializers.CharField(read_only=True)


class PasswordPolicySerializer(serializers.Serializer):
    """
    Serializer for password policy information.
    """
    min_length = serializers.IntegerField(read_only=True)
    require_uppercase = serializers.BooleanField(read_only=True)
    require_lowercase = serializers.BooleanField(read_only=True)
    require_digits = serializers.BooleanField(read_only=True)
    require_symbols = serializers.BooleanField(read_only=True)
    history_length = serializers.IntegerField(read_only=True)
    expiry_days = serializers.IntegerField(read_only=True)


class BackupCodeSerializer(serializers.Serializer):
    """
    Serializer for MFA backup codes.
    """
    codes = serializers.ListField(
        child=serializers.CharField(max_length=9),
        read_only=True
    )
    generated_at = serializers.DateTimeField(read_only=True)
    used_count = serializers.IntegerField(read_only=True)


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate email format and availability."""
        user = self.context['request'].user
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class PhoneVerificationSerializer(serializers.Serializer):
    """
    Serializer for phone number verification.
    """
    phone_number = serializers.RegexField(
        regex=r'^\+?1?\d{9,15}$',
        required=True,
        error_message="Enter a valid phone number."
    )
    verification_code = serializers.CharField(
        required=False,
        min_length=6,
        max_length=6
    )


class TrustedDeviceSerializer(serializers.Serializer):
    """
    Serializer for trusted device management.
    """
    device_id = serializers.CharField(read_only=True)
    device_name = serializers.CharField(max_length=100)
    device_type = serializers.CharField(read_only=True)
    is_trusted = serializers.BooleanField(default=False)
    added_at = serializers.DateTimeField(read_only=True)
    last_used = serializers.DateTimeField(read_only=True)
