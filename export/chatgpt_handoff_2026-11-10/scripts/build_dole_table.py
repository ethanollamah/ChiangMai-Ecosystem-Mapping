"""Flatten DOLE Zero Dropout aggregate JSON into a district table plus a Thai-English glossary."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "dole"
OUT = ROOT / "outputs" / "step1"

# Direct translations of the dashboard's own Thai labels.
GLOSSARY = {
    "ย้ายไปพื้นที่อื่น": "Moved to another area",
    "ไม่ยินดีให้ข้อมูล": "Did not consent to provide information",
    "เข้าศึกษาแล้ว": "Already enrolled in education",
    "หาบ้านไม่พบ": "Home could not be found",
    "ยินดีให้ข้อมูล": "Consented to provide information",
    "การศึกษาทางเลือก ม.12": "Alternative education (Section 12, National Education Act)",
    "เสียชีวิต": "Deceased",
    "อยู่ในสถานสงเคราะห์": "Living in a welfare home",
    "อยู่ในสถานพินิจฯ": "In a juvenile observation and protection centre",
    "อยู่ในกระบวนการยุติธรรม": "In the justice process",
    "ไทย": "Thai",
    "ไม่ได้สัญชาติไทย": "Not of Thai nationality",
    "บุคคลที่ไม่มีสถานะทางทะเบียน": "Person without registration status",
    "ปฐมวัย (3-6 ปี)": "Early childhood (3-6 years)",
    "ประถมศึกษา (7-12 ปี)": "Primary (7-12 years)",
    "มัธยมศึกษาตอนต้น (13-15 ปี)": "Lower secondary (13-15 years)",
    "มัธยมศึกษาตอนปลาย (16-18 ปี)": "Upper secondary (16-18 years)",
}

SCREENING = list(GLOSSARY)[:10]
NATIONS = ["ไทย", "ไม่ได้สัญชาติไทย", "บุคคลที่ไม่มีสถานะทางทะเบียน"]
AGES = list(GLOSSARY)[13:17]
SLUG = {
    "ย้ายไปพื้นที่อื่น": "moved_away", "ไม่ยินดีให้ข้อมูล": "declined_info",
    "เข้าศึกษาแล้ว": "already_enrolled", "หาบ้านไม่พบ": "home_not_found",
    "ยินดีให้ข้อมูล": "consented_info", "การศึกษาทางเลือก ม.12": "alt_education_s12",
    "เสียชีวิต": "deceased", "อยู่ในสถานสงเคราะห์": "in_welfare_home",
    "อยู่ในสถานพินิจฯ": "in_juvenile_centre", "อยู่ในกระบวนการยุติธรรม": "in_justice_process",
    "ไทย": "thai", "ไม่ได้สัญชาติไทย": "non_thai", "บุคคลที่ไม่มีสถานะทางทะเบียน": "no_registration_status",
    "ปฐมวัย (3-6 ปี)": "age_3_6", "ประถมศึกษา (7-12 ปี)": "age_7_12",
    "มัธยมศึกษาตอนต้น (13-15 ปี)": "age_13_15", "มัธยมศึกษาตอนปลาย (16-18 ปี)": "age_16_18",
}


def row_for(path, log_by_file):
    d = json.loads(path.read_text(encoding="utf-8"))
    meta = log_by_file[path.name]
    r = {
        "area_code": meta["parameters"]["district_id"] or "50",
        "area_name_th": meta["area_name_th"],
        "retrieved_utc": meta["retrieved_utc"],
        "total_records": d["total"],
    }
    screening = {x["name"]: x["total"] for x in d.get("screening", [])}
    for k in SCREENING:
        r[f"screen_{SLUG[k]}"] = screening.get(k, 0)
    unknown = set(screening) - set(SCREENING)
    r["screen_other_labels"] = "; ".join(f"{k}={screening[k]}" for k in sorted(unknown))
    nations = {x["nationality"]: int(x["total"]) for x in d.get("nation", [])}
    for k in NATIONS:
        r[f"nat_{SLUG[k]}"] = nations.get(k, 0)
    r["nat_other_listed"] = sum(v for k, v in nations.items() if k not in NATIONS)
    for a in d.get("age_survey", []):
        s = SLUG.get(a["label"], a["label"])
        r[f"{s}_total"] = a["total"]
        r[f"{s}_surveyed"] = a["surveyed"]
        r[f"{s}_not_surveyed"] = a["not_surveyed"]
    r["help_wanted"] = d.get("help", {}).get("want", 0)
    r["help_not_wanted"] = d.get("help", {}).get("notwant", 0)
    r["ever_studied"] = d.get("ever_study", {}).get("ever", 0)
    r["never_studied"] = d.get("ever_study", {}).get("never", 0)
    return r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = json.loads((RAW / "acquisition_log.json").read_text(encoding="utf-8"))
    log_by_file = {e["file"]: e for e in log}
    paths = [RAW / "dole_50_province.json"] + sorted(RAW.glob("dole_50[0-9][0-9].json"))
    rows = [row_for(p, log_by_file) for p in paths]
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / "dole_zero_dropout_by_district.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "dole_glossary.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["thai_label", "english_translation", "column_slug"])
        for th, en in GLOSSARY.items():
            w.writerow([th, en, SLUG.get(th, "")])
    print(len(rows), "rows,", len(fields), "columns")


if __name__ == "__main__":
    main()
