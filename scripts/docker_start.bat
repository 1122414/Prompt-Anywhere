@echo off
echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

echo Creating directories...
if not exist data mkdir data
if not exist exports mkdir exports
if not exist backups mkdir backups
if not exist logs mkdir logs

echo Starting Prompt Anywhere in Docker...
docker compose -f docker/docker-compose.yml up -d --build

echo.
echo Prompt Anywhere is starting...
echo Access it at: http://localhost:6080
echo.
pause
