"""
Celery tasks for datasets app.
"""
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Dataset, DatasetReview
from .utils import upload_to_ipfs, generate_dataset_preview, calculate_dataset_quality_score
import logging
import os

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_dataset_upload(self, dataset_id):
    """
    Process dataset upload in background.
    
    Args:
        dataset_id: ID of the dataset to process
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        
        logger.info(f"Processing dataset upload: {dataset.title}")
        
        # Generate preview and statistics
        if dataset.file:
            preview_data = generate_dataset_preview(
                dataset.file.path, 
                dataset.file_type
            )
            
            # Update dataset with preview data
            dataset.sample_data = preview_data.get('sample_data', {})
            dataset.schema_info = preview_data.get('schema_info', {})
            dataset.statistics = preview_data.get('statistics', {})
            dataset.save()
            
            logger.info(f"Generated preview data for dataset: {dataset.title}")
        
        # Upload to IPFS if configured
        if hasattr(settings, 'IPFS_SETTINGS') and settings.IPFS_SETTINGS.get('ENABLED'):
            ipfs_result = upload_to_ipfs(dataset.file.path)
            
            if not ipfs_result.get('error'):
                dataset.ipfs_hash = ipfs_result['ipfs_hash']
                dataset.ipfs_url = ipfs_result['ipfs_url']
                dataset.save()
                
                logger.info(f"Uploaded dataset to IPFS: {dataset.ipfs_hash}")
            else:
                logger.error(f"IPFS upload failed: {ipfs_result['error']}")
        
        # Calculate quality score
        quality_score = calculate_dataset_quality_score(dataset)
        logger.info(f"Dataset quality score: {quality_score}")
        
        # Update dataset status to pending review
        dataset.status = 'pending'
        dataset.save()
        
        # Send notification to owner
        send_dataset_upload_notification.delay(dataset_id)
        
        logger.info(f"Dataset processing completed: {dataset.title}")
        
    except Dataset.DoesNotExist:
        logger.error(f"Dataset not found: {dataset_id}")
    except Exception as e:
        logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        else:
            # Mark dataset as failed after max retries
            try:
                dataset = Dataset.objects.get(id=dataset_id)
                dataset.status = 'rejected'
                dataset.rejection_reason = f"Processing failed: {str(e)}"
                dataset.save()
            except Dataset.DoesNotExist:
                pass


@shared_task
def send_dataset_upload_notification(dataset_id):
    """
    Send email notification when dataset is uploaded.
    
    Args:
        dataset_id: ID of the dataset
    """
    try:
        dataset = Dataset.objects.select_related('owner').get(id=dataset_id)
        
        subject = f'Dataset Upload Confirmation - {dataset.title}'
        
        context = {
            'dataset': dataset,
            'user': dataset.owner,
            'site_name': 'NeuroData'
        }
        
        # Render email templates
        html_message = render_to_string('datasets/dataset_upload_notification.html', context)
        text_message = render_to_string('datasets/dataset_upload_notification.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dataset.owner.email],
            fail_silently=False
        )
        
        logger.info(f"Upload notification sent to {dataset.owner.email}")
        
    except Dataset.DoesNotExist:
        logger.error(f"Dataset not found: {dataset_id}")
    except Exception as e:
        logger.error(f"Error sending upload notification: {str(e)}")


@shared_task
def send_dataset_approval_notification(dataset_id):
    """
    Send email notification when dataset is approved.
    
    Args:
        dataset_id: ID of the dataset
    """
    try:
        dataset = Dataset.objects.select_related('owner').get(id=dataset_id)
        
        subject = f'Dataset Approved - {dataset.title}'
        
        context = {
            'dataset': dataset,
            'user': dataset.owner,
            'site_name': 'NeuroData',
            'dataset_url': f"{settings.FRONTEND_URL}/datasets/{dataset.slug}"
        }
        
        # Render email templates
        html_message = render_to_string('datasets/dataset_approval_notification.html', context)
        text_message = render_to_string('datasets/dataset_approval_notification.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dataset.owner.email],
            fail_silently=False
        )
        
        logger.info(f"Approval notification sent to {dataset.owner.email}")
        
    except Dataset.DoesNotExist:
        logger.error(f"Dataset not found: {dataset_id}")
    except Exception as e:
        logger.error(f"Error sending approval notification: {str(e)}")


@shared_task
def send_dataset_rejection_notification(dataset_id, reason):
    """
    Send email notification when dataset is rejected.
    
    Args:
        dataset_id: ID of the dataset
        reason: Rejection reason
    """
    try:
        dataset = Dataset.objects.select_related('owner').get(id=dataset_id)
        
        subject = f'Dataset Rejected - {dataset.title}'
        
        context = {
            'dataset': dataset,
            'user': dataset.owner,
            'reason': reason,
            'site_name': 'NeuroData'
        }
        
        # Render email templates
        html_message = render_to_string('datasets/dataset_rejection_notification.html', context)
        text_message = render_to_string('datasets/dataset_rejection_notification.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dataset.owner.email],
            fail_silently=False
        )
        
        logger.info(f"Rejection notification sent to {dataset.owner.email}")
        
    except Dataset.DoesNotExist:
        logger.error(f"Dataset not found: {dataset_id}")
    except Exception as e:
        logger.error(f"Error sending rejection notification: {str(e)}")


@shared_task
def update_dataset_statistics(dataset_id):
    """
    Update dataset statistics and ratings.
    
    Args:
        dataset_id: ID of the dataset
    """
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        
        # Recalculate rating
        dataset.calculate_rating()
        
        # Update owner profile statistics
        if hasattr(dataset.owner, 'profile'):
            dataset.owner.profile.update_stats()
        
        logger.info(f"Updated statistics for dataset: {dataset.title}")
        
    except Dataset.DoesNotExist:
        logger.error(f"Dataset not found: {dataset_id}")
    except Exception as e:
        logger.error(f"Error updating dataset statistics: {str(e)}")


@shared_task
def cleanup_old_dataset_files():
    """
    Clean up old dataset files that are no longer needed.
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        # Find datasets that were rejected more than 30 days ago
        cutoff_date = timezone.now() - timedelta(days=30)
        old_rejected_datasets = Dataset.objects.filter(
            status='rejected',
            updated_at__lt=cutoff_date
        )
        
        cleaned_count = 0
        for dataset in old_rejected_datasets:
            if dataset.file:
                try:
                    # Delete the file
                    dataset.file.delete(save=False)
                    cleaned_count += 1
                    logger.info(f"Cleaned up file for rejected dataset: {dataset.title}")
                except Exception as e:
                    logger.error(f"Error deleting file for dataset {dataset.id}: {str(e)}")
        
        logger.info(f"Cleaned up {cleaned_count} old dataset files")
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")


