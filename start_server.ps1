# Startup script for AI Chatbot using Waitress (Windows PowerShell)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Starting AI Chatbot Server with Waitress" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Warning: Virtual environment not found" -ForegroundColor Red
}

# Get port from .env or use default
$PORT = 80

Write-Host ""
Write-Host "Server Configuration:" -ForegroundColor Green
Write-Host "- Host: 0.0.0.0 (all interfaces)"
Write-Host "- Port: $PORT"
Write-Host "- WSGI Server: Waitress"
Write-Host "- Flask App: index:app"
Write-Host ""

# Check if running as administrator (required for port 80)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($PORT -eq 80 -and -not $isAdmin) {
    Write-Host "WARNING: Port 80 requires administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator or use a different port (e.g., 5000)" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit
    }
}

# Run with Waitress
Write-Host "Starting server..." -ForegroundColor Green
waitress-serve --host=0.0.0.0 --port=$PORT --threads=4 index:app
