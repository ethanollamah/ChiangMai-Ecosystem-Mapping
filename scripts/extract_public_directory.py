"""Extract the 2025 Chiang Mai public children's-homes directory.

Source PDF is one landscape page with three headed lists:
  ทำเนียบสถานสงเคราะห์เด็กภาครัฐ (2 welfare homes)
  ทำเนียบสถานแรกรับเด็กภาครัฐ (1 reception / family shelter)
  สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดเชียงใหม่ (1 juvenile centre)

These are not interchangeable service types. None of the four names appear in the
29 October organisation-location audit. Juvenile-justice stays separately labelled.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "raw" / "project_snapshot" / "public_directory.pdf"
OUT = ROOT / "outputs" / "step1" / "public_childrens_homes_2025.csv"

# Canonical rows after visual read of page 1. PyMuPDF table extract scrambles Thai
# combining marks; get_text preserves the names used here.
ROWS = [
    {
        "section_th": "ทำเนียบสถานสงเคราะห์เด็กภาครัฐ จังหวัดเชียงใหม่",
        "facility_type": "public_welfare_home",
        "facility_type_en": "Public children's welfare home",
        "core_universe_role": "public_welfare",
        "directory_row": 1,
        "facility_name_th": "สถานสงเคราะห์เด็กชายบ้านเชียงใหม่",
        "facility_name_en": "Chiang Mai Boys' Welfare Home (Ban Chiang Mai)",
        "address_th": "63/1 หมู่ 4 ต.ดอนแก้ว อ.แม่ริม จ.เชียงใหม่ 50180",
        "tambon_th": "ดอนแก้ว",
        "district_th": "แม่ริม",
        "district_en": "Mae Rim",
        "district_code": "5007",
        "head_th": "นางเพทาย เมฆี ผู้ปกครองสถานสงเคราะห์เด็กชายบ้านเชียงใหม่",
        "phone": "0 5312 1157-60",
        "fax": "0 5312 1160",
        "notes_th": "",
        "audit_match": "not_in_29_oct_audit",
        "campus_note": "Adjacent Don Kaeo public campus with rows 2 and 3 (63/1, 63/3, 63/4).",
    },
    {
        "section_th": "ทำเนียบสถานสงเคราะห์เด็กภาครัฐ จังหวัดเชียงใหม่",
        "facility_type": "public_welfare_home",
        "facility_type_en": "Public children's welfare home",
        "core_universe_role": "public_welfare",
        "directory_row": 2,
        "facility_name_th": "สถานสงเคราะห์เด็กบ้านเวียงพิงค์",
        "facility_name_en": "Ban Wiang Phing Children's Welfare Home",
        "address_th": "63/3 หมู่ 4 ต.ดอนแก้ว อ.แม่ริม จ.เชียงใหม่ 50180",
        "tambon_th": "ดอนแก้ว",
        "district_th": "แม่ริม",
        "district_en": "Mae Rim",
        "district_code": "5007",
        "head_th": "นางสาวอรุณี นะมะมุติ ผู้ปกครองสถานสงเคราะห์เด็กบ้านเวียงพิงค์",
        "phone": "0 5312 1161-63",
        "fax": "0 5312 1162",
        "notes_th": "",
        "audit_match": "not_in_29_oct_audit",
        "campus_note": "Adjacent Don Kaeo public campus with rows 1 and 3 (63/1, 63/3, 63/4).",
    },
    {
        "section_th": "ทำเนียบสถานแรกรับเด็กภาครัฐ จังหวัดเชียงใหม่",
        "facility_type": "public_reception_home",
        "facility_type_en": "Public children's reception / family shelter",
        "core_universe_role": "public_reception",
        "directory_row": 1,
        "facility_name_th": "บ้านพักเด็กและครอบครัวจังหวัดเชียงใหม่",
        "facility_name_en": "Chiang Mai Children's and Family Shelter",
        "address_th": "63/4 หมู่ 4 ตำบลดอนแก้ว อำเภอแม่ริม จังหวัดเชียงใหม่ 50180",
        "tambon_th": "ดอนแก้ว",
        "district_th": "แม่ริม",
        "district_en": "Mae Rim",
        "district_code": "5007",
        "head_th": "นางสายวรุณ ศรีจินดา หัวหน้าบ้านพักเด็กและครอบครัวจังหวัดเชียงใหม่",
        "phone": "0 5312 1036",
        "fax": "0 5312 1164",
        "notes_th": "",
        "audit_match": "not_in_29_oct_audit",
        "campus_note": "Adjacent Don Kaeo public campus with welfare homes (63/1, 63/3, 63/4).",
    },
    {
        "section_th": "สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดเชียงใหม่",
        "facility_type": "juvenile_observation_protection",
        "facility_type_en": "Juvenile observation and protection centre",
        "core_universe_role": "juvenile_justice_separately_labelled",
        "directory_row": 1,
        "facility_name_th": "สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดเชียงใหม่",
        "facility_name_en": "Chiang Mai Juvenile Observation and Protection Centre",
        "address_th": "309 หมู่ที่ 3 ตำบลแม่สา อำเภอแม่ริม จังหวัดเชียงใหม่ 50180",
        "tambon_th": "แม่สา",
        "district_th": "แม่ริม",
        "district_en": "Mae Rim",
        "district_code": "5007",
        "head_th": "นายเทอดธรรม อดิศัยเดชรินทร์ ผู้อำนวยการสถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดเชียงใหม่",
        "phone": "0 5329 7405",
        "fax": "0 5329 9485",
        "notes_th": "",
        "audit_match": "not_in_29_oct_audit",
        "campus_note": "Separate Mae Sa site; not the Don Kaeo welfare/reception campus.",
    },
]

FIELDS = [
    "section_th", "facility_type", "facility_type_en", "core_universe_role",
    "directory_row", "facility_name_th", "facility_name_en", "address_th",
    "tambon_th", "district_th", "district_en", "district_code",
    "head_th", "phone", "fax", "notes_th", "audit_match", "campus_note",
    "source_page", "source_pdf",
]


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def main() -> None:
    doc = pymupdf.open(PDF)
    if doc.page_count != 1:
        raise ValueError(f"expected 1 page, got {doc.page_count}")
    page_text = compact(doc[0].get_text("text"))
    for row in ROWS:
        if compact(row["facility_name_th"]) not in page_text:
            raise ValueError(f"name not found in PDF text: {row['facility_name_th']}")
        row["source_page"] = 1
        row["source_pdf"] = "Chiang Mai Public Children's homes 2025.pdf"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(ROWS)
    print("rows", len(ROWS), "wrote", OUT)


if __name__ == "__main__":
    main()
