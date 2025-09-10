"""
Authentication views for the Intelligent LMS system.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.shortcuts import get_object_or_404
from oauth2_provider.decorators import protected_resource
from social_django.utils import psa

from .models import User, UserActivity
from .serializers import (
    CustomTokenObtainPairSerializer, UserRegistrationSerializer, UserSerializer,
    PasswordResetSerializer, PasswordResetConfirmSerializer, PasswordChangeSerializer,
    EmailVerificationSerializer, UserPreferencesSerializer, SocialAuthSerializer
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with enhanced login capabilities.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log the login activity
            user_data = response.data.get('user', {})
            if user_data.get('id'):
                try:
                    user = User.objects.get(id=user_data['id'])
                    UserActivity.objects.create(
                        user=user,
                        activity_type='login',
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'login_method': 'jwt',
                            'success': True
                        }
                    )
                    # Update user profile login streak
                    user.profile.update_login_streak()
                except User.DoesNotExist:
                    pass
        
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegistrationView(generics.CreateAPIView):
    """
    User registration view with email verification.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send email verification
        self.send_verification_email(user, request)

        # Create response data
        response_data = {
            'user': UserSerializer(user).data,
            'message': 'Registration successful. Please check your email to verify your account.',
            'email_sent': True
        }

        return Response(response_data, status=status.HTTP_201_CREATED)

    def send_verification_email(self, user, request):
        """Send email verification to the user."""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verification_url = f"{request.scheme}://{request.get_host()}/auth/verify-email/{uid}/{token}/"
        
        subject = 'Verify your email - Intelligent LMS'
        message = render_to_string('emails/email_verification.txt', {
            'user': user,
            'verification_url': verification_url,
            'domain': request.get_host(),
        })
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        except Exception as e:
            # Log the error but don't fail registration
            print(f"Failed to send verification email: {e}")


class EmailVerificationView(APIView):
    """
    Email verification view.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid verification link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            
            return Response(
                {'message': 'Email verified successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Invalid or expired verification link'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetView(APIView):
    """
    Password reset request view.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate reset token
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Send reset email
            reset_url = f"{request.scheme}://{request.get_host()}/auth/reset-password/{uid}/{token}/"
            
            subject = 'Password Reset - Intelligent LMS'
            message = render_to_string('emails/password_reset.txt', {
                'user': user,
                'reset_url': reset_url,
                'domain': request.get_host(),
            })
            
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                return Response(
                    {'message': 'Password reset email sent'},
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {'error': 'Failed to send reset email'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation view.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if default_token_generator.check_token(user, token):
            serializer = PasswordResetConfirmSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['password'])
                user.save()
                
                return Response(
                    {'message': 'Password reset successfully'},
                    status=status.HTTP_200_OK
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'error': 'Invalid or expired reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordChangeView(APIView):
    """
    Change password for authenticated users.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Password changed successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View for retrieving and updating user profile.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserPreferencesView(generics.RetrieveUpdateAPIView):
    """
    View for user preferences and settings.
    """
    serializer_class = UserPreferencesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    """
    Logout view with JWT token blacklisting.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Log the logout activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={'logout_method': 'jwt'}
            )

            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Failed to logout'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SocialAuthView(APIView):
    """
    Social authentication view for third-party login.
    """
    permission_classes = [permissions.AllowAny]

    @psa('social:complete')
    def post(self, request, backend):
        """
        Handle social authentication with various providers.
        """
        serializer = SocialAuthSerializer(data=request.data)
        if serializer.is_valid():
            provider = serializer.validated_data['provider']
            access_token = serializer.validated_data['access_token']

            try:
                # Use python-social-auth to authenticate
                user = request.backend.do_auth(access_token)
                
                if user and user.is_active:
                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # Log social login activity
                    UserActivity.objects.create(
                        user=user,
                        activity_type='login',
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        metadata={
                            'login_method': 'social_auth',
                            'provider': provider,
                            'success': True
                        }
                    )

                    return Response({
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                        'user': UserSerializer(user).data,
                    }, status=status.HTTP_200_OK)
                else:
                    return Response(
                        {'error': 'Authentication failed'},
                        status=status.HTTP_401_UNAUTHORIZED
                    )
                    
            except Exception as e:
                return Response(
                    {'error': f'Social authentication failed: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_me(request):
    """
    Get current user information.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_email(request):
    """
    Resend email verification.
    """
    email = request.data.get('email')
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
        if user.is_verified:
            return Response(
                {'message': 'Email is already verified'},
                status=status.HTTP_200_OK
            )

        # Send verification email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        verification_url = f"{request.scheme}://{request.get_host()}/auth/verify-email/{uid}/{token}/"
        
        subject = 'Verify your email - Intelligent LMS'
        message = render_to_string('emails/email_verification.txt', {
            'user': user,
            'verification_url': verification_url,
            'domain': request.get_host(),
        })
        
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        
        return Response(
            {'message': 'Verification email sent'},
            status=status.HTTP_200_OK
        )

    except User.DoesNotExist:
        return Response(
            {'error': 'User with this email does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to send verification email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
