"""
Review serializers.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Review, ReviewHelpful, ReviewReport
from apps.marketplace.models import Purchase

User = get_user_model()


class ReviewerSerializer(serializers.ModelSerializer):
    """Serializer for review author information."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id', 'username', 'email']


class ReviewListSerializer(serializers.ModelSerializer):
    """Serializer for review list view."""
    
    reviewer = ReviewerSerializer(read_only=True)
    dataset_title = serializers.CharField(source='dataset.title', read_only=True)
    is_helpful_by_user = serializers.SerializerMethodField()
    can_report = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'dataset_title', 'rating', 'title', 'comment',
            'is_verified_purchase', 'helpful_count', 'report_count',
            'is_helpful_by_user', 'can_report', 'created_at'
        ]
        read_only_fields = [
            'id', 'reviewer', 'dataset_title', 'is_verified_purchase',
            'helpful_count', 'report_count', 'created_at'
        ]
    
    def get_is_helpful_by_user(self, obj):
        """Check if current user marked this review as helpful."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return ReviewHelpful.objects.filter(
            review=obj,
            user=request.user,
            is_helpful=True
        ).exists()
    
    def get_can_report(self, obj):
        """Check if current user can report this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Can't report own reviews
        if obj.reviewer == request.user:
            return False
        
        # Check if already reported
        return not ReviewReport.objects.filter(
            review=obj,
            reporter=request.user
        ).exists()


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed review view."""
    
    reviewer = ReviewerSerializer(read_only=True)
    dataset_title = serializers.CharField(source='dataset.title', read_only=True)
    is_helpful_by_user = serializers.SerializerMethodField()
    can_report = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'dataset_title', 'rating', 'title', 'comment',
            'is_verified_purchase', 'purchase_date', 'helpful_count', 'report_count',
            'is_helpful_by_user', 'can_report', 'can_edit', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reviewer', 'dataset_title', 'is_verified_purchase', 'purchase_date',
            'helpful_count', 'report_count', 'created_at', 'updated_at'
        ]
    
    def get_is_helpful_by_user(self, obj):
        """Check if current user marked this review as helpful."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return ReviewHelpful.objects.filter(
            review=obj,
            user=request.user,
            is_helpful=True
        ).exists()
    
    def get_can_report(self, obj):
        """Check if current user can report this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return (obj.reviewer != request.user and 
                not ReviewReport.objects.filter(review=obj, reporter=request.user).exists())
    
    def get_can_edit(self, obj):
        """Check if current user can edit this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.reviewer == request.user


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
    
    def validate_rating(self, value):
        """Validate rating is between 1-5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_title(self, value):
        """Validate title length and content."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        return value.strip()
    
    def validate_comment(self, value):
        """Validate comment length and content."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Comment must be at least 10 characters long.")
        if len(value) > 2000:
            raise serializers.ValidationError("Comment cannot exceed 2000 characters.")
        return value.strip()
    
    def create(self, validated_data):
        """Create review with automatic verification check."""
        request = self.context['request']
        dataset = self.context['dataset']
        
        # Check if user has purchased the dataset
        purchase = Purchase.objects.filter(
            buyer=request.user,
            dataset=dataset,
            status='completed'
        ).first()
        
        review = Review.objects.create(
            reviewer=request.user,
            dataset=dataset,
            is_verified_purchase=bool(purchase),
            purchase_date=purchase.created_at if purchase else None,
            **validated_data
        )
        
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating reviews."""
    
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
    
    def validate_rating(self, value):
        """Validate rating is between 1-5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def validate_title(self, value):
        """Validate title length and content."""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters.")
        return value.strip()
    
    def validate_comment(self, value):
        """Validate comment length and content."""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Comment must be at least 10 characters long.")
        if len(value) > 2000:
            raise serializers.ValidationError("Comment cannot exceed 2000 characters.")
        return value.strip()


class ReviewHelpfulSerializer(serializers.ModelSerializer):
    """Serializer for review helpful votes."""
    
    class Meta:
        model = ReviewHelpful
        fields = ['is_helpful']


class ReviewReportSerializer(serializers.ModelSerializer):
    """Serializer for reporting reviews."""
    
    class Meta:
        model = ReviewReport
        fields = ['reason', 'description']
    
    def validate_description(self, value):
        """Validate report description."""
        if value and len(value) > 500:
            raise serializers.ValidationError("Description cannot exceed 500 characters.")
        return value


class ReviewStatsSerializer(serializers.Serializer):
    """Serializer for review statistics."""
    
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    verified_percentage = serializers.FloatField()
    
    # Rating breakdown
    five_star_count = serializers.IntegerField()
    four_star_count = serializers.IntegerField()
    three_star_count = serializers.IntegerField()
    two_star_count = serializers.IntegerField()
    one_star_count = serializers.IntegerField()
    
    # Percentages
    five_star_percentage = serializers.FloatField()
    four_star_percentage = serializers.FloatField()
    three_star_percentage = serializers.FloatField()
    two_star_percentage = serializers.FloatField()
    one_star_percentage = serializers.FloatField()


class ReviewFilterSerializer(serializers.Serializer):
    """Serializer for review filtering options."""
    
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    verified_only = serializers.BooleanField(required=False, default=False)
    sort_by = serializers.ChoiceField(
        choices=['newest', 'oldest', 'highest_rated', 'lowest_rated', 'most_helpful'],
        required=False,
        default='newest'
    )
    search = serializers.CharField(required=False, max_length=100)
