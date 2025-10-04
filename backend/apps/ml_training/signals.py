"""
Signals for ML training app.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TrainingJob, TrainedModel, TrainingQueue, ComputeResource


@receiver(post_save, sender=TrainingJob)
def training_job_post_save(sender, instance, created, **kwargs):
    """
    Handle training job creation and status updates.
    """
    if created:
        # Add to training queue
        queue_position = TrainingQueue.objects.count() + 1
        TrainingQueue.objects.create(
            training_job=instance,
            queue_position=queue_position
        )
    
    # Handle status changes
    if instance.status == 'running' and not instance.started_at:
        instance.started_at = timezone.now()
        instance.save(update_fields=['started_at'])
    
    elif instance.status in ['completed', 'failed', 'cancelled']:
        if not instance.completed_at:
            instance.completed_at = timezone.now()
            instance.save(update_fields=['completed_at'])
        
        # Calculate actual cost
        if instance.status == 'completed' and instance.actual_runtime_seconds:
            instance.actual_cost = instance.calculate_cost()
            instance.save(update_fields=['actual_cost'])
        
        # Remove from queue
        if hasattr(instance, 'queue_entry'):
            instance.queue_entry.delete()
        
        # Free up compute resource
        try:
            # Get the resource that was assigned to this job
            resource = ComputeResource.objects.filter(current_job=instance).first()
            if resource:
                resource.current_job = None
                resource.status = 'available'
                resource.last_used_at = timezone.now()
                
                if instance.status == 'completed':
                    resource.total_jobs_completed += 1
                    if instance.actual_runtime_seconds:
                        resource.total_runtime_hours += instance.actual_runtime_seconds / 3600
                
                resource.save()
        except Exception as e:
            # Log the error but don't fail the signal
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating compute resource for job {instance.id}: {e}")


@receiver(post_save, sender=TrainedModel)
def trained_model_post_save(sender, instance, created, **kwargs):
    """
    Handle trained model creation.
    """
    if created and instance.model_file:
        # Calculate model file size
        instance.model_size_bytes = instance.model_file.size
        instance.save(update_fields=['model_size_bytes'])


@receiver(pre_save, sender=TrainingJob)
def training_job_pre_save(sender, instance, **kwargs):
    """
    Handle training job updates before saving.
    """
    # Estimate cost based on configuration
    if instance.algorithm and not instance.actual_cost:
        estimated_hours = instance.max_runtime_hours
        instance.estimated_cost = instance.algorithm.cost_per_hour * estimated_hours
