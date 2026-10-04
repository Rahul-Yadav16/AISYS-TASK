@echo off
echo =========================================
echo    Starting AISYS RFID Library Solution  
echo =========================================

if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt
)

echo Starting server on http://localhost:8000...
.venv\Scripts\python -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload
