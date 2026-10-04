# Build standalone offline distribution package for AISYS
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Building AISYS Standalone Offline Package   " -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

$TargetDir = "dist\aisys_offline_v1.0.0"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
New-Item -ItemType Directory -Force -Path "$TargetDir\wheelhouse" | Out-Null

Write-Host "1. Downloading offline wheels into wheelhouse..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip wheel -r requirements.txt -w "$TargetDir\wheelhouse"

Write-Host "2. Copying source files and documentation..." -ForegroundColor Yellow
Copy-Item -Recurse -Force src, config, data, docs, tools, scripts, requirements.txt, LICENSE, SBOM.json, README.md $TargetDir

Write-Host "3. Creating distribution zip archive..." -ForegroundColor Yellow
Compress-Archive -Path "$TargetDir\*" -DestinationPath "dist\aisys_offline_v1.0.0.zip" -Force

Write-Host "Offline package built successfully at: dist\aisys_offline_v1.0.0.zip" -ForegroundColor Green
