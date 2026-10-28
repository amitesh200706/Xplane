@echo off
REM Open a file in File Cache App. Used by Explorer context menu / Open with.

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

if "%~1"=="" (
    echo Usage: OpenWithFileCache.bat "C:\path\to\file"
    pause
    exit /b 1
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py "%APP_DIR%\app.py" "%~1"
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%APP_DIR%\app.py" "%~1"
    exit /b %ERRORLEVEL%
)

echo Python not found.
pause
exit /b 1
