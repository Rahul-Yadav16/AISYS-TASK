# Run automated test suite for AISYS
Write-Host "Running AISYS Automated Test Suite..." -ForegroundColor Cyan
.\.venv\Scripts\pytest -v --tb=short
