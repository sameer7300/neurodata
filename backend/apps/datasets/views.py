"""
Views for datasets app.
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Avg, Sum
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

from .models import Dataset, Category, Tag, DatasetReview, DatasetCollection
from .serializers import (
    DatasetListSerializer, DatasetDetailSerializer, DatasetCreateSerializer,
    DatasetUpdateSerializer, CategorySerializer, TagSerializer,
    DatasetReviewSerializer, DatasetCollectionSerializer, DatasetSearchSerializer,
    DatasetStatsSerializer
)
from .utils import search_datasets, generate_dataset_recommendations, get_dataset_analytics
from apps.authentication.permissions import IsVerifiedUser, HasWalletConnected
from apps.authentication.models import UserProfile
from apps.marketplace.models import Purchase
from core.permissions import IsOwnerOrReadOnly
from core.utils import create_response_data, get_client_ip
from core.pagination import CustomPageNumberPagination

import logging

logger = logging.getLogger(__name__)


class DatasetViewSet(ModelViewSet):
    """
    ViewSet for dataset CRUD operations.
    """
    queryset = Dataset.objects.all()
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DatasetListSerializer
        elif self.action == 'create':
            return DatasetCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DatasetUpdateSerializer
        return DatasetDetailSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Require authenticated and verified users to upload datasets
            permission_classes = [permissions.IsAuthenticated, IsVerifiedUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action in ['purchase', 'download']:
            permission_classes = [permissions.IsAuthenticated, HasWalletConnected]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = Dataset.objects.select_related('owner', 'category').prefetch_related('tags')
        
        if self.action == 'list':
            # Show: public approved datasets + user's own datasets + purchased datasets
            if self.request.user.is_authenticated:
                from apps.marketplace.models import Purchase
                queryset = queryset.filter(
                    Q(status='approved', is_public=True) |  # Public approved datasets
                    Q(owner=self.request.user) |            # User's own datasets (any status)
                    Q(purchases__buyer=self.request.user, purchases__status='completed')  # Purchased datasets
                ).distinct()
            else:
                # Anonymous users only see public approved datasets
                queryset = queryset.filter(status='approved', is_public=True)
        elif self.action == 'retrieve':
            # Show dataset if: public approved, owned by user, or purchased by user
            if self.request.user.is_authenticated:
                from apps.marketplace.models import Purchase
                queryset = queryset.filter(
                    Q(status='approved', is_public=True) |  # Public approved datasets
                    Q(owner=self.request.user) |            # User's own datasets
                    Q(purchases__buyer=self.request.user, purchases__status='completed')  # Purchased datasets
                ).distinct()
            else:
                # Anonymous users only see public approved datasets
                queryset = queryset.filter(status='approved', is_public=True)
        
        return queryset
    
    def retrieve(self, request, *args, **kwargs):
        """Get dataset details and increment view count."""
        instance = self.get_object()
        
        # Increment view count (only once per user per session)
        session_key = f"viewed_dataset_{instance.id}"
        if not request.session.get(session_key):
            instance.increment_view_count()
            request.session[session_key] = True
        
        serializer = self.get_serializer(instance)
        return Response(
            create_response_data(
                success=True,
                data=serializer.data
            )
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new dataset."""
        logger.info(f"Dataset creation request data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Dataset serializer validation errors: {serializer.errors}")
        
        serializer.is_valid(raise_exception=True)
        
        dataset = serializer.save()
        
        # Log dataset creation
        from apps.authentication.models import UserActivity
        UserActivity.objects.create(
            user=request.user,
            activity_type='dataset_upload',
            description=f'Uploaded dataset: {dataset.title}',
            metadata={
                'dataset_id': str(dataset.id),
                'file_size': dataset.file_size,
                'file_type': dataset.file_type
            }
        )
        
        return Response(
            create_response_data(
                success=True,
                message="Dataset uploaded successfully",
                data=DatasetDetailSerializer(dataset, context={'request': request}).data
            ),
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase a dataset."""
        dataset = self.get_object()
        
        # Check if dataset is free
        if dataset.is_free:
            return Response(
                create_response_data(
                    success=False,
                    message="This dataset is free and doesn't require purchase",
                    errors={'dataset': 'Dataset is free'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already owns this dataset
        if dataset.owner == request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You cannot purchase your own dataset",
                    errors={'dataset': 'Cannot purchase own dataset'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user has already purchased this dataset
        existing_purchase = Purchase.objects.filter(
            buyer=request.user,
            dataset=dataset,
            status='completed'
        ).first()
        
        if existing_purchase:
            return Response(
                create_response_data(
                    success=False,
                    message="You have already purchased this dataset",
                    errors={'dataset': 'Already purchased'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create purchase record
        purchase = Purchase.objects.create(
            buyer=request.user,
            dataset=dataset,
            amount=dataset.price,
            currency='NRC',
            payment_method='crypto',
            status='pending'
        )
        
        return Response(
            create_response_data(
                success=True,
                message="Purchase initiated successfully",
                data={
                    'purchase_id': str(purchase.id),
                    'amount': str(purchase.amount),
                    'currency': purchase.currency,
                    'status': purchase.status
                }
            ),
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download a dataset."""
        dataset = self.get_object()
        
        # Check if user can download this dataset
        can_download = False
        
        # Owner can always download
        if dataset.owner == request.user:
            can_download = True
        # Free datasets can be downloaded by anyone
        elif dataset.is_free:
            can_download = True
        # Check if user has purchased this dataset
        else:
            purchase = Purchase.objects.filter(
                buyer=request.user,
                dataset=dataset,
                status='completed'
            ).first()
            can_download = bool(purchase)
        
        if not can_download:
            return Response(
                create_response_data(
                    success=False,
                    message="You don't have permission to download this dataset",
                    errors={'permission': 'Purchase required'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Log download
        from .models import DatasetAccess
        DatasetAccess.objects.create(
            dataset=dataset,
            user=request.user,
            access_type='download',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Increment download count
        dataset.increment_download_count()
        
        # Return file download response
        try:
            if dataset.file and dataset.file.name:
                import os
                import mimetypes
                
                # Get the actual file path
                file_path = dataset.file.path
                
                logger.info(f"Attempting to download file: {file_path}")
                logger.info(f"Dataset file name: {dataset.file_name}")
                logger.info(f"Dataset file size in DB: {dataset.file_size}")
                
                # Check if file exists on disk
                if not os.path.exists(file_path):
                    logger.error(f"File not found on disk: {file_path}")
                    return Response(
                        create_response_data(
                            success=False,
                            message="Dataset file not found on disk",
                            errors={'file': 'File not available'}
                        ),
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                # Get file size from disk
                file_size = os.path.getsize(file_path)
                logger.info(f"Actual file size on disk: {file_size}")
                
                # Verify file is not empty
                if file_size == 0:
                    logger.error(f"File is empty: {file_path}")
                    return Response(
                        create_response_data(
                            success=False,
                            message="Dataset file is empty",
                            errors={'file': 'File is corrupted or empty'}
                        ),
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Determine content type
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'
                
                # Create a generator to stream the file
                def file_iterator(file_path, chunk_size=8192):
                    try:
                        with open(file_path, 'rb') as f:
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                yield chunk
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
                        raise
                
                # Create streaming response
                response = StreamingHttpResponse(
                    file_iterator(file_path),
                    content_type=content_type
                )
                
                # Set proper headers
                response['Content-Disposition'] = f'attachment; filename="{dataset.file_name}"'
                response['Content-Length'] = str(file_size)
                response['Accept-Ranges'] = 'bytes'
                
                logger.info(f"Successfully created download response for {dataset.file_name}")
                return response
            else:
                logger.error(f"Dataset {dataset.id} has no file attached")
                return Response(
                    create_response_data(
                        success=False,
                        message="Dataset file not found",
                        errors={'file': 'File not available'}
                    ),
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            logger.error(f"Error downloading dataset {dataset.id}: {str(e)}")
            return Response(
                create_response_data(
                    success=False,
                    message="Error downloading file",
                    errors={'download': str(e)}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get dataset analytics (owner only)."""
        dataset = self.get_object()
        
        # Only owner can view analytics
        if dataset.owner != request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You don't have permission to view analytics for this dataset",
                    errors={'permission': 'Owner only'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics_data = get_dataset_analytics(dataset)
        
        return Response(
            create_response_data(
                success=True,
                data=analytics_data
            )
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        """Toggle favorite status for a dataset."""
        dataset = self.get_object()
        
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)
        
        # Toggle favorite status
        if profile.favorite_datasets.filter(id=dataset.id).exists():
            profile.favorite_datasets.remove(dataset)
            is_favorited = False
            message = "Removed from favorites"
        else:
            profile.favorite_datasets.add(dataset)
            is_favorited = True
            message = "Added to favorites"
        
        return Response(
            create_response_data(
                success=True,
                message=message,
                data={'is_favorited': is_favorited}
            )
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def favorites(self, request):
        """Get user's favorite datasets."""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)
        
        # Get user's favorite datasets - less restrictive filtering
        all_favorites = profile.favorite_datasets.all()
        logger.info(f"User {request.user.id} has {all_favorites.count()} total favorites")
        
        for fav in all_favorites:
            logger.info(f"Favorite dataset: {fav.title}, status: {fav.status}, is_public: {fav.is_public}")
        
        # Filter for available datasets (more permissive)
        favorite_datasets = profile.favorite_datasets.filter(
            status__in=['published', 'approved'],  # Accept both published and approved
            is_public=True
        ).order_by('-created_at')[:10]  # Limit to 10 most recent
        
        logger.info(f"Filtered favorites count: {favorite_datasets.count()}")
        
        serializer = DatasetListSerializer(favorite_datasets, many=True, context={'request': request})
        
        return Response(
            create_response_data(
                success=True,
                data=serializer.data,
                message=f"Found {len(favorite_datasets)} favorite datasets"
            )
        )
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get reviews for a dataset."""
        dataset = self.get_object()
        reviews = dataset.reviews.filter(is_approved=True).order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = DatasetReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DatasetReviewSerializer(reviews, many=True)
        return Response(
            create_response_data(
                success=True,
                message="Reviews retrieved successfully",
                data=serializer.data
            )
        )

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Add a review to a dataset."""
        dataset = self.get_object()
        
        # Check if user has purchased this dataset (or it's free)
        can_review = False
        
        if dataset.is_free:
            can_review = True
        else:
            purchase = Purchase.objects.filter(
                buyer=request.user,
                dataset=dataset,
                status='completed'
            ).first()
            can_review = bool(purchase)
        
        if not can_review:
            return Response(
                create_response_data(
                    success=False,
                    message="You must purchase this dataset before reviewing it",
                    errors={'permission': 'Purchase required'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user has already reviewed this dataset
        existing_review = DatasetReview.objects.filter(
            dataset=dataset,
            reviewer=request.user
        ).first()
        
        if existing_review:
            return Response(
                create_response_data(
                    success=False,
                    message="You have already reviewed this dataset",
                    errors={'review': 'Already reviewed'}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = DatasetReviewSerializer(
            data=request.data,
            context={'request': request, 'dataset': dataset}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        return Response(
            create_response_data(
                success=True,
                message="Review added successfully",
                data=DatasetReviewSerializer(review).data
            ),
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Get dataset preview data."""
        dataset = self.get_object()
        
        # Check if user has access to preview
        # Allow preview for: owner, purchasers, or if dataset is free
        has_access = (
            dataset.owner == request.user or
            dataset.is_free or
            (request.user.is_authenticated and 
             Purchase.objects.filter(
                 buyer=request.user,
                 dataset=dataset,
                 status='completed'
             ).exists())
        )
        
        if not has_access:
            return Response(
                create_response_data(
                    success=False,
                    message="You need to purchase this dataset to view preview",
                    errors={'access': 'Purchase required for preview'}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate preview if not exists
        if not dataset.sample_data:
            dataset.update_metadata()
        
        preview_data = {
            'sample_data': dataset.sample_data,
            'statistics': dataset.statistics,
            'schema_info': dataset.schema_info,
            'file_info': {
                'name': dataset.file_name,
                'size': dataset.file_size,
                'type': dataset.file_type,
                'size_human': dataset.file_size_human
            }
        }
        
        return Response(
            create_response_data(
                success=True,
                data=preview_data
            )
        )
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get dataset reviews."""
        dataset = self.get_object()
        reviews = dataset.reviews.filter(is_approved=True).order_by('-created_at')
        
        # Paginate reviews
        paginator = CustomPageNumberPagination()
        page = paginator.paginate_queryset(reviews, request)
        
        if page is not None:
            serializer = DatasetReviewSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = DatasetReviewSerializer(reviews, many=True)
        return Response(
            create_response_data(
                success=True,
                data=serializer.data
            )
        )
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a review for the dataset."""
        dataset = self.get_object()
        
        # Check if user has purchased the dataset or it's free
        if not dataset.is_free and dataset.owner != request.user:
            has_purchased = Purchase.objects.filter(
                buyer=request.user,
                dataset=dataset,
                status='completed'
            ).exists()
            
            if not has_purchased:
                return Response(
                    create_response_data(
                        success=False,
                        message="You can only review datasets you have purchased",
                        errors={'access': 'Purchase required to review'}
                    ),
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Check if user already reviewed this dataset
        existing_review = DatasetReview.objects.filter(
            dataset=dataset,
            reviewer=request.user
        ).first()
        
        if existing_review:
            # Update existing review
            serializer = DatasetReviewSerializer(
                existing_review, 
                data=request.data, 
                partial=True
            )
        else:
            # Create new review
            serializer = DatasetReviewSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        
        if existing_review:
            review = serializer.save()
        else:
            review = serializer.save(dataset=dataset, reviewer=request.user)
        
        # Update dataset rating
        dataset.calculate_rating()
        
        return Response(
            create_response_data(
                success=True,
                message="Review saved successfully",
                data=DatasetReviewSerializer(review).data
            ),
            status=status.HTTP_201_CREATED if not existing_review else status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['get'])
    def quality_score(self, request, pk=None):
        """Get dataset quality indicators."""
        dataset = self.get_object()
        
        # Generate statistics if not exists
        if not dataset.statistics:
            dataset.update_metadata()
        
        stats = dataset.statistics
        quality_indicators = {}
        
        if stats:
            # Calculate completeness (percentage of non-null values)
            missing_values = stats.get('missing_values', {})
            total_rows = stats.get('total_rows', 1)
            total_columns = stats.get('total_columns', 1)
            
            if missing_values and total_rows > 0:
                total_cells = total_rows * total_columns
                missing_cells = sum(missing_values.values())
                completeness = ((total_cells - missing_cells) / total_cells) * 100
            else:
                completeness = 100
            
            # Calculate consistency (based on data types)
            data_types = stats.get('data_types', {})
            consistency_score = 100  # Start with perfect score
            
            # Reduce score for mixed types or inconsistencies
            for col, dtype in data_types.items():
                if 'object' in str(dtype).lower():
                    consistency_score -= 5  # Reduce for string columns (might be inconsistent)
            
            # Calculate richness (variety of data types)
            unique_types = len(set(str(dt) for dt in data_types.values()))
            richness = min(100, (unique_types / max(1, len(data_types))) * 100)
            
            quality_indicators = {
                'completeness': round(completeness, 2),
                'consistency': max(0, round(consistency_score, 2)),
                'richness': round(richness, 2),
                'overall_score': round((completeness + consistency_score + richness) / 3, 2),
                'total_rows': total_rows,
                'total_columns': total_columns,
                'missing_values_count': sum(missing_values.values()) if missing_values else 0,
                'data_types_variety': unique_types
            }
        
        return Response(
            create_response_data(
                success=True,
                data=quality_indicators
            )
        )


class DatasetSearchView(ListAPIView):
    """
    Search and filter datasets.
    """
    serializer_class = DatasetListSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get filtered queryset based on search parameters."""
        # Validate search parameters
        search_serializer = DatasetSearchSerializer(data=self.request.query_params)
        search_serializer.is_valid(raise_exception=True)
        
        # Get search results
        search_results = search_datasets(search_serializer.validated_data)
        return search_results['queryset']
    
    def list(self, request, *args, **kwargs):
        """Return search results with metadata."""
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            create_response_data(
                success=True,
                data={
                    'results': serializer.data,
                    'count': queryset.count()
                }
            )
        )


@method_decorator(cache_page(60 * 15), name='get')  # Cache for 15 minutes
class CategoryListView(ListAPIView):
    """
    List all active categories.
    """
    queryset = Category.objects.filter(is_active=True).order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


@method_decorator(cache_page(60 * 15), name='get')  # Cache for 15 minutes
class TagListView(ListAPIView):
    """
    List all tags.
    """
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]


class DatasetCollectionViewSet(ModelViewSet):
    """
    ViewSet for dataset collections.
    """
    serializer_class = DatasetCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Return user's collections and public collections."""
        if self.request.user.is_authenticated:
            return DatasetCollection.objects.filter(
                Q(owner=self.request.user) | Q(is_public=True)
            ).order_by('-updated_at')
        return DatasetCollection.objects.filter(is_public=True).order_by('-updated_at')
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_datasets(request):
    """
    Get current user's datasets.
    """
    datasets = Dataset.objects.filter(owner=request.user).order_by('-created_at')
    
    # Add status filter
    status_filter = request.query_params.get('status')
    if status_filter:
        datasets = datasets.filter(status=status_filter)
    
    # Paginate results
    paginator = CustomPageNumberPagination()
    page = paginator.paginate_queryset(datasets, request)
    
    if page is not None:
        serializer = DatasetListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = DatasetListSerializer(datasets, many=True, context={'request': request})
    return Response(
        create_response_data(
            success=True,
            data=serializer.data
        )
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_purchases(request):
    """
    Get current user's dataset purchases.
    """
    purchases = Purchase.objects.filter(
        buyer=request.user,
        status='completed'
    ).select_related('dataset').order_by('-completed_at')
    
    # Paginate results
    paginator = CustomPageNumberPagination()
    page = paginator.paginate_queryset(purchases, request)
    
    purchase_data = []
    for purchase in (page if page is not None else purchases):
        purchase_data.append({
            'id': str(purchase.id),
            'dataset': DatasetListSerializer(purchase.dataset, context={'request': request}).data,
            'amount': str(purchase.amount),
            'currency': purchase.currency,
            'purchased_at': purchase.completed_at,
            'transaction_hash': purchase.transaction_hash
        })
    
    if page is not None:
        return paginator.get_paginated_response(purchase_data)
    
    return Response(
        create_response_data(
            success=True,
            data=purchase_data
        )
    )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recommendations(request):
    """
    Get dataset recommendations for current user.
    """
    recommended_datasets = generate_dataset_recommendations(request.user, limit=10)
    
    serializer = DatasetListSerializer(
        recommended_datasets, 
        many=True, 
        context={'request': request}
    )
    
    return Response(
        create_response_data(
            success=True,
            data=serializer.data
        )
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(60 * 30)  # Cache for 30 minutes
def popular_datasets(request):
    """
    Get popular datasets.
    """
    # Get most downloaded datasets
    popular = Dataset.objects.filter(
        status='approved'
    ).order_by('-download_count', '-rating_average')[:20]
    
    serializer = DatasetListSerializer(popular, many=True, context={'request': request})
    
    return Response(
        create_response_data(
            success=True,
            data=serializer.data
        )
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(60 * 30)  # Cache for 30 minutes
def featured_datasets(request):
    """
    Get featured datasets (high quality, well-rated).
    """
    featured = Dataset.objects.filter(
        status='approved',
        rating_average__gte=4.0,
        rating_count__gte=5
    ).order_by('-rating_average', '-download_count')[:10]
    
    serializer = DatasetListSerializer(featured, many=True, context={'request': request})
    
    return Response(
        create_response_data(
            success=True,
            data=serializer.data
        )
    )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_page(60 * 60)  # Cache for 1 hour
def dataset_stats(request):
    """
    Get overall dataset statistics.
    """
    stats = {
        'total_datasets': Dataset.objects.filter(status='approved').count(),
        'total_downloads': Dataset.objects.filter(status='approved').aggregate(
            total=Sum('download_count')
        )['total'] or 0,
        'total_revenue': Purchase.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'avg_rating': Dataset.objects.filter(
            status='approved',
            rating_count__gt=0
        ).aggregate(avg=Avg('rating_average'))['avg'] or 0,
        'popular_categories': list(
            Category.objects.annotate(
                dataset_count=Count('datasets', filter=Q(datasets__status='approved'))
            ).filter(dataset_count__gt=0).order_by('-dataset_count')[:5].values(
                'name', 'dataset_count'
            )
        ),
        'recent_activity': []  # This would include recent uploads, purchases, etc.
    }
    
    serializer = DatasetStatsSerializer(data=stats)
    serializer.is_valid()
    
    return Response(
        create_response_data(
            success=True,
            data=serializer.validated_data
        )
    )
