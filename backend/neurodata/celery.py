"""
Celery configuration for NeuroData project.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurodata.settings.development')

app = Celery('neurodata')

# Explicitly configure Redis as broker and result backend
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'monitor-blockchain-events': {
        'task': 'apps.blockchain.tasks.monitor_blockchain_events',
        'schedule': 30.0,  # Run every 30 seconds
    },
    'cleanup-expired-sessions': {
        'task': 'apps.authentication.tasks.cleanup_expired_sessions',
        'schedule': 3600.0,  # Run every hour
    },
    'update-dataset-statistics': {
        'task': 'apps.analytics.tasks.update_dataset_statistics',
        'schedule': 1800.0,  # Run every 30 minutes
    },
    'process-training-queue': {
        'task': 'apps.ml_training.tasks.process_training_queue',
        'schedule': 60.0,  # Run every minute
    },
    'cleanup-old-training-files': {
        'task': 'apps.ml_training.tasks.cleanup_old_training_files',
        'schedule': 86400.0,  # Run daily
    },
    'update-training-statistics': {
        'task': 'apps.ml_training.tasks.update_training_statistics',
        'schedule': 3600.0,  # Run every hour
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
