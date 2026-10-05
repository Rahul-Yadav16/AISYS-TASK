param (
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1",
    [switch]$KillExisting = $false
)

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

# Check if port is already in use
$activeConn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }
if ($activeConn) {
    $existingPid = $activeConn[0].OwningProcess
    Write-Host "Port $Port is currently in use by Process ID: $existingPid" -ForegroundColor Yellow
    
    if ($KillExisting) {
        Write-Host "Terminating process $existingPid..." -ForegroundColor Yellow
        Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Notice: The server appears to ALREADY BE RUNNING!" -ForegroundColor Green
        Write-Host "You can open http://localhost:$Port directly in your browser." -ForegroundColor Cyan
        Write-Host "To force-restart on port $Port, run:" -ForegroundColor Gray
        Write-Host "    .\scripts\run_dev.ps1 -KillExisting" -ForegroundColor White
        Write-Host "Or to run on a different port, run:" -ForegroundColor Gray
        Write-Host "    .\scripts\run_dev.ps1 -Port 8080" -ForegroundColor White
        exit 0
    }
}

Write-Host "Starting server on http://${HostAddress}:${Port}..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray
& $VenvPython -m uvicorn src.app:app --host $HostAddress --port $Port --reload

