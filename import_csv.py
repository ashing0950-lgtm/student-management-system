"""
import_csv.py
Bulk-import students from a CSV file into the Student Management System.

Expected CSV columns (case-sensitive header row):
    StudentID, FirstName, LastName, DateOfBirth, Email, Phone, Address,
    Department, EnrollmentYear, CGPA

Usage:
    python import_csv.py path/to/students.csv --university <uni_id> --college <college_id>

If a row's email or StudentID already exists in the database, that row is
skipped and reported in the summary at the end (nothing is overwritten).
"""

import csv
import sys
import argparse
from database import initialize_database  # <- YAHA FIX KIYA: Sahi naam import kiya
import models


def parse_row(row, university_id, college_id):
    """Convert a raw CSV row (dict of strings) into the fields add_student expects."""
    def clean(value):
        value = (value or "").strip()
        return value or None

    enrollment_year = clean(row.get("EnrollmentYear"))
    cgpa = clean(row.get("CGPA"))

    return {
        "external_id": clean(row.get("StudentID")),
        "first_name": clean(row.get("FirstName")),
        "last_name": clean(row.get("LastName")),
        "email": clean(row.get("Email")),
        "date_of_birth": clean(row.get("DateOfBirth")),
        "phone": clean(row.get("Phone")),
        "address": clean(row.get("Address")),
        "department": clean(row.get("Department")),
        "enrollment_year": int(enrollment_year) if enrollment_year else None,
        "cgpa": float(cgpa) if cgpa else None,
        "university_id": university_id,
        "college_id": college_id,
    }


def load_csv(path, university_id, college_id):
    records = []
    row_errors = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 is the header
            try:
                rec = parse_row(row, university_id, college_id)
                if not rec["email"] or not rec["first_name"] or not rec["last_name"]:
                    row_errors.append((i, "Missing required field (name or email)"))
                    continue
                records.append(rec)
            except ValueError as e:
                row_errors.append((i, f"Bad numeric value: {e}"))
    return records, row_errors


def main():
    parser = argparse.ArgumentParser(description="Bulk-import students from a CSV file.")
    parser.add_argument("csv_path", help="Path to the students CSV file")
    parser.add_argument("--university", type=int, required=True, help="Target University ID")
    parser.add_argument("--college", type=int, required=True, help="Target College ID")
    
    args = parser.parse_args()

    # YAHA FIX KIYA: Sahi function call kiya database setup ke liye
    initialize_database()

    print(f"Reading {args.csv_path} ...")
    records, row_errors = load_csv(args.csv_path, args.university, args.college)
    print(f"Parsed {len(records)} valid rows ({len(row_errors)} rows had errors).")

    if not records:
        print("Nothing to import.")
        return

    print("Importing into the database (this may take a moment for large files)...")
    inserted, skipped = models.bulk_import_students(
        records, 
        default_university_id=args.university, 
        default_college_id=args.college
    )

    print("\n--- Import Summary ---")
    print(f"Inserted:             {inserted}")
    print(f"Skipped (duplicates or errors): {len(skipped)}")
    print(f"Rows with parse errors:         {len(row_errors)}")

    if skipped:
        print("\nFirst 10 skipped records:")
        for rec, err in skipped[:10]:
            print(f"  - {rec.get('email')} ({rec.get('external_id')}): {err}")

    if row_errors:
        print("\nFirst 10 rows with parse errors:")
        for line_no, err in row_errors[:10]:
            print(f"  - Line {line_no}: {err}")

    print("\nDone.")


if __name__ == "__main__":
    main()