"""Rebuild the ChatGPT handoff pack from the current workspace.

Run after each completed step:

    python scripts/extract_classification.py   # if FINAL.xlsx is available
    python scripts/convert_dopa.py             # if DOPA outputs need refresh
    python scripts/build_chatgpt_handoff.py

Always overwrites:
  export/chatgpt_handoff/
  export/Chiang_Mai_ChatGPT_Handoff.zip
and copies the zip to the TSA Mapping folder when that folder exists.

A dated zip is also written under export/ so earlier packs can be kept.
New files under outputs/step1/ through outputs/step6/ are picked up
automatically (batch folders skipped).
"""
from __future__ import annotations

import csv
import hashlib
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "export" / "chatgpt_handoff"
SRC_SNAP = ROOT / "raw" / "project_snapshot"
SRC_DOLE = ROOT / "raw" / "dole"
SRC_OUT = ROOT / "outputs" / "step1"
SRC_STEPS = [
    ROOT / "outputs" / "step1",
    ROOT / "outputs" / "step2",
    ROOT / "outputs" / "step3",
    ROOT / "outputs" / "step4",
    ROOT / "outputs" / "step5",
    ROOT / "outputs" / "step6",
]
PLAN = ROOT / "Chiang_Mai_Geographical_Analysis_Plan.md"
FINAL_XLSX = Path(
    "/Users/ethan/Documents/Werk/University/Extra Curriculars/Thrive/"
    "TSA Project/Mapping/landscape mapping (FINAL).xlsx"
)
DOCS_COPY = Path(
    "/Users/ethan/Documents/Werk/University/Extra Curriculars/Thrive/"
    "TSA Project/Mapping"
)
SKIP_OUT_DIRS = {"accommodation_batches", "accommodation_results"}
CORE_SNAPSHOT = [
    ("Chiang_Mai_Organisation_Location_Audit.xlsx", "29 Oct 2026 geographic audit. Raw starting point; do not edit. Cleaned tables are outputs/step2/."),
    ("private_directory.pdf", "Private childcare PDF (สถานรับเลี้ยงเด็กเอกชน), 16 Oct 2025."),
    ("public_directory.pdf", "Public welfare/reception/juvenile directory. Extracted to outputs/step1/public_childrens_homes_2025.csv."),
    ("dopa_2025_12_chiang_mai.txt", "DOPA Dec 2025 Chiang Mai raw pipe-delimited text."),
    ("tpmap_69_50_amphur_common.csv", "TPMAP 2569 Chiang Mai district common indicators."),
    ("tpmap_69_50_amphur_11111.csv", "TPMAP 2569 poverty-filter file. Mueang (5001) zeros match the live page."),
]
OUT_ROLES = {
    "classification_FINAL_checkbox.json": "Seven-stage ticks from landscape mapping (FINAL).xlsx / CM Mapping (checkbox).",
    "dole_zero_dropout_by_district.csv": "DOLE Zero Dropout province + 25 districts.",
    "dole_glossary.csv": "Thai–English glossary of DOLE dashboard labels.",
    "private_childcare_directory_2025.csv": "148 numbered rows from the 16 Oct 2025 private childcare PDF.",
    "accommodation_register.csv": "Merged overnight/boarding check for all 148 private-childcare rows.",
    "accommodation_unresolved_cases.csv": "Watch list: unresolved, identity_not_confirmed, and the overnight flag.",
    "accommodation_register.json": "Same register with evidence URLs and search logs.",
    "dopa_schema.csv": "Official DOPA field meanings.",
    "dopa_rows.csv": "Every DOPA registration row with geography slice and age bands. Do not sum parent+child.",
    "dopa_district_totals.csv": "Whole-district denominators (residual + assigned municipalities).",
    "dopa_province_summary.csv": "Province totals and child-denominator coverage note.",
    "dopa_municipality_assignment.csv": "Which municipality was assigned to which district.",
    "dopa_worked_example.csv": "Mueang / Nakhon / Chang Phueak worked example rows.",
    "dopa_validation.json": "Identity and geography reconciliation checks.",
    "public_childrens_homes_2025.csv": "Four public sites from the 2025 directory: two welfare homes, one reception shelter, one juvenile centre. Juvenile stays separately labelled.",
    "tpmap_glossary.csv": "TPMAP column and 38-indicator labels from the official Plan 13 data dictionary.",
    "tpmap_district_evidence.csv": "2569 district TPMAP headline measures with provenance. Mueang zeros are live-page confirmed.",
    "tpmap_capture_log.json": "Live-page check of Mueang 5001 and how to use the TPMAP table.",
    "tpmap_2569_mueang_5001.png": "Screenshot of https://www.tpmap.in.th/2569/5001 on 10 Nov 2026: 0 target poor / 52,312 surveyed.",
    "sites.csv": "Step 2 cleaned sites (72). Use level1_*_eligible flags; do not treat every row as a point.",
    "organisations.csv": "Step 2 organisations (57). level1_org_eligible is the unique-org numerator.",
    "site_stages.csv": "Organisation-level stage evidence copied to sites. FINAL checkbox remains the classification source.",
    "change_log.csv": "Every district, geocode and public-directory addition. Raw 29 Oct file was not edited.",
    "district_crosswalk.csv": "Audit district labels onto DOPA 5001–5025. Non-district phrases are non-joins. Wiang Pa Pao is Chiang Rai.",
    "cleaning_summary.json": "Step 2 counts and eligibility rule.",
    "geocode_cache.json": "Nominatim response cache. Reproducible geocodes; not a finding.",
    "Chiang_Mai_Organisation_Location_Audit_2026-10-29.xlsx": "Dated copy of the 29 Oct audit. The raw snapshot is also packed as 04_.",
    "counts_overall.csv": "Level 1 numerators: 53 orgs, 57 sites, 12 points, with definitions.",
    "orgs_by_stage.csv": "Unique organisations by FINAL stage. Do not add across stages.",
    "org_stage_overlap.csv": "How many FINAL stages each mapped organisation has.",
    "sites_by_stage.csv": "Eligible sites by FINAL stage of the owning organisation.",
    "sites_by_district.csv": "All 25 DOPA districts including zeros, plus a non-join row. Zero mapped is not absent.",
    "nearest_neighbour.csv": "Descriptive great-circle NN among 12 public house/building points. Not a clustering test.",
    "level1_points.csv": "The 12 NN points plus the juvenile centre (in_nearest_neighbour=no).",
    "level1_points.geojson": "Same points as GeoJSON.",
    "level1_points.svg": "Offline scatter of the public points. Linear lon/lat, not a map projection.",
    "level1_summary.json": "Level 1 headline counts, NN summary and limitations.",
    "stage_source_disagreement.csv": "Audit Applicable_Stages that disagree with FINAL; not used in Level 1 stage counts.",
    "district_presence.csv": "Level 2A: one row per DOPA district. Presence per 10,000 registered Thai children 0–17. DOLE and TPMAP stay in separate columns.",
    "site_presence_role.csv": "Each Level 1 site as office, delivery, or mixed. Former/closed flagged.",
    "measure_definitions.csv": "Numerator, denominator, and what must not be added.",
    "signals_for_closer_look.csv": "Separate rule hits. Not a priority score and not an unmet-need ranking.",
    "level2a_summary.json": "Level 2A thresholds, headline rates, and limitations.",
    "design_decisions.csv": "Level 2B origin, destination, mode and threshold, each with the reason it was chosen.",
    "district_centroids.csv": "25 district centroids used as administrative proxies. Not children's homes.",
    "destinations.csv": "The eight exact public delivery or mixed sites used as route destinations.",
    "district_access.csv": "Private-vehicle time and distance from each centroid, walking sensitivity, and Valhalla check.",
    "gaps_not_modelled.csv": "Affordability, eligibility and shared transport were not given numbers.",
    "level2b_summary.json": "Level 2B spread of times, descriptive bins, and engine comparison.",
    "routing_cache.json": "Cached FOSSGIS and Valhalla responses. Reproducible routes; not a finding.",
    "comparison_family_support.csv": "Unranked family-support comparison, DOPA code order. Not a score.",
    "comparison_educational_reengagement.csv": "Unranked educational re-engagement comparison. DOLE flags stay in separate columns.",
    "family_support_rule_hits.csv": "Separate yes/no rule hits for family support. Not a rank.",
    "education_rule_hits.csv": "Separate yes/no rule hits for DOLE flags. Not a rank.",
    "local_validation_questions.csv": "Questions for TSA and local partners. Not measured answers.",
    "provisional_outcomes.csv": "Outcomes to monitor if a partnership proceeds. Not targets.",
    "level2c_summary.json": "Level 2C decision, cuts, and uncertainties.",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def packed_now() -> str:
    return datetime.now(ZoneInfo("Asia/Singapore")).strftime("%-d %B %Y, %H:%M %Z")


def stamp() -> str:
    return datetime.now(ZoneInfo("Asia/Singapore")).strftime("%Y-%m-%d")


def next_action_from_plan() -> str:
    text = PLAN.read_text(encoding="utf-8")
    m = re.search(r"^Next action:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else "See 01_Chiang_Mai_Geographical_Analysis_Plan.md."


def copy(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def add(files: list[dict], src: Path, rel: str, role: str) -> None:
    dest = copy(src, PACK / rel)
    files.append({
        "file": rel.replace("\\", "/"),
        "bytes": dest.stat().st_size,
        "sha256": sha256(dest),
        "role": role,
    })


def maybe_extract_classification() -> Path:
    out = SRC_OUT / "classification_FINAL_checkbox.json"
    if FINAL_XLSX.is_file():
        import sys
        scripts = str(ROOT / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        from extract_classification import main as extract_main
        return extract_main(FINAL_XLSX)
    if out.is_file():
        return out
    raise FileNotFoundError("No FINAL.xlsx and no existing classification JSON.")


def write_readme(files: list[dict], zip_name: str, packed: str) -> None:
    index_rows = "\n".join(
        f"| `{r['file']}` | {r['role']} |"
        for r in files
        if not r["file"].startswith("scripts/")
        and not r["file"].startswith("17_")
        and not r["file"].startswith("raw/")
    )
    next_action = next_action_from_plan()
    template = (ROOT / "scripts" / "_handoff_readme.md").read_text(encoding="utf-8")
    text = (
        template
        .replace("{{PACKED_DATE}}", packed)
        .replace("{{ZIP_NAME}}", zip_name)
        .replace("{{NEXT_ACTION}}", next_action)
        .replace("{{FILE_INDEX_ROWS}}", index_rows)
    )
    (PACK / "00_READ_ME_FIRST.md").write_text(text, encoding="utf-8")


def main() -> None:
    if not PLAN.is_file():
        raise FileNotFoundError(PLAN)
    packed = packed_now()
    date_stamp = stamp()
    if PACK.exists():
        shutil.rmtree(PACK)
    PACK.mkdir(parents=True)

    files: list[dict] = []
    classification = maybe_extract_classification()

    add(files, PLAN, "01_Chiang_Mai_Geographical_Analysis_Plan.md",
        "Living working plan. Update after each completed step.")
    add(files, classification, "02_classification_FINAL_checkbox.json",
        "Seven-stage ticks extracted from landscape mapping (FINAL).xlsx / CM Mapping (checkbox).")
    if FINAL_XLSX.is_file():
        add(files, FINAL_XLSX, "03_landscape_mapping_FINAL.xlsx",
            "Confirmed classification workbook. Do not substitute an older copy.")
    add(files, SRC_SNAP / "Chiang_Mai_Organisation_Location_Audit.xlsx",
        "04_Chiang_Mai_Organisation_Location_Audit.xlsx",
        "29 Oct 2026 geographic audit. Starting point; not yet cleaned.")

    skip_out_files = {classification.name}
    for src_out in SRC_STEPS:
        if not src_out.is_dir():
            continue
        step_name = src_out.name
        for path in sorted(src_out.iterdir()):
            if path.name.startswith(".") or path.name in skip_out_files:
                continue
            if path.is_dir():
                if path.name in SKIP_OUT_DIRS:
                    continue
                for child in sorted(path.rglob("*")):
                    if child.is_file():
                        rel = f"outputs/{step_name}/{child.relative_to(src_out).as_posix()}"
                        add(files, child, rel, OUT_ROLES.get(child.name, f"{step_name} output."))
                continue
            rel = f"outputs/{step_name}/{path.name}"
            add(files, path, rel, OUT_ROLES.get(path.name, f"{step_name} output. See the plan for how to use it."))

    for name, role in CORE_SNAPSHOT:
        src = SRC_SNAP / name
        if src.is_file():
            add(files, src, f"raw/project_snapshot/{name}", role)

    datadict = ROOT / "raw" / "tpmap" / "TPMAP_datadict_plan13.xlsx"
    if datadict.is_file():
        add(files, datadict, "raw/tpmap/TPMAP_datadict_plan13.xlsx",
            "Official TPMAP Plan 13 data dictionary used for the glossary.")

    if (SRC_DOLE / "acquisition_log.json").is_file():
        add(files, SRC_DOLE / "acquisition_log.json", "raw/dole/acquisition_log.json",
            "One-attempt public POST log: URL, parameters, UTC time, SHA-256, totals.")
    for p in sorted(SRC_DOLE.glob("dole_*.json")):
        add(files, p, f"raw/dole/{p.name}", "Unflattened DOLE aggregate JSON.")

    for script in sorted((ROOT / "scripts").glob("*.py")):
        add(files, script, f"scripts/{script.name}",
            "Reproducible script. Do not treat scripts as findings.")
    readme_src = ROOT / "scripts" / "_handoff_readme.md"
    if readme_src.is_file():
        add(files, readme_src, "scripts/_handoff_readme.md",
            "Template for 00_READ_ME_FIRST.md. Placeholders are filled at pack time.")

    man_path = PACK / "FILE_MANIFEST.csv"
    with man_path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["file", "bytes", "sha256", "role"])
        w.writeheader()
        w.writerows(files)

    zip_name = "Chiang_Mai_ChatGPT_Handoff.zip"
    write_readme(files, zip_name, packed)

    def write_zip(path: Path) -> None:
        if path.exists():
            path.unlink()
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(PACK.rglob("*")):
                if p.is_file():
                    z.write(p, arcname=p.relative_to(PACK).as_posix())

    stable_zip = ROOT / "export" / zip_name
    dated_zip = ROOT / "export" / f"Chiang_Mai_ChatGPT_Handoff_{date_stamp}.zip"
    write_zip(stable_zip)
    shutil.copy2(stable_zip, dated_zip)
    if DOCS_COPY.is_dir():
        shutil.copy2(stable_zip, DOCS_COPY / zip_name)

    n_files = sum(1 for p in PACK.rglob("*") if p.is_file())
    print("files", n_files)
    print("pack", PACK)
    print("zip", stable_zip, stable_zip.stat().st_size)
    print("dated", dated_zip)


if __name__ == "__main__":
    main()
