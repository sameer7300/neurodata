@echo off
echo Installing Redis for NeuroData ML Training...

REM Check if Chocolatey is installed
choco --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Chocolatey...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
)

REM Install Redis
echo Installing Redis...
choco install redis-64 -y

REM Start Redis service
echo Starting Redis service...
net start redis

REM Test Redis connection
echo Testing Redis connection...
redis-cli ping

echo.
echo Redis setup complete!
echo Redis is running on localhost:6379
echo.
echo To start Redis manually: redis-server
echo To test connection: redis-cli ping
echo To stop Redis service: net stop redis
echo.
pause