@shared_task
def generate_dataset_sitemap():
    """
    Generate sitemap for approved datasets.
    """
    try:
        from django.urls import reverse
        
        approved_datasets = Dataset.objects.filter(status='approved').values(
            'slug', 'updated_at'
        )
        
        sitemap_data = []
        for dataset in approved_datasets:
            sitemap_data.append({
                'url': f"/datasets/{dataset['slug']}/",
                'lastmod': dataset['updated_at'].isoformat(),
                'changefreq': 'weekly',
                'priority': '0.8'
            })
        
        # Save sitemap data (this could be saved to a file or database)
        logger.info(f"Generated sitemap for {len(sitemap_data)} datasets")
        
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")


@shared_task
def send_review_notification(review_id):
    """
    Send notification when a new review is posted.
    
    Args:
        review_id: ID of the review
    """
    try:
        review = DatasetReview.objects.select_related('dataset', 'reviewer').get(id=review_id)
        dataset_owner = review.dataset.owner
        
        # Don't send notification if reviewer is the owner
        if review.reviewer == dataset_owner:
            return
        
        subject = f'New Review for Your Dataset - {review.dataset.title}'
        
        context = {
            'review': review,
            'dataset': review.dataset,
            'owner': dataset_owner,
            'reviewer': review.reviewer,
            'site_name': 'NeuroData'
        }
        
        # Render email templates
        html_message = render_to_string('datasets/review_notification.html', context)
        text_message = render_to_string('datasets/review_notification.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[dataset_owner.email],
            fail_silently=False
        )
        
        logger.info(f"Review notification sent to {dataset_owner.email}")
        
    except DatasetReview.DoesNotExist:
        logger.error(f"Review not found: {review_id}")
    except Exception as e:
        logger.error(f"Error sending review notification: {str(e)}")


@shared_task
def batch_update_quality_scores():
    """
    Batch update quality scores for all datasets.
    """
    try:
        datasets = Dataset.objects.filter(status='approved')
        updated_count = 0
        
        for dataset in datasets:
            try:
                quality_score = calculate_dataset_quality_score(dataset)
                # You could store this score in a separate field if needed
                updated_count += 1
            except Exception as e:
                logger.error(f"Error calculating quality score for dataset {dataset.id}: {str(e)}")
        
        logger.info(f"Updated quality scores for {updated_count} datasets")
        
    except Exception as e:
        logger.error(f"Error in batch quality score update: {str(e)}")


@shared_task
def sync_ipfs_metadata():
    """
    Sync metadata with IPFS for datasets that have IPFS hashes.
    """
    try:
        datasets_with_ipfs = Dataset.objects.filter(
            status='approved',
            ipfs_hash__isnull=False
        ).exclude(ipfs_hash='')
        
        synced_count = 0
        for dataset in datasets_with_ipfs:
            try:
                # Verify IPFS hash is still accessible
                # This would involve checking with IPFS gateway
                # For now, we'll just log it
                logger.info(f"IPFS hash for {dataset.title}: {dataset.ipfs_hash}")
                synced_count += 1
            except Exception as e:
                logger.error(f"Error syncing IPFS metadata for dataset {dataset.id}: {str(e)}")
        
        logger.info(f"Synced IPFS metadata for {synced_count} datasets")
        
    except Exception as e:
        logger.error(f"Error in IPFS metadata sync: {str(e)}")
