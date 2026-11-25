@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0peppymeter.py"
) else (
    python "%~dp0peppymeter.py"
)
set "APP_EXIT_CODE=%ERRORLEVEL%"

if not "%APP_EXIT_CODE%"=="0" (
    echo PeppyMeter failed with exit code %APP_EXIT_CODE%.
    pause
)

exit /b %APP_EXIT_CODE%
