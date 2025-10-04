"""
Signals for marketplace app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Purchase, Transaction, Payout
from apps.authentication.models import UserActivity


@receiver(post_save, sender=Purchase)
def purchase_post_save(sender, instance, created, **kwargs):
    """
    Handle purchase creation and status updates.
    """
    if created:
        # Log purchase activity
        UserActivity.objects.create(
            user=instance.buyer,
            activity_type='dataset_purchase',
            description=f'Purchased dataset "{instance.dataset.title}" for {instance.amount} {instance.currency}',
            metadata={
                'purchase_id': str(instance.id),
                'dataset_id': str(instance.dataset.id),
                'dataset_title': instance.dataset.title,
                'amount': str(instance.amount),
                'currency': instance.currency,
                'payment_method': instance.payment_method
            }
        )
    
    # Handle status changes
    if instance.status == 'completed' and not instance.completed_at:
        instance.completed_at = timezone.now()
        instance.save(update_fields=['completed_at'])
        
        # Update user profile statistics
        if hasattr(instance.buyer, 'profile'):
            instance.buyer.profile.update_stats()
        
        if hasattr(instance.dataset.owner, 'profile'):
            instance.dataset.owner.profile.update_stats()


@receiver(post_save, sender=Transaction)
def transaction_post_save(sender, instance, created, **kwargs):
    """
    Handle transaction confirmation.
    """
    if instance.status == 'confirmed' and instance.purchase:
        # Mark related purchase as completed if transaction is confirmed
        if instance.purchase.status == 'processing':
            instance.purchase.mark_completed()


@receiver(post_save, sender=Payout)
def payout_post_save(sender, instance, created, **kwargs):
    """
    Handle payout processing.
    """
    if created:
        # Create payout transaction record
        if instance.transaction_hash:
            Transaction.objects.create(
                transaction_type='payout',
                transaction_hash=instance.transaction_hash,
                from_address='platform_wallet',  # This would be the platform wallet
                to_address=instance.recipient_address,
                amount=instance.net_amount,
                currency=instance.currency,
                user=instance.seller,
                purchase=instance.purchase,
                status='pending'
            )
