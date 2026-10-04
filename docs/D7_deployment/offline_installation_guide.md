# Deliverable D7: Offline Installation Guide (Air-Gapped Environment)

## 1. Scope & Prerequisites
This runbook guides system administrators in deploying the AISYS RFID Library Management System in completely isolated, air-gapped institutional environments on **Windows 11** or **Windows Server 2022+**.

### Hardware Requirements
- **Processor**: Intel Core i5 / Xeon 4-core @ 2.5GHz or better
- **RAM**: 8 GB minimum (16 GB recommended for high concurrent turnover)
- **Disk Storage**: 50 GB free NVMe/SSD storage for application, SQLite database, and CCTV surveillance snapshots
- **Network Interface**: 1 Gbps Ethernet controller (Static institutional IP recommended)

### Software Prerequisites
- Windows 11 Enterprise / Windows Server 2022 64-bit
- Python 3.12 64-bit pre-installed or embedded
- Microsoft Edge Chromium or Google Chrome for local kiosk display

---

## 2. Air-Gapped Media Transfer Procedure
1. On an internet-connected staging machine, bundle the repository and local pip wheelhouse:
   ```powershell
   pip wheel -r requirements.txt -w ./wheelhouse
   ```
2. Copy the entire repository directory (`AISYS`) including the `wheelhouse/` folder to a secure, virus-scanned USB flash drive or physical installation media.
3. Mount the media onto the air-gapped target server at `C:\AISYS`.

---

## 3. Step-by-Step Installation Commands

### Step 1: Open Elevated PowerShell
Open PowerShell as Administrator and navigate to the project directory:
```powershell
cd C:\AISYS
```

### Step 2: Initialize Offline Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Offline Wheels (No Internet Required)
```powershell
pip install --no-index --find-links=./wheelhouse -r requirements.txt
```

### Step 4: Run Automated Offline Environment Installer
Execute the self-verifying installer utility:
```powershell
python tools/offline_installer.py --install
```
This utility:
- Validates disk write permissions and free capacity.
- Applies baseline schema migrations `V1__initial_schema.sql` and `V2__additional_indexes.sql`.
- Populates synthetic administrative, catalog, and patron seed data.
- Configures SQLite WAL mode and FTS5 full-text search indexes.

### Step 5: Launch the Server
```powershell
.\scripts\run_dev.ps1
```
The server will start on `http://0.0.0.0:8000`.

### Step 6: Verify Service Readiness
Open Microsoft Edge and navigate to `http://localhost:8000/`.
Verify that the Dashboard displays baseline counts, and navigate to `/api/admin/health` to confirm the diagnostic status reports `"status": "HEALTHY"`.
