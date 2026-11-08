@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
echo.
echo HAMAPP PRIVATE PUBLISHER SERVICE - LOCAL HOST ONLY
echo Does NOT change unrelated Docker services or install packages on the host.
echo.
where py.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 scripts\hamapp_service_windows_setup.py
) else (
  python scripts\hamapp_service_windows_setup.py
)
if errorlevel 1 (
  echo.
  echo Private service configuration failed. Existing secrets are preserved.
) else (
  echo.
  echo The HamApp app can now probe the local TLS service.
)
echo.
pause
endlocal
