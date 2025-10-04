# Local environment variables for development
# Force Celery to use Redis

import os

# Set Celery Redis configuration
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Disable problematic logging for development
os.environ['DJANGO_LOG_LEVEL'] = 'WARNING'
