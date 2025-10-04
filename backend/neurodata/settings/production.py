"""
Production settings for NeuroData project.
"""
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# Security settings
DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Static files configuration for production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database connection pooling for production
DATABASES['default'].update({
    'CONN_MAX_AGE': 60,
    'OPTIONS': {
        'client_encoding': 'UTF8',
        'sslmode': 'require',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'isolation_level': None,
    }
})

# Caching configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Sentry configuration for error tracking
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
                propagate_traces=True,
            ),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment='production',
    )

# Logging configuration for production
LOGGING['handlers']['file']['filename'] = '/var/log/neurodata/neurodata.log'
LOGGING['handlers']['console']['level'] = 'WARNING'
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['neurodata']['level'] = 'INFO'

# Production blockchain settings
WEB3_PROVIDER_URL = config('WEB3_PROVIDER_URL', default='https://polygon-mainnet.g.alchemy.com/v2/your-api-key')

# Production IPFS settings
IPFS_SETTINGS.update({
    'API_URL': config('IPFS_API_URL', default='https://ipfs.infura.io:5001'),
})

# Additional security headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TZ = True

# CORS settings for production (more restrictive)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://neurodata.app,https://www.neurodata.app',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

print("🔒 NeuroData Backend running in PRODUCTION mode")
