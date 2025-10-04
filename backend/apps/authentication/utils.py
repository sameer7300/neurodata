"""
Utility functions for authentication app.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from eth_account.messages import encode_defunct
from eth_account import Account
import logging

logger = logging.getLogger(__name__)


def generate_nonce(wallet_address):
    """
    Generate a unique nonce for wallet authentication.
    """
    timestamp = int(timezone.now().timestamp())
    random_string = secrets.token_hex(16)
    
    nonce_message = (
        f"Welcome to NeuroData!\n\n"
        f"Please sign this message to authenticate your wallet.\n\n"
        f"Wallet: {wallet_address}\n"
        f"Timestamp: {timestamp}\n"
        f"Nonce: {random_string}\n\n"
        f"This request will not trigger a blockchain transaction or cost any gas fees."
    )
    
    # Store nonce in cache for 10 minutes
    cache_key = f"wallet_nonce:{wallet_address.lower()}"
    nonce_data = {
        'nonce': nonce_message,
        'timestamp': timestamp,
        'random': random_string
    }
    
    logger.info(f"Storing nonce with key: {cache_key}")
    logger.info(f"Nonce data: {nonce_data}")
    
    cache.set(cache_key, nonce_data, timeout=600)  # 10 minutes
    
    # Verify it was stored
    stored_check = cache.get(cache_key)
    logger.info(f"Verification - stored nonce: {stored_check}")
    
    return nonce_message


def verify_wallet_signature(wallet_address, nonce_message, signature):
    """
    Verify wallet signature for authentication.
    """
    try:
        # Normalize wallet address
        wallet_address = wallet_address.lower()
        
        # Get stored nonce from cache
        cache_key = f"wallet_nonce:{wallet_address}"
        stored_nonce_data = cache.get(cache_key)
        
        logger.info(f"Looking for nonce with key: {cache_key}")
        logger.info(f"Found nonce data: {stored_nonce_data}")
        
        if not stored_nonce_data:
            logger.warning(f"No nonce found for wallet {wallet_address}")
            return False, "No nonce found for this wallet"
        
        # Verify nonce matches
        if stored_nonce_data['nonce'] != nonce_message:
            logger.warning(f"Nonce mismatch for wallet {wallet_address}")
            return False, "Nonce mismatch"
        
        # Check if nonce is not too old (additional safety check)
        nonce_timestamp = stored_nonce_data['timestamp']
        current_timestamp = int(timezone.now().timestamp())
        
        if current_timestamp - nonce_timestamp > 600:  # 10 minutes
            logger.warning(f"Nonce expired for wallet {wallet_address}")
            return False, "Nonce expired"
        
        # Verify signature
        message_hash = encode_defunct(text=nonce_message)
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Compare addresses (case-insensitive)
        is_valid = recovered_address.lower() == wallet_address
        
        if is_valid:
            # Clear the nonce after successful verification
            cache.delete(cache_key)
            logger.info(f"Wallet signature verified for {wallet_address}")
            return True, "Signature verified successfully"
        else:
            logger.warning(f"Invalid signature for wallet {wallet_address}")
            return False, "Invalid signature"
        
    except Exception as e:
        logger.error(f"Error verifying wallet signature: {str(e)}")
        return False, f"Verification error: {str(e)}"


def generate_password_reset_token(user):
    """
    Generate a password reset token.
    """
    timestamp = int(timezone.now().timestamp())
    user_data = f"{user.id}:{user.email}:{timestamp}"
    token = hashlib.sha256(user_data.encode()).hexdigest()
    
    # Store token in cache for 1 hour
    cache_key = f"password_reset:{token}"
    cache.set(cache_key, {
        'user_id': str(user.id),
        'email': user.email,
        'timestamp': timestamp
    }, timeout=3600)  # 1 hour
    
    return token


def verify_password_reset_token(token):
    """
    Verify password reset token and return user.
    """
    try:
        cache_key = f"password_reset:{token}"
        token_data = cache.get(cache_key)
        
        if not token_data:
            return None
        
        # Check if token is not too old
        token_timestamp = token_data['timestamp']
        current_timestamp = int(timezone.now().timestamp())
        
        if current_timestamp - token_timestamp > 3600:  # 1 hour
            cache.delete(cache_key)
            return None
        
        # Get user
        from .models import User
        user = User.objects.get(id=token_data['user_id'])
        
        # Clear token after use
        cache.delete(cache_key)
        
        return user
        
    except Exception as e:
        logger.error(f"Error verifying password reset token: {str(e)}")
        return None


def send_password_reset_email(user, reset_url):
    """
    Send password reset email to user.
    """
    try:
        subject = 'NeuroData - Password Reset Request'
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'NeuroData',
            'expiry_hours': 1
        }
        
        # Render email templates
        html_message = render_to_string('authentication/password_reset_email.html', context)
        text_message = render_to_string('authentication/password_reset_email.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending password reset email: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user.
    """
    try:
        subject = 'Welcome to NeuroData!'
        
        context = {
            'user': user,
            'site_name': 'NeuroData',
            'login_url': f"{settings.FRONTEND_URL}/login"
        }
        
        # Render email templates
        html_message = render_to_string('authentication/welcome_email.html', context)
        text_message = render_to_string('authentication/welcome_email.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        return False


def create_user_from_wallet(wallet_address):
    """
    Create a new user from wallet address.
    """
    from .models import User
    
    # Generate a unique email and username
    username = f"user_{wallet_address[-8:].lower()}"
    email = f"{username}@neurodata.temp"
    
    # Ensure uniqueness
    counter = 1
    original_username = username
    original_email = email
    
    while User.objects.filter(username=username).exists():
        username = f"{original_username}_{counter}"
        counter += 1
    
    counter = 1
    while User.objects.filter(email=email).exists():
        email = f"{original_username}_{counter}@neurodata.temp"
        counter += 1
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=None  # No password for wallet-only users
    )
    
    # Set wallet address in profile and auto-verify wallet users
    user.profile.wallet_address = wallet_address.lower()
    user.profile.verification_status = 'verified'  # Auto-verify wallet users
    user.profile.save()
    
    logger.info(f"Created new verified user from wallet: {wallet_address}")
    return user


