#!/usr/bin/env python3
"""
Simple Redis connectivity test for NeuroData ML training.
Tests Docker Redis connection without checking for local Redis install.
"""

import sys
import os

def test_redis_connection():
    """Test Redis connection (Docker or local)."""
    try:
        import redis
        print("🔌 Testing Redis connection...")
        
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test basic operations
        r.set('neurodata_test', 'ML Training Ready!')
        value = r.get('neurodata_test')
        
        if value == 'ML Training Ready!':
            print("✅ Redis connection successful!")
            print(f"   📍 Connected to: localhost:6379")
            print(f"   🧪 Test value: {value}")
            
            # Cleanup test key
            r.delete('neurodata_test')
            
            # Get Redis info
            info = r.info()
            print(f"   📊 Redis version: {info.get('redis_version', 'Unknown')}")
            print(f"   💾 Used memory: {info.get('used_memory_human', 'Unknown')}")
            
            return True
        else:
            print("❌ Redis test failed - unexpected value")
            return False
            
    except ImportError:
        print("❌ Redis Python package not installed")
        print("   💡 Run: pip install redis")
        return False
    except redis.ConnectionError:
        print("❌ Cannot connect to Redis")
        print("   💡 Make sure Redis is running:")
        print("   🐳 Docker: docker run -d --name redis -p 6379:6379 redis:alpine")
        return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_celery_redis():
    """Test Celery Redis configuration."""
    try:
        # Set up Django environment
        backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
        if os.path.exists(backend_dir):
            sys.path.insert(0, backend_dir)
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurodata.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print("\n🔧 Testing Celery Redis configuration...")
        
        # Check Celery settings
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        result_backend = getattr(settings, 'CELERY_RESULT_BACKEND', None)
        
        print(f"   📡 Broker URL: {broker_url}")
        print(f"   📦 Result Backend: {result_backend}")
        
        if 'redis' in str(broker_url).lower():
            print("✅ Celery configured for Redis")
            return True
        else:
            print("⚠️  Celery not configured for Redis")
            return False
            
    except Exception as e:
        print(f"⚠️  Could not test Celery config: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 NeuroData Redis Connection Test")
    print("=" * 40)
    
    # Test Redis connection
    redis_ok = test_redis_connection()
    
    # Test Celery configuration
    celery_ok = test_celery_redis()
    
    print("\n" + "=" * 40)
    
    if redis_ok:
        print("🎉 Redis is ready for ML training!")
        print("\n🚀 Next steps:")
        print("1. Start Django server:")
        print("   cd backend && python manage.py runserver")
        print("\n2. Start Celery worker:")
        print("   cd backend && celery -A neurodata worker -l info")
        print("\n3. Access ML Training Lab:")
        print("   http://localhost:8000/ml/training")
        
        if celery_ok:
            print("\n✅ Full ML training stack ready!")
        else:
            print("\n⚠️  Check Celery configuration in settings.py")
    else:
        print("❌ Redis connection failed")
        print("   Make sure Redis is running with Docker:")
        print("   docker run -d --name redis -p 6379:6379 redis:alpine")
    
    return redis_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
