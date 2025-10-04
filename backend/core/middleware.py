"""
Custom middleware for NeuroData project.
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log request/response information.
    """
    
    def process_request(self, request):
        """Log incoming requests."""
        request.start_time = time.time()
        
        # Log request details
        logger.info(f"Request: {request.method} {request.path}", extra={
            'method': request.method,
            'path': request.path,
            'user': getattr(request.user, 'id', 'anonymous'),
            'ip': self.get_client_ip(request),
        })
        
        return None
    
    def process_response(self, request, response):
        """Log response details."""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            logger.info(f"Response: {response.status_code} in {duration:.3f}s", extra={
                'status_code': response.status_code,
                'duration': duration,
                'path': request.path,
                'method': request.method,
                'user': getattr(request.user, 'id', 'anonymous'),
            })
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers.
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}  # In production, use Redis
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check rate limits."""
        if settings.DEBUG:
            return None  # Skip rate limiting in development
        
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries (simple cleanup)
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(t > current_time - 60 for t in timestamps)  # Keep last minute
        }
        
        # Check current IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Remove old timestamps for this IP
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] 
            if t > current_time - 60
        ]
        
        # Check rate limit (60 requests per minute)
        if len(self.requests[client_ip]) >= 60:
            return JsonResponse({
                'error': True,
                'message': 'Rate limit exceeded. Please try again later.',
                'status_code': 429
            }, status=429)
        
        # Add current request
        self.requests[client_ip].append(current_time)
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CORSMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware for additional control.
    """
    
    def process_response(self, request, response):
        """Add CORS headers."""
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Accept-Language, Content-Language, Content-Type, '
                'Authorization, X-Requested-With'
            )
            response['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return response
