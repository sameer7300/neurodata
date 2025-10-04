"""
Review URLs.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reviews'

router = DefaultRouter()
router.register(r'reviews', views.ReviewViewSet, basename='reviews')

urlpatterns = [
    path('', include(router.urls)),
    path('datasets/<str:dataset_id>/reviews/', views.DatasetReviewsView.as_view(), name='dataset-reviews'),
]
