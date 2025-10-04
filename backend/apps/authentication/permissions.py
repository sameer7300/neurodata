"""
Custom permissions for authentication app.
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from .models import APIKey


class IsVerifiedUser(BasePermission):
    """
    Permission to check if user is verified.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_verified


class HasWalletConnected(BasePermission):
    """
    Permission to check if user has a wallet connected.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        profile = getattr(request.user, 'profile', None)
        return profile and profile.wallet_address


class APIKeyAuthentication(BasePermission):
    """
    Custom authentication using API keys.
    """
    
    def has_permission(self, request, view):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return False
        
        try:
            api_key_obj = APIKey.objects.select_related('user').get(
                key=api_key,
                is_active=True
            )
            
            # Check if API key is expired
            if api_key_obj.is_expired:
                return False
            
            # Check permissions based on request method
            if request.method in ['GET', 'HEAD', 'OPTIONS']:
                if not api_key_obj.can_read:
                    return False
            elif request.method in ['POST', 'PUT', 'PATCH']:
                if not api_key_obj.can_write:
                    return False
            elif request.method == 'DELETE':
                if not api_key_obj.can_delete:
                    return False
            
            # Set user in request
            request.user = api_key_obj.user
            
            # Increment usage count
            api_key_obj.increment_usage()
            
            return True
            
        except APIKey.DoesNotExist:
            return False


class IsOwnerOrVerifiedUser(BasePermission):
    """
    Permission that allows access to owners or verified users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if user is verified for read access
        if request.method in permissions.SAFE_METHODS:
            profile = getattr(request.user, 'profile', None)
            return profile and profile.is_verified
        
        return False


class CanManageProfile(BasePermission):
    """
    Permission to manage user profiles.
    """
    
    def has_object_permission(self, request, view, obj):
        # Users can only manage their own profile
        return obj.user == request.user


class IsAdminOrOwner(BasePermission):
    """
    Permission that allows access to admins or object owners.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin users have full access
        if request.user.is_staff:
            return True
        
        # Check if user is the owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        return False


class RateLimitPermission(BasePermission):
    """
    Permission that implements rate limiting.
    """
    
    def has_permission(self, request, view):
        from .utils import check_rate_limit
        from core.utils import get_client_ip
        
        # Different limits for different endpoints
        if hasattr(view, 'rate_limit_key'):
            key = f"{view.rate_limit_key}:{get_client_ip(request)}"
            limit = getattr(view, 'rate_limit_count', 60)
            window = getattr(view, 'rate_limit_window', 3600)
        else:
            key = f"api:{get_client_ip(request)}"
            limit = 100  # Default: 100 requests per hour
            window = 3600
        
        is_allowed, remaining, reset_time = check_rate_limit(key, limit, window)
        
        if not is_allowed:
            # Add rate limit info to response headers
            if hasattr(request, '_request'):
                request._request.rate_limit_remaining = 0
                request._request.rate_limit_reset = reset_time
            return False
        
        # Add rate limit info to response headers
        if hasattr(request, '_request'):
            request._request.rate_limit_remaining = remaining
        
        return True


class IsActiveUser(BasePermission):
    """
    Permission to check if user account is active.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_active


class CanAccessPremiumFeatures(BasePermission):
    """
    Permission for premium features access.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return False
        
        # Check if user is verified and has minimum reputation
        return (profile.is_verified and 
                profile.reputation_score >= 50)  # Minimum reputation for premium features
