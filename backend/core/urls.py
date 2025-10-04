"""
Core URLs for health checks and system status.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.health_check, name='health_check'),
    path('status/', views.system_status, name='system_status'),
]
