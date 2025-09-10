"""
Authentication and user serializers for the Intelligent LMS system.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user information.
    """
    username_field = User.USERNAME_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = serializers.EmailField(required=False)
        self.fields['username'] = serializers.CharField(required=False)

    def validate(self, attrs):
        # Allow login with either email or username
        email = attrs.get('email')
        username = attrs.get('username')
        password = attrs.get('password')

        if not (email or username):
            raise serializers.ValidationError('Either email or username is required.')

        # Try to authenticate with email first, then username
        user = None
        if email:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(
                    request=self.context.get('request'),
                    username=user_obj.username,
                    password=password
                )
            except User.DoesNotExist:
                pass
        
        if not user and username:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )

        if not user:
            raise serializers.ValidationError('Invalid credentials.')

        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')

        # Update the validated data for the parent class
        attrs[self.username_field] = user.username
        
        data = super().validate(attrs)
        
        # Add custom claims
        data['user'] = UserSerializer(user).data
        data['user_role'] = user.role
        data['is_verified'] = user.is_verified
        
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_id'] = str(user.id)
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified'] = user.is_verified
        token['full_name'] = user.full_name
        
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    User registration serializer with password validation.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    terms_accepted = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 
            'password_confirm', 'role', 'student_id', 'major', 'terms_accepted'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the terms and conditions.")
        
        # Remove password_confirm and terms_accepted from attrs
        attrs.pop('password_confirm')
        attrs.pop('terms_accepted')
        
        return attrs

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate_student_id(self, value):
        if value and User.objects.filter(student_id=value).exists():
            raise serializers.ValidationError("A user with this student ID already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    """
    full_name = serializers.ReadOnlyField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'avatar', 'bio', 'student_id', 'major', 'graduation_year',
            'is_verified', 'created_at', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'last_login']

    def get_profile(self, obj):
        try:
            return UserProfileSerializer(obj.profile).data
        except:
            return None


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    class Meta:
        model = UserProfile
        fields = [
            'total_study_hours', 'courses_completed', 'average_score', 'skill_level',
            'login_streak', 'max_login_streak', 'forum_posts', 'forum_reputation',
            'badges_earned', 'learning_path_recommendation', 'strengths', 
            'improvement_areas', 'predicted_success_rate'
        ]
        read_only_fields = ['__all__']


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    password_confirm = serializers.CharField()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password when user is authenticated.
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField()

    def validate_token(self, value):
        # Token validation logic would go here
        # This would typically involve checking a verification token
        return value


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for user preferences and settings.
    """
    class Meta:
        model = User
        fields = [
            'learning_style', 'preferred_difficulty', 'study_time_preference',
            'email_notifications', 'push_notifications', 'marketing_emails',
            'profile_visibility', 'language', 'timezone'
        ]


class SocialAuthSerializer(serializers.Serializer):
    """
    Serializer for social authentication data.
    """
    provider = serializers.CharField()
    access_token = serializers.CharField()
    user_data = serializers.DictField(read_only=True)
