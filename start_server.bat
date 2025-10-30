@echo off
REM Startup script for AI Chatbot using Waitress (Windows)

echo ================================================
echo Starting AI Chatbot Server with Waitress
echo ================================================

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
)

REM Get port from .env or use default
set PORT=80

echo.
echo Server Configuration:
echo - Host: 0.0.0.0 (all interfaces)
echo - Port: %PORT%
echo - WSGI Server: Waitress
echo - Flask App: index:app
echo.

REM Run with Waitress
echo Starting server...
waitress-serve --host=0.0.0.0 --port=%PORT% --threads=4 index:app
