@echo off
echo ================================================
echo    PupilPrep - Quick Start Script
echo ================================================
echo.

echo [1/4] Checking Node.js installation...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)
echo     Node.js found: 
node --version
echo.

echo [2/4] Checking Python installation...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo     Python found: 
python --version
echo.

echo [3/4] Setting up Frontend...
cd frontend
if not exist "node_modules" (
    echo     Installing frontend dependencies...
    call npm install
) else (
    echo     Dependencies already installed
)
cd ..
echo.

echo [4/4] Setup complete!
echo.
echo ================================================
echo    To start the application:
echo ================================================
echo.
echo 1. Start Backend (Terminal 1):
echo    python main.py
echo.
echo 2. Start Frontend (Terminal 2):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Open browser:
echo    http://localhost:3000
echo.
echo ================================================
echo    Demo Accounts:
echo ================================================
echo    Teacher: teacher@demo.com / password123
echo    Student: student@demo.com / password123
echo ================================================
echo.
pause
