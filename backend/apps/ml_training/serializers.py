"""
Serializers for ML Training app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    MLAlgorithm, TrainingJob, TrainedModel, ModelInference, 
    TrainingQueue, ComputeResource
)
from apps.datasets.models import Dataset

User = get_user_model()


class MLAlgorithmSerializer(serializers.ModelSerializer):
    """Serializer for ML algorithms."""
    
    class Meta:
        model = MLAlgorithm
        fields = [
            'id', 'name', 'slug', 'algorithm_type', 'description',
            'library', 'class_name', 'parameters_schema', 'default_parameters',
            'min_memory_mb', 'min_cpu_cores', 'supports_gpu', 'cost_per_hour',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TrainingJobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating training jobs."""
    
    class Meta:
        model = TrainingJob
        fields = [
            'id', 'name', 'description', 'algorithm', 'dataset', 'parameters',
            'train_test_split', 'random_seed', 'max_runtime_hours',
            'memory_limit_mb', 'cpu_cores', 'use_gpu', 'priority'
        ]
        read_only_fields = ['id']
    
    def validate_dataset(self, value):
        """Validate that user has access to the dataset."""
        user = self.context['request'].user
        
        # Check if user owns the dataset or has purchased it
        if value.owner != user:
            from apps.marketplace.models import Purchase
            if not Purchase.objects.filter(
                buyer=user, 
                dataset=value, 
                status='completed'
            ).exists():
                raise serializers.ValidationError(
                    "You don't have access to this dataset."
                )
        return value
    
    def validate_algorithm(self, value):
        """Validate algorithm is active."""
        if not value.is_active:
            raise serializers.ValidationError(
                "This algorithm is not currently available."
            )
        return value
    
    def validate_parameters(self, value):
        """Validate parameters against algorithm schema."""
        # TODO: Implement JSON schema validation
        return value


class TrainingJobSerializer(serializers.ModelSerializer):
    """Serializer for training jobs."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    algorithm_name = serializers.CharField(source='algorithm.name', read_only=True)
    dataset_title = serializers.CharField(source='dataset.title', read_only=True)
    runtime_hours = serializers.ReadOnlyField()
    is_running = serializers.ReadOnlyField()
    is_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = TrainingJob
        fields = [
            'id', 'name', 'description', 'user_email', 'algorithm', 'algorithm_name',
            'dataset', 'dataset_title', 'parameters', 'train_test_split', 'random_seed',
            'max_runtime_hours', 'memory_limit_mb', 'cpu_cores', 'use_gpu',
            'status', 'priority', 'progress_percentage', 'model_file', 'model_metrics',
            'training_logs', 'actual_runtime_seconds', 'peak_memory_usage_mb',
            'estimated_cost', 'actual_cost', 'error_message', 'runtime_hours',
            'is_running', 'is_completed', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'algorithm_name', 'dataset_title', 'status',
            'progress_percentage', 'model_file', 'model_metrics', 'training_logs',
            'actual_runtime_seconds', 'peak_memory_usage_mb', 'actual_cost',
            'error_message', 'runtime_hours', 'is_running', 'is_completed',
            'created_at', 'started_at', 'completed_at'
        ]


class TrainedModelSerializer(serializers.ModelSerializer):
    """Serializer for trained models."""
    
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    algorithm_name = serializers.CharField(source='algorithm.name', read_only=True)
    source_dataset_title = serializers.CharField(source='source_dataset.title', read_only=True)
    training_job_name = serializers.CharField(source='training_job.name', read_only=True)
    model_size_human = serializers.ReadOnlyField()
    is_public = serializers.ReadOnlyField()
    
    class Meta:
        model = TrainedModel
        fields = [
            'id', 'name', 'description', 'owner_email', 'training_job',
            'training_job_name', 'algorithm', 'algorithm_name', 'source_dataset',
            'source_dataset_title', 'model_file', 'model_size_bytes',
            'model_size_human', 'model_format', 'metrics', 'accuracy',
            'precision', 'recall', 'f1_score', 'status', 'price',
            'download_count', 'rating_average', 'rating_count', 'is_public',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner_email', 'training_job_name', 'algorithm_name',
            'source_dataset_title', 'model_size_bytes', 'model_size_human',
            'download_count', 'rating_average', 'rating_count', 'is_public',
            'created_at', 'updated_at'
        ]


class ModelInferenceSerializer(serializers.ModelSerializer):
    """Serializer for model inference requests."""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    
    class Meta:
        model = ModelInference
        fields = [
            'id', 'user_email', 'model', 'model_name', 'input_data',
            'input_file', 'status', 'predictions', 'confidence_scores',
            'processing_time_ms', 'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'user_email', 'model_name', 'status', 'predictions',
            'confidence_scores', 'processing_time_ms', 'error_message',
            'created_at', 'completed_at'
        ]


class TrainingQueueSerializer(serializers.ModelSerializer):
    """Serializer for training queue."""
    
    training_job_name = serializers.CharField(source='training_job.name', read_only=True)
    user_email = serializers.CharField(source='training_job.user.email', read_only=True)
    
    class Meta:
        model = TrainingQueue
        fields = [
            'id', 'training_job', 'training_job_name', 'user_email',
            'queue_position', 'estimated_start_time', 'created_at'
        ]
        read_only_fields = [
            'id', 'training_job_name', 'user_email', 'queue_position',
            'estimated_start_time', 'created_at'
        ]


class ComputeResourceSerializer(serializers.ModelSerializer):
    """Serializer for compute resources."""
    
    current_job_name = serializers.CharField(source='current_job.name', read_only=True)
    is_available = serializers.ReadOnlyField()
    
    class Meta:
        model = ComputeResource
        fields = [
            'id', 'name', 'description', 'cpu_cores', 'memory_gb',
            'gpu_count', 'gpu_type', 'storage_gb', 'status',
            'current_job', 'current_job_name', 'total_jobs_completed',
            'total_runtime_hours', 'is_available', 'created_at', 'last_used_at'
        ]
        read_only_fields = [
            'id', 'current_job_name', 'total_jobs_completed',
            'total_runtime_hours', 'is_available', 'created_at', 'last_used_at'
        ]


class TrainingJobStatsSerializer(serializers.Serializer):
    """Serializer for training job statistics."""
    
    total_jobs = serializers.IntegerField()
    completed_jobs = serializers.IntegerField()
    running_jobs = serializers.IntegerField()
    failed_jobs = serializers.IntegerField()
    total_runtime_hours = serializers.FloatField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=8)
    avg_accuracy = serializers.FloatField()
    
    
class MLDashboardSerializer(serializers.Serializer):
    """Serializer for ML dashboard data."""
    
    user_stats = TrainingJobStatsSerializer()
    recent_jobs = TrainingJobSerializer(many=True)
    popular_algorithms = MLAlgorithmSerializer(many=True)
    queue_status = TrainingQueueSerializer(many=True)
