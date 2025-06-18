@echo off
echo.
echo ============================================================
echo   WatchHer Surveillance System - Windows CMD Setup
echo ============================================================
echo.
echo Activating virtual environment...
cd /d "%~dp0"
call venv\Scripts\activate.bat
echo.
echo ✅ Virtual environment activated!
echo    You should see (venv) at the beginning of your prompt.
echo.
echo 🚀 You can now run:
echo    • python main.py           - Start surveillance system
echo    • python quick_test.py     - Test risk scoring  
echo    • python app.py            - Start web dashboard
echo    • python                   - Interactive Python
echo.
echo 💡 To verify GPU setup, run 'python' then:
echo    import torch; print(torch.cuda.is_available())
echo.
cmd /k 