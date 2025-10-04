#!/usr/bin/env python3
"""
Simple Redis test script for NeuroData ML training.
This script helps you test if Redis is working without complex setup.
"""

import subprocess
import sys
import time
import os

def check_redis_installed():
    """Check if Redis is available."""
    try:
        result = subprocess.run(['redis-cli', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_redis_running():
    """Check if Redis server is running."""
    try:
        result = subprocess.run(['redis-cli', 'ping'], 
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() == 'PONG'
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def start_redis_server():
    """Start Redis server in background."""
    try:
        print("🚀 Starting Redis server...")
        # Start Redis server in background
        process = subprocess.Popen(['redis-server'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Check if it's running
        if check_redis_running():
            print("✅ Redis server started successfully!")
            return process
        else:
            print("❌ Failed to start Redis server")
            return None
    except FileNotFoundError:
        print("❌ Redis not found. Please install Redis first.")
        return None

def test_python_redis():
    """Test Redis connection with Python."""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Test basic operations
        r.set('test_key', 'Hello NeuroData!')
        value = r.get('test_key')
        
        if value and value.decode() == 'Hello NeuroData!':
            print("✅ Python Redis connection working!")
            r.delete('test_key')  # Cleanup
            return True
        else:
            print("❌ Python Redis test failed")
            return False
            
    except ImportError:
        print("❌ Redis Python package not installed. Run: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False

def test_celery_connection():
    """Test Celery connection to Redis."""
    try:
        # Change to backend directory
        backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
        os.chdir(backend_dir)
        
        # Test Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurodata.settings')
        
        import django
        django.setup()
        
        from celery import current_app
        
        # Test Celery broker connection
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print("✅ Celery connection to Redis working!")
            return True
        else:
            print("⚠️  Celery connected but no workers running")
            return True
            
    except Exception as e:
        print(f"❌ Celery connection error: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 NeuroData Redis Setup Test")
    print("=" * 40)
    
    # Check if Redis is installed
    if not check_redis_installed():
        print("❌ Redis not installed")
        print("\n📥 Quick Install Options:")
        print("1. Docker: docker run -d --name redis -p 6379:6379 redis:alpine")
        print("2. Windows: choco install redis-64")
        print("3. Download: https://github.com/tporadowski/redis/releases")
        return False
    
    print("✅ Redis is installed")
    
    # Check if Redis is running
    if not check_redis_running():
        print("⚠️  Redis not running, attempting to start...")
        redis_process = start_redis_server()
        if not redis_process:
            return False
    else:
        print("✅ Redis server is running")
    
    # Test Python Redis connection
    if not test_python_redis():
        return False
    
    # Test Celery connection
    print("\n🔧 Testing Celery connection...")
    test_celery_connection()
    
    print("\n🎉 Redis setup test completed!")
    print("\n🚀 Next steps:")
    print("1. Start Django: python manage.py runserver")
    print("2. Start Celery: celery -A neurodata worker -l info")
    print("3. Test ML training at: http://localhost:8000/ml/training")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
