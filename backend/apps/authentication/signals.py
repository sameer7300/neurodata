"""
Signals for authentication app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import User, UserProfile, UserActivity
from core.utils import generate_api_key, get_client_ip


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a new User is created.
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log user login activity.
    """
    UserActivity.objects.create(
        user=user,
        activity_type='login',
        description=f'User logged in from {get_client_ip(request)}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'session_key': request.session.session_key,
            'login_method': 'standard'
        }
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout activity.
    """
    if user:
        UserActivity.objects.create(
            user=user,
            activity_type='logout',
            description=f'User logged out from {get_client_ip(request)}',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'session_key': request.session.session_key if request.session else None
            }
        )


def log_wallet_connection(user, wallet_address, request):
    """
    Log wallet connection activity.
    """
    UserActivity.objects.create(
        user=user,
        activity_type='wallet_connect',
        description=f'Wallet {wallet_address} connected',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'wallet_address': wallet_address,
            'connection_type': 'metamask'
        }
    )


def log_profile_update(user, changes, request):
    """
    Log profile update activity.
    """
    UserActivity.objects.create(
        user=user,
        activity_type='profile_update',
        description=f'Profile updated: {", ".join(changes)}',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        metadata={
            'updated_fields': changes
        }
    )
