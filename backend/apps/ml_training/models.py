"""
ML Training models for NeuroData platform.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class MLAlgorithm(models.Model):
    """
    Available ML algorithms for training.
    """
    ALGORITHM_TYPES = [
        ('classification', 'Classification'),
        ('regression', 'Regression'),
        ('clustering', 'Clustering'),
        ('dimensionality_reduction', 'Dimensionality Reduction'),
        ('deep_learning', 'Deep Learning'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    algorithm_type = models.CharField(max_length=30, choices=ALGORITHM_TYPES)
    description = models.TextField()
    
    # Implementation details
    library = models.CharField(max_length=50)  # scikit-learn, tensorflow, pytorch
    class_name = models.CharField(max_length=100)  # Python class name
    
    # Parameters schema (JSON schema for validation)
    parameters_schema = models.JSONField(default=dict)
    default_parameters = models.JSONField(default=dict)
    
    # Resource requirements
    min_memory_mb = models.PositiveIntegerField(default=512)
    min_cpu_cores = models.PositiveIntegerField(default=1)
    supports_gpu = models.BooleanField(default=False)
    
    # Pricing
    cost_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=Decimal('0.01000000')
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ml_algorithms'
        verbose_name = 'ML Algorithm'
        verbose_name_plural = 'ML Algorithms'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TrainingJob(models.Model):
    """
    ML training job instances.
    """
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Ownership
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_jobs')
    
    # Training Configuration
    algorithm = models.ForeignKey(MLAlgorithm, on_delete=models.CASCADE, related_name='training_jobs')
    dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE, related_name='training_jobs')
    
    # Parameters and Configuration
    parameters = models.JSONField(default=dict)
    train_test_split = models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.1), MaxValueValidator(0.9)]
    )
    random_seed = models.PositiveIntegerField(default=42)
    
    # Resource Configuration
    max_runtime_hours = models.PositiveIntegerField(default=24)
    memory_limit_mb = models.PositiveIntegerField(default=2048)
    cpu_cores = models.PositiveIntegerField(default=2)
    use_gpu = models.BooleanField(default=False)
    
    # Status and Progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    progress_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)]
    )
    
    # Results
    model_file = models.FileField(upload_to='trained_models/', null=True, blank=True)
    model_metrics = models.JSONField(default=dict, blank=True)
    training_logs = models.TextField(blank=True)
    
    # Resource Usage
    actual_runtime_seconds = models.PositiveIntegerField(null=True, blank=True)
    peak_memory_usage_mb = models.PositiveIntegerField(null=True, blank=True)
    
    # Cost Calculation
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    actual_cost = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True
    )
    
    # Error Information
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ml_training_jobs'
        verbose_name = 'Training Job'
        verbose_name_plural = 'Training Jobs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'priority', 'created_at']),
            models.Index(fields=['algorithm', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.algorithm.name}"
    
    @property
    def is_running(self):
        return self.status in ['queued', 'running']
    
    @property
    def is_completed(self):
        return self.status in ['completed', 'failed', 'cancelled']
    
    @property
    def runtime_hours(self):
        if self.actual_runtime_seconds:
            return self.actual_runtime_seconds / 3600
        return 0
    
    def calculate_cost(self):
        """Calculate the cost based on runtime and algorithm pricing."""
        if self.actual_runtime_seconds and self.algorithm:
            hours = self.actual_runtime_seconds / 3600
            return self.algorithm.cost_per_hour * Decimal(str(hours))
        return self.estimated_cost


class TrainedModel(models.Model):
    """
    Trained ML models that can be shared or sold.
    """
    STATUS_CHOICES = [
        ('private', 'Private'),
        ('public', 'Public'),
        ('for_sale', 'For Sale'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Ownership and Source
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trained_models')
    training_job = models.OneToOneField(TrainingJob, on_delete=models.CASCADE, related_name='trained_model')
    
    # Model Information
    algorithm = models.ForeignKey(MLAlgorithm, on_delete=models.CASCADE, related_name='trained_models')
    source_dataset = models.ForeignKey('datasets.Dataset', on_delete=models.CASCADE, related_name='trained_models')
    
    # Model Files
    model_file = models.FileField(upload_to='trained_models/')
    model_size_bytes = models.BigIntegerField()
    model_format = models.CharField(max_length=50)  # pickle, joblib, onnx, etc.
    
    # Performance Metrics
    metrics = models.JSONField(default=dict)
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    
    # Marketplace
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='private')
    price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )
    
    # Usage Statistics
    download_count = models.PositiveIntegerField(default=0)
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00')
    )
    rating_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ml_trained_models'
        verbose_name = 'Trained Model'
        verbose_name_plural = 'Trained Models'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.algorithm.name})"
    
    @property
    def is_public(self):
        return self.status in ['public', 'for_sale']
    
    @property
    def model_size_human(self):
        """Return human-readable model size."""
        from core.utils import format_file_size
        return format_file_size(self.model_size_bytes)


class ModelInference(models.Model):
    """
    Model inference requests and results.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='model_inferences')
    model = models.ForeignKey(TrainedModel, on_delete=models.CASCADE, related_name='inferences')
    
    # Input Data
    input_data = models.JSONField()
    input_file = models.FileField(upload_to='inference_inputs/', null=True, blank=True)
    
    # Processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    predictions = models.JSONField(default=dict, blank=True)
    confidence_scores = models.JSONField(default=dict, blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Error Information
    error_message = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ml_model_inferences'
        verbose_name = 'Model Inference'
        verbose_name_plural = 'Model Inferences'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Inference for {self.model.name} by {self.user.email}"


class TrainingQueue(models.Model):
    """
    Queue management for training jobs.
    """
    training_job = models.OneToOneField(TrainingJob, on_delete=models.CASCADE, related_name='queue_entry')
    queue_position = models.PositiveIntegerField()
    estimated_start_time = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ml_training_queue'
        verbose_name = 'Training Queue Entry'
        verbose_name_plural = 'Training Queue Entries'
        ordering = ['queue_position']
    
    def __str__(self):
        return f"Queue #{self.queue_position} - {self.training_job.name}"


class ComputeResource(models.Model):
    """
    Available compute resources for ML training.
    """
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('maintenance', 'Maintenance'),
        ('offline', 'Offline'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Resource Specifications
    cpu_cores = models.PositiveIntegerField()
    memory_gb = models.PositiveIntegerField()
    gpu_count = models.PositiveIntegerField(default=0)
    gpu_type = models.CharField(max_length=100, blank=True)
    storage_gb = models.PositiveIntegerField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    current_job = models.ForeignKey(
        TrainingJob,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_resource'
    )
    
    # Usage Statistics
    total_jobs_completed = models.PositiveIntegerField(default=0)
    total_runtime_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ml_compute_resources'
        verbose_name = 'Compute Resource'
        verbose_name_plural = 'Compute Resources'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.cpu_cores}C/{self.memory_gb}GB)"
    
    @property
    def is_available(self):
        return self.status == 'available' and self.current_job is None
