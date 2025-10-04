django server: scripts\start-django-redis.bat
celery radis server: celery -A neurodata worker -l info --pool=solo --concurrency=1
frontend server: npm start