#!/usr/bin/env python3
"""
Check NeuroData ML Training System Status
"""

import os
import sys
import django
from django.conf import settings

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

# Set environment
os.environ['DJANGO_SETTINGS_MODULE'] = 'neurodata.settings.development'

# Setup Django
django.setup()

def check_system_status():
    """Check the status of ML training system components."""
    print("🔍 NeuroData ML Training System Status Check")
    print("=" * 50)
    
    # Check Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis: Connected")
    except Exception as e:
        print(f"❌ Redis: Failed - {e}")
        return False
    
    # Check database
    try:
        from apps.ml_training.models import TrainingJob
        job_count = TrainingJob.objects.count()
        created_jobs = TrainingJob.objects.filter(status='created').count()
        print(f"✅ Database: Connected ({job_count} total jobs, {created_jobs} created)")
    except Exception as e:
        print(f"❌ Database: Failed - {e}")
        return False
    
    # Check Celery configuration
    try:
        from neurodata.celery import app
        print(f"✅ Celery App: Configured")
        print(f"   Broker: {app.conf.broker_url}")
        print(f"   Backend: {app.conf.result_backend}")
    except Exception as e:
        print(f"❌ Celery App: Failed - {e}")
        return False
    
    # Check for stuck jobs
    try:
        from apps.ml_training.models import TrainingJob
        from django.utils import timezone
        from datetime import timedelta
        
        # Jobs created more than 5 minutes ago but still in 'created' status
        five_min_ago = timezone.now() - timedelta(minutes=5)
        stuck_jobs = TrainingJob.objects.filter(
            status='created',
            created_at__lt=five_min_ago
        )
        
        if stuck_jobs.exists():
            print(f"⚠️  Stuck Jobs: {stuck_jobs.count()} jobs stuck in 'created' status")
            for job in stuck_jobs[:3]:  # Show first 3
                print(f"   - {job.name} (ID: {job.id[:8]}...) - {job.created_at}")
        else:
            print("✅ No stuck jobs found")
            
    except Exception as e:
        print(f"❌ Job Status Check: Failed - {e}")
    
    print("\n🚀 Recommendations:")
    print("1. Ensure Redis is running: docker ps | findstr redis")
    print("2. Start Celery worker: celery -A neurodata worker -l info --pool=solo --concurrency=1")
    print("3. Check Django logs for errors")
    
    return True

if __name__ == "__main__":
    check_system_status()
