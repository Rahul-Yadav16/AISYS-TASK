param (
    [int]$Port = 8000
)

Write-Host "Checking for processes listening on port $Port..." -ForegroundColor Cyan
$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }

if ($connections) {
    foreach ($conn in $connections) {
        $pidToKill = $conn.OwningProcess
        Write-Host "Found listening process ID: $pidToKill on port $Port" -ForegroundColor Yellow
        try {
            $proc = Get-Process -Id $pidToKill -ErrorAction Stop
            Write-Host "Stopping process: $($proc.ProcessName) (PID: $pidToKill)..." -ForegroundColor Yellow
            Stop-Process -Id $pidToKill -Force
            Write-Host "Successfully stopped PID $pidToKill." -ForegroundColor Green
        } catch {
            Write-Host "Failed to stop PID $pidToKill : $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No process found listening on port $Port." -ForegroundColor Green
}
