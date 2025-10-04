"""
Review views with automatic filtering.
"""
from rest_framework import status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count
from django.utils import timezone

from .models import Review, ReviewHelpful, ReviewReport
from .serializers import (
    ReviewListSerializer, ReviewDetailSerializer, ReviewCreateSerializer,
    ReviewUpdateSerializer, ReviewHelpfulSerializer, ReviewReportSerializer,
    ReviewStatsSerializer, ReviewFilterSerializer
)
from .utils import ReviewAnalytics, get_review_recommendations
from apps.datasets.models import Dataset
from apps.marketplace.models import Purchase
from core.utils import create_response_data
from core.pagination import CustomPageNumberPagination

import logging

logger = logging.getLogger(__name__)


class ReviewViewSet(ModelViewSet):
    """
    ViewSet for review management with automatic filtering.
    """
    
    queryset = Review.objects.all()
    pagination_class = CustomPageNumberPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'comment']
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        elif self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        else:
            return ReviewDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on permissions and filters."""
        queryset = Review.objects.select_related('reviewer', 'dataset').prefetch_related('helpful_votes')
        
        # Only show approved reviews to non-staff users
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(status__in=['approved', 'auto_approved'])
        
        # Apply filters
        dataset_id = self.request.query_params.get('dataset')
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        verified_only = self.request.query_params.get('verified_only', '').lower() == 'true'
        if verified_only:
            queryset = queryset.filter(is_verified_purchase=True)
        
        # Sort options
        sort_by = self.request.query_params.get('sort_by', 'newest')
        if sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'highest_rated':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort_by == 'lowest_rated':
            queryset = queryset.order_by('rating', '-created_at')
        elif sort_by == 'most_helpful':
            queryset = queryset.order_by('-helpful_count', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new review with automatic filtering."""
        dataset_id = request.data.get('dataset_id')
        if not dataset_id:
            return Response(
                create_response_data(
                    success=False,
                    message="Dataset ID is required",
                    errors={'dataset_id': ['This field is required.']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dataset = get_object_or_404(Dataset, id=dataset_id)
        
        # Check if user already reviewed this dataset
        existing_review = Review.objects.filter(
            reviewer=request.user,
            dataset=dataset
        ).first()
        
        if existing_review:
            return Response(
                create_response_data(
                    success=False,
                    message="You have already reviewed this dataset",
                    errors={'review': ['You can only review a dataset once.']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user can review (has purchased or dataset is free)
        can_review = (
            dataset.is_free or
            dataset.owner == request.user or
            Purchase.objects.filter(
                buyer=request.user,
                dataset=dataset,
                status='completed'
            ).exists()
        )
        
        if not can_review:
            return Response(
                create_response_data(
                    success=False,
                    message="You must purchase this dataset before reviewing it",
                    errors={'access': ['Purchase required to review.']}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request, 'dataset': dataset}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Update dataset rating
        dataset.calculate_rating()
        
        logger.info(f"Review created: {review.id} by {request.user.email}")
        
        return Response(
            create_response_data(
                success=True,
                message="Review submitted successfully",
                data=ReviewDetailSerializer(review, context={'request': request}).data
            ),
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update review (only by author)."""
        review = self.get_object()
        
        if review.reviewer != request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You can only edit your own reviews",
                    errors={'permission': ['Access denied.']}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Re-run automatic filtering for updated content
        review.run_automatic_filters()
        review.save()
        
        # Update dataset rating
        if review.dataset:
            review.dataset.calculate_rating()
        
        return Response(
            create_response_data(
                success=True,
                message="Review updated successfully",
                data=ReviewDetailSerializer(review, context={'request': request}).data
            )
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete review (only by author or staff)."""
        review = self.get_object()
        
        if review.reviewer != request.user and not request.user.is_staff:
            return Response(
                create_response_data(
                    success=False,
                    message="You can only delete your own reviews",
                    errors={'permission': ['Access denied.']}
                ),
                status=status.HTTP_403_FORBIDDEN
            )
        
        dataset = review.dataset
        review.delete()
        
        # Update dataset rating
        if dataset:
            dataset.calculate_rating()
        
        return Response(
            create_response_data(
                success=True,
                message="Review deleted successfully"
            ),
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def helpful(self, request, pk=None):
        """Mark review as helpful/not helpful."""
        review = self.get_object()
        
        if review.reviewer == request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You cannot mark your own review as helpful",
                    errors={'action': ['Cannot vote on own review.']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewHelpfulSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        helpful_vote, created = ReviewHelpful.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={'is_helpful': serializer.validated_data['is_helpful']}
        )
        
        action_text = "marked as helpful" if helpful_vote.is_helpful else "marked as not helpful"
        
        return Response(
            create_response_data(
                success=True,
                message=f"Review {action_text}",
                data={
                    'is_helpful': helpful_vote.is_helpful,
                    'helpful_count': review.helpful_count
                }
            )
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def report(self, request, pk=None):
        """Report inappropriate review."""
        review = self.get_object()
        
        if review.reviewer == request.user:
            return Response(
                create_response_data(
                    success=False,
                    message="You cannot report your own review",
                    errors={'action': ['Cannot report own review.']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already reported
        if ReviewReport.objects.filter(review=review, reporter=request.user).exists():
            return Response(
                create_response_data(
                    success=False,
                    message="You have already reported this review",
                    errors={'action': ['Already reported.']}
                ),
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report = ReviewReport.objects.create(
            review=review,
            reporter=request.user,
            **serializer.validated_data
        )
        
        # Auto-flag review if it gets multiple reports
        if review.report_count >= 3:
            review.status = 'flagged'
            review.save()
        
        return Response(
            create_response_data(
                success=True,
                message="Review reported successfully",
                data={'report_count': review.report_count}
            )
        )
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get review statistics."""
        dataset_id = request.query_params.get('dataset')
        user_id = request.query_params.get('user')
        
        stats = ReviewAnalytics.get_review_stats(dataset_id, user_id)
        
        # Add rating breakdown percentages
        total = stats['total_reviews']
        if total > 0:
            for rating in range(1, 6):
                count = stats['rating_distribution'][rating]
                stats[f'{["one", "two", "three", "four", "five"][rating-1]}_star_count'] = count
                stats[f'{["one", "two", "three", "four", "five"][rating-1]}_star_percentage'] = (count / total) * 100
        else:
            for rating in range(1, 6):
                stats[f'{["one", "two", "three", "four", "five"][rating-1]}_star_count'] = 0
                stats[f'{["one", "two", "three", "four", "five"][rating-1]}_star_percentage'] = 0
        
        return Response(
            create_response_data(
                success=True,
                data=stats
            )
        )
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recommendations(self, request):
        """Get datasets user might want to review."""
        datasets = get_review_recommendations(request.user)
        
        data = []
        for dataset in datasets:
            data.append({
                'id': dataset.id,
                'title': dataset.title,
                'description': dataset.description[:200] + '...' if len(dataset.description) > 200 else dataset.description,
                'rating_average': float(dataset.rating_average),
                'rating_count': dataset.rating_count
            })
        
        return Response(
            create_response_data(
                success=True,
                data=data
            )
        )


class DatasetReviewsView(ListAPIView):
    """
    List reviews for a specific dataset with filtering.
    """
    
    serializer_class = ReviewListSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Get reviews for specific dataset."""
        dataset_id = self.kwargs.get('dataset_id')
        dataset = get_object_or_404(Dataset, id=dataset_id)
        
        queryset = Review.objects.filter(
            dataset=dataset,
            status__in=['approved', 'auto_approved']
        ).select_related('reviewer').prefetch_related('helpful_votes')
        
        # Apply filters
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        verified_only = self.request.query_params.get('verified_only', '').lower() == 'true'
        if verified_only:
            queryset = queryset.filter(is_verified_purchase=True)
        
        # Sort options
        sort_by = self.request.query_params.get('sort_by', 'newest')
        if sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'highest_rated':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort_by == 'lowest_rated':
            queryset = queryset.order_by('rating', '-created_at')
        elif sort_by == 'most_helpful':
            queryset = queryset.order_by('-helpful_count', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List reviews with additional stats."""
        try:
            queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            
            # Add review stats
            dataset_id = self.kwargs.get('dataset_id')
            stats = ReviewAnalytics.get_review_stats(dataset_id=dataset_id)
            
            if page is not None:
                serializer = self.get_serializer(page, many=True, context={'request': request})
                response_data = self.get_paginated_response(serializer.data)
                
                # Modify the paginated response to include stats
                response_data.data['stats'] = stats
                response_data.data['success'] = True
                
                return response_data
            
            serializer = self.get_serializer(queryset, many=True, context={'request': request})
            
            return Response(
                create_response_data(
                    success=True,
                    data={
                        'reviews': serializer.data,
                        'stats': stats
                    }
                )
            )
        except Exception as e:
            logger.error(f"Error listing dataset reviews: {str(e)}")
            return Response(
                create_response_data(
                    success=False,
                    message="Failed to fetch reviews",
                    errors={'error': [str(e)]}
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
