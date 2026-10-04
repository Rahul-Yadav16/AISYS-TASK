"""
Synthetic 20,000 Record Spreadsheet Generator for AISYS.
Generates realistic bibliographic and item records with controlled edge cases:
- 19,850 Valid records
- 100 Invalid rows (missing mandatory title, author, or barcode)
- 50 Duplicate records (repeating barcodes or accession numbers)
Fulfills FR 10, AC 01, NFR 02.
"""
import csv
import os
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "sample_import_20000.csv"

DISCIPLINES = [
    ("Computer Science", "005", ["Algorithms", "Data Structures", "Operating Systems", "Networking", "AI", "Cloud Computing"]),
    ("Physics", "530", ["Quantum Mechanics", "Thermodynamics", "Electromagnetism", "Astrophysics", "Optics"]),
    ("Mathematics", "510", ["Linear Algebra", "Calculus", "Probability", "Discrete Math", "Number Theory"]),
    ("Economics", "330", ["Microeconomics", "Macroeconomics", "Econometrics", "Game Theory", "Finance"]),
    ("Literature", "800", ["Modern Fiction", "Poetry", "Literary Theory", "Drama", "World Literature"]),
    ("Medicine", "610", ["Anatomy", "Physiology", "Biochemistry", "Pathology", "Pharmacology"])
]

PUBLISHERS = ["Academic Press", "MIT Press", "Oxford University Press", "Springer", "Wiley", "Pearson", "Routledge", "Cambridge University Press"]
AUTHORS = [
    "Alan Turing", "Ada Lovelace", "Claude Shannon", "John von Neumann",
    "Richard Feynman", "Marie Curie", "Albert Einstein", "Stephen Hawking",
    "John Nash", "Adam Smith", "Milton Friedman", "Amartya Sen",
    "Virginia Woolf", "George Orwell", "Jane Austen", "William Shakespeare"
]

def generate_sample_dataset(total_records: int = 20000, output_path: str = str(OUTPUT_FILE)):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    print(f"Generating {total_records} synthetic bibliographic records...")

    # Planned distribution:
    # Valid: total_records - 150
    # Invalid: 100
    # Duplicate: 50
    invalid_target = 100
    duplicate_target = 50
    valid_target = total_records - invalid_target - duplicate_target

    rows = []
    seen_barcodes = []

    # 1. Generate Valid Records
    for i in range(1, valid_target + 1):
        disc, ddc, topics = random.choice(DISCIPLINES)
        topic = random.choice(topics)
        author = random.choice(AUTHORS) + f" ({i})"
        title = f"Principles of {topic}: Volume {i % 10 + 1}"
        isbn = f"978{random.randint(1000000000, 9999999999)}"
        pub = random.choice(PUBLISHERS)
        year = random.randint(1990, 2025)
        call_num = f"{ddc}.{i % 100:02d} {author[:3].upper()}"
        acc_num = f"MIG-{i:06d}"
        barcode = f"BC-MIG-{i:06d}"
        shelf = f"Shelf-{'ABCDEF'[i % 6]}-{(i % 20) + 1:02d}"
        is_ref = 1 if (i % 50 == 0) else 0

        rows.append({
            "title": title,
            "author": author,
            "isbn": isbn,
            "publisher": pub,
            "publication_year": year,
            "edition": f"{((i % 5) + 1)}th Edition",
            "call_number": call_num,
            "subject": f"{disc}, {topic}",
            "material_type": "REFERENCE" if is_ref else "BOOK",
            "shelf_location": shelf,
            "accession_number": acc_num,
            "barcode": barcode,
            "is_reference": is_ref
        })
        seen_barcodes.append((acc_num, barcode, title, author, call_num, shelf))

    # 2. Inject Invalid Rows (Missing mandatory fields)
    for j in range(1, invalid_target + 1):
        defect_type = j % 3
        if defect_type == 0:
            # Missing Title
            rows.append({
                "title": "",
                "author": f"Author Defect {j}",
                "isbn": "9781111111111",
                "publisher": "Defect Press",
                "publication_year": 2022,
                "edition": "1st",
                "call_number": "000.00 DEF",
                "subject": "Testing",
                "material_type": "BOOK",
                "shelf_location": "Shelf-A-01",
                "accession_number": f"INV-ACC-{j:04d}",
                "barcode": f"INV-BC-{j:04d}",
                "is_reference": 0
            })
        elif defect_type == 1:
            # Missing Barcode
            rows.append({
                "title": f"Title Without Barcode {j}",
                "author": f"Author Defect {j}",
                "isbn": "9782222222222",
                "publisher": "Defect Press",
                "publication_year": 2022,
                "edition": "1st",
                "call_number": "000.00 DEF",
                "subject": "Testing",
                "material_type": "BOOK",
                "shelf_location": "Shelf-A-01",
                "accession_number": f"INV-ACC-NOBC-{j:04d}",
                "barcode": "", # Empty barcode!
                "is_reference": 0
            })
        else:
            # Missing Call Number
            rows.append({
                "title": f"Title Without Call Number {j}",
                "author": f"Author Defect {j}",
                "isbn": "9783333333333",
                "publisher": "Defect Press",
                "publication_year": 2022,
                "edition": "1st",
                "call_number": "", # Empty Call Number!
                "subject": "Testing",
                "material_type": "BOOK",
                "shelf_location": "Shelf-A-01",
                "accession_number": f"INV-ACC-NOCALL-{j:04d}",
                "barcode": f"INV-BC-NOCALL-{j:04d}",
                "is_reference": 0
            })

    # 3. Inject Duplicate Rows (Duplicate barcode or accession from already generated records)
    for k in range(1, duplicate_target + 1):
        target_dup = seen_barcodes[k * 10]
        rows.append({
            "title": f"Duplicate Copy of: {target_dup[2]}",
            "author": target_dup[3],
            "isbn": "9789999999999",
            "publisher": "Duplicate Reprints",
            "publication_year": 2024,
            "edition": "Duplicate Edition",
            "call_number": target_dup[4],
            "subject": "Duplicate Test",
            "material_type": "BOOK",
            "shelf_location": target_dup[5],
            "accession_number": f"DUP-{k:04d}",
            "barcode": target_dup[1], # Exact duplicate barcode!
            "is_reference": 0
        })

    # Shuffle slightly so defects are distributed
    random.seed(42)
    random.shuffle(rows)

    fieldnames = [
        "title", "author", "isbn", "publisher", "publication_year",
        "edition", "call_number", "subject", "material_type",
        "shelf_location", "accession_number", "barcode", "is_reference"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} records in {output_path} (Valid: {valid_target}, Invalid: {invalid_target}, Duplicate: {duplicate_target})")
    return output_path

if __name__ == "__main__":
    generate_sample_dataset()
