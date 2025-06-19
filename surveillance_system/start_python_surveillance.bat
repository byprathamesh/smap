@echo off
echo ===================================
echo   WatchHer Surveillance System
echo   Unified Reflex Application
echo ===================================
echo.

echo [INFO] Activating Python virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking Reflex installation...
python -m pip show reflex > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Reflex not found. Installing...
    python -m pip install reflex
)

echo [INFO] Starting unified surveillance system...
echo [INFO] Access the system at: http://localhost:3000
echo [INFO] Press Ctrl+C to stop the system
echo.

reflex run

pause 