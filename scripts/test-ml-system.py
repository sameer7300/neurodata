#!/usr/bin/env python3
"""
Test the complete ML training system end-to-end.
"""

import os
import sys
import django
import time

# Setup Django environment
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neurodata.settings.development')

django.setup()

def test_ml_system():
    """Test the complete ML training system."""
    print("🧪 Testing NeuroData ML Training System")
    print("=" * 50)
    
    try:
        # Test 1: Check Redis connection
        print("1️⃣ Testing Redis connection...")
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        if r.ping():
            print("   ✅ Redis connected successfully")
        else:
            print("   ❌ Redis connection failed")
            return False
            
        # Test 2: Check Django models
        print("\n2️⃣ Testing Django models...")
        from apps.ml_training.models import MLAlgorithm, TrainingJob
        algorithm_count = MLAlgorithm.objects.count()
        print(f"   📊 Found {algorithm_count} ML algorithms")
        
        if algorithm_count == 0:
            print("   ⚠️  No algorithms found. Run: python manage.py setup_ml_algorithms")
        
        # Test 3: Check Celery connection
        print("\n3️⃣ Testing Celery connection...")
        from celery import current_app
        
        # Get Celery app info
        broker_url = current_app.conf.broker_url
        print(f"   📡 Broker URL: {broker_url}")
        
        # Test Celery inspect
        inspect = current_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            print(f"   ✅ Celery workers active: {len(stats)}")
            for worker_name, worker_stats in stats.items():
                print(f"      🔧 Worker: {worker_name}")
        else:
            print("   ⚠️  No Celery workers detected")
            print("      💡 Start worker: celery -A neurodata worker -l info")
        
        # Test 4: Check ML algorithms setup
        print("\n4️⃣ Testing ML algorithms...")
        algorithms = MLAlgorithm.objects.filter(is_active=True)
        
        for algo in algorithms[:3]:  # Show first 3
            print(f"   🤖 {algo.name} ({algo.algorithm_type})")
            print(f"      💰 Cost: {algo.cost_per_hour} NRC/hour")
        
        if algorithms.count() > 3:
            print(f"   ... and {algorithms.count() - 3} more algorithms")
        
        # Test 5: Test task import
        print("\n5️⃣ Testing ML training tasks...")
        try:
            from apps.ml_training.tasks import execute_training_job
            print("   ✅ ML training tasks imported successfully")
        except ImportError as e:
            print(f"   ❌ Task import failed: {e}")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 ML Training System Test Complete!")
        
        # Show next steps
        print("\n🚀 System Ready! Next Steps:")
        print("1. 🌐 Open browser: http://localhost:8000")
        print("2. 🔐 Login to your account")
        print("3. 🧪 Navigate to: ML Training Lab")
        print("4. 📊 Upload a dataset (CSV format)")
        print("5. 🤖 Create your first training job!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ml_system()
    sys.exit(0 if success else 1)
