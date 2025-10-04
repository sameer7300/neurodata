"""
Filters for datasets app.
"""
import django_filters
from django.db.models import Q
from .models import Dataset, Category, Tag


class DatasetFilter(django_filters.FilterSet):
    """
    Filter class for datasets with advanced filtering options.
    """
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        label='Category'
    )
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
        label='Category Slug'
    )
    
    # Tag filters
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        label='Tags'
    )
    tag_slugs = django_filters.CharFilter(
        method='filter_tag_slugs',
        label='Tag Slugs (comma-separated)'
    )
    
    # Price filters
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum Price'
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum Price'
    )
    is_free = django_filters.BooleanFilter(
        method='filter_is_free',
        label='Free Datasets Only'
    )
    
    # File type filters
    file_type = django_filters.ChoiceFilter(
        choices=[
            ('csv', 'CSV'),
            ('json', 'JSON'),
            ('parquet', 'Parquet'),
            ('xlsx', 'Excel'),
            ('tsv', 'TSV')
        ],
        label='File Type'
    )
    
    # Size filters
    file_size_min = django_filters.NumberFilter(
        field_name='file_size',
        lookup_expr='gte',
        label='Minimum File Size (bytes)'
    )
    file_size_max = django_filters.NumberFilter(
        field_name='file_size',
        lookup_expr='lte',
        label='Maximum File Size (bytes)'
    )
    
    # Rating filters
    rating_min = django_filters.NumberFilter(
        field_name='rating_average',
        lookup_expr='gte',
        label='Minimum Rating'
    )
    min_reviews = django_filters.NumberFilter(
        field_name='rating_count',
        lookup_expr='gte',
        label='Minimum Number of Reviews'
    )
    
    # Popularity filters
    min_downloads = django_filters.NumberFilter(
        field_name='download_count',
        lookup_expr='gte',
        label='Minimum Downloads'
    )
    min_views = django_filters.NumberFilter(
        field_name='view_count',
        lookup_expr='gte',
        label='Minimum Views'
    )
    
    # License filters
    license_type = django_filters.ChoiceFilter(
        choices=Dataset.LICENSE_CHOICES,
        label='License Type'
    )
    
    # Date filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created Before'
    )
    
    # Owner filters
    owner = django_filters.CharFilter(
        field_name='owner__username',
        lookup_expr='icontains',
        label='Owner Username'
    )
    verified_owners_only = django_filters.BooleanFilter(
        method='filter_verified_owners',
        label='Verified Owners Only'
    )
    
    # Sorting
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('title', 'title'),
            ('price', 'price'),
            ('download_count', 'download_count'),
            ('rating_average', 'rating_average'),
            ('view_count', 'view_count'),
            ('file_size', 'file_size'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'title': 'Title',
            'price': 'Price',
            'download_count': 'Downloads',
            'rating_average': 'Rating',
            'view_count': 'Views',
            'file_size': 'File Size',
        }
    )
    
    class Meta:
        model = Dataset
        fields = []
    
    def filter_search(self, queryset, name, value):
        """
        Full-text search across multiple fields.
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(keywords__icontains=value) |
            Q(tags__name__icontains=value)
        ).distinct()
    
    def filter_tag_slugs(self, queryset, name, value):
        """
        Filter by comma-separated tag slugs.
        """
        if not value:
            return queryset
        
        tag_slugs = [slug.strip() for slug in value.split(',')]
        return queryset.filter(tags__slug__in=tag_slugs).distinct()
    
    def filter_is_free(self, queryset, name, value):
        """
        Filter for free datasets.
        """
        if value is True:
            return queryset.filter(price=0)
        elif value is False:
            return queryset.filter(price__gt=0)
        return queryset
    
    def filter_verified_owners(self, queryset, name, value):
        """
        Filter datasets by verified owners only.
        """
        if value is True:
            return queryset.filter(owner__profile__verification_status='verified')
        return queryset


class CategoryFilter(django_filters.FilterSet):
    """
    Filter class for categories.
    """
    
    search = django_filters.CharFilter(
        method='filter_search',
        label='Search Categories'
    )
    
    parent = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(is_active=True),
        label='Parent Category'
    )
    
    has_datasets = django_filters.BooleanFilter(
        method='filter_has_datasets',
        label='Has Datasets'
    )
    
    class Meta:
        model = Category
        fields = ['is_active']
    
    def filter_search(self, queryset, name, value):
        """Search categories by name and description."""
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )
    
    def filter_has_datasets(self, queryset, name, value):
        """Filter categories that have datasets."""
        if value is True:
            return queryset.filter(datasets__status='approved').distinct()
        return queryset


class TagFilter(django_filters.FilterSet):
    """
    Filter class for tags.
    """
    
    search = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Search Tags'
    )
    
    color = django_filters.CharFilter(
        field_name='color',
        lookup_expr='exact',
        label='Tag Color'
    )
    
    popular = django_filters.BooleanFilter(
        method='filter_popular',
        label='Popular Tags Only'
    )
    
    class Meta:
        model = Tag
        fields = []
    
    def filter_popular(self, queryset, name, value):
        """Filter popular tags (used by many datasets)."""
        if value is True:
            return queryset.filter(datasets__status='approved').annotate(
                dataset_count=django_filters.Count('datasets')
            ).filter(dataset_count__gte=5).distinct()
        return queryset


class DatasetReviewFilter(django_filters.FilterSet):
    """
    Filter class for dataset reviews.
    """
    
    rating = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='exact',
        label='Rating'
    )
    
    rating_min = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='gte',
        label='Minimum Rating'
    )
    
    rating_max = django_filters.NumberFilter(
        field_name='rating',
        lookup_expr='lte',
        label='Maximum Rating'
    )
    
    has_comment = django_filters.BooleanFilter(
        method='filter_has_comment',
        label='Has Comment'
    )
    
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created After'
    )
    
    class Meta:
        model = Dataset
        fields = ['is_approved']
    
    def filter_has_comment(self, queryset, name, value):
        """Filter reviews that have comments."""
        if value is True:
            return queryset.exclude(comment='')
        elif value is False:
            return queryset.filter(comment='')
        return queryset
