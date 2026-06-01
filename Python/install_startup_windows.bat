@echo off
REM Install CH340 Relay Controller.exe to run at Windows startup.

setlocal

set SCRIPT_DIR=%~dp0
set APP_NAME=CH340 Relay Controller
set APP_EXE=%SCRIPT_DIR%dist\%APP_NAME%.exe
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT=%STARTUP%\%APP_NAME%.lnk

if not exist "%APP_EXE%" (
    call "%SCRIPT_DIR%create_app_windows.bat"
)

if not exist "%APP_EXE%" (
    echo ERROR: Could not find:
    echo   "%APP_EXE%"
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$sc = $ws.CreateShortcut('%SHORTCUT%'); " ^
    "$sc.TargetPath = '%APP_EXE%'; " ^
    "$sc.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$sc.IconLocation = '%APP_EXE%'; " ^
    "$sc.Save()"

echo Startup shortcut created at:
echo   %SHORTCUT%
echo.
echo The app will launch automatically at next login.
echo To run now, double-click:
echo   %APP_EXE%
pause
