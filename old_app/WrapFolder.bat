@echo off
REM Set a folder wrapper and open the GUI.
REM Usage: WrapFolder.bat "C:\path\to\target\folder"
REM    or: drag a folder onto this file

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

if "%~1"=="" (
    echo Usage: WrapFolder.bat "C:\path\to\folder"
    echo    or drag a folder onto this file.
    pause
    exit /b 1
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py "%APP_DIR%\app.py" --wrap "%~1"
    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
    py "%APP_DIR%\app.py"
    exit /b %ERRORLEVEL%
)

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%APP_DIR%\app.py" --wrap "%~1"
    if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%
    python "%APP_DIR%\app.py"
    exit /b %ERRORLEVEL%
)

echo Python not found.
pause
exit /b 1
