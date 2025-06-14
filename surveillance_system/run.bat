@echo off
echo ================================================================================
echo                    WatchHer Surveillance System - Windows Launcher
echo                      Context-Aware Threat Analysis System
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.9+ and add it to your system PATH.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python detected. Checking dependencies...

REM Install required packages if needed
echo [INFO] Installing/updating required packages...
pip install opencv-python numpy tensorflow pillow python-dotenv requests

if errorlevel 1 (
    echo [WARNING] Some packages may have failed to install.
    echo The system may still work if packages were already installed.
    echo.
)

REM Check if basic models exist
echo [INFO] Checking for AI models...
if not exist "models\gender_net.caffemodel" (
    echo [INFO] Basic models not found. Downloading...
    python download_models.py
    if errorlevel 1 (
        echo [ERROR] Failed to download basic models.
        pause
        exit /b 1
    )
)

REM Check if advanced models exist
if not exist "models\yolov3-tiny.weights" (
    echo [INFO] Advanced models not found. Downloading...
    python download_advanced_models.py
    if errorlevel 1 (
        echo [ERROR] Failed to download advanced models.
        pause
        exit /b 1
    )
)

echo [INFO] All models are ready!
echo.

REM Check if video file exists
if not exist "C:\Users\prath\Downloads\delhigully.webm" (
    echo [WARNING] Test video file not found at: C:\Users\prath\Downloads\delhigully.webm
    echo Please ensure the video file exists or update the path in config.py
    echo.
    echo Press any key to continue anyway, or Ctrl+C to exit...
    pause >nul
)

echo ================================================================================
echo                           Starting WatchHer System
echo ================================================================================
echo [INFO] Launching Context-Aware Threat Analysis System...
echo [INFO] Processing video: C:\Users\prath\Downloads\delhigully.webm
echo [INFO] Press Ctrl+C to stop the system
echo.

REM Run the main surveillance system
python main.py

REM Handle exit
echo.
echo ================================================================================
echo [INFO] WatchHer System has stopped.
echo ================================================================================
pause 