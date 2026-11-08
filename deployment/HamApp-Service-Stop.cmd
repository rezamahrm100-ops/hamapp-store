@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
echo Stops ONLY HamApp private publisher intake; preserves all volumes and tokens.
docker compose -f deployment\compose.yaml -p hamapp-private stop publisher-intake
echo.
pause
endlocal
