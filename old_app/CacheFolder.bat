@echo off
REM File Cache App launcher — opens the GUI.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python "%SCRIPT_DIR%app.py"
    exit /b %ERRORLEVEL%
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py "%SCRIPT_DIR%app.py"
    exit /b %ERRORLEVEL%
)

echo Python is not installed or not on PATH.
echo Install Python 3.10+ from https://python.org and try again.
pause
exit /b 1
