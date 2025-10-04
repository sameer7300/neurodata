@echo off
echo Starting Celery Worker for Windows...
echo.

REM Change to backend directory
cd /d "C:\Users\samee\OneDrive\Desktop\neuro chain\backend"

REM Activate virtual environment
call venv\Scripts\activate.bat

echo 🚀 Starting Celery with Windows-optimized settings...
echo.

REM Start Celery with solo pool (no multiprocessing issues)
celery -A neurodata worker -l info --pool=solo --concurrency=1

pause
