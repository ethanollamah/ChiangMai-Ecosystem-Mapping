"""Extract seven-stage ticks from landscape mapping (FINAL).xlsx.

Uses cached values on sheet `CM Mapping (checkbox)` (data_only=True).
The sheet still contains external-link formulas to SharePoint; analysis uses
the stored checkbox values, including advocacy ticks for ZOE and Daughters Rising.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "step1" / "classification_FINAL_checkbox.json"
DEFAULT_XLSX = Path(
    "/Users/ethan/Documents/Werk/University/Extra Curriculars/Thrive/"
    "TSA Project/Mapping/landscape mapping (FINAL).xlsx"
)

STAGES = [
    ("Parent Capability Building", slice(1, 5)),
    ("Identification & Routing", slice(5, 7)),
    ("Short-term Intervention", slice(7, 11)),
    ("Kinship Care", slice(11, 15)),
    ("Foster Care / Adoption", slice(15, 19)),
    ("Residential and Institutional Care", slice(19, 23)),
    ("Reintegration, Reunification and Adoption", slice(23, 26)),
]


def clean_name(raw: str) -> str:
    return " ".join(str(raw).replace("\xa0", " ").replace("\n", " ").split())


def is_ticked(value) -> bool:
    return value is True or value == 1


def extract(xlsx: Path) -> dict:
    wb = load_workbook(xlsx, data_only=True)
    ws = wb["CM Mapping (checkbox)"]
    sub = [c if c is None else str(c).strip() for c in next(ws.iter_rows(min_row=2, max_row=2, values_only=True))]
    orgs = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        raw = row[0]
        if raw is None or str(raw).strip() == "":
            continue
        raw_s = str(raw).strip()
        if raw_s in {"Organisation", "Sub-categories"} or raw_s.startswith("Summary") or raw_s.startswith("ROW "):
            continue
        stages = []
        subcats: dict[str, list[str]] = {}
        for stage, sl in STAGES:
            ticks = []
            for i in range(sl.start, sl.stop):
                if i < len(row) and is_ticked(row[i]):
                    ticks.append(sub[i])
            if ticks:
                stages.append(stage)
                subcats[stage] = ticks
        orgs.append({
            "organisation": clean_name(raw),
            "organisation_raw": raw if isinstance(raw, str) else str(raw),
            "stages": stages,
            "subcategories": subcats,
            "any_tick": bool(stages),
        })
    return {
        "source_file": xlsx.name,
        "source_tab": "CM Mapping (checkbox)",
        "extracted_date": date.today().isoformat(),
        "note": (
            "Cached checkbox values from FINAL, as confirmed by the user. "
            "Includes advocacy-for-family-placement ticks for ZOE and Daughters Rising."
        ),
        "n_rows_including_unticked": len(orgs),
        "n_with_at_least_one_tick": sum(1 for o in orgs if o["any_tick"]),
        "organisations": orgs,
    }


def main(xlsx: Path | None = None) -> Path:
    src = xlsx or DEFAULT_XLSX
    if not src.is_file():
        raise FileNotFoundError(f"Classification workbook not found: {src}")
    payload = extract(src)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("orgs", payload["n_rows_including_unticked"],
          "ticked", payload["n_with_at_least_one_tick"],
          "wrote", OUT)
    return OUT


if __name__ == "__main__":
    main()
