"""
Admin configuration for datasets app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Dataset, Category, Tag, DatasetVersion, DatasetReview, 
    DatasetAccess, DatasetCollection
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    
    list_display = ('name', 'slug', 'parent', 'dataset_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'icon')
        }),
        ('Hierarchy', {
            'fields': ('parent',)
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
    )
    
    def dataset_count(self, obj):
        """Get count of datasets in this category."""
        count = obj.datasets.filter(status='approved').count()
        if count > 0:
            url = reverse('admin:datasets_dataset_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} datasets</a>', url, count)
        return '0 datasets'
    dataset_count.short_description = 'Datasets'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""
    
    list_display = ('name', 'slug', 'color_display', 'dataset_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    
    def color_display(self, obj):
        """Display color as a colored box."""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc;"></div>',
            obj.color
        )
    color_display.short_description = 'Color'
    
    def dataset_count(self, obj):
        """Get count of datasets with this tag."""
        count = obj.datasets.filter(status='approved').count()
        if count > 0:
            url = reverse('admin:datasets_dataset_changelist') + f'?tags__id__exact={obj.id}'
            return format_html('<a href="{}">{} datasets</a>', url, count)
        return '0 datasets'
    dataset_count.short_description = 'Datasets'


class DatasetVersionInline(admin.TabularInline):
    """Inline admin for dataset versions."""
    model = DatasetVersion
    extra = 0
    readonly_fields = ('file_size', 'file_hash', 'created_at')
    fields = ('version', 'file', 'file_size', 'changelog', 'is_current', 'created_at')


class DatasetReviewInline(admin.TabularInline):
    """Inline admin for dataset reviews."""
    model = DatasetReview
    extra = 0
    readonly_fields = ('reviewer', 'rating', 'created_at')
    fields = ('reviewer', 'rating', 'title', 'comment', 'is_approved', 'created_at')


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model."""
    
    list_display = (
        'title', 'owner', 'category', 'status', 'price', 'is_free',
        'download_count', 'rating_display', 'created_at'
    )
    list_filter = (
        'status', 'category', 'tags', 'license_type', 'created_at'
    )
    search_fields = ('title', 'description', 'owner__username', 'owner__email')
    readonly_fields = (
        'slug', 'file_hash', 'file_size_human', 'download_count', 'view_count',
        'rating_average', 'rating_count', 'created_at', 'updated_at'
    )
    filter_horizontal = ('tags',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'owner')
        }),
        ('Classification', {
            'fields': ('category', 'tags', 'keywords')
        }),
        ('File Information', {
            'fields': ('file', 'file_name', 'file_size_human', 'file_type', 'file_hash')
        }),
        ('IPFS Storage', {
            'fields': ('ipfs_hash', 'ipfs_url'),
            'classes': ('collapse',)
        }),
        ('Pricing & Licensing', {
            'fields': ('price', 'license_type', 'license_text')
        }),
        ('Metadata', {
            'fields': ('sample_data', 'schema_info', 'statistics'),
            'classes': ('collapse',)
        }),
        ('Status & Moderation', {
            'fields': ('status', 'rejection_reason')
        }),
        ('Statistics', {
            'fields': ('download_count', 'view_count', 'rating_average', 'rating_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [DatasetVersionInline, DatasetReviewInline]
    
    actions = ['approve_datasets', 'reject_datasets', 'update_statistics']
    
    def is_free(self, obj):
        """Display if dataset is free."""
        return obj.price == 0
    is_free.boolean = True
    is_free.short_description = 'Free'
    
    def rating_display(self, obj):
        """Display rating with stars."""
        if obj.rating_count > 0:
            stars = '★' * int(obj.rating_average) + '☆' * (5 - int(obj.rating_average))
            return format_html(
                '{} ({:.1f}/5, {} reviews)',
                stars, obj.rating_average, obj.rating_count
            )
        return 'No ratings'
    rating_display.short_description = 'Rating'
    
    def approve_datasets(self, request, queryset):
        """Bulk approve datasets."""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} datasets approved successfully.')
    approve_datasets.short_description = 'Approve selected datasets'
    
    def reject_datasets(self, request, queryset):
        """Bulk reject datasets."""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} datasets rejected.')
    reject_datasets.short_description = 'Reject selected datasets'
    
    def update_statistics(self, request, queryset):
        """Update dataset statistics."""
        for dataset in queryset:
            dataset.calculate_rating()
        self.message_user(request, f'Statistics updated for {queryset.count()} datasets.')
    update_statistics.short_description = 'Update statistics'


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    """Admin interface for DatasetVersion model."""
    
    list_display = ('dataset', 'version', 'file_size_human', 'is_current', 'created_at')
    list_filter = ('is_current', 'created_at')
    search_fields = ('dataset__title', 'version')
    readonly_fields = ('file_size', 'file_hash', 'created_at')
    
    def file_size_human(self, obj):
        """Display human-readable file size."""
        from core.utils import format_file_size
        return format_file_size(obj.file_size)
    file_size_human.short_description = 'File Size'


@admin.register(DatasetReview)
class DatasetReviewAdmin(admin.ModelAdmin):
    """Admin interface for DatasetReview model."""
    
    list_display = (
        'dataset', 'reviewer', 'rating', 'title_short', 'is_approved', 
        'is_flagged', 'created_at'
    )
    list_filter = ('rating', 'is_approved', 'is_flagged', 'created_at')
    search_fields = ('dataset__title', 'reviewer__username', 'title', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Review Information', {
            'fields': ('dataset', 'reviewer', 'rating', 'title', 'comment')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_flagged')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_reviews', 'flag_reviews']
    
    def title_short(self, obj):
        """Display shortened title."""
        if obj.title and len(obj.title) > 50:
            return obj.title[:50] + '...'
        return obj.title or 'No title'
    title_short.short_description = 'Title'
    
    def approve_reviews(self, request, queryset):
        """Bulk approve reviews."""
        updated = queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{updated} reviews approved successfully.')
    approve_reviews.short_description = 'Approve selected reviews'
    
    def flag_reviews(self, request, queryset):
        """Bulk flag reviews."""
        updated = queryset.update(is_flagged=True)
        self.message_user(request, f'{updated} reviews flagged for review.')
    flag_reviews.short_description = 'Flag selected reviews'


@admin.register(DatasetAccess)
class DatasetAccessAdmin(admin.ModelAdmin):
    """Admin interface for DatasetAccess model."""
    
    list_display = ('dataset', 'user', 'access_type', 'ip_address', 'timestamp')
    list_filter = ('access_type', 'timestamp')
    search_fields = ('dataset__title', 'user__username', 'ip_address')
    readonly_fields = ('dataset', 'user', 'access_type', 'ip_address', 'user_agent', 'timestamp')
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DatasetCollection)
class DatasetCollectionAdmin(admin.ModelAdmin):
    """Admin interface for DatasetCollection model."""
    
    list_display = ('name', 'owner', 'dataset_count_display', 'is_public', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    filter_horizontal = ('datasets',)
    readonly_fields = ('slug', 'dataset_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'owner')
        }),
        ('Datasets', {
            'fields': ('datasets', 'dataset_count')
        }),
        ('Settings', {
            'fields': ('is_public',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def dataset_count_display(self, obj):
        """Display dataset count with link."""
        count = obj.dataset_count
        if count > 0:
            return format_html('{} datasets', count)
        return '0 datasets'
    dataset_count_display.short_description = 'Datasets'


# Customize admin site
admin.site.site_header = "NeuroData Administration"
admin.site.site_title = "NeuroData Admin"
admin.site.index_title = "Dataset Management"
