@echo off
REM Drag a file onto this script to cache it, or run without args to open the GUI.

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

if "%~1"=="" (
    where python >nul 2>&1 && python "%APP_DIR%\app.py" & exit /b %ERRORLEVEL%
    where py >nul 2>&1 && py "%APP_DIR%\app.py" & exit /b %ERRORLEVEL%
    echo Python not found.
    pause
    exit /b 1
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%APP_DIR%\app.py" --cli "%~1"
    pause
    exit /b %ERRORLEVEL%
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py "%APP_DIR%\app.py" --cli "%~1"
    pause
    exit /b %ERRORLEVEL%
)

echo Python not found.
pause
exit /b 1
