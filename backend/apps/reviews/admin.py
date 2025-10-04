"""
Review admin interface.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Review, ReviewFilter, ReviewHelpful, ReviewReport, ReviewModeration


@admin.register(ReviewFilter)
class ReviewFilterAdmin(admin.ModelAdmin):
    list_display = ['name', 'filter_type', 'severity', 'action', 'is_active', 'created_at']
    list_filter = ['filter_type', 'severity', 'action', 'is_active']
    search_fields = ['name', 'pattern']
    ordering = ['-created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'reviewer_info', 'dataset_info', 'rating', 'status_badge', 
        'is_verified_purchase', 'helpful_count', 'report_count', 'created_at'
    ]
    list_filter = [
        'status', 'rating', 'is_verified_purchase', 'content_type', 
        'is_featured', 'created_at'
    ]
    search_fields = ['title', 'comment', 'reviewer__username', 'dataset__title']
    readonly_fields = [
        'id', 'filter_score', 'flagged_reasons', 'auto_moderation_notes',
        'helpful_count', 'report_count', 'created_at', 'updated_at'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'reviewer', 'content_type', 'dataset', 'reviewed_user')
        }),
        ('Review Content', {
            'fields': ('rating', 'title', 'comment')
        }),
        ('Verification', {
            'fields': ('is_verified_purchase', 'purchase_date')
        }),
        ('Status & Moderation', {
            'fields': ('status', 'is_featured', 'moderator', 'moderation_notes', 'moderated_at')
        }),
        ('Automatic Filtering', {
            'fields': ('filter_score', 'flagged_reasons', 'auto_moderation_notes'),
            'classes': ('collapse',)
        }),
        ('Engagement', {
            'fields': ('helpful_count', 'report_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_reviews', 'reject_reviews', 'flag_reviews', 'feature_reviews']
    
    def reviewer_info(self, obj):
        """Display reviewer information."""
        verified = "✓" if obj.is_verified_purchase else "○"
        return format_html(
            '<strong>{}</strong><br><small>{} {}</small>',
            obj.reviewer.username,
            obj.reviewer.email,
            verified
        )
    reviewer_info.short_description = 'Reviewer'
    
    def dataset_info(self, obj):
        """Display dataset information."""
        if obj.dataset:
            return format_html(
                '<strong>{}</strong><br><small>Rating: {}/5</small>',
                obj.dataset.title[:30] + '...' if len(obj.dataset.title) > 30 else obj.dataset.title,
                obj.dataset.rating_average
            )
        return '-'
    dataset_info.short_description = 'Dataset'
    
    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'auto_approved': 'lightgreen',
            'rejected': 'red',
            'flagged': 'darkred'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def approve_reviews(self, request, queryset):
        """Bulk approve reviews."""
        count = 0
        for review in queryset:
            if review.status in ['pending', 'flagged']:
                review.approve(moderator=request.user)
                count += 1
        
        self.message_user(request, f'{count} reviews approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def reject_reviews(self, request, queryset):
        """Bulk reject reviews."""
        count = 0
        for review in queryset:
            if review.status in ['pending', 'flagged']:
                review.reject(moderator=request.user, reason="Bulk rejection by admin")
                count += 1
        
        self.message_user(request, f'{count} reviews rejected.')
    reject_reviews.short_description = "Reject selected reviews"
    
    def flag_reviews(self, request, queryset):
        """Bulk flag reviews for manual review."""
        count = queryset.filter(status__in=['pending', 'approved', 'auto_approved']).update(
            status='flagged',
            moderator=request.user,
            moderated_at=timezone.now()
        )
        self.message_user(request, f'{count} reviews flagged.')
    flag_reviews.short_description = "Flag selected reviews"
    
    def feature_reviews(self, request, queryset):
        """Mark reviews as featured."""
        count = queryset.filter(status__in=['approved', 'auto_approved']).update(
            is_featured=True
        )
        self.message_user(request, f'{count} reviews marked as featured.')
    feature_reviews.short_description = "Feature selected reviews"


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review_info', 'user', 'is_helpful', 'created_at']
    list_filter = ['is_helpful', 'created_at']
    search_fields = ['review__title', 'user__username']
    
    def review_info(self, obj):
        """Display review information."""
        return f"{obj.review.title[:30]}... ({obj.review.rating}/5)"
    review_info.short_description = 'Review'


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['review_info', 'reporter', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['review__title', 'reporter__username', 'description']
    
    def review_info(self, obj):
        """Display review information."""
        return f"{obj.review.title[:30]}... by {obj.review.reviewer.username}"
    review_info.short_description = 'Review'


@admin.register(ReviewModeration)
class ReviewModerationAdmin(admin.ModelAdmin):
    list_display = ['review_info', 'moderator', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['review__title', 'moderator__username', 'reason']
    
    def review_info(self, obj):
        """Display review information."""
        return f"{obj.review.title[:30]}..."
    review_info.short_description = 'Review'
