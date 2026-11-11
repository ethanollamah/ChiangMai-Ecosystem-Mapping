"""Fetch DOLE Zero Dropout aggregate dashboard data for Chiang Mai (province + 25 districts).

Uses only the public aggregate endpoint called by the dashboard's filter button
(https://zerodropout.dole.go.th/). One attempt per request, no retries or access
workarounds; failures are logged rather than re-probed.
"""
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "raw" / "dole"
URL = "https://dbzerodropout.dole.go.th/api/dashboard_68.php"

DISTRICTS = {
    "5001": "เมืองเชียงใหม่", "5002": "จอมทอง", "5003": "แม่แจ่ม", "5004": "เชียงดาว",
    "5005": "ดอยสะเก็ด", "5006": "แม่แตง", "5007": "แม่ริม", "5008": "สะเมิง",
    "5009": "ฝาง", "5010": "แม่อาย", "5011": "พร้าว", "5012": "สันป่าตอง",
    "5013": "สันกำแพง", "5014": "สันทราย", "5015": "หางดง", "5016": "ฮอด",
    "5017": "ดอยเต่า", "5018": "อมก๋อย", "5019": "สารภี", "5020": "เวียงแหง",
    "5021": "ไชยปราการ", "5022": "แม่วาง", "5023": "แม่ออน", "5024": "ดอยหล่อ",
    "5025": "กัลยาณิวัฒนา",
}


def fetch(district_code, name_th):
    params = {"province_id": "50", "district_id": district_code, "subdistrict_id": ""}
    filename = f"dole_{district_code or '50_province'}.json"
    entry = {
        "file": filename, "url": URL, "method": "POST", "parameters": params,
        "area_name_th": name_th, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        r = requests.post(URL, data=params, timeout=60,
                          headers={"Referer": "https://zerodropout.dole.go.th/"})
        entry.update(status=r.status_code, content_type=r.headers.get("Content-Type"))
        if r.status_code != 200:
            entry["error"] = "Not retrieved; no retry or access workaround"
            return entry
        data = r.json()
        if not isinstance(data, dict) or "total" not in data:
            raise ValueError("Unexpected aggregate schema")
        (OUT / filename).write_bytes(r.content)
        entry.update(bytes=len(r.content), sha256=hashlib.sha256(r.content).hexdigest(),
                     total=data["total"])
    except Exception as e:  # noqa: BLE001 - log every failure type
        entry["error"] = f"{type(e).__name__}: {e}"
    return entry


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [("", "เชียงใหม่ (province)")] + list(DISTRICTS.items())
    log = []
    for code, name in jobs:
        entry = fetch(code, name)
        print(entry["file"], entry.get("status"), entry.get("total", entry.get("error")), flush=True)
        log.append(entry)
        time.sleep(1.5)
    (OUT / "acquisition_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