def get_or_create_user_from_wallet(wallet_address):
    """
    Get or create a user from wallet address.
    """
    from .models import UserProfile, User
    
    wallet_address = wallet_address.lower()
    
    try:
        # Try to find existing user with this wallet
        profile = UserProfile.objects.get(wallet_address=wallet_address)
        
        # Auto-verify existing wallet users if not already verified
        if profile.verification_status != 'verified':
            profile.verification_status = 'verified'
            profile.save()
            logger.info(f"Auto-verified existing wallet user: {wallet_address}")
        
        return profile.user
    except UserProfile.DoesNotExist:
        # Create new user
        return create_user_from_wallet(wallet_address)


def validate_api_key(api_key):
    """
    Validate API key and return user.
    """
    try:
        from .models import APIKey
        
        api_key_obj = APIKey.objects.select_related('user').get(
            key=api_key,
            is_active=True
        )
        
        # Check if API key is expired
        if api_key_obj.is_expired:
            return None
        
        # Increment usage count
        api_key_obj.increment_usage()
        
        return api_key_obj.user
        
    except APIKey.DoesNotExist:
        return None


def log_authentication_event(user, event_type, request, metadata=None):
    """
    Log authentication events.
    """
    from .models import UserActivity
    from core.utils import get_client_ip
    
    UserActivity.objects.create(
        user=user,
        activity_type=event_type,
        description=f"Authentication event: {event_type}",
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata=metadata or {}
    )


def check_rate_limit(identifier, limit=5, window=300):
    """
    Check rate limit for authentication attempts.
    
    Args:
        identifier: IP address or user identifier
        limit: Maximum attempts allowed
        window: Time window in seconds
    
    Returns:
        tuple: (is_allowed, remaining_attempts, reset_time)
    """
    cache_key = f"rate_limit:{identifier}"
    current_time = int(timezone.now().timestamp())
    
    # Get current attempts
    attempts = cache.get(cache_key, [])
    
    # Remove old attempts outside the window
    attempts = [timestamp for timestamp in attempts if current_time - timestamp < window]
    
    # Check if limit exceeded
    if len(attempts) >= limit:
        oldest_attempt = min(attempts)
        reset_time = oldest_attempt + window
        return False, 0, reset_time
    
    # Add current attempt
    attempts.append(current_time)
    cache.set(cache_key, attempts, timeout=window)
    
    remaining = limit - len(attempts)
    return True, remaining, None
