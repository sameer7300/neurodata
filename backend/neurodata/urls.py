"""
NeuroData URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# API URL patterns
api_v1_patterns = [
    path('auth/', include('apps.authentication.urls')),
    path('datasets/', include('apps.datasets.urls')),
    path('marketplace/', include('apps.marketplace.urls')),
    path('ml/', include('apps.ml_training.urls')),
    path('reviews/', include('apps.reviews.urls')),
    path('web3/', include('core.web3_urls')),
    path('ipfs/', include('core.ipfs_urls')),
    # path('users/', include('apps.users.urls')),
    # path('notifications/', include('apps.notifications.urls')),
    # path('analytics/', include('apps.analytics.urls')),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Core URLs
    path('', include('core.urls')),
    
    # App URLs
    path('api/v1/', include(api_v1_patterns)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom admin configuration
admin.site.site_header = "NeuroData Administration"
admin.site.site_title = "NeuroData Admin"
admin.site.index_title = "Welcome to NeuroData Administration"
