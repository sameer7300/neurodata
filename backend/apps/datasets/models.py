"""
Dataset models for NeuroData marketplace.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid
import os

User = get_user_model()


class Category(models.Model):
    """
    Dataset categories for organization.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome icon class
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dataset_categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def full_name(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class Tag(models.Model):
    """
    Tags for dataset classification.
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dataset_tags'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Dataset(models.Model):
    """
    Main dataset model.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ]
    
    LICENSE_CHOICES = [
        ('cc0', 'CC0 - Public Domain'),
        ('cc_by', 'CC BY - Attribution'),
        ('cc_by_sa', 'CC BY-SA - Attribution-ShareAlike'),
        ('cc_by_nc', 'CC BY-NC - Attribution-NonCommercial'),
        ('mit', 'MIT License'),
        ('apache', 'Apache License 2.0'),
        ('custom', 'Custom License'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    
    # Ownership and Classification
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='datasets')
    tags = models.ManyToManyField(Tag, blank=True, related_name='datasets')
    
    # File Information
    file = models.FileField(upload_to='datasets/', null=True, blank=True)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  # Size in bytes
    file_type = models.CharField(max_length=50)  # csv, json, parquet, etc.
    file_hash = models.CharField(max_length=64, unique=True)  # SHA-256 hash
    
    # IPFS Storage
    ipfs_hash = models.CharField(max_length=100, blank=True)
    ipfs_url = models.URLField(blank=True)
    
    # Pricing and Licensing
    price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000'),
        validators=[MinValueValidator(Decimal('0.00000000'))]
    )
    license_type = models.CharField(max_length=20, choices=LICENSE_CHOICES, default='cc_by')
    license_text = models.TextField(blank=True)
    
    # Metadata
    sample_data = models.JSONField(default=dict, blank=True)  # Preview data
    schema_info = models.JSONField(default=dict, blank=True)  # Column info, data types
    statistics = models.JSONField(default=dict, blank=True)   # Row count, file size, etc.
    
    # Privacy and Visibility
    is_public = models.BooleanField(
        default=True,
        help_text="Whether this dataset is publicly visible to all users"
    )
    
    # Status and Moderation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)
    
    # Engagement Metrics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    rating_average = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    rating_count = models.PositiveIntegerField(default=0)
    
    # SEO and Discovery
    keywords = models.TextField(blank=True, help_text="Comma-separated keywords for search")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'datasets'
        verbose_name = 'Dataset'
        verbose_name_plural = 'Datasets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['file_hash']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def is_free(self):
        return self.price == 0
    
    @property
    def is_published(self):
        return self.status == 'approved' and self.published_at is not None
    
    @property
    def file_size_human(self):
        """Return human-readable file size."""
        from core.utils import format_file_size
        return format_file_size(self.file_size)
    
    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def calculate_rating(self):
        """Recalculate average rating from reviews."""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            self.rating_average = reviews.aggregate(
                avg_rating=models.Avg('rating')
            )['avg_rating'] or Decimal('0.00')
            self.rating_count = reviews.count()
        else:
            self.rating_average = Decimal('0.00')
            self.rating_count = 0
        self.save(update_fields=['rating_average', 'rating_count'])
    
    def generate_preview_data(self, max_rows=10):
        """Generate preview data for the dataset."""
        if not self.file:
            return None
            
        try:
            import pandas as pd
            import json
            
            file_path = self.file.path
            
            # Read data based on file type
            if self.file_type.lower() == 'csv':
                df = pd.read_csv(file_path, nrows=max_rows)
            elif self.file_type.lower() == 'json':
                df = pd.read_json(file_path, lines=True).head(max_rows)
            elif self.file_type.lower() in ['xlsx', 'xls']:
                df = pd.read_excel(file_path, nrows=max_rows)
            else:
                return None
            
            # Convert to JSON-serializable format
            preview_data = {
                'columns': df.columns.tolist(),
                'data': df.fillna('').to_dict('records'),
                'total_rows_preview': len(df),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            return preview_data
            
        except Exception as e:
            print(f"Error generating preview for dataset {self.id}: {e}")
            return None
    
    def generate_statistics(self):
        """Generate comprehensive dataset statistics."""
        if not self.file:
            return {}
            
        try:
            import pandas as pd
            
            file_path = self.file.path
            
            # Read full dataset for statistics
            if self.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif self.file_type.lower() == 'json':
                df = pd.read_json(file_path, lines=True)
            elif self.file_type.lower() in ['xlsx', 'xls']:
                df = pd.read_excel(file_path)
            else:
                return {}
            
            # Calculate statistics
            stats = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'file_size_bytes': self.file_size,
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
                'missing_values': df.isnull().sum().to_dict(),
                'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
                'categorical_columns': df.select_dtypes(include=['object']).columns.tolist(),
                'datetime_columns': df.select_dtypes(include=['datetime']).columns.tolist(),
            }
            
            # Add basic statistics for numeric columns
            numeric_stats = {}
            for col in stats['numeric_columns']:
                try:
                    numeric_stats[col] = {
                        'mean': float(df[col].mean()),
                        'median': float(df[col].median()),
                        'std': float(df[col].std()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'unique_count': int(df[col].nunique())
                    }
                except:
                    pass
            
            stats['numeric_statistics'] = numeric_stats
            
            return stats
            
        except Exception as e:
            print(f"Error generating statistics for dataset {self.id}: {e}")
            return {}
    
    def update_metadata(self):
        """Update sample_data and statistics fields."""
        self.sample_data = self.generate_preview_data() or {}
        self.statistics = self.generate_statistics()
        self.save(update_fields=['sample_data', 'statistics'])


class DatasetVersion(models.Model):
    """
    Version control for datasets.
    """
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='versions')
    version = models.CharField(max_length=20)  # e.g., "1.0", "1.1", "2.0"
    
    # File Information
    file = models.FileField(upload_to='dataset_versions/')
    file_size = models.BigIntegerField()
    file_hash = models.CharField(max_length=64)
    ipfs_hash = models.CharField(max_length=100, blank=True)
    
    # Version Details
    changelog = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dataset_versions'
        verbose_name = 'Dataset Version'
        verbose_name_plural = 'Dataset Versions'
        unique_together = ['dataset', 'version']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.dataset.title} v{self.version}"
    
    def save(self, *args, **kwargs):
        if self.is_current:
            # Set all other versions of this dataset to not current
            DatasetVersion.objects.filter(
                dataset=self.dataset
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class DatasetReview(models.Model):
    """
    User reviews and ratings for datasets.
    """
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dataset_reviews')
    
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField(blank=True)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dataset_reviews'
        verbose_name = 'Dataset Review'
        verbose_name_plural = 'Dataset Reviews'
        unique_together = ['dataset', 'reviewer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.reviewer.email} - {self.dataset.title} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate dataset rating
        self.dataset.calculate_rating()


class DatasetAccess(models.Model):
    """
    Track dataset access and downloads.
    """
    ACCESS_TYPES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('preview', 'Preview'),
    ]
    
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dataset_accesses')
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    
    # Request Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'dataset_access_logs'
        verbose_name = 'Dataset Access'
        verbose_name_plural = 'Dataset Accesses'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['dataset', 'access_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.email} {self.access_type} {self.dataset.title}"


class DatasetCollection(models.Model):
    """
    User-created collections of datasets.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    datasets = models.ManyToManyField(Dataset, blank=True, related_name='collections')
    
    is_public = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dataset_collections'
        verbose_name = 'Dataset Collection'
        verbose_name_plural = 'Dataset Collections'
        unique_together = ['owner', 'slug']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.owner.email} - {self.name}"
    
    @property
    def dataset_count(self):
        return self.datasets.count()
