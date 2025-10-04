"""
Authentication views for NeuroData platform.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils import timezone

from .models import User, UserProfile, APIKey
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    WalletAuthSerializer,
    WalletConnectSerializer,
    UserProfileSerializer,
    APIKeySerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserSerializer
)
from .utils import (
    generate_nonce,
    get_or_create_user_from_wallet,
    send_password_reset_email,
    send_welcome_email,
    verify_password_reset_token,
    log_authentication_event,
    check_rate_limit
)
from core.utils import create_response_data, get_client_ip
from core.permissions import IsOwnerOrReadOnly

import logging

logger = logging.getLogger(__name__)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view with additional user data.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Check rate limit
        client_ip = get_client_ip(request)
        is_allowed, remaining, reset_time = check_rate_limit(client_ip, limit=5, window=300)
        
        if not is_allowed:
            return Response(
                create_response_data(
                    success=False,
                    message="Too many login attempts. Please try again later.",
                    errors={'rate_limit': f'Reset time: {reset_time}'}
                ),
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                log_authentication_event(user, 'login', request)
            except User.DoesNotExist:
                pass
        
        return response


class UserRegistrationView(CreateAPIView):
    """
    User registration endpoint.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Check rate limit
        client_ip = get_client_ip(request)
        is_allowed, remaining, reset_time = check_rate_limit(
            f"register:{client_ip}", limit=3, window=3600  # 3 registrations per hour
        )
        
        if not is_allowed:
            return Response(
                create_response_data(
                    success=False,
                    message="Too many registration attempts. Please try again later.",
                    errors={'rate_limit': f'Reset time: {reset_time}'}
                ),
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Send welcome email
        send_welcome_email(user)
        
        # Log registration
        log_authentication_event(user, 'registration', request, {
            'registration_method': 'email',
            'wallet_address': user.profile.wallet_address
        })
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response(
            create_response_data(
                success=True,
                message="User registered successfully",
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }
            ),
            status=status.HTTP_201_CREATED
        )


