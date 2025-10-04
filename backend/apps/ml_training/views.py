"""
Views for ML Training app.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from decimal import Decimal
import logging

from .models import (
    MLAlgorithm, TrainingJob, TrainedModel, ModelInference,
    TrainingQueue, ComputeResource
)
from .serializers import (
    MLAlgorithmSerializer, TrainingJobSerializer, TrainingJobCreateSerializer,
    TrainedModelSerializer, ModelInferenceSerializer, TrainingQueueSerializer,
    ComputeResourceSerializer, MLDashboardSerializer
)
from .tasks import start_training_job, run_model_inference
from core.utils import create_response_data

logger = logging.getLogger(__name__)


class MLAlgorithmViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for ML algorithms."""
    
    queryset = MLAlgorithm.objects.filter(is_active=True)
    serializer_class = MLAlgorithmSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        algorithm_type = self.request.query_params.get('type')
        
        if algorithm_type:
            queryset = queryset.filter(algorithm_type=algorithm_type)
            
        return queryset.order_by('name')


class TrainingJobViewSet(viewsets.ModelViewSet):
    """ViewSet for training jobs."""
    
    serializer_class = TrainingJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TrainingJob.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TrainingJobCreateSerializer
        return TrainingJobSerializer
    
    def perform_create(self, serializer):
        """Create a new training job."""
        training_job = serializer.save(user=self.request.user)
        
        # Calculate estimated cost
        algorithm = training_job.algorithm
        estimated_hours = training_job.max_runtime_hours
        training_job.estimated_cost = algorithm.cost_per_hour * Decimal(str(estimated_hours))
        training_job.save()
        
        # Add to queue and start training
        start_training_job.delay(str(training_job.id))
        
        logger.info(f"Training job created: {training_job.name} by {self.request.user.email}")
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a training job."""
        training_job = self.get_object()
        
        if training_job.status not in ['created', 'queued', 'running']:
            return Response(
                create_response_data(
                    success=False,
                    message="Cannot cancel job in current status",
                    errors={"status": ["Job is already completed or cancelled"]}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        training_job.status = 'cancelled'
        training_job.completed_at = timezone.now()
        training_job.save()
        
        # Remove from queue if present
        TrainingQueue.objects.filter(training_job=training_job).delete()
        
        logger.info(f"Training job cancelled: {training_job.name}")
        
        return Response(
            create_response_data(
                success=True,
                message="Training job cancelled successfully",
                data=self.get_serializer(training_job).data
            )
        )
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Get training logs for a job."""
        training_job = self.get_object()
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'logs': training_job.training_logs,
                    'status': training_job.status,
                    'progress': training_job.progress_percentage
                }
            )
        )
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get training metrics for a job."""
        training_job = self.get_object()
        
        return Response(
            create_response_data(
                success=True,
                data={
                    'metrics': training_job.model_metrics,
                    'status': training_job.status,
                    'runtime_hours': training_job.runtime_hours,
                    'actual_cost': training_job.actual_cost
                }
            )
        )
    
    @action(detail=True, methods=['get'])
    def download_model(self, request, pk=None):
        """Download the trained model file."""
        training_job = self.get_object()
        
        # Check if job is completed and has a model file
        if training_job.status != 'completed':
            return Response(
                create_response_data(
                    success=False,
                    message="Training job is not completed yet",
                    errors={"status": ["Job must be completed to download model"]}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not training_job.model_file:
            return Response(
                create_response_data(
                    success=False,
                    message="Model file not available",
                    errors={"model": ["No model file found for this job"]}
                ),
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            import os
            from django.http import FileResponse
            from django.conf import settings
            
            # Get the file path from FileField
            model_path = training_job.model_file.path
            
            if not os.path.exists(model_path):
                return Response(
                    create_response_data(
                        success=False,
                        message="Model file not found on disk",
                        errors={"file": ["Model file has been deleted or moved"]}
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create file response
            response = FileResponse(
                open(model_path, 'rb'),
                as_attachment=True,
                filename=f"{training_job.name}_model.pkl"
            )
            response['Content-Type'] = 'application/octet-stream'
            
            logger.info(f"Model downloaded: {training_job.name} by {request.user.email}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading model for job {pk}: {str(e)}")
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to download model",
                    errors={"download": [str(e)]}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrainedModelViewSet(viewsets.ModelViewSet):
    """ViewSet for trained models."""
    
    serializer_class = TrainedModelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            # Show public models and user's own models
            return TrainedModel.objects.filter(
                Q(status__in=['public', 'for_sale']) | Q(owner=self.request.user)
            ).order_by('-created_at')
        
        # For detail views, check ownership or public status
        return TrainedModel.objects.filter(
            Q(status__in=['public', 'for_sale']) | Q(owner=self.request.user)
        )
    
    def perform_create(self, serializer):
        """Create a trained model from a training job."""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Download a trained model."""
        model = self.get_object()
        
        # Check permissions
        if model.status == 'private' and model.owner != request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="Access denied",
                    errors={"permission": ["You don't have access to this model"]}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # For paid models, check purchase
        if model.status == 'for_sale' and model.owner != request.user:
            # TODO: Implement model purchase system
            pass
        
        # Increment download count
        model.download_count += 1
        model.save()
        
        return Response(
            create_response_data(
                success=True,
                message="Model download started",
                data={
                    'download_url': model.model_file.url,
                    'filename': model.model_file.name,
                    'size': model.model_size_bytes
                }
            )
        )
    
    @action(detail=True, methods=['post'])
    def inference(self, request, pk=None):
        """Run inference on a trained model."""
        model = self.get_object()
        
        # Check permissions
        if model.status == 'private' and model.owner != request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="Access denied"
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create inference request
        inference = ModelInference.objects.create(
            user=request.user,
            model=model,
            input_data=request.data.get('input_data', {}),
            input_file=request.FILES.get('input_file')
        )
        
        # Start inference task
        run_model_inference.delay(str(inference.id))
        
        return Response(
            create_response_data(
                success=True,
                message="Inference started",
                data=ModelInferenceSerializer(inference).data
            )
        )


class ModelInferenceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for model inference requests."""
    
    serializer_class = ModelInferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ModelInference.objects.filter(user=self.request.user).order_by('-created_at')


class TrainingQueueViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for training queue."""
    
    serializer_class = TrainingQueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return TrainingQueue.objects.filter(
            training_job__user=self.request.user
        ).order_by('queue_position')


class ComputeResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for compute resources."""
    
    serializer_class = ComputeResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ComputeResource.objects.all().order_by('name')


class MLDashboardViewSet(viewsets.ViewSet):
    """ViewSet for ML dashboard data."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get ML dashboard data."""
        user = request.user
        
        # User statistics
        user_jobs = TrainingJob.objects.filter(user=user)
        total_jobs = user_jobs.count()
        completed_jobs = user_jobs.filter(status='completed').count()
        running_jobs = user_jobs.filter(status__in=['queued', 'running']).count()
        failed_jobs = user_jobs.filter(status='failed').count()
        
        # Calculate total runtime and cost
        completed_jobs_qs = user_jobs.filter(
            status='completed',
            actual_runtime_seconds__isnull=False
        )
        total_runtime_seconds = completed_jobs_qs.aggregate(
            total=Sum('actual_runtime_seconds')
        )['total'] or 0
        total_runtime_hours = total_runtime_seconds / 3600
        
        total_cost = completed_jobs_qs.aggregate(
            total=Sum('actual_cost')
        )['total'] or Decimal('0.00')
        
        # Average accuracy from trained models
        user_models = TrainedModel.objects.filter(owner=user, accuracy__isnull=False)
        avg_accuracy = user_models.aggregate(avg=Avg('accuracy'))['avg'] or 0.0
        
        user_stats = {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'running_jobs': running_jobs,
            'failed_jobs': failed_jobs,
            'total_runtime_hours': total_runtime_hours,
            'total_cost': total_cost,
            'avg_accuracy': avg_accuracy
        }
        
        # Recent jobs
        recent_jobs = user_jobs.order_by('-created_at')[:5]
        
        # Popular algorithms
        popular_algorithms = MLAlgorithm.objects.filter(
            is_active=True
        ).annotate(
            job_count=Count('training_jobs')
        ).order_by('-job_count')[:5]
        
        # Queue status
        queue_status = TrainingQueue.objects.filter(
            training_job__user=user
        ).order_by('queue_position')[:5]
        
        dashboard_data = {
            'user_stats': user_stats,
            'recent_jobs': TrainingJobSerializer(recent_jobs, many=True).data,
            'popular_algorithms': MLAlgorithmSerializer(popular_algorithms, many=True).data,
            'queue_status': TrainingQueueSerializer(queue_status, many=True).data
        }
        
        return Response(
            create_response_data(
                success=True,
                data=dashboard_data
            )
        )
