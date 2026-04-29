@echo off
echo Stopping Prompt Anywhere Docker...
docker compose -f docker/docker-compose.yml down
echo Done.
pause
