@echo off
echo Starting Universal Clipboard Server...

:: Start the Python server in a NEW window so you can easily close it later
start "Clipboard Server" cmd /c "python app.py"

:: Wait 2 seconds to give the server time to wake up
timeout /t 2 >nul

:: Open your default web browser directly to the local address
start http://localhost:5000