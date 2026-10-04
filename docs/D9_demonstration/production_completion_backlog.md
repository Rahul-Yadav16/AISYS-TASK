# Deliverable D9: Production-Completion Backlog

This backlog outlines the prioritized engineering roadmap required to transition the verified AISYS prototype into a fully certified institutional production rollout.

---

## 1. Production Readiness Work Packages

| Epic / Work Package | Priority | Description | Target Environment / Dependency |
|---|---|---|---|
| **WP-01: Vendor SDK Hardware Drivers** | P1 | Replace mock RFID serial/TCP handlers with certified vendor SDK C/C++ DLL bindings for FEIG, Nordic ID, and Impinj Speedway readers. | Physical Windows 11 client stations & USB readers. |
| **WP-02: RTSP/ONVIF Camera Integration** | P1 | Integrate live RTSP video frame capture from Hikvision / Axis institutional IP security cameras upon gate EAS trigger. | Institutional CCTV security VLAN. |
| **WP-03: Active Directory / LDAP / SAML SSO** | P2 | Extend authentication layer to support campus Kerberos, Active Directory, and SAML 2.0 / Shibboleth single sign-on. | Institutional Identity Provider (IdP). |
| **WP-04: Multi-Node Database Clustering** | P2 | Add optional PostgreSQL / MS SQL Server dialect support for distributed multi-branch library networks exceeding 2M volumes. | Enterprise SQL Cluster. |
| **WP-05: Formal ISO & SIP2 Certification** | P3 | Submit SIP2 and NCIP 2.0 implementations for formal NISO and OEM vendor certification test suites. | External standard certification labs. |
| **WP-06: Automated Windows Service Packaging** | P2 | Package the FastAPI backend as an automated Windows Service installer (MSI / Inno Setup) with automatic reboot recovery. | Windows Server 2022 service control manager. |
| **WP-07: Hardware Self-Checkout Kiosk Shell** | P2 | Build a touch-optimized electron/kiosk full-screen UI with multi-lingual audio prompting for patron self-checkout. | Touchscreen Kiosk Hardware. |

---

## 2. Transition Plan & Risk Matrix

- **Risk: Driver Incompatibility**: Mitigated by abstract `RFIDReaderInterface` isolating vendor-specific driver quirks behind Python C-types wrappers.
- **Risk: CCTV Stream Latency**: Mitigated by asynchronous background frame grabbing ensuring gate alarm buzzer triggers in < 50ms regardless of camera network latency.
