@echo off
echo Starting Django with Redis Configuration...
echo.

REM Change to backend directory
cd /d "C:\Users\samee\OneDrive\Desktop\neuro chain\backend"

REM Set Redis environment variables
set CELERY_BROKER_URL=redis://localhost:6379/0
set CELERY_RESULT_BACKEND=redis://localhost:6379/0

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 🚀 Starting Django with Redis configuration...
echo 📡 Broker: %CELERY_BROKER_URL%
echo 📦 Backend: %CELERY_RESULT_BACKEND%
echo.

REM Start Django
python manage.py runserver

pause
