# Deliverable D7: Pre-Flight Environment Verification Checklist

Before deploying AISYS into production or isolated institutional evaluation, verify each requirement:

| Category | Verification Item | Required Standard | Status |
|---|---|---|---|
| **Operating System** | Windows 11 Enterprise (64-bit) or Windows Server 2022 | Build 22000+ / Server 2022 Datacenter | Verified |
| **Python Runtime** | Python 3.12 (64-bit) | Version 3.12.0+ with standard library | Verified |
| **Network Isolation** | Isolated Ethernet LAN | Subnet 192.168.10.0/24 without internet gateway | Verified |
| **Firewall Inbound** | Port 8000 (HTTP/WS API) & Port 6001 (SIP2 Socket) | Open on private network profile | Verified |
| **Disk Storage** | Free disk capacity | Minimum 5.0 GB free SSD storage | Verified |
| **Disk Permissions** | Write permissions for `storage/` and `data/` | Full Read/Write/Modify for service account | Verified |
| **Browser Display** | Microsoft Edge Chromium | Version 110+ in Kiosk mode for self-check | Verified |
| **Dependencies** | Offline Wheelhouse | All 27 dependencies pinned in `requirements.txt` | Verified |
| **Security Secrets** | Dedicated `config/production_config.json` | Generated 32-byte secret key outside source control | Verified |
| **Synthetic Seed Data**| Zero real PII data committed | 100% synthetic patron/bib records verified | Verified |
