#!/usr/bin/env python3
"""
Test Celery Redis connection directly.
"""

import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)

# Force Redis configuration
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
os.environ['DJANGO_SETTINGS_MODULE'] = 'neurodata.settings.development'

# Import Django and Celery
import django
django.setup()

from neurodata.celery import app

def test_celery_redis():
    """Test Celery Redis connection."""
    print("🧪 Testing Celery Redis Connection")
    print("=" * 40)
    
    # Check configuration
    print(f"📡 Broker URL: {app.conf.broker_url}")
    print(f"📦 Result Backend: {app.conf.result_backend}")
    
    # Test connection
    try:
        # Try to get broker connection
        with app.broker_connection() as conn:
            conn.ensure_connection(max_retries=3)
        print("✅ Celery can connect to Redis broker")
        
        # Test task creation
        from celery import current_app
        inspect = current_app.control.inspect()
        
        print("✅ Celery app initialized successfully")
        print("✅ Ready to queue tasks!")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery Redis connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_celery_redis()
    if success:
        print("\n🎉 Celery Redis connection working!")
        print("🚀 You can now start Django and Celery worker")
    else:
        print("\n❌ Fix the connection issues above")
    
    sys.exit(0 if success else 1)
