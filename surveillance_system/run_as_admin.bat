@echo off
echo Starting WatchHer with Administrative Privileges...
echo.
echo If Windows asks for permission, click "Yes"
echo.

cd /d "%~dp0"
echo Current directory: %CD%
echo.

echo Testing Python availability...
python --version
echo.

echo Starting WatchHer surveillance system...
echo Navigate to: http://127.0.0.1:5000/
echo.
echo Press Ctrl+C to stop the server
echo.

python -c "print('=== WatchHer Startup ==='); import app; print('Starting Flask server...'); app.app.run(host='0.0.0.0', port=5000, debug=False)"

pause 