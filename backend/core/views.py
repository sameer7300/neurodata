"""
Core views for health checks and system status.
"""
from django.http import JsonResponse
from django.conf import settings
from django.db import connection
from django.utils import timezone
import redis
import logging

logger = logging.getLogger(__name__)


def health_check(request):
    """
    Simple health check endpoint.
    """
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


def system_status(request):
    """
    Detailed system status endpoint.
    """
    status_data = {
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status_data['services']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        status_data['services']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.CELERY_BROKER_URL)
        redis_client.ping()
        status_data['services']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        status_data['services']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis connection failed: {str(e)}'
        }
        logger.error(f"Redis health check failed: {e}")
    
    # Check IPFS connection (if configured)
    if hasattr(settings, 'IPFS_SETTINGS') and settings.IPFS_SETTINGS.get('API_URL'):
        try:
            import requests
            response = requests.get(f"{settings.IPFS_SETTINGS['API_URL']}/api/v0/version", timeout=5)
            if response.status_code == 200:
                status_data['services']['ipfs'] = {
                    'status': 'healthy',
                    'message': 'IPFS connection successful'
                }
            else:
                status_data['services']['ipfs'] = {
                    'status': 'unhealthy',
                    'message': f'IPFS returned status code: {response.status_code}'
                }
        except Exception as e:
            status_data['services']['ipfs'] = {
                'status': 'unhealthy',
                'message': f'IPFS connection failed: {str(e)}'
            }
            logger.error(f"IPFS health check failed: {e}")
    
    # Overall status
    all_healthy = all(
        service['status'] == 'healthy' 
        for service in status_data['services'].values()
    )
    
    status_data['overall_status'] = 'healthy' if all_healthy else 'degraded'
    
    return JsonResponse(status_data)
