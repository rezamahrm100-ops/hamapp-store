@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
docker compose -f deployment\compose.yaml -p hamapp-private ps publisher-intake
docker compose -f deployment\compose.yaml -p hamapp-private run --rm --no-deps -T publisher-intake status --root /data/service
echo.
pause
endlocal
