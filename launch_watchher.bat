@echo off
echo =====================================================
echo    WatchHer - Intelligent Public Safety Monitoring
echo =====================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Launching WatchHer Desktop Application...
python launch_watchher.py --app watchher

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch WatchHer
    echo Please check that all dependencies are installed:
    echo    pip install -r requirements.txt
    echo.
    pause
) 