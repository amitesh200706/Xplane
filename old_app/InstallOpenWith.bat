@echo off
REM Add File Cache App to the right-click menu for every file type.

set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"
set "LAUNCHER=%APP_DIR%\OpenWithFileCache.bat"
set "KEY=HKCU\Software\Classes\*\shell\FileCacheApp"

if not exist "%LAUNCHER%" (
    echo Missing launcher: %LAUNCHER%
    pause
    exit /b 1
)

reg add "%KEY%" /ve /d "Open with File Cache App" /f >nul
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

reg add "%KEY%" /v "Icon" /d "%SystemRoot%\System32\shell32.dll,167" /f >nul
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

reg add "%KEY%\command" /ve /d "\"%LAUNCHER%\" \"%%1\"" /f >nul
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

echo Installed. Right-click any file and choose "Open with File Cache App".
pause
