"""Assemble a ChatGPT-uploadable handoff pack with a manifest."""
import csv
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-11-10"
PACK = ROOT / "export" / f"chatgpt_handoff_{STAMP}"
SRC_SNAP = ROOT / "raw" / "project_snapshot"
SRC_DOLE = ROOT / "raw" / "dole"
SRC_OUT = ROOT / "outputs" / "step1"
FINAL_XLSX = Path(
    "/Users/ethan/Documents/Werk/University/Extra Curriculars/Thrive/"
    "TSA Project/Mapping/landscape mapping (FINAL).xlsx"
)
CLASSIFICATION = Path("/tmp/cm_classification_final.json")
DOCS_COPY = Path(
    "/Users/ethan/Documents/Werk/University/Extra Curriculars/Thrive/"
    "TSA Project/Mapping"
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def main():
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)

    files = []

    def add(src: Path, rel: str, role: str):
        dest = copy(src, PACK / rel)
        files.append({
            "file": rel.replace("\\", "/"),
            "bytes": dest.stat().st_size,
            "sha256": sha256(dest),
            "role": role,
        })

    add(ROOT / "Chiang_Mai_Geographical_Analysis_Plan.md",
        "01_Chiang_Mai_Geographical_Analysis_Plan.md",
        "Working plan. Update this after each completed step.")
    add(CLASSIFICATION, "02_classification_FINAL_checkbox.json",
        "Seven-stage ticks extracted from landscape mapping (FINAL).xlsx / CM Mapping (checkbox).")
    add(FINAL_XLSX, "03_landscape_mapping_FINAL.xlsx",
        "Confirmed classification workbook. Do not substitute an older copy.")
    add(SRC_SNAP / "Chiang_Mai_Organisation_Location_Audit.xlsx",
        "04_Chiang_Mai_Organisation_Location_Audit.xlsx",
        "29 Oct 2026 geographic audit. Starting point, not yet validated.")
    add(SRC_OUT / "dole_zero_dropout_by_district.csv",
        "05_dole_zero_dropout_by_district.csv",
        "DOLE Zero Dropout province + 25 districts, flattened 10 Nov 2026.")
    add(SRC_OUT / "dole_glossary.csv",
        "06_dole_glossary.csv",
        "Thai–English glossary of DOLE dashboard labels.")
    add(SRC_DOLE / "acquisition_log.json",
        "07_dole_acquisition_log.json",
        "One-attempt public POST log: URL, parameters, UTC time, SHA-256, totals.")
    add(SRC_OUT / "private_childcare_directory_2025.csv",
        "08_private_childcare_directory_2025.csv",
        "148 numbered rows from the 16 Oct 2025 private childcare PDF.")
    add(SRC_OUT / "accommodation_register.csv",
        "09_accommodation_register.csv",
        "Merged facility-by-facility overnight/boarding check for all 148 rows.")
    add(SRC_OUT / "accommodation_unresolved_cases.csv",
        "10_accommodation_unresolved_cases.csv",
        "Watch list: unresolved, identity_not_confirmed, and the one overnight flag.")
    add(SRC_OUT / "accommodation_register.json",
        "11_accommodation_register.json",
        "Same register with evidence URLs and search logs.")
    add(SRC_SNAP / "private_directory.pdf",
        "12_Chiang_Mai_Private_Childcare_facilities_2025.pdf",
        "Source PDF. Visual verification still needed for ambiguous cells.")
    add(SRC_SNAP / "public_directory.pdf",
        "13_Chiang_Mai_Public_Childrens_homes_2025.pdf",
        "Public welfare/reception/juvenile directory. Not yet extracted to a table.")
    add(SRC_SNAP / "dopa_2025_12_chiang_mai.txt",
        "14_dopa_2025_12_chiang_mai.txt",
        "DOPA Dec 2025 Chiang Mai raw pipe-delimited text. Not yet converted.")
    add(SRC_SNAP / "tpmap_69_50_amphur_common.csv",
        "15_tpmap_69_50_amphur_common.csv",
        "TPMAP 2569 Chiang Mai district common indicators. Labels not yet glossed.")
    add(SRC_SNAP / "tpmap_69_50_amphur_11111.csv",
        "16_tpmap_69_50_amphur_11111.csv",
        "TPMAP 2569 Chiang Mai district poverty-filter file. Mueang (5001) is all zeros — verify on the live page before treating as zero poverty.")

    raw_dole = PACK / "17_dole_raw_json"
    raw_dole.mkdir()
    for p in sorted(SRC_DOLE.glob("dole_*.json")):
        add(p, f"17_dole_raw_json/{p.name}", "Unflattened DOLE aggregate JSON.")

    for script in [
        "fetch_dole_districts.py", "build_dole_table.py",
        "extract_private_directory.py", "merge_accommodation_register.py",
        "write_batches_4_5.py", "build_chatgpt_handoff.py",
    ]:
        add(ROOT / "scripts" / script, f"scripts/{script}", "Reproducible script. Do not treat scripts as findings.")

    # Manifest
    man_path = PACK / "FILE_MANIFEST.csv"
    with man_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["file", "bytes", "sha256", "role"])
        w.writeheader()
        w.writerows(files)
    files.append({
        "file": "FILE_MANIFEST.csv",
        "bytes": man_path.stat().st_size,
        "sha256": sha256(man_path),
        "role": "Checksums for every packed file except this row and 00_READ_ME_FIRST.md.",
    })

    readme = (ROOT / "scripts" / "_handoff_readme.md").read_text(encoding="utf-8")
    readme_path = PACK / "00_READ_ME_FIRST.md"
    readme_path.write_text(readme, encoding="utf-8")

    zip_path = ROOT / "export" / f"Chiang_Mai_Step1_ChatGPT_Handoff_{STAMP}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(PACK.rglob("*")):
            if p.is_file():
                z.write(p, arcname=p.relative_to(PACK))

    if DOCS_COPY.is_dir():
        shutil.copy2(zip_path, DOCS_COPY / zip_path.name)

    print("files", len(list(PACK.rglob("*"))))
    print("pack", PACK)
    print("zip", zip_path, zip_path.stat().st_size)
    print("docs copy", DOCS_COPY / zip_path.name)


if __name__ == "__main__":
    main()
