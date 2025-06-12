@echo off
echo Starting Turkish Legal Document Parser...
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements_local.txt

REM Create uploads directory
if not exist "static\uploads" (
    mkdir static\uploads
)

REM Set environment variable for session secret
set SESSION_SECRET=your-secret-key-change-this-in-production

REM Start the application
echo Starting application...
echo Application will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
python main.py

pause