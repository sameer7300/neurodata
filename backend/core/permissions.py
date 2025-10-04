"""
Custom permissions for NeuroData API.
"""
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsDatasetOwner(BasePermission):
    """
    Permission to check if user owns the dataset.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class HasPurchasedDataset(BasePermission):
    """
    Permission to check if user has purchased the dataset.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user has purchased this dataset
        from apps.marketplace.models import Purchase
        return Purchase.objects.filter(
            buyer=request.user,
            dataset=obj,
            status='completed'
        ).exists()


class IsDatasetOwnerOrHasPurchased(BasePermission):
    """
    Permission that allows access to dataset owners or purchasers.
    """
    
    def has_object_permission(self, request, view, obj):
        # Owner has full access
        if obj.owner == request.user:
            return True
        
        # Check if user has purchased this dataset
        from apps.marketplace.models import Purchase
        return Purchase.objects.filter(
            buyer=request.user,
            dataset=obj,
            status='completed'
        ).exists()


class IsMLTrainingOwner(BasePermission):
    """
    Permission to check if user owns the ML training job.
    """
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Permission that allows read access to everyone and write access to admins only.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff


class HasValidWallet(BasePermission):
    """
    Permission to check if user has a valid wallet address.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        profile = getattr(request.user, 'profile', None)
        return profile and profile.wallet_address


class CanAffordDataset(BasePermission):
    """
    Permission to check if user can afford to purchase a dataset.
    """
    
    def has_object_permission(self, request, view, obj):
        # Only check for purchase-related actions
        if view.action not in ['purchase', 'create_purchase']:
            return True
        
        # Check user's balance (this would integrate with blockchain)
        # For now, we'll assume they can afford it
        return True


class IsVerifiedUser(BasePermission):
    """
    Permission to check if user is verified.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        profile = getattr(request.user, 'profile', None)
        return profile and profile.is_verified
