"""
URL patterns for IPFS storage API endpoints.
"""
from django.urls import path
from . import ipfs_views

app_name = 'ipfs'

urlpatterns = [
    # Dataset upload/download endpoints
    path('upload/', ipfs_views.upload_dataset, name='upload_dataset'),
    path('download/<int:dataset_id>/', ipfs_views.download_dataset, name='download_dataset'),
    path('info/<int:dataset_id>/', ipfs_views.dataset_info, name='dataset_info'),
    path('verify/<int:dataset_id>/', ipfs_views.verify_integrity, name='verify_integrity'),
    
    # Service management endpoints
    path('status/', ipfs_views.ipfs_status, name='ipfs_status'),
    path('test/', ipfs_views.test_connection, name='test_connection'),
    
    # User datasets endpoints
    path('user/datasets/', ipfs_views.user_datasets_ipfs, name='user_datasets_ipfs'),
]
