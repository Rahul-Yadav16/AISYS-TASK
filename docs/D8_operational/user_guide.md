# Deliverable D8: Staff & Patron User Operations Guide

## 1. Circulation Desk Operations

### 1.1 Checking Out an Item (Lending)
1. In the **Circulation Desk** view, enter the Patron ID (e.g., `MEM-1001`) or tap the patron's smart card on the desk reader.
2. Place the physical book(s) on the RFID staff station antenna pad.
3. The system scans the tag UID or accession number automatically.
4. Click **Authorize Check-Out**.
5. The system verifies:
   - Patron is not blocked.
   - Patron does not have outstanding fines exceeding policy limit ($10.00).
   - Item is not designated as Reference Material.
6. Upon approval, the system disarms the RFID tag's EAS security bit (set to `0x01` - Disarmed), sounds a confirmation chime (880Hz), and displays the calculated due date.

### 1.2 Returning an Item (Check-In)
1. Place the returned book on the staff station reader.
2. Enter the item barcode or accession number in **Desk Check-In**.
3. Click **Process Item Return**.
4. The system updates the loan record, calculates overdue fines if returned late, rearms the tag EAS security bit (set to `0x00` - Armed), and displays the destination shelf location.

---

## 2. Cataloguing & RFID Tag Encoding

### 2.1 Encoding New RFID Item Tags
1. Navigate to **RFID Staff Station**.
2. Enter the physical copy accession number (e.g. `ACC-005001`) and click **Validate Item Record**.
3. Place a blank RFID label tag on the writer antenna.
4. Enter or scan the tag UID (e.g. `E00401509988A501`).
5. Click **Encode & Bind Tag to Item**.
6. The system programs the memory blocks, arms the EAS bit (`0x00`), links the database record, and emits an audible confirmation chime.

### 2.2 Generating Spine Labels
1. In **OPAC & Catalog**, find the target title and click **Spine Label**.
2. The modal displays a standard call-number spine label and barcode slip formatted in SVG for direct printing on thermal adhesive stock.

---

## 3. Handheld RFID Shelf Inventory

### 3.1 Conducting a Shelf Sweep
1. Open the **Handheld Inventory** view on a tablet or mobile workstation.
2. Enter the audit name and select the target shelf (e.g. `Shelf-A-01`).
3. Click **Start Audit Session**.
4. Sweep the RFID wand smoothly across the book spines.
5. Pay attention to auditory cues:
   - **Single High Beep (880Hz)**: Book is in the correct place.
   - **Double Pulse Warning (440Hz)**: Book is misplaced! Check screen for actual assigned shelf.
6. When finished scanning the shelf, click **Finalize Audit**.
7. The system compares scans against catalog records and presents a list of any **Missing Items**.
