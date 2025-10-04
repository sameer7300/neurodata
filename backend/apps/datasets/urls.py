"""
URL patterns for datasets app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'datasets'

# Create router for viewsets
router = DefaultRouter()
router.register(r'datasets', views.DatasetViewSet, basename='dataset')
router.register(r'collections', views.DatasetCollectionViewSet, basename='collection')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Search and filtering
    path('search/', views.DatasetSearchView.as_view(), name='dataset_search'),
    
    # Categories and tags
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    
    # User-specific endpoints
    path('my-datasets/', views.user_datasets, name='user_datasets'),
    path('my-purchases/', views.user_purchases, name='user_purchases'),
    path('recommendations/', views.recommendations, name='recommendations'),
    
    # Public endpoints
    path('popular/', views.popular_datasets, name='popular_datasets'),
    path('featured/', views.featured_datasets, name='featured_datasets'),
    path('stats/', views.dataset_stats, name='dataset_stats'),
]