class WalletConnectView(APIView):
    """
    Generate nonce for wallet connection.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = WalletConnectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        
        # Generate nonce
        nonce = generate_nonce(wallet_address)
        
        return Response(
            create_response_data(
                success=True,
                message="Nonce generated successfully",
                data={'nonce': nonce}
            )
        )


class WalletAuthView(APIView):
    """
    Authenticate user with wallet signature.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Check rate limit
        client_ip = get_client_ip(request)
        is_allowed, remaining, reset_time = check_rate_limit(
            f"wallet_auth:{client_ip}", limit=10, window=300
        )
        
        if not is_allowed:
            return Response(
                create_response_data(
                    success=False,
                    message="Too many authentication attempts. Please try again later.",
                    errors={'rate_limit': f'Reset time: {reset_time}'}
                ),
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = WalletAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        wallet_address = serializer.validated_data['wallet_address']
        
        # Get or create user
        user = get_or_create_user_from_wallet(wallet_address)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Log authentication
        log_authentication_event(user, 'wallet_login', request, {
            'wallet_address': wallet_address,
            'authentication_method': 'wallet_signature'
        })
        
        return Response(
            create_response_data(
                success=True,
                message="Wallet authentication successful",
                data={
                    'user': UserSerializer(user).data,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }
            )
        )


class LogoutView(APIView):
    """
    Logout user and blacklist refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log logout
            log_authentication_event(request.user, 'logout', request)
            
            return Response(
                create_response_data(
                    success=True,
                    message="Logged out successfully"
                )
            )
        except Exception as e:
            return Response(
                create_response_data(
                    success=False,
                    message="Error during logout",
                    errors={'detail': str(e)}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )


class UserView(RetrieveUpdateAPIView):
    """
    Get and update user data.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class UserProfileView(RetrieveUpdateAPIView):
    """
    Get and update user profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user.profile
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log profile update
            log_authentication_event(request.user, 'profile_update', request, {
                'updated_fields': list(request.data.keys())
            })
        
        return response


class APIKeyListCreateView(ListCreateAPIView):
    """
    List and create API keys.
    """
    serializer_class = APIKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        # Limit number of API keys per user
        if self.get_queryset().count() >= 10:
            return Response(
                create_response_data(
                    success=False,
                    message="Maximum number of API keys reached (10)",
                    errors={'limit': 'Delete some API keys before creating new ones'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


class PasswordChangeView(APIView):
    """
    Change user password.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        
        # Log password change
        log_authentication_event(user, 'password_change', request)
        
        return Response(
            create_response_data(
                success=True,
                message="Password changed successfully"
            )
        )


class PasswordResetRequestView(APIView):
    """
    Request password reset.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Check rate limit
        client_ip = get_client_ip(request)
        is_allowed, remaining, reset_time = check_rate_limit(
            f"password_reset:{client_ip}", limit=3, window=3600  # 3 requests per hour
        )
        
        if not is_allowed:
            return Response(
                create_response_data(
                    success=False,
                    message="Too many password reset requests. Please try again later.",
                    errors={'rate_limit': f'Reset time: {reset_time}'}
                ),
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate reset token and send email
            from .utils import generate_password_reset_token
            token = generate_password_reset_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            
            send_password_reset_email(user, reset_url)
            
            # Log password reset request
            log_authentication_event(user, 'password_reset_request', request)
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not
            pass
        
        return Response(
            create_response_data(
                success=True,
                message="If an account with this email exists, a password reset link has been sent."
            )
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        # Verify token and get user
        user = verify_password_reset_token(token)
        
        if not user:
            return Response(
                create_response_data(
                    success=False,
                    message="Invalid or expired reset token",
                    errors={'token': 'Token is invalid or has expired'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Log password reset
        log_authentication_event(user, 'password_reset_confirm', request)
        
        return Response(
            create_response_data(
                success=True,
                message="Password reset successfully"
            )
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_stats(request):
    """
    Get user statistics including escrow data.
    """
    user = request.user
    profile = user.profile
    
    # Update stats
    profile.update_stats()
    
    # Get escrow statistics
    from apps.marketplace.models import Escrow
    from decimal import Decimal
    
    escrows = Escrow.objects.filter(purchase__buyer=user)
    active_escrows = escrows.filter(status='active').count()
    completed_escrows = escrows.filter(status__in=['completed', 'auto_released']).count()
    disputed_escrows = escrows.filter(status='disputed').count()
    total_escrows = escrows.count()
    
    # Calculate success rate
    if total_escrows > 0:
        success_rate = ((completed_escrows) / total_escrows) * 100
    else:
        success_rate = 0
    
    # Calculate total escrow fees paid
    total_escrow_fees = sum(e.escrow_fee for e in escrows if e.escrow_fee) or Decimal('0.00')
    
    stats = {
        'datasets_uploaded': profile.total_datasets_uploaded,
        'datasets_purchased': profile.total_datasets_purchased,
        'total_earnings': str(profile.total_earnings),
        'total_spent': str(profile.total_spent),
        'reputation_score': str(profile.reputation_score),
        'verification_status': profile.verification_status,
        'wallet_connected': bool(profile.wallet_address),
        'account_age_days': (timezone.now() - user.created_at).days,
        # Escrow stats
        'active_escrows': active_escrows,
        'completed_escrows': completed_escrows,
        'disputed_escrows': disputed_escrows,
        'total_escrow_fees': str(total_escrow_fees),
        'escrow_success_rate': str(round(success_rate, 1)),
    }
    
    return Response(
        create_response_data(
            success=True,
            data=stats
        )
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def link_wallet(request):
    """
    Link wallet to existing account.
    """
    serializer = WalletAuthSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    wallet_address = serializer.validated_data['wallet_address']
    user = request.user
    
    # Check if wallet is already linked to another account
    existing_profile = UserProfile.objects.filter(wallet_address=wallet_address).first()
    if existing_profile and existing_profile.user != user:
        return Response(
            create_response_data(
                success=False,
                message="This wallet is already linked to another account",
                errors={'wallet_address': 'Wallet already linked to another account'}
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Link wallet to current user
    user.profile.wallet_address = wallet_address
    user.profile.save()
    
    # Log wallet linking
    log_authentication_event(user, 'wallet_connect', request, {
        'wallet_address': wallet_address,
        'action': 'link_to_existing_account'
    })
    
    return Response(
        create_response_data(
            success=True,
            message="Wallet linked successfully",
            data={'wallet_address': wallet_address}
        )
    )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unlink_wallet(request):
    """
    Unlink wallet from account.
    """
    user = request.user
    
    if not user.profile.wallet_address:
        return Response(
            create_response_data(
                success=False,
                message="No wallet linked to this account",
                errors={'wallet_address': 'No wallet linked'}
            ),
            status=status.HTTP_400_BAD_REQUEST
        )
    
    old_wallet = user.profile.wallet_address
    user.profile.wallet_address = None
    user.profile.save()
    
    # Log wallet unlinking
    log_authentication_event(user, 'wallet_disconnect', request, {
        'old_wallet_address': old_wallet,
        'action': 'unlink_from_account'
    })
    
    return Response(
        create_response_data(
            success=True,
            message="Wallet unlinked successfully"
        )
    )
