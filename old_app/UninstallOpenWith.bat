@echo off
REM Remove File Cache App from the all-files right-click menu.

reg delete "HKCU\Software\Classes\*\shell\FileCacheApp" /f >nul 2>&1

echo Removed "Open with File Cache App" from the right-click menu.
pause
