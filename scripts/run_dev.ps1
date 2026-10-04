# PowerShell execution script for AISYS
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting AISYS RFID Library Solution  " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$VenvPython = ".\.venv\Scripts\python.exe"
if (-Not (Test-Path $VenvPython)) {
    Write-Host "Virtual environment not found! Creating .venv..." -ForegroundColor Yellow
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -r requirements.txt
}

Write-Host "Starting server on http://localhost:8000..." -ForegroundColor Green
& $VenvPython -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
