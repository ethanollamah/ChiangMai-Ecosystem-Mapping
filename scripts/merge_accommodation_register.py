"""Merge the six accommodation-check batches with the extracted directory into one register."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP1 = ROOT / "outputs" / "step1"
DIR_CSV = STEP1 / "private_childcare_directory_2025.csv"
OUT_JSON = STEP1 / "accommodation_register.json"
OUT_CSV = STEP1 / "accommodation_register.csv"
OUT_UNRESOLVED = STEP1 / "accommodation_unresolved_cases.csv"

DISTRICT_FIX = {"147": "เชียงดาว"}


def main():
    directory = list(csv.DictReader(DIR_CSV.open(encoding="utf-8-sig")))
    by_row = {r["row_no"]: r for r in directory}
    checks = []
    for i in range(1, 7):
        checks.extend(json.loads((STEP1 / "accommodation_results" / f"batch_{i}.json").read_text(encoding="utf-8")))
    if [c["row_no"] for c in checks] != [str(i) for i in range(1, 149)]:
        raise SystemExit(f"Expected rows 1-148 in order; got {[c['row_no'] for c in checks][:5]}…{[c['row_no'] for c in checks][-3:]}")

    register = []
    for c in checks:
        d = by_row[c["row_no"]]
        district = DISTRICT_FIX.get(c["row_no"], d["district_th"])
        register.append({
            "row_no": c["row_no"],
            "source_page": d["source_page"],
            "facility_name_th": d["facility_name_th"],
            "facility_name_en": c.get("facility_name_en", ""),
            "operator_th": d["operator_th"],
            "address_th": d["address_th"],
            "district_th": district,
            "district_th_raw": d["district_th"],
            "phone": d["phone"],
            "online_contact": d["online_contact"],
            "licensed_age_range_th": d["licensed_age_range_th"],
            "status_th": d["status_th"],
            "fee_th": d["fee_th"],
            "licence": d["licence"],
            "ssc_affiliation": d["ssc_affiliation"],
            "administrative_licence_category": "สถานรับเลี้ยงเด็กเอกชน (licensed private childcare)",
            "evidenced_model": c["evidenced_model"],
            "confidence": c["confidence"],
            "evidence_th": c.get("evidence_th", ""),
            "evidence_en": c.get("evidence_en", ""),
            "operating_hours_found": c.get("operating_hours_found", ""),
            "stay_length_pattern": c.get("stay_length_pattern", ""),
            "identity_match_basis": c.get("identity_match_basis", ""),
            "needs_partner_verification": c.get("needs_partner_verification", True),
            "notes": c.get("notes", ""),
            "evidence_sources": c.get("evidence_sources", []),
            "searches_run": c.get("searches_run", []),
            "check_date": "2026-11-10",
            "in_core_nonprofit_count": False,
        })

    OUT_JSON.write_text(json.dumps(register, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    csv_fields = [
        "row_no", "source_page", "facility_name_th", "facility_name_en", "district_th",
        "status_th", "licensed_age_range_th", "administrative_licence_category",
        "evidenced_model", "confidence", "operating_hours_found", "stay_length_pattern",
        "evidence_th", "evidence_en", "identity_match_basis", "needs_partner_verification",
        "in_core_nonprofit_count", "notes", "phone", "online_contact", "fee_th",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(register)

    watch = {"unresolved", "identity_not_confirmed", "occasional_overnight_or_respite",
             "recurring_boarding", "long_term_residential", "mixed_provision"}
    flagged = [r for r in register if r["evidenced_model"] in watch]
    with OUT_UNRESOLVED.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(flagged)

    counts = Counter(r["evidenced_model"] for r in register)
    print("register", len(register), dict(counts))
    print("flagged", len(flagged))
    print("partner_verification", sum(1 for r in register if r["needs_partner_verification"] is True))


if __name__ == "__main__":
    main()
