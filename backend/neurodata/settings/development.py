"""
Development settings for NeuroData project.
"""
from .base import *

# Import local environment variables (forces Redis configuration)
try:
    import local_env
except ImportError:
    pass

# Debug settings
DEBUG = True

# Database
# Use SQLite for development (easier setup)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Uncomment below for PostgreSQL development setup
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'neurodata_dev',
#         'USER': 'postgres',
#         'PASSWORD': 'your_password_here',
#         'HOST': 'localhost',
#         'PORT': '5432',
#         'OPTIONS': {
#             'client_encoding': 'UTF8',
#         },
#     }
# }

# Additional apps for development
INSTALLED_APPS += [
    'debug_toolbar',
]

# Additional middleware for development
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable caching in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Static files configuration for development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Security settings (relaxed for development)
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Logging for development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['neurodata']['level'] = 'DEBUG'

# Development-specific blockchain settings
WEB3_PROVIDER_URL = config('WEB3_PROVIDER_URL', default='https://polygon-mumbai.g.alchemy.com/v2/demo')

# Development IPFS settings (use local node if available)
IPFS_SETTINGS.update({
    'API_URL': config('IPFS_API_URL', default='http://localhost:5001'),
})

print("🚀 NeuroData Backend running in DEVELOPMENT mode")
