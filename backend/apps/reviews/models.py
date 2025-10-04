"""
Review models with automatic filtering and moderation.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import re

User = get_user_model()


class ReviewFilter(models.Model):
    """
    Automatic review filtering rules.
    """
    FILTER_TYPES = [
        ('profanity', 'Profanity Filter'),
        ('spam', 'Spam Detection'),
        ('sentiment', 'Negative Sentiment'),
        ('length', 'Length Validation'),
        ('keyword', 'Keyword Filter'),
    ]
    
    name = models.CharField(max_length=100)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES)
    pattern = models.TextField(help_text="Regex pattern or keywords (comma-separated)")
    is_active = models.BooleanField(default=True)
    severity = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    action = models.CharField(
        max_length=20,
        choices=[
            ('flag', 'Flag for Review'),
            ('auto_reject', 'Auto Reject'),
            ('require_approval', 'Require Approval')
        ],
        default='flag'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_filters'
        verbose_name = 'Review Filter'
        verbose_name_plural = 'Review Filters'
    
    def __str__(self):
        return f"{self.name} ({self.filter_type})"


class Review(models.Model):
    """
    Enhanced review model with automatic filtering.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('flagged', 'Flagged'),
        ('auto_approved', 'Auto Approved'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('dataset', 'Dataset Review'),
        ('seller', 'Seller Review'),
        ('platform', 'Platform Review'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='dataset')
    
    # Content References
    dataset = models.ForeignKey(
        'datasets.Dataset', 
        on_delete=models.CASCADE, 
        related_name='dataset_reviews',
        null=True, blank=True
    )
    reviewed_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews_received',
        null=True, blank=True
    )
    
    # Review Content
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200)
    comment = models.TextField()
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(null=True, blank=True)
    
    # Moderation and Filtering
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    
    # Automatic Filtering Results
    filter_score = models.FloatField(default=0.0, help_text="Automatic filter confidence score")
    flagged_reasons = models.JSONField(default=list, blank=True)
    auto_moderation_notes = models.TextField(blank=True)
    
    # Manual Moderation
    moderator = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='moderated_reviews'
    )
    moderation_notes = models.TextField(blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    # Engagement
    helpful_count = models.PositiveIntegerField(default=0)
    report_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        unique_together = [['reviewer', 'dataset'], ['reviewer', 'reviewed_user']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['dataset', 'status']),
            models.Index(fields=['rating', 'status']),
        ]
    
    def __str__(self):
        target = self.dataset.title if self.dataset else self.reviewed_user.username
        return f"{self.reviewer.username} - {target} ({self.rating}/5)"
    
    def save(self, *args, **kwargs):
        # Run automatic filtering before saving
        if not self.pk:  # Only for new reviews
            self.run_automatic_filters()
        super().save(*args, **kwargs)
    
    def run_automatic_filters(self):
        """Run automatic content filtering."""
        from .utils import ReviewFilterEngine
        
        filter_engine = ReviewFilterEngine()
        results = filter_engine.analyze_review(self)
        
        self.filter_score = results['score']
        self.flagged_reasons = results['reasons']
        self.auto_moderation_notes = results['notes']
        
        # Determine status based on filter results
        if results['score'] >= 0.8:  # High confidence problematic content
            self.status = 'rejected'
        elif results['score'] >= 0.5:  # Medium confidence
            self.status = 'flagged'
        elif results['score'] <= 0.2 and self.is_verified_purchase:  # Low risk + verified
            self.status = 'auto_approved'
        else:
            self.status = 'pending'
    
    @property
    def is_approved(self):
        return self.status in ['approved', 'auto_approved']
    
    def approve(self, moderator=None):
        """Approve the review."""
        self.status = 'approved'
        self.moderator = moderator
        self.moderated_at = timezone.now()
        self.save()
    
    def reject(self, moderator=None, reason=""):
        """Reject the review."""
        self.status = 'rejected'
        self.moderator = moderator
        self.moderated_at = timezone.now()
        if reason:
            self.moderation_notes = reason
        self.save()


class ReviewHelpful(models.Model):
    """
    Track helpful votes for reviews.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpful'
        unique_together = ['review', 'user']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update helpful count
        self.review.helpful_count = self.review.helpful_votes.filter(is_helpful=True).count()
        self.review.save(update_fields=['helpful_count'])


class ReviewReport(models.Model):
    """
    User reports for inappropriate reviews.
    """
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('inappropriate', 'Inappropriate Content'),
        ('fake', 'Fake Review'),
        ('offensive', 'Offensive Language'),
        ('irrelevant', 'Irrelevant Content'),
        ('other', 'Other'),
    ]
    
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_reports'
        unique_together = ['review', 'reporter']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update report count
        self.review.report_count = self.review.reports.count()
        self.review.save(update_fields=['report_count'])


class ReviewModeration(models.Model):
    """
    Review moderation history.
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='moderation_history')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_moderation_history'
        ordering = ['-created_at']
