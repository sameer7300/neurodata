#!/usr/bin/env python3
"""
Verify Redis and Celery configuration before starting services.
"""

import os
import sys

def test_redis_connection():
    """Test Redis connection."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running:")
        print("   docker run -d --name neurodata-redis -p 6379:6379 redis:alpine")
        return False

def test_celery_config():
    """Test Celery configuration."""
    try:
        # Setup Django
        backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
        sys.path.insert(0, backend_dir)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurodata.settings.development')
        
        # Import Celery app
        from neurodata.celery import app
        
        # Check broker URL
        broker_url = app.conf.broker_url
        result_backend = app.conf.result_backend
        
        print(f"✅ Celery broker URL: {broker_url}")
        print(f"✅ Celery result backend: {result_backend}")
        
        if 'redis' in broker_url.lower():
            print("✅ Celery configured for Redis")
            return True
        else:
            print("❌ Celery not configured for Redis")
            return False
            
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 NeuroData Redis & Celery Verification")
    print("=" * 45)
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    # Test Celery config
    celery_ok = test_celery_config()
    
    print("\n" + "=" * 45)
    
    if redis_ok and celery_ok:
        print("🎉 All systems ready!")
        print("\n🚀 Start your services:")
        print("Terminal 1: python manage.py runserver")
        print("Terminal 2: celery -A neurodata worker -l info --pool=solo --concurrency=1")
        return True
    else:
        print("❌ System not ready. Fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
