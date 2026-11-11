"""Build a TPMAP district evidence table and glossary from the packed CSVs.

Default view matches the live page filter used for the packed files:
  year 2569, Chiang Mai, 5 MPI dimensions (metric 11111), welfare-card = มีบัตร.

Mueang (5001) poverty counts are zero on the live page as well as in the CSV.
That is a displayed result, not a blank download. It is not evidence of no need.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SNAP = ROOT / "raw" / "project_snapshot"
DICT = ROOT / "raw" / "tpmap" / "TPMAP_datadict_plan13.xlsx"
OUT = ROOT / "outputs" / "step1"

DISTRICT_EN = {
    "5001": ("อำเภอเมืองเชียงใหม่", "Mueang Chiang Mai"),
    "5002": ("อำเภอจอมทอง", "Chom Thong"),
    "5003": ("อำเภอแม่แจ่ม", "Mae Chaem"),
    "5004": ("อำเภอเชียงดาว", "Chiang Dao"),
    "5005": ("อำเภอดอยสะเก็ด", "Doi Saket"),
    "5006": ("อำเภอแม่แตง", "Mae Taeng"),
    "5007": ("อำเภอแม่ริม", "Mae Rim"),
    "5008": ("อำเภอสะเมิง", "Samoeng"),
    "5009": ("อำเภอฝาง", "Fang"),
    "5010": ("อำเภอแม่อาย", "Mae Ai"),
    "5011": ("อำเภอพร้าว", "Phrao"),
    "5012": ("อำเภอสันป่าตอง", "San Pa Tong"),
    "5013": ("อำเภอสันกำแพง", "San Kamphaeng"),
    "5014": ("อำเภอสันทราย", "San Sai"),
    "5015": ("อำเภอหางดง", "Hang Dong"),
    "5016": ("อำเภอฮอด", "Hot"),
    "5017": ("อำเภอดอยเต่า", "Doi Tao"),
    "5018": ("อำเภออมก๋อย", "Omkoi"),
    "5019": ("อำเภอสารภี", "Saraphi"),
    "5020": ("อำเภอเวียงแหง", "Wiang Haeng"),
    "5021": ("อำเภอไชยปราการ", "Chai Prakan"),
    "5022": ("อำเภอแม่วาง", "Mae Wang"),
    "5023": ("อำเภอแม่ออน", "Mae On"),
    "5024": ("อำเภอดอยหล่อ", "Doi Lo"),
    "5025": ("อำเภอกัลยาณิวัฒนา", "Galyani Vadhana"),
}

DIM_EN = {
    "ด้านสุขภาพ": "Health",
    "ด้านมาตรฐานความเป็นอยู่": "Living standards",
    "ด้านความเป็นอยู่": "Living standards",
    "ด้านการศึกษา": "Education",
    "ด้านเศรษฐกิจ": "Economy",
    "ด้านรายได้": "Economy / income",
    "ด้านการคุ้มครองทางสังคมและการมีส่วนร่วม": "Social protection and participation",
    "ด้านการเข้าถึงบริการรัฐ": "Access to public services",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(value) -> float | int:
    if value is None or value == "":
        return 0
    x = float(value)
    return int(x) if x.is_integer() else x


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    poor = {r["amphur_ID"].strip('"'): r for r in load_csv(SNAP / "tpmap_69_50_amphur_11111.csv")}
    common = {r["amphur_ID"].strip('"'): r for r in load_csv(SNAP / "tpmap_69_50_amphur_common.csv")}
    if set(poor) != set(DISTRICT_EN):
        raise ValueError("district codes in TPMAP files do not match the 25 Chiang Mai districts")

    wb = load_workbook(DICT, data_only=True)
    ws = wb["datadict"]
    glossary = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        col, meaning, extra, dimension = (list(row) + [None, None, None, None])[:4]
        if not col:
            continue
        glossary.append({
            "column": str(col).strip(),
            "meaning_th": (meaning or "").strip(),
            "indicator_th": (extra or "").strip(),
            "mpi_dimension_th": (dimension or "").strip(),
            "mpi_dimension_en": DIM_EN.get((dimension or "").strip(), ""),
            "source": "TPMAP_datadict_plan13.xlsx",
        })
    with (OUT / "tpmap_glossary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(glossary[0].keys()))
        w.writeheader()
        w.writerows(glossary)

    captured = datetime.now(timezone.utc).isoformat()
    evidence = []
    for code, (district_th, district_en) in DISTRICT_EN.items():
        p = poor[code]
        c = common[code]
        surveyed = num(c["HOUSEMEMBER_CNT"])
        target = num(p["poor.JPT.MOFval.CNT"])
        rate = num(p["JPT.MOFval.pov.rate"])
        evidence.append({
            "district_code": code,
            "district_th": district_th,
            "district_en": district_en,
            "dashboard_year": 2569,
            "page_last_update_th": "3 เม.ย. 2569",
            "underlying_sources": "JPT 2568 integrated with State Welfare Card 2565 (as stated on the 2569 page)",
            "welfare_card_filter": "card",
            "welfare_card_filter_th": "มีบัตร",
            "mpi_metric": "11111",
            "mpi_metric_meaning": "all five MPI dimensions included",
            "jpt_households": num(c["household.CNT"]),
            "jpt_people": surveyed,
            "welfare_card_registrants": num(c["MOF_REG_CNT"]),
            "welfare_card_validated": num(c["MOF_VAL_CNT"]),
            "poor_households_mpi": num(p["poor.household.CNT"]),
            "poor_people_jpt": num(p["poor.JPT.CNT"]),
            "target_poor_people": target,
            "target_poor_rate_percent": round(float(rate), 4) if not isinstance(rate, int) else rate,
            "target_poor_rate_denominator": "jpt_people (HOUSEMEMBER_CNT)",
            "poor_health": num(p["poor.JPT.MOFval.health"]),
            "poor_living": num(p["poor.JPT.MOFval.living"]),
            "poor_education": num(p["poor.JPT.MOFval.education"]),
            "poor_economy": num(p["poor.JPT.MOFval.income"]),
            "poor_social_protection": num(p["poor.JPT.MOFval.accessibility"]),
            "page_url": f"https://www.tpmap.in.th/2569/{code}",
            "dimensions_overlap": "yes — one person can fail more than one MPI dimension; do not add the five counts",
            "coverage_note": (
                "Target poor = JPT MPI-poor people in the selected welfare-card filter. "
                "Not all residents. Not all poor children. Registered/surveyed is not resident. "
                "Poverty is an area need indicator, not a reason any particular child should enter care."
            ),
        })

    fields = list(evidence[0].keys())
    with (OUT / "tpmap_district_evidence.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(evidence)

    mueang = next(r for r in evidence if r["district_code"] == "5001")
    mae_chaem = next(r for r in evidence if r["district_code"] == "5003")
    log = {
        "captured_utc": captured,
        "live_page_checked": {
            "url": "https://www.tpmap.in.th/2569/5001",
            "filters": "year 2569; อ.เมืองเชียงใหม่; 5 MPI dimensions; welfare card = มีบัตร; ทุกตำบล",
            "displayed": {
                "target_poor_people": 0,
                "jpt_people": 52312,
                "jpt_households": 24044,
                "mpi_poor_households": 0,
                "mpi_poor_people": 0,
                "target_poor_in_welfare_households": 0,
                "rate": "0.00%",
                "page_last_update_th": "3 เม.ย. 2569",
            },
            "matches_packed_csv": True,
            "also_zero_under_filters": ["all", "nocard"],
            "interpretation": (
                "Mueang is the only Chiang Mai district with 0 target-poor people under this "
                "2569 / 5-dimension view. The JPT survey still enumerates 24,044 households "
                "and 52,312 people. Do not read this as 'no poverty' or 'no need' in Mueang. "
                "Urban JPT/welfare-card coverage may be incomplete."
            ),
        },
        "packed_files": {
            "tpmap_69_50_amphur_11111.csv": sha256(SNAP / "tpmap_69_50_amphur_11111.csv"),
            "tpmap_69_50_amphur_common.csv": sha256(SNAP / "tpmap_69_50_amphur_common.csv"),
            "datadict": str(DICT.relative_to(ROOT)),
        },
        "headline": {
            "districts": 25,
            "districts_with_target_poor": sum(1 for r in evidence if r["target_poor_people"] > 0),
            "mueang_target_poor": mueang["target_poor_people"],
            "highest_target_poor_count": {
                "district_en": mae_chaem["district_en"],
                "target_poor_people": mae_chaem["target_poor_people"],
                "rate_percent": mae_chaem["target_poor_rate_percent"],
            },
        },
        "how_to_use": {
            "file": "outputs/step1/tpmap_district_evidence.csv",
            "join": "district_code 5001–5025, same codes as DOPA/DOLE",
            "do_not": [
                "treat 0 in Mueang as missing data",
                "treat 0 in Mueang as proof of no need",
                "add the five dimension counts as unique people",
                "treat target poor as a child-only count",
            ],
        },
    }
    (OUT / "tpmap_capture_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("districts", len(evidence))
    print("mueang target poor", mueang["target_poor_people"], "of", mueang["jpt_people"])
    print("wrote", OUT / "tpmap_district_evidence.csv")


if __name__ == "__main__":
    main()
