param (
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1",
    [switch]$KillExisting = $false,
    [switch]$NoReload = $false,
    [switch]$Background = $false
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
        Write-Host "Notice: The server is ALREADY ACTIVE and running!" -ForegroundColor Green
        Write-Host "Open in browser: http://${HostAddress}:${Port}/" -ForegroundColor Cyan
        Write-Host "To restart fresh on port $Port, run:" -ForegroundColor Gray
        Write-Host "    .\scripts\run_dev.ps1 -KillExisting" -ForegroundColor White
        Write-Host "Or to run on a different port, run:" -ForegroundColor Gray
        Write-Host "    .\scripts\run_dev.ps1 -Port 8080" -ForegroundColor White
        exit 0
    }
}

if ($Background) {
    Write-Host "Starting server in BACKGROUND (Daemon Mode)..." -ForegroundColor Green
    $argsList = @("-m", "uvicorn", "src.app:app", "--host", $HostAddress, "--port", "$Port")
    $proc = Start-Process -FilePath $VenvPython -ArgumentList $argsList -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "Server successfully started in background!" -ForegroundColor Green
    Write-Host "Process ID: $($proc.Id)" -ForegroundColor Cyan
    Write-Host "Access URL: http://${HostAddress}:${Port}/" -ForegroundColor Cyan
    Write-Host "To stop the server at any time, run: .\scripts\stop_dev.ps1 -Port $Port" -ForegroundColor Gray
    exit 0
}

Write-Host "Starting server on http://${HostAddress}:${Port}..." -ForegroundColor Green
Write-Host "Tip: Press Ctrl+C in this terminal to stop the server." -ForegroundColor Gray
Write-Host "Tip: Run with -Background to keep it running independently." -ForegroundColor Gray

if ($NoReload) {
    & $VenvPython -m uvicorn src.app:app --host $HostAddress --port $Port
} else {
    # Strictly watch only src/ to prevent OneDrive file-sync interference with data/ or logs
    & $VenvPython -m uvicorn src.app:app --host $HostAddress --port $Port --reload --reload-dir src
}


