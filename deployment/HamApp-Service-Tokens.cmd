@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0.."
echo HamApp private publisher token operations. No publication or other Docker projects.
where py.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 scripts\hamapp_service_windows_tokens.py
) else (
  python scripts\hamapp_service_windows_tokens.py
)
echo.
pause
endlocal
