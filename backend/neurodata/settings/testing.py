"""
Testing settings for NeuroData project.
"""
from .base import *

# Test database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Fast password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Celery settings for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable logging during tests
LOGGING_CONFIG = None

# Test-specific blockchain settings (use mock/test network)
WEB3_PROVIDER_URL = 'http://localhost:8545'  # Local test network
BLOCKCHAIN_PRIVATE_KEY = '0x' + '0' * 64  # Test private key

# Test IPFS settings (use mock)
IPFS_SETTINGS = {
    'API_URL': 'http://localhost:5001',
    'API_KEY': 'test-key',
    'API_SECRET': 'test-secret',
}

# Security settings for testing
SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True

print("🧪 NeuroData Backend running in TESTING mode")
