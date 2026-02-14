import csv
import json
import os
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path(os.getenv("FILE_LANDING_DIR", "./data/landing"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_ndjson(path, rows):
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row))
            handle.write("\n")


def main():
    now = datetime.now(timezone.utc).isoformat()

    claims = [
        {
            "claim_id": "C1001",
            "member_id": "M100",
            "provider_id": "P200",
            "claim_status": "PAID",
            "claim_type": "MEDICAL",
            "total_allowed_amount": 1200.00,
            "total_paid_amount": 900.00,
            "service_start_date": "2025-01-05",
            "service_end_date": "2025-01-06",
            "updated_at": now,
        },
        {
            "claim_id": "C1002",
            "member_id": "M101",
            "provider_id": "P201",
            "claim_status": "PENDING",
            "claim_type": "PHARMACY",
            "total_allowed_amount": 350.00,
            "total_paid_amount": 0.00,
            "service_start_date": "2025-01-10",
            "service_end_date": "2025-01-10",
            "updated_at": now,
        },
    ]

    claim_lines = [
        {
            "claim_line_id": "CL1001",
            "claim_id": "C1001",
            "procedure_code": "99213",
            "diagnosis_code": "E11.9",
            "units": 1,
            "allowed_amount": 1200.00,
            "paid_amount": 900.00,
            "service_date": "2025-01-05",
            "updated_at": now,
        },
        {
            "claim_line_id": "CL1002",
            "claim_id": "C1002",
            "procedure_code": "J3490",
            "diagnosis_code": "I10",
            "units": 1,
            "allowed_amount": 350.00,
            "paid_amount": 0.00,
            "service_date": "2025-01-10",
            "updated_at": now,
        },
    ]

    members = [
        {
            "member_id": "M100",
            "first_name": "Ava",
            "last_name": "Lopez",
            "date_of_birth": "1984-04-12",
            "gender": "F",
            "zip_code": "94107",
            "plan_id": "PLN1",
            "updated_at": now,
        },
        {
            "member_id": "M101",
            "first_name": "Noah",
            "last_name": "Chen",
            "date_of_birth": "1976-09-30",
            "gender": "M",
            "zip_code": "10001",
            "plan_id": "PLN2",
            "updated_at": now,
        },
    ]

    providers = [
        {
            "provider_id": "P200",
            "provider_name": "Green Valley Clinic",
            "specialty": "Internal Medicine",
            "npi": "1234567890",
            "updated_at": now,
        },
        {
            "provider_id": "P201",
            "provider_name": "Sunrise Pharmacy",
            "specialty": "Pharmacy",
            "npi": "0987654321",
            "updated_at": now,
        },
    ]

    write_csv(DATA_DIR / "claims.csv", claims, claims[0].keys())
    write_csv(DATA_DIR / "claim_lines.csv", claim_lines, claim_lines[0].keys())
    write_csv(DATA_DIR / "members.csv", members, members[0].keys())
    write_ndjson(DATA_DIR / "providers.ndjson", providers)

    print(f"Sample data written to {DATA_DIR}")


if __name__ == "__main__":
    main()
