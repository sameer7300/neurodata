"""
Serializers for datasets app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from decimal import Decimal
from .models import (
    Dataset, Category, Tag, DatasetVersion, DatasetReview, 
    DatasetAccess, DatasetCollection
)
from .utils import validate_dataset_file, generate_dataset_preview, calculate_file_hash
from core.utils import format_file_size
import os

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for dataset categories.
    """
    full_name = serializers.ReadOnlyField()
    dataset_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'icon', 'parent', 
            'full_name', 'dataset_count', 'is_active', 'created_at'
        )
        read_only_fields = ('created_at',)
    
    def get_dataset_count(self, obj):
        """Get count of datasets in this category."""
        return obj.datasets.filter(status='approved').count()


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset tags.
    """
    dataset_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'color', 'dataset_count', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_dataset_count(self, obj):
        """Get count of datasets with this tag."""
        return obj.datasets.filter(status='approved').count()


class DatasetVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset versions.
    """
    file_size_human = serializers.SerializerMethodField()
    
    class Meta:
        model = DatasetVersion
        fields = (
            'id', 'version', 'file', 'file_size', 'file_size_human',
            'file_hash', 'ipfs_hash', 'changelog', 'is_current', 'created_at'
        )
        read_only_fields = ('file_size', 'file_hash', 'ipfs_hash', 'created_at')
    
    def get_file_size_human(self, obj):
        """Get human-readable file size."""
        return format_file_size(obj.file_size)


class DatasetReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset reviews.
    """
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True)
    reviewer_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = DatasetReview
        fields = (
            'id', 'rating', 'title', 'comment', 'reviewer_name', 'reviewer_avatar',
            'is_approved', 'created_at', 'updated_at'
        )
        read_only_fields = ('reviewer_name', 'reviewer_avatar', 'is_approved', 'created_at', 'updated_at')
    
    def get_reviewer_avatar(self, obj):
        """Get reviewer avatar URL."""
        if hasattr(obj.reviewer, 'profile') and obj.reviewer.profile.avatar:
            return obj.reviewer.profile.avatar.url
        return None
    
    def create(self, validated_data):
        """Create review with current user as reviewer."""
        validated_data['reviewer'] = self.context['request'].user
        validated_data['dataset'] = self.context['dataset']
        return super().create(validated_data)


class DatasetListSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset list view (minimal data).
    """
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    file_size_human = serializers.ReadOnlyField()
    is_free = serializers.ReadOnlyField()
    review_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = (
            'id', 'title', 'slug', 'description', 'owner_name', 'category_name',
            'tags', 'price', 'is_free', 'file_size', 'file_size_human', 'file_type',
            'rating_average', 'rating_count', 'download_count', 'is_public', 'created_at',
            'review_stats'
        )
    
    def get_review_stats(self, obj):
        """Get review statistics from the review system."""
        try:
            from apps.reviews.utils import ReviewAnalytics
            stats = ReviewAnalytics.get_review_stats(dataset_id=obj.id)
            return {
                'total_reviews': stats.get('total_reviews', 0),
                'average_rating': stats.get('average_rating', 0),
                'verified_percentage': stats.get('verified_percentage', 0)
            }
        except Exception:
            # Fallback to dataset model values
            return {
                'total_reviews': obj.rating_count or 0,
                'average_rating': obj.rating_average or 0,
                'verified_percentage': 0
            }


class DatasetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset detail view (complete data).
    """
    owner = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    versions = DatasetVersionSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    file_size_human = serializers.ReadOnlyField()
    is_free = serializers.ReadOnlyField()
    is_published = serializers.ReadOnlyField()
    can_download = serializers.SerializerMethodField()
    has_purchased = serializers.SerializerMethodField()
    escrow = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Dataset
        fields = (
            'id', 'title', 'slug', 'description', 'owner', 'category', 'tags',
            'file_name', 'file_size', 'file_size_human', 'file_type', 'file_hash',
            'ipfs_hash', 'price', 'license_type', 'license_text', 'sample_data',
            'schema_info', 'statistics', 'status', 'rating_average', 'rating_count',
            'download_count', 'view_count', 'keywords', 'versions', 'reviews',
            'can_download', 'is_favorited', 'is_public', 'is_published', 'is_free', 
            'has_purchased', 'escrow', 'created_at', 'updated_at', 'published_at'
        )
    
    def get_owner(self, obj):
        """Get owner information."""
        return {
            'id': str(obj.owner.id),
            'username': obj.owner.username,
            'email': obj.owner.email if obj.owner == self.context['request'].user else None,
            'avatar': obj.owner.profile.avatar.url if hasattr(obj.owner, 'profile') and obj.owner.profile.avatar else None,
            'reputation_score': str(obj.owner.profile.reputation_score) if hasattr(obj.owner, 'profile') else '0.00',
            'is_verified': obj.owner.profile.is_verified if hasattr(obj.owner, 'profile') else False,
        }
    
    def get_reviews(self, obj):
        """Get recent reviews."""
        reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        return DatasetReviewSerializer(reviews, many=True).data
    
    def get_can_download(self, obj):
        """Check if current user can download this dataset."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_free
        
        # Owner can always download
        if obj.owner == request.user:
            return True
        
        # Free datasets can be downloaded by anyone
        if obj.is_free:
            return True
        
        # Check if user has purchased this dataset
        from apps.marketplace.models import Purchase
        return Purchase.objects.filter(
            buyer=request.user,
            dataset=obj,
            status='completed'
        ).exists()
    
    def get_has_purchased(self, obj):
        """Check if current user has purchased this dataset."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        if obj.owner == request.user:
            return True
        
        from apps.marketplace.models import Purchase
        return Purchase.objects.filter(
            buyer=request.user,
            dataset=obj,
            status='completed'
        ).exists()
    
    def get_escrow(self, obj):
        """Get escrow information for current user's purchase."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        from apps.marketplace.models import Purchase, Escrow
        
        # Find user's purchase of this dataset
        purchase = Purchase.objects.filter(
            buyer=request.user,
            dataset=obj,
            status='completed'
        ).first()
        
        if not purchase:
            return None
        
        # Check if escrow exists for this purchase
        try:
            escrow = purchase.escrow
            return {
                'id': str(escrow.id),
                'status': escrow.status,
                'buyer_confirmed': escrow.buyer_confirmed,
                'seller_delivered': escrow.seller_delivered,
                'created_at': escrow.created_at.isoformat(),
                'auto_release_time': escrow.auto_release_time.isoformat() if escrow.auto_release_time else None,
                'dispute_reason': escrow.dispute_reason,
                'can_confirm': escrow.status == 'active' and escrow.seller_delivered and not escrow.buyer_confirmed,
                'can_dispute': escrow.can_dispute,
                'can_auto_release': escrow.can_auto_release,
                'dispute_status': 'open' if escrow.status == 'disputed' else 'closed'
            }
        except Escrow.DoesNotExist:
            return None
    
    def get_is_favorited(self, obj):
        """Check if current user has favorited this dataset."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        try:
            profile = request.user.profile
            return profile.favorite_datasets.filter(id=obj.id).exists()
        except:
            return False


class DatasetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset creation.
    """
    file = serializers.FileField(write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Dataset
        fields = (
            'title', 'description', 'category', 'tags', 'file', 'price',
            'license_type', 'license_text', 'keywords', 'is_public'
        )
    
    def validate(self, attrs):
        """Custom validation for the dataset."""
        # If no tags provided but keywords exist, that's fine
        if not attrs.get('tags') and not attrs.get('keywords'):
            # At least one should be provided for discoverability
            pass  # We'll allow empty for now
        
        return attrs
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 500MB)
        max_size = 500 * 1024 * 1024  # 500MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size too large. Maximum size is {format_file_size(max_size)}."
            )
        
        # Validate file type - expand to support more data formats
        allowed_extensions = [
            # Structured data
            '.csv', '.json', '.parquet', '.xlsx', '.xls', '.tsv', '.txt',
            # Images (for computer vision datasets)
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            # Archives (for dataset collections)
            '.zip', '.tar', '.gz', '.rar',
            # Other data formats
            '.xml', '.yaml', '.yml', '.h5', '.hdf5', '.pkl', '.pickle'
        ]
        file_ext = os.path.splitext(value.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file type '{file_ext}'. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def validate_price(self, value):
        """Validate dataset price."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        
        # Maximum price limit
        max_price = Decimal('10000.00000000')  # 10,000 NRC
        if value > max_price:
            raise serializers.ValidationError(f"Price cannot exceed {max_price} NRC.")
        
        return value
    
    def create(self, validated_data):
        """Create dataset with file processing."""
        file = validated_data.pop('file')
        tags = validated_data.pop('tags', [])
        
        # Set owner
        validated_data['owner'] = self.context['request'].user
        
        # Generate file metadata
        validated_data['file_name'] = file.name
        validated_data['file_size'] = file.size
        validated_data['file_type'] = os.path.splitext(file.name)[1].lower().replace('.', '')
        
        # Calculate file hash
        file_hash = calculate_file_hash(file.read())
        file.seek(0)  # Reset file pointer
        
        # Check for duplicate files
        from .models import Dataset
        existing_dataset = Dataset.objects.filter(file_hash=file_hash).first()
        if existing_dataset:
            raise serializers.ValidationError({
                'file': f'This file has already been uploaded. Existing dataset: "{existing_dataset.title}" by {existing_dataset.owner.username}'
            })
        
        validated_data['file_hash'] = file_hash
        
        # Generate slug from title
        from django.utils.text import slugify
        base_slug = slugify(validated_data['title'])
        slug = base_slug
        counter = 1
        while Dataset.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        validated_data['slug'] = slug
        
        # Create dataset with approved status for development
        validated_data['status'] = 'approved'  # Auto-approve for development
        dataset = Dataset.objects.create(**validated_data)
        
        # Save file
        dataset.file.save(file.name, file, save=True)
        
        # Add tags
        if tags:
            dataset.tags.set(tags)
        
        # Generate preview and statistics
        try:
            preview_data = generate_dataset_preview(dataset.file.path, dataset.file_type)
            dataset.sample_data = preview_data.get('sample_data', {})
            dataset.schema_info = preview_data.get('schema_info', {})
            dataset.statistics = preview_data.get('statistics', {})
            dataset.save()
        except Exception as e:
            # Log error but don't fail the upload
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error generating dataset preview: {str(e)}")
        
        return dataset


class DatasetUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset updates.
    """
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Dataset
        fields = (
            'title', 'description', 'category', 'tags', 'price',
            'license_type', 'license_text', 'keywords'
        )
    
    def validate_price(self, value):
        """Validate dataset price."""
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        
        max_price = Decimal('10000.00000000')
        if value > max_price:
            raise serializers.ValidationError(f"Price cannot exceed {max_price} NRC.")
        
        return value
    
    def update(self, instance, validated_data):
        """Update dataset."""
        tags = validated_data.pop('tags', None)
        
        # Update fields
        for field, value in validated_data.items():
            setattr(instance, field, value)
        
        # Update slug if title changed
        if 'title' in validated_data:
            from django.utils.text import slugify
            base_slug = slugify(validated_data['title'])
            slug = base_slug
            counter = 1
            while Dataset.objects.filter(slug=slug).exclude(id=instance.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = slug
        
        instance.save()
        
        # Update tags
        if tags is not None:
            instance.tags.set(tags)
        
        return instance


class DatasetCollectionSerializer(serializers.ModelSerializer):
    """
    Serializer for dataset collections.
    """
    datasets = DatasetListSerializer(many=True, read_only=True)
    dataset_ids = serializers.PrimaryKeyRelatedField(
        queryset=Dataset.objects.filter(status='approved'),
        many=True,
        write_only=True,
        source='datasets'
    )
    dataset_count = serializers.ReadOnlyField()
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = DatasetCollection
        fields = (
            'id', 'name', 'slug', 'description', 'owner_name', 'datasets',
            'dataset_ids', 'dataset_count', 'is_public', 'created_at', 'updated_at'
        )
        read_only_fields = ('owner_name', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create collection with current user as owner."""
        validated_data['owner'] = self.context['request'].user
        
        # Generate slug
        from django.utils.text import slugify
        base_slug = slugify(validated_data['name'])
        slug = base_slug
        counter = 1
        while DatasetCollection.objects.filter(
            owner=validated_data['owner'], 
            slug=slug
        ).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        validated_data['slug'] = slug
        
        return super().create(validated_data)


class DatasetSearchSerializer(serializers.Serializer):
    """
    Serializer for dataset search parameters.
    """
    q = serializers.CharField(required=False, help_text="Search query")
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        help_text="Filter by category"
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        help_text="Filter by tags"
    )
    price_min = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False,
        help_text="Minimum price"
    )
    price_max = serializers.DecimalField(
        max_digits=20, decimal_places=8, required=False,
        help_text="Maximum price"
    )
    file_type = serializers.ChoiceField(
        choices=[('csv', 'CSV'), ('json', 'JSON'), ('parquet', 'Parquet'), ('xlsx', 'Excel')],
        required=False,
        help_text="Filter by file type"
    )
    is_free = serializers.BooleanField(required=False, help_text="Show only free datasets")
    sort_by = serializers.ChoiceField(
        choices=[
            ('created_at', 'Newest'),
            ('-created_at', 'Oldest'),
            ('title', 'Title A-Z'),
            ('-title', 'Title Z-A'),
            ('price', 'Price Low-High'),
            ('-price', 'Price High-Low'),
            ('-download_count', 'Most Downloaded'),
            ('-rating_average', 'Highest Rated'),
            ('-view_count', 'Most Viewed')
        ],
        default='-created_at',
        help_text="Sort order"
    )


class DatasetStatsSerializer(serializers.Serializer):
    """
    Serializer for dataset statistics.
    """
    total_datasets = serializers.IntegerField()
    total_downloads = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=20, decimal_places=8)
    avg_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    popular_categories = serializers.ListField()
    recent_activity = serializers.ListField()
