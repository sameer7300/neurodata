"""
Signals for datasets app.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Dataset, DatasetReview, DatasetAccess
from apps.authentication.models import UserActivity


@receiver(post_save, sender=Dataset)
def dataset_post_save(sender, instance, created, **kwargs):
    """
    Handle dataset creation and updates.
    """
    if created:
        # Log dataset upload activity
        UserActivity.objects.create(
            user=instance.owner,
            activity_type='dataset_upload',
            description=f'Dataset "{instance.title}" uploaded',
            metadata={
                'dataset_id': str(instance.id),
                'dataset_title': instance.title,
                'file_size': instance.file_size,
                'price': str(instance.price)
            }
        )
    
    # Set published_at when status changes to approved
    if instance.status == 'approved' and not instance.published_at:
        instance.published_at = timezone.now()
        instance.save(update_fields=['published_at'])


@receiver(post_save, sender=DatasetReview)
def review_post_save(sender, instance, created, **kwargs):
    """
    Handle review creation and updates.
    """
    if created:
        # Update dataset rating
        instance.dataset.calculate_rating()


@receiver(post_delete, sender=DatasetReview)
def review_post_delete(sender, instance, **kwargs):
    """
    Handle review deletion.
    """
    # Update dataset rating
    instance.dataset.calculate_rating()


@receiver(post_save, sender=DatasetAccess)
def dataset_access_post_save(sender, instance, created, **kwargs):
    """
    Handle dataset access logging.
    """
    if created and instance.access_type == 'download':
        # Increment download count
        instance.dataset.increment_download_count()
    elif created and instance.access_type == 'view':
        # Increment view count
        instance.dataset.increment_view_count()
