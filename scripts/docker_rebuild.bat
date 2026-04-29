@echo off
echo Rebuilding Prompt Anywhere Docker...
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d --build
echo Done.
echo Access it at: http://localhost:6080
pause
