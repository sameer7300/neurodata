"""
URL configuration for ML Training app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'ml_training'

router = DefaultRouter()
router.register(r'algorithms', views.MLAlgorithmViewSet, basename='algorithms')
router.register(r'jobs', views.TrainingJobViewSet, basename='training-jobs')
router.register(r'models', views.TrainedModelViewSet, basename='trained-models')
router.register(r'inference', views.ModelInferenceViewSet, basename='model-inference')
router.register(r'queue', views.TrainingQueueViewSet, basename='training-queue')
router.register(r'resources', views.ComputeResourceViewSet, basename='compute-resources')
router.register(r'dashboard', views.MLDashboardViewSet, basename='ml-dashboard')

urlpatterns = [
    path('', include(router.urls)),
]
