# PowerShell script to run the RAG system

# Create necessary directories
if (-not (Test-Path "docs")) {
    New-Item -ItemType Directory -Path "docs" | Out-Null
}

# Check if backend directory exists
if (-not (Test-Path "backend")) {
    Write-Host "Error: backend directory not found" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv-new")) {
    Write-Host "Error: Virtual environment not found" -ForegroundColor Red
    Write-Host "Please run: python -m venv .venv-new" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting Course Materials RAG System..." -ForegroundColor Green
Write-Host "Make sure you have set your ANTHROPIC_API_KEY in .env" -ForegroundColor Yellow

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found. Copy .env.example to .env and add your API key." -ForegroundColor Yellow
}

# Start the server from backend directory
try {
    Write-Host "Starting uvicorn server on http://127.0.0.1:8000" -ForegroundColor Cyan
    Set-Location backend
    & "..\\.venv-new\Scripts\python.exe" -m uvicorn app:app --reload --port 8000
}
catch {
    Write-Host "Error starting server: $_" -ForegroundColor Red
    Set-Location ..
    exit 1
}
