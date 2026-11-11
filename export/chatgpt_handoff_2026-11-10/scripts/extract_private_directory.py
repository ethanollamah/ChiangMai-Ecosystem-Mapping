"""Extract the 2025 Chiang Mai private childcare directory (สถานรับเลี้ยงเด็กเอกชน) into a CSV.

Table rows are detected with PyMuPDF; each cell is re-read with a clip box because the
table extractor scrambles Thai combining marks. The PDF's font maps "า" to "ำ", so text
is normalised (see fix_thai). Original page numbers are kept for visual verification.
"""
import csv
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "raw" / "project_snapshot" / "private_directory.pdf"
OUT = ROOT / "outputs" / "step1" / "private_childcare_directory_2025.csv"

COLUMNS = [
    "row_no", "licence", "facility_name_th", "operator_th", "address_th", "district_th",
    "phone", "online_contact", "licensed_age_range_th", "status_th", "fee_th", "ssc_affiliation",
]


def fix_thai(text):
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    # Genuine sara am is rendered as " ำ" (space + U+0E33); a bare U+0E33 is a mis-mapped sara aa.
    text = re.sub(r" \u0e33", "\x00", text).replace("\u0e33", "\u0e32").replace("\x00", "\u0e33")
    return re.sub(r"[ \t]+", " ", text).strip()


def cell_text(page, bbox):
    if bbox is None:
        return ""
    raw = page.get_text("text", clip=pymupdf.Rect(bbox))
    return fix_thai(" ".join(line.strip() for line in raw.splitlines() if line.strip()))


def main():
    doc = pymupdf.open(PDF)
    rows = []
    for pno in range(doc.page_count):
        page = doc[pno]
        for table in page.find_tables().tables:
            if table.col_count != len(COLUMNS):
                continue
            for trow in table.rows:
                values = [cell_text(page, c) for c in trow.cells]
                if not re.fullmatch(r"\d+", values[0]):
                    continue
                rec = dict(zip(COLUMNS, values))
                rec["source_page"] = pno + 1
                rows.append(rec)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS + ["source_page"])
        w.writeheader()
        w.writerows(rows)
    nums = [int(r["row_no"]) for r in rows]
    missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
    print(f"{len(rows)} rows; max row_no {max(nums)}; missing {missing}; duplicates {len(nums) - len(set(nums))}")


if __name__ == "__main__":
    main()
