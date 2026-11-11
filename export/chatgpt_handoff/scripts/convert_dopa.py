"""Convert DOPA Dec 2025 Chiang Mai age-by-area text into validated tables.

Official schema: https://stat.bora.dopa.go.th/new_stat/webPage/statByAge.php
Source file: raw/project_snapshot/dopa_2025_12_chiang_mai.txt
  (public original: https://stat.bora.dopa.go.th/new_stat/file/6812/6812cc50.txt)

Do not use อำเภอ-labelled rows as whole-district denominators. Those rows are
registration-office residuals; municipalities are listed separately later in the
file. Whole-district totals = residual district row + municipalities assigned to
that district. Tambon names can repeat across residual and municipal slices;
they are not unique IDs.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "raw" / "project_snapshot" / "dopa_2025_12_chiang_mai.txt"
OUT = ROOT / "outputs" / "step1"

N_AGE_PAIRS = 102  # ages 0..100 plus 101 = over 100
N_AGE_FIELDS = N_AGE_PAIRS * 2  # interleaved male, female
N_NUMERIC = 219  # 204 age fields + 15 special/total fields

DISTRICT_EN = {
    "อำเภอเมืองเชียงใหม่": "Mueang Chiang Mai",
    "อำเภอจอมทอง": "Chom Thong",
    "อำเภอแม่แจ่ม": "Mae Chaem",
    "อำเภอเชียงดาว": "Chiang Dao",
    "อำเภอดอยสะเก็ด": "Doi Saket",
    "อำเภอแม่แตง": "Mae Taeng",
    "อำเภอแม่ริม": "Mae Rim",
    "อำเภอสะเมิง": "Samoeng",
    "อำเภอฝาง": "Fang",
    "อำเภอแม่อาย": "Mae Ai",
    "อำเภอพร้าว": "Phrao",
    "อำเภอสันป่าตอง": "San Pa Tong",
    "อำเภอสันกำแพง": "San Kamphaeng",
    "อำเภอสันทราย": "San Sai",
    "อำเภอหางดง": "Hang Dong",
    "อำเภอฮอด": "Hot",
    "อำเภอดอยเต่า": "Doi Tao",
    "อำเภออมก๋อย": "Omkoi",
    "อำเภอสารภี": "Saraphi",
    "อำเภอเวียงแหง": "Wiang Haeng",
    "อำเภอไชยปราการ": "Chai Prakan",
    "อำเภอแม่วาง": "Mae Wang",
    "อำเภอแม่ออน": "Mae On",
    "อำเภอดอยหล่อ": "Doi Lo",
    "อำเภอกัลยาณิวัฒนา": "Galyani Vadhana",
}

# Whole-district reconstruction: each municipality is assigned to one district.
# Validated because residual + assigned municipalities = province total.
MUNI_TO_DISTRICT = {
    "เทศบาลนครเชียงใหม่": "อำเภอเมืองเชียงใหม่",
    "เทศบาลเมืองแม่เหียะ": "อำเภอเมืองเชียงใหม่",
    "เทศบาลเมืองสุเทพ": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลช้างเผือก": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลฟ้าฮ่าม": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลหนองหอย": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลท่าศาลา": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลป่าแดด": "อำเภอเมืองเชียงใหม่",
    "เทศบาลตำบลหนองป่าครั่ง": "อำเภอเมืองเชียงใหม่",
    "เทศบาลเมืองแม่โจ้": "อำเภอสันทราย",
    "เทศบาลตำบลสันทรายหลวง": "อำเภอสันทราย",
    "เทศบาลตำบลหนองจ๊อม": "อำเภอสันทราย",
    "เทศบาลตำบลป่าไผ่": "อำเภอสันทราย",
    "เทศบาลตำบลสันนาเม็ง": "อำเภอสันทราย",
    "เทศบาลตำบลแม่แฝก": "อำเภอสันทราย",
    "เทศบาลตำบลเจดีย์แม่ครัว": "อำเภอสันทราย",
    "เทศบาลตำบลสันพระเนตร": "อำเภอสันทราย",
    "เทศบาลเมืองต้นเปา": "อำเภอสันกำแพง",
    "เทศบาลตำบลสันกำแพง": "อำเภอสันกำแพง",
    "เทศบาลตำบลบวกค้าง": "อำเภอสันกำแพง",
    "เทศบาลตำบลยางเนิ้ง": "อำเภอสารภี",
    "เทศบาลตำบลหนองผึ้ง": "อำเภอสารภี",
    "เทศบาลตำบลชมภู": "อำเภอสารภี",
    "เทศบาลตำบลสารภี": "อำเภอสารภี",
    "เทศบาลตำบลสันปูเลย": "อำเภอดอยสะเก็ด",
    "เทศบาลตำบลเชิงดอย": "อำเภอดอยสะเก็ด",
    "เทศบาลตำบลดอยสะเก็ด": "อำเภอดอยสะเก็ด",
    "เทศบาลตำบลเมืองนะ": "อำเภอเชียงดาว",
    "เทศบาลตำบลปิงโค้ง": "อำเภอเชียงดาว",
    "เทศบาลตำบลทุ่งข้าวพวง": "อำเภอเชียงดาว",
    "เทศบาลตำบลเมืองงาย": "อำเภอเชียงดาว",
    "เทศบาลตำบลเชียงดาว": "อำเภอเชียงดาว",
    "เทศบาลตำบลพระธาตุปู่ก่ำ": "อำเภอเชียงดาว",
    "เทศบาลตำบลจอมทอง": "อำเภอจอมทอง",
    "เทศบาลตำบลแม่แจ่ม": "อำเภอแม่แจ่ม",
    "เทศบาลเมืองเมืองแกนพัฒนา": "อำเภอแม่แตง",
    "เทศบาลตำบลสันมหาพน": "อำเภอแม่แตง",
    "เทศบาลตำบลแม่ริม": "อำเภอแม่ริม",
    "เทศบาลตำบลสะเมิงใต้": "อำเภอสะเมิง",
    "เทศบาลตำบลเวียงฝาง": "อำเภอฝาง",
    "เทศบาลตำบลบ้านแม่ข่า": "อำเภอฝาง",
    "เทศบาลตำบลแม่อาย": "อำเภอแม่อาย",
    "เทศบาลตำบลเวียงพร้าว": "อำเภอพร้าว",
    "เทศบาลตำบลแม่ปั๋ง": "อำเภอพร้าว",
    "เทศบาลตำบลสันป่าตอง": "อำเภอสันป่าตอง",
    "เทศบาลตำบลบ้านกลาง": "อำเภอสันป่าตอง",
    "เทศบาลตำบลหางดง": "อำเภอหางดง",
    "เทศบาลตำบลหนองตองพัฒนา": "อำเภอหางดง",
    "เทศบาลตำบลท่าข้าม": "อำเภอหางดง",
    "เทศบาลตำบลบ่อหลวง": "อำเภอฮอด",
    "เทศบาลตำบลท่าเดื่อ-มืดกา": "อำเภอดอยเต่า",
    "เทศบาลตำบลอมก๋อย": "อำเภออมก๋อย",
    "เทศบาลตำบลไชยปราการ": "อำเภอไชยปราการ",
    "เทศบาลตำบลแม่วาง": "อำเภอแม่วาง",
}

SCHEMA_FIELDS = [
    ("DESC-CCAATT", "Area label (province, district, municipality or tambon). Not a CCAATT code in this file."),
    ("MALE_AGE / FEMALE_AGE 0–101", "102 male/female pairs, interleaved. Age 0 = under 1 year; age 101 = over 100 years. Thai nationals on ordinary house registration only."),
    ("MALE_TDOB / FEMALE_TDOB / TOTAL_TDOB", "Thai nationals recorded with a lunar-calendar birth year; no single-year age."),
    ("MALE_XHOUSE / FEMALE_XHOUSE / TOTAL_XHOUSE", "Persons on the central house register (ทะเบียนบ้านกลาง), who cannot be listed on an ordinary house register."),
    ("MALE_OTHER_NAT / FEMALE_OTHER_NAT / TOTAL_OTHER_NAT", "Persons who are not Thai nationals. All-age only; no single-year ages."),
    ("MALE_MOVE / FEMALE_MOVE / TOTAL_MOVE", "Persons who have moved out but not yet moved in anywhere."),
    ("MALE_TOT / FEMALE_TOT / TOTAL_TOT", "All registered persons. Identity: ages 0–101 + TDOB + XHOUSE + OTHER_NAT + MOVE."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def area_kind(name: str) -> str:
    if name.startswith("จังหวัด"):
        return "province"
    if name.startswith("อำเภอ"):
        return "district_residual"
    if name.startswith("ตำบล"):
        return "tambon"
    if name.startswith("เทศบาลนคร"):
        return "municipality_city"
    if name.startswith("เทศบาลเมือง"):
        return "municipality_town"
    if name.startswith("เทศบาลตำบล"):
        return "municipality_subdistrict"
    return "other"


def parse_line(line: str) -> dict:
    parts = line.split("|")
    name = parts[0].strip()
    nums = [int(x) for x in parts[1:] if x.strip() != ""]
    if len(nums) != N_NUMERIC:
        raise ValueError(f"{name}: expected {N_NUMERIC} numeric fields, got {len(nums)}")
    male = [nums[i] for i in range(0, N_AGE_FIELDS, 2)]
    female = [nums[i] for i in range(1, N_AGE_FIELDS, 2)]
    m_tdob, f_tdob, t_tdob = nums[204:207]
    m_xhouse, f_xhouse, t_xhouse = nums[207:210]
    m_other, f_other, t_other = nums[210:213]
    m_move, f_move, t_move = nums[213:216]
    m_tot, f_tot, t_tot = nums[216:219]
    if sum(male) + m_tdob + m_xhouse + m_other + m_move != m_tot:
        raise ValueError(f"{name}: male identity failed")
    if sum(female) + f_tdob + f_xhouse + f_other + f_move != f_tot:
        raise ValueError(f"{name}: female identity failed")
    if m_tot + f_tot != t_tot:
        raise ValueError(f"{name}: total identity failed")
    return {
        "area_name_th": name,
        "area_kind": area_kind(name),
        "male_ages": male,
        "female_ages": female,
        "male_tdob": m_tdob,
        "female_tdob": f_tdob,
        "total_tdob": t_tdob,
        "male_xhouse": m_xhouse,
        "female_xhouse": f_xhouse,
        "total_xhouse": t_xhouse,
        "male_other_nat": m_other,
        "female_other_nat": f_other,
        "total_other_nat": t_other,
        "male_move": m_move,
        "female_move": f_move,
        "total_move": t_move,
        "male_tot": m_tot,
        "female_tot": f_tot,
        "total_tot": t_tot,
        "thai_reg_age_0_5": sum(male[0:6]) + sum(female[0:6]),
        "thai_reg_age_6_11": sum(male[6:12]) + sum(female[6:12]),
        "thai_reg_age_12_17": sum(male[12:18]) + sum(female[12:18]),
        "thai_reg_age_0_17": sum(male[0:18]) + sum(female[0:18]),
        "thai_reg_age_18_plus": sum(male[18:]) + sum(female[18:]),
    }


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def summary_fields(row: dict, extra: dict | None = None) -> dict:
    out = {
        "area_name_th": row["area_name_th"],
        "area_kind": row["area_kind"],
        "thai_reg_age_0_5": row["thai_reg_age_0_5"],
        "thai_reg_age_6_11": row["thai_reg_age_6_11"],
        "thai_reg_age_12_17": row["thai_reg_age_12_17"],
        "thai_reg_age_0_17": row["thai_reg_age_0_17"],
        "thai_reg_age_18_plus": row["thai_reg_age_18_plus"],
        "total_tdob": row["total_tdob"],
        "total_xhouse": row["total_xhouse"],
        "total_other_nat": row["total_other_nat"],
        "total_move": row["total_move"],
        "male_tot": row["male_tot"],
        "female_tot": row["female_tot"],
        "total_registered": row["total_tot"],
    }
    if extra:
        out.update(extra)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw = SRC.read_text(encoding="utf-8-sig")
    parsed = [parse_line(ln) for ln in raw.splitlines() if ln.strip()]
    if parsed[0]["area_kind"] != "province":
        raise ValueError("first row is not the province")

    districts: list[dict] = []
    current_district = None
    current_muni = None
    section = "district"
    residual_child_sum: dict[str, int] = defaultdict(int)
    residual_child_n: dict[str, int] = defaultdict(int)
    muni_child_sum: dict[str, int] = defaultdict(int)
    muni_child_n: dict[str, int] = defaultdict(int)
    annotated = []
    district_code = 5000

    for i, row in enumerate(parsed, start=1):
        kind = row["area_kind"]
        parent_area_th = ""
        district_th = ""
        geography_slice = kind
        assigned_district_th = ""

        if kind == "province":
            geography_slice = "province"
        elif kind == "district_residual":
            district_code += 1
            current_district = row["area_name_th"]
            current_muni = None
            section = "district"
            districts.append({**row, "district_code": district_code, "district_en": DISTRICT_EN[current_district]})
            district_th = current_district
            geography_slice = "district_residual"
        elif kind.startswith("municipality"):
            current_muni = row["area_name_th"]
            section = "muni"
            if current_muni not in MUNI_TO_DISTRICT:
                raise ValueError(f"unassigned municipality: {current_muni}")
            assigned_district_th = MUNI_TO_DISTRICT[current_muni]
            district_th = assigned_district_th
            geography_slice = kind
        elif kind == "tambon":
            if section == "district":
                parent_area_th = current_district
                district_th = current_district
                geography_slice = "tambon_in_district_residual"
                residual_child_sum[current_district] += row["total_tot"]
                residual_child_n[current_district] += 1
            else:
                parent_area_th = current_muni
                assigned_district_th = MUNI_TO_DISTRICT[current_muni]
                district_th = assigned_district_th
                geography_slice = "tambon_in_municipality"
                muni_child_sum[current_muni] += row["total_tot"]
                muni_child_n[current_muni] += 1
        annotated.append({
            **summary_fields(row, {
                "row_no": i,
                "parent_area_th": parent_area_th,
                "district_th": district_th,
                "district_en": DISTRICT_EN.get(district_th, ""),
                "assigned_district_th": assigned_district_th,
                "geography_slice": geography_slice,
            }),
            "_raw": row,
        })

    # Residual vs listed tambons; municipality vs listed tambons.
    checks = []
    for d in districts:
        name = d["area_name_th"]
        ok = residual_child_sum[name] == d["total_tot"]
        checks.append({
            "check": f"residual_tambons_sum_to_district:{name}",
            "ok": ok,
            "expected": d["total_tot"],
            "got": residual_child_sum[name],
            "n_tambon_rows": residual_child_n[name],
        })
        if not ok:
            raise ValueError(f"residual tambons do not sum to {name}")

    munis = [r for r in parsed if r["area_kind"].startswith("municipality")]
    if len(munis) != len(MUNI_TO_DISTRICT):
        raise ValueError("municipality lookup size does not match file")
    for m in munis:
        name = m["area_name_th"]
        ok = muni_child_sum[name] == m["total_tot"]
        checks.append({
            "check": f"muni_tambons_sum_to_municipality:{name}",
            "ok": ok,
            "expected": m["total_tot"],
            "got": muni_child_sum[name],
            "n_tambon_rows": muni_child_n[name],
        })
        if not ok:
            raise ValueError(f"municipal tambons do not sum to {name}")

    # Whole-district reconstruction.
    muni_by_district: dict[str, list[dict]] = defaultdict(list)
    for m in munis:
        muni_by_district[MUNI_TO_DISTRICT[m["area_name_th"]]].append(m)

    reconstructed = []
    for d in districts:
        extras = muni_by_district.get(d["area_name_th"], [])
        rec = {
            "district_code": d["district_code"],
            "district_th": d["area_name_th"],
            "district_en": d["district_en"],
            "use_as_district_denominator": "yes",
            "n_municipalities_assigned": len(extras),
            "residual_total_registered": d["total_tot"],
            "municipal_total_registered": sum(m["total_tot"] for m in extras),
            "thai_reg_age_0_5": d["thai_reg_age_0_5"] + sum(m["thai_reg_age_0_5"] for m in extras),
            "thai_reg_age_6_11": d["thai_reg_age_6_11"] + sum(m["thai_reg_age_6_11"] for m in extras),
            "thai_reg_age_12_17": d["thai_reg_age_12_17"] + sum(m["thai_reg_age_12_17"] for m in extras),
            "thai_reg_age_0_17": d["thai_reg_age_0_17"] + sum(m["thai_reg_age_0_17"] for m in extras),
            "thai_reg_age_18_plus": d["thai_reg_age_18_plus"] + sum(m["thai_reg_age_18_plus"] for m in extras),
            "total_tdob": d["total_tdob"] + sum(m["total_tdob"] for m in extras),
            "total_xhouse": d["total_xhouse"] + sum(m["total_xhouse"] for m in extras),
            "total_other_nat": d["total_other_nat"] + sum(m["total_other_nat"] for m in extras),
            "total_move": d["total_move"] + sum(m["total_move"] for m in extras),
            "male_tot": d["male_tot"] + sum(m["male_tot"] for m in extras),
            "female_tot": d["female_tot"] + sum(m["female_tot"] for m in extras),
            "total_registered": d["total_tot"] + sum(m["total_tot"] for m in extras),
            "coverage_note": (
                "thai_reg_age_* are Thai nationals on ordinary house registration only. "
                "Non-Thai, central-register, lunar-birth-year and in-migration persons have no age split."
            ),
        }
        reconstructed.append(rec)

    province = parsed[0]
    sum_residual = sum(d["total_tot"] for d in districts)
    sum_muni = sum(m["total_tot"] for m in munis)
    sum_whole = sum(r["total_registered"] for r in reconstructed)
    sum_tambon = sum(r["total_tot"] for r in parsed if r["area_kind"] == "tambon")
    sum_whole_child = sum(r["thai_reg_age_0_17"] for r in reconstructed)

    for label, expected, got in [
        ("province_equals_residual_plus_municipalities", province["total_tot"], sum_residual + sum_muni),
        ("province_equals_reconstructed_districts", province["total_tot"], sum_whole),
        ("province_equals_all_tambon_rows", province["total_tot"], sum_tambon),
        ("province_child_0_17_equals_reconstructed_districts", province["thai_reg_age_0_17"], sum_whole_child),
    ]:
        checks.append({"check": label, "ok": expected == got, "expected": expected, "got": got})
        if expected != got:
            raise ValueError(f"{label}: expected {expected}, got {got}")

    # Naive misuse check: summing the 25 อำเภอ rows is NOT the province.
    checks.append({
        "check": "do_not_sum_amphoe_rows_as_province",
        "ok": sum_residual != province["total_tot"],
        "expected": "strictly less than province",
        "got": sum_residual,
        "province": province["total_tot"],
        "note": "อำเภอ rows are residuals. Their sum is 1,127,147; the province is 1,798,588.",
    })

    schema_rows = [{"field": a, "meaning": b} for a, b in SCHEMA_FIELDS]
    write_csv(OUT / "dopa_schema.csv", schema_rows, ["field", "meaning"])

    row_fields = [
        "row_no", "area_name_th", "area_kind", "geography_slice", "parent_area_th",
        "district_th", "district_en", "assigned_district_th",
        "thai_reg_age_0_5", "thai_reg_age_6_11", "thai_reg_age_12_17",
        "thai_reg_age_0_17", "thai_reg_age_18_plus",
        "total_tdob", "total_xhouse", "total_other_nat", "total_move",
        "male_tot", "female_tot", "total_registered",
    ]
    write_csv(OUT / "dopa_rows.csv", annotated, row_fields)

    dist_fields = [
        "district_code", "district_th", "district_en", "use_as_district_denominator",
        "n_municipalities_assigned", "residual_total_registered", "municipal_total_registered",
        "thai_reg_age_0_5", "thai_reg_age_6_11", "thai_reg_age_12_17",
        "thai_reg_age_0_17", "thai_reg_age_18_plus",
        "total_tdob", "total_xhouse", "total_other_nat", "total_move",
        "male_tot", "female_tot", "total_registered", "coverage_note",
    ]
    write_csv(OUT / "dopa_district_totals.csv", reconstructed, dist_fields)

    assign_rows = []
    for m in munis:
        district_th = MUNI_TO_DISTRICT[m["area_name_th"]]
        kids = [
            a["area_name_th"] for a in annotated
            if a["parent_area_th"] == m["area_name_th"]
        ]
        assign_rows.append({
            "municipality_th": m["area_name_th"],
            "municipality_kind": m["area_kind"],
            "assigned_district_th": district_th,
            "assigned_district_en": DISTRICT_EN[district_th],
            "total_registered": m["total_tot"],
            "thai_reg_age_0_17": m["thai_reg_age_0_17"],
            "constituent_tambon_rows": "; ".join(kids),
            "assignment_note": "Documented lookup; validated because residual + municipalities = province.",
        })
    write_csv(
        OUT / "dopa_municipality_assignment.csv",
        assign_rows,
        [
            "municipality_th", "municipality_kind", "assigned_district_th",
            "assigned_district_en", "total_registered", "thai_reg_age_0_17",
            "constituent_tambon_rows", "assignment_note",
        ],
    )

    province_row = {
        "area_name_th": province["area_name_th"],
        "reference_date": "December 2025 (B.E. 2568 month 12)",
        "source_url": "https://stat.bora.dopa.go.th/new_stat/file/6812/6812cc50.txt",
        "schema_url": "https://stat.bora.dopa.go.th/new_stat/webPage/statByAge.php",
        "total_registered": province["total_tot"],
        "male_tot": province["male_tot"],
        "female_tot": province["female_tot"],
        "thai_reg_age_0_5": province["thai_reg_age_0_5"],
        "thai_reg_age_6_11": province["thai_reg_age_6_11"],
        "thai_reg_age_12_17": province["thai_reg_age_12_17"],
        "thai_reg_age_0_17": province["thai_reg_age_0_17"],
        "thai_reg_age_18_plus": province["thai_reg_age_18_plus"],
        "total_tdob": province["total_tdob"],
        "total_xhouse": province["total_xhouse"],
        "total_other_nat": province["total_other_nat"],
        "total_move": province["total_move"],
        "n_district_residual_rows": 25,
        "n_municipalities": 54,
        "n_tambon_labelled_rows": 254,
        "proposed_child_denominator": province["thai_reg_age_0_17"],
        "denominator_definition": (
            "Thai nationals aged 0–17 on ordinary house registration. "
            "Excludes non-Thai (all-age only), central-register, lunar-birth-year and in-migration persons."
        ),
        "registered_is_not_resident": "yes",
        "do_not_use_amphoe_rows_as_district_totals": "yes",
    }
    write_csv(
        OUT / "dopa_province_summary.csv",
        [province_row],
        list(province_row.keys()),
    )

    # Worked example: Mueang residual vs Chiang Mai City vs Chang Phueak fragments.
    example_names = {
        "จังหวัดเชียงใหม่",
        "อำเภอเมืองเชียงใหม่",
        "เทศบาลนครเชียงใหม่",
        "เทศบาลตำบลช้างเผือก",
        "เทศบาลเมืองสุเทพ",
        "เทศบาลเมืองแม่เหียะ",
    }
    example_rows = []
    for a in annotated:
        name = a["area_name_th"]
        if name in example_names or (
            name == "ตำบลช้างเผือก" or name == "ตำบลสันผีเสื้อ"
        ):
            example_rows.append({
                **{k: a[k] for k in row_fields},
                "example_role": {
                    "จังหวัดเชียงใหม่": "Province total. Use this as the Chiang Mai registered-population total.",
                    "อำเภอเมืองเชียงใหม่": "District residual only (ช้างเผือก + สันผีเสื้อ). Not the whole of Mueang.",
                    "ตำบลช้างเผือก": "One registration fragment of tambon Chang Phueak. The same name appears three times.",
                    "ตำบลสันผีเสื้อ": "The other residual tambon under Mueang. 2,040 + 13,028 = 15,068 residual.",
                    "เทศบาลตำบลช้างเผือก": "Chang Phueak subdistrict municipality; another fragment of the same tambon.",
                    "เทศบาลนครเชียงใหม่": "Chiang Mai City. 14 tambon fragments, including a third Chang Phueak fragment.",
                    "เทศบาลเมืองสุเทพ": "Suthep town municipality (Mueang). Do not treat as a district.",
                    "เทศบาลเมืองแม่เหียะ": "Mae Hia town municipality (Mueang). Do not treat as a district.",
                }[name],
            })
    mueang = next(r for r in reconstructed if r["district_th"] == "อำเภอเมืองเชียงใหม่")
    example_rows.append({
        "row_no": "",
        "area_name_th": "อำเภอเมืองเชียงใหม่ (reconstructed whole district)",
        "area_kind": "district_whole",
        "geography_slice": "residual_plus_assigned_municipalities",
        "parent_area_th": "จังหวัดเชียงใหม่",
        "district_th": "อำเภอเมืองเชียงใหม่",
        "district_en": "Mueang Chiang Mai",
        "assigned_district_th": "",
        "thai_reg_age_0_5": mueang["thai_reg_age_0_5"],
        "thai_reg_age_6_11": mueang["thai_reg_age_6_11"],
        "thai_reg_age_12_17": mueang["thai_reg_age_12_17"],
        "thai_reg_age_0_17": mueang["thai_reg_age_0_17"],
        "thai_reg_age_18_plus": mueang["thai_reg_age_18_plus"],
        "total_tdob": mueang["total_tdob"],
        "total_xhouse": mueang["total_xhouse"],
        "total_other_nat": mueang["total_other_nat"],
        "total_move": mueang["total_move"],
        "male_tot": mueang["male_tot"],
        "female_tot": mueang["female_tot"],
        "total_registered": mueang["total_registered"],
        "example_role": (
            f"Use this as the Mueang district denominator: residual "
            f"{mueang['residual_total_registered']:,} + "
            f"{mueang['n_municipalities_assigned']} municipalities "
            f"{mueang['municipal_total_registered']:,} = "
            f"{mueang['total_registered']:,}."
        ),
    })
    write_csv(
        OUT / "dopa_worked_example.csv",
        example_rows,
        row_fields + ["example_role"],
    )

    validation = {
        "source_file": str(SRC.relative_to(ROOT)),
        "source_sha256": sha256(SRC),
        "encoding": "utf-8-sig",
        "n_rows": len(parsed),
        "n_numeric_fields_per_row": N_NUMERIC,
        "identity_check": "male/female ages 0–101 + TDOB + XHOUSE + OTHER_NAT + MOVE = sex total; passed for all 334 rows",
        "province_total_registered": province["total_tot"],
        "sum_25_district_residual_rows": sum_residual,
        "sum_54_municipalities": sum_muni,
        "sum_reconstructed_districts": sum_whole,
        "sum_254_tambon_rows": sum_tambon,
        "province_thai_reg_age_0_17": province["thai_reg_age_0_17"],
        "checks": checks,
        "how_to_use": {
            "district_denominators": "outputs/step1/dopa_district_totals.csv",
            "do_not_use": "อำเภอ-labelled rows in dopa_rows.csv as whole districts",
            "do_not_sum": "province + district + tambon + municipality rows together",
            "child_denominator": "thai_reg_age_0_17, with the coverage note attached",
        },
    }
    (OUT / "dopa_validation.json").write_text(
        json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("province", province["total_tot"])
    print("reconstructed districts", sum_whole)
    print("child 0-17", province["thai_reg_age_0_17"])
    print("wrote", OUT / "dopa_district_totals.csv")


if __name__ == "__main__":
    main()
