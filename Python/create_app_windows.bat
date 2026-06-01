@echo off
REM Build CH340 Relay Controller.exe for Windows 11.

setlocal

set SCRIPT_DIR=%~dp0
set APP_NAME=CH340 Relay Controller
set PY_SCRIPT=%SCRIPT_DIR%relay_controller.py
set DIST_DIR=%SCRIPT_DIR%dist
set BUILD_DIR=%SCRIPT_DIR%build_windows
set ICON_FILE=%SCRIPT_DIR%relay_icon.ico

python -m pip install -q -r "%SCRIPT_DIR%requirements.txt"

echo Generating icon...
python "%SCRIPT_DIR%create_icon.py"

echo Building Windows EXE...
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon "%ICON_FILE%" ^
    --distpath "%DIST_DIR%" ^
    --workpath "%BUILD_DIR%" ^
    --specpath "%BUILD_DIR%" ^
    --hidden-import serial.tools.list_ports ^
    --hidden-import serial.tools.list_ports_windows ^
    "%PY_SCRIPT%"

echo.
echo Done! EXE created at:
echo   %DIST_DIR%\%APP_NAME%.exe
echo.
echo Double-click the EXE to launch it.
pause
