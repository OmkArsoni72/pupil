@echo off
echo Starting PupilPrep Frontend and Backend...
echo.

REM Start Backend
echo Starting Backend on port 8080...
start "PupilPrep Backend" python simple_server_new.py

REM Wait a second
timeout /t 2 /nobreak

REM Start Frontend
echo Starting Frontend on port 3000...
cd frontend
call npm run dev
