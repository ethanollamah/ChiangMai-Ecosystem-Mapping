"""Step 2: clean and validate the geographic base.

Does not edit raw/project_snapshot/Chiang_Mai_Organisation_Location_Audit.xlsx.
Writes a dated copy plus analysis-ready organisation / site / site-stage tables.
Geocodes only publicly disclosed exact street addresses via Nominatim.
Protected, approximate and service-area records are not turned into fake points.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW_AUDIT = ROOT / "raw" / "project_snapshot" / "Chiang_Mai_Organisation_Location_Audit.xlsx"
CLASSIFICATION = ROOT / "outputs" / "step1" / "classification_FINAL_checkbox.json"
PUBLIC_DIR = ROOT / "outputs" / "step1" / "public_childrens_homes_2025.csv"
OUT = ROOT / "outputs" / "step2"
SOURCE_COPY = OUT / "source_copy" / "Chiang_Mai_Organisation_Location_Audit_2026-10-29.xlsx"
CACHE = OUT / "geocode_cache.json"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "ChiangMaiMapping/2.0 (Thrive TSA geographical analysis)"
TODAY = date.today().isoformat()

DISTRICT_CROSSWALK = {
    "Mueang Chiang Mai": ("5001", "อำเภอเมืองเชียงใหม่", "Mueang Chiang Mai", "chiang_mai"),
    "Chom Thong": ("5002", "อำเภอจอมทอง", "Chom Thong", "chiang_mai"),
    "Mae Chaem": ("5003", "อำเภอแม่แจ่ม", "Mae Chaem", "chiang_mai"),
    "Chiang Dao": ("5004", "อำเภอเชียงดาว", "Chiang Dao", "chiang_mai"),
    "Doi Saket": ("5005", "อำเภอดอยสะเก็ด", "Doi Saket", "chiang_mai"),
    "Mae Taeng": ("5006", "อำเภอแม่แตง", "Mae Taeng", "chiang_mai"),
    "Mae Rim": ("5007", "อำเภอแม่ริม", "Mae Rim", "chiang_mai"),
    "Samoeng": ("5008", "อำเภอสะเมิง", "Samoeng", "chiang_mai"),
    "Fang": ("5009", "อำเภอฝาง", "Fang", "chiang_mai"),
    "Mae Ai": ("5010", "อำเภอแม่อาย", "Mae Ai", "chiang_mai"),
    "Phrao": ("5011", "อำเภอพร้าว", "Phrao", "chiang_mai"),
    "San Pa Tong": ("5012", "อำเภอสันป่าตอง", "San Pa Tong", "chiang_mai"),
    "San Kamphaeng": ("5013", "อำเภอสันกำแพง", "San Kamphaeng", "chiang_mai"),
    "San Sai": ("5014", "อำเภอสันทราย", "San Sai", "chiang_mai"),
    "Hang Dong": ("5015", "อำเภอหางดง", "Hang Dong", "chiang_mai"),
    "Hot": ("5016", "อำเภอฮอด", "Hot", "chiang_mai"),
    "Doi Tao": ("5017", "อำเภอดอยเต่า", "Doi Tao", "chiang_mai"),
    "Omkoi": ("5018", "อำเภออมก๋อย", "Omkoi", "chiang_mai"),
    "Saraphi": ("5019", "อำเภอสารภี", "Saraphi", "chiang_mai"),
    "Wiang Haeng": ("5020", "อำเภอเวียงแหง", "Wiang Haeng", "chiang_mai"),
    "Chai Prakan": ("5021", "อำเภอไชยปราการ", "Chai Prakan", "chiang_mai"),
    "Mae Wang": ("5022", "อำเภอแม่วาง", "Mae Wang", "chiang_mai"),
    "Mae On": ("5023", "อำเภอแม่ออน", "Mae On", "chiang_mai"),
    "Doi Lo": ("5024", "อำเภอดอยหล่อ", "Doi Lo", "chiang_mai"),
    "Galyani Vadhana": ("5025", "อำเภอกัลยาณิวัฒนา", "Galyani Vadhana", "chiang_mai"),
    "แม่ริม": ("5007", "อำเภอแม่ริม", "Mae Rim", "chiang_mai"),
    "Wiang Pa Pao": ("", "อำเภอเวียงป่าเป้า", "Wiang Pa Pao", "chiang_rai"),
}

NON_JOIN_DISTRICTS = {
    "Undisclosed in Chiang Mai Province",
    "Province-wide / multiple districts",
    "Near Chiang Mai city; district not public",
    "Multiple / not publicly specified",
    "N/A",
    "Province-wide / not specified",
    "Province-wide / assessment scope",
    "Undisclosed / conflicting public clues",
}

# Nominatim class/type treated as too coarse for nearest-neighbour points.
COARSE_TYPES = {
    ("place", "village"), ("place", "town"), ("place", "city"),
    ("place", "suburb"), ("place", "hamlet"), ("place", "municipality"),
    ("boundary", "administrative"), ("place", "county"), ("place", "district"),
}
NAMED_FACILITY_TYPES = {
    "house", "residential", "yes", "building", "place_of_worship", "prison",
    "social_facility", "community_centre", "office", "school", "kindergarten",
    "ngo", "foundation", "social_centre", "childcare",
}
LANDMARK_QUERIES = {
    "CM-029": ["วัดดอนจั่น ท่าศาลา เชียงใหม่"],
    "CM-072": ["สถานพินิจและคุ้มครองเด็กและเยาวชนจังหวัดเชียงใหม่"],
    "CM-069": ["สถานสงเคราะห์เด็กชายบ้านเชียงใหม่ แม่ริม"],
    "CM-070": ["สถานสงเคราะห์เด็กบ้านเวียงพิงค์ แม่ริม"],
    "CM-003": ["Vineyard Methodist School San Sai Chiang Mai"],
    "CM-009": ["Warm Heart Foundation Phrao Chiang Mai"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def blank(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def load_cache() -> dict:
    if CACHE.is_file():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def nominatim_search(query: str, cache: dict) -> list[dict]:
    if query in cache:
        return cache[query]
    time.sleep(1.1)
    r = requests.get(
        NOMINATIM,
        params={
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "countrycodes": "th",
            "limit": 3,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    cache[query] = data
    save_cache(cache)
    return data


def in_chiang_mai(hit: dict) -> bool:
    addr = hit.get("address") or {}
    blob = " ".join(str(v) for v in addr.values()) + " " + str(hit.get("display_name") or "")
    return "Chiang Mai" in blob or "เชียงใหม่" in blob


def pick_hit(hits: list[dict]) -> dict | None:
    cm = [h for h in hits if in_chiang_mai(h)]
    return (cm or hits or [None])[0]


def point_kind(hit: dict) -> str:
    pair = (hit.get("category") or hit.get("class"), hit.get("type"))
    ntype = hit.get("type") or ""
    if pair in COARSE_TYPES:
        return "coarse_locality"
    if ntype in NAMED_FACILITY_TYPES:
        return "building_or_house"
    if hit.get("addresstype") in {"building", "house", "residential"}:
        return "building_or_house"
    if (hit.get("category") or hit.get("class")) == "highway":
        return "coarse_street"
    return "other"


def map_district(label: str) -> dict:
    label = blank(label)
    if label in DISTRICT_CROSSWALK:
        code, th, en, scope = DISTRICT_CROSSWALK[label]
        return {
            "district_label_original": label,
            "district_code": code,
            "district_th": th,
            "district_en": en,
            "district_join_eligible": "yes" if scope == "chiang_mai" and code else "no",
            "province_scope": scope,
        }
    return {
        "district_label_original": label,
        "district_code": "",
        "district_th": "",
        "district_en": "",
        "district_join_eligible": "no",
        "province_scope": "chiang_mai_non_join" if label in NON_JOIN_DISTRICTS else "unmapped",
    }


def is_exact_public(row: dict) -> bool:
    prec = blank(row.get("Location_Precision"))
    return prec == "Exact public street address"


def is_service_area(row: dict) -> bool:
    prec = blank(row.get("Location_Precision")).lower()
    site = blank(row.get("Site_Type")).lower()
    return "service-area" in prec or "service-area" in site or "service area" in site


def is_physical_site(row: dict) -> bool:
    prec = blank(row.get("Location_Precision")).lower()
    if "no verified" in prec:
        return False
    if "service-area" in prec or "service-area" in blank(row.get("Site_Type")).lower():
        return False
    if "network geography" in prec and "not separately mapped" in blank(row.get("Site_or_Marker")).lower():
        return False
    if blank(row.get("Include_in_Map")) == "No" and "out of scope" in blank(row.get("Scope_Status")).lower():
        return False
    return True


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)


def load_master() -> tuple[list[str], list[dict]]:
    wb = load_workbook(RAW_AUDIT, data_only=True)
    ws = wb["Master Locations"]
    hdr = [c.value for c in ws[3]]
    rows = []
    for r in ws.iter_rows(min_row=4, values_only=True):
        if r[0] is None:
            continue
        rows.append(dict(zip(hdr, r)))
    return hdr, rows


def load_org_summary() -> list[dict]:
    wb = load_workbook(RAW_AUDIT, data_only=True)
    ws = wb["Organisation Summary"]
    hdr = [c.value for c in ws[3]]
    out = []
    for r in ws.iter_rows(min_row=4, values_only=True):
        if r[0] is None:
            continue
        out.append(dict(zip(hdr, r)))
    return out


def geocode_address(queries: list[str], cache: dict) -> dict:
    tried = []
    for q in queries:
        q = blank(q)
        if not q or q in tried:
            continue
        tried.append(q)
        hits = nominatim_search(q, cache)
        hit = pick_hit(hits)
        if hit:
            return {
                "ok": True,
                "query_used": q,
                "queries_tried": " | ".join(tried),
                "lat": float(hit["lat"]),
                "lon": float(hit["lon"]),
                "display_name": hit.get("display_name", ""),
                "osm_type": hit.get("osm_type", ""),
                "osm_id": hit.get("osm_id", ""),
                "nominatim_class": hit.get("category") or hit.get("class") or "",
                "nominatim_type": hit.get("type", ""),
                "point_kind": point_kind(hit),
                "in_chiang_mai": "yes" if in_chiang_mai(hit) else "no",
                "n_hits": len(hits),
            }
    return {
        "ok": False,
        "query_used": "",
        "queries_tried": " | ".join(tried),
        "lat": "",
        "lon": "",
        "display_name": "",
        "osm_type": "",
        "osm_id": "",
        "nominatim_class": "",
        "nominatim_type": "",
        "point_kind": "",
        "in_chiang_mai": "",
        "n_hits": 0,
    }


def apply_geocode_result(site: dict, result: dict, log_change) -> None:
    site["geocode_status"] = "ok" if result["ok"] else "failed"
    site["geocode_point_kind"] = result.get("point_kind", "")
    site["geocode_display_name"] = result.get("display_name", "")
    site["geocode_query_used"] = result.get("query_used", "")
    if not result["ok"]:
        return
    old_lat, old_lon = site.get("latitude", ""), site.get("longitude", "")
    site["latitude"] = f"{result['lat']:.6f}"
    site["longitude"] = f"{result['lon']:.6f}"
    log_change(
        site["marker_id"], site["organisation"], "latitude,longitude",
        f"{old_lat},{old_lon}", f"{site['latitude']},{site['longitude']}",
        f"Nominatim {result['point_kind']} ({result.get('nominatim_class','')}/{result.get('nominatim_type','')}); in_chiang_mai={result['in_chiang_mai']}.",
        f"nominatim:{result['query_used']}",
    )
    juvenile = site.get("core_universe_role") == "juvenile_justice_separately_labelled"
    house = result["point_kind"] == "building_or_house"
    if (
        site["include_in_map"] == "Yes"
        and site["in_chiang_mai_scope"] == "yes"
        and result["in_chiang_mai"] == "yes"
        and house
        and not juvenile
    ):
        site["level1_point_eligible"] = "yes"
    else:
        site["level1_point_eligible"] = "no"
        if not house:
            site["geocode_status"] = "ok_coarse"


def public_sites() -> list[dict]:
    with PUBLIC_DIR.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCE_COPY.parent.mkdir(parents=True, exist_ok=True)
    if not SOURCE_COPY.is_file() or sha256(SOURCE_COPY) != sha256(RAW_AUDIT):
        shutil.copy2(RAW_AUDIT, SOURCE_COPY)

    hdr, master = load_master()
    org_sum = load_org_summary()
    classif = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
    class_by_name = {o["organisation"]: o for o in classif["organisations"]}
    cache = load_cache()
    log = []
    now = datetime.now(timezone.utc).isoformat()

    def log_change(marker_id, organisation, field, old, new, reason, source):
        log.append({
            "timestamp_utc": now,
            "marker_id": marker_id,
            "organisation": organisation,
            "field": field,
            "old_value": old,
            "new_value": new,
            "reason": reason,
            "source": source,
        })

    org_id_by_name = {}
    for o in org_sum:
        org_id_by_name[o["Organisation"]] = f"ORG-{int(o['No.']):03d}"

    sites = []
    for row in master:
        dist = map_district(row.get("District"))
        if dist["province_scope"] == "unmapped" and blank(row.get("District")):
            dist["province_scope"] = "chiang_mai_non_join"
        include = blank(row.get("Include_in_Map"))
        scope = blank(row.get("Scope_Status"))
        in_cm = "no" if "Chiang Rai" in scope or dist["province_scope"] == "chiang_rai" else "yes"
        exact = is_exact_public(row)
        service = is_service_area(row)
        physical = is_physical_site(row) and in_cm == "yes"
        if include == "No" and "out of scope" in scope.lower():
            physical = False
        if include == "No" and "no verified" in blank(row.get("Location_Precision")).lower():
            physical = False
        if include == "No" and "not separately mapped" in blank(row.get("Site_or_Marker")).lower():
            physical = False
        if include == "No" and "alternate" in blank(row.get("Site_or_Marker")).lower():
            physical = False

        site = {
            "marker_id": row["Marker_ID"],
            "org_id": org_id_by_name.get(row["Organisation"], ""),
            "organisation": row["Organisation"],
            "site_or_marker": row["Site_or_Marker"],
            "parent_or_network": blank(row.get("Parent_or_Network")),
            "site_type": blank(row.get("Site_Type")),
            "map_location": blank(row.get("Map_Location")),
            "address_thai": blank(row.get("Address_Thai")),
            "address_english": blank(row.get("Address_English")),
            "province_original": blank(row.get("Province")),
            **dist,
            "latitude_original": blank(row.get("Latitude")),
            "longitude_original": blank(row.get("Longitude")),
            "latitude": blank(row.get("Latitude")),
            "longitude": blank(row.get("Longitude")),
            "location_precision": blank(row.get("Location_Precision")),
            "public_or_protected": blank(row.get("Public_or_Protected")),
            "approximation_method": blank(row.get("Approximation_Method")),
            "verified_physical_site": blank(row.get("Verified_Physical_Site")),
            "multi_site_flag": blank(row.get("Multi_Site_Flag")),
            "operational_status": blank(row.get("Operational_Status")),
            "scope_status": scope,
            "include_in_map": include,
            "confidence": blank(row.get("Confidence")),
            "primary_source_url": blank(row.get("Primary_Source_URL")),
            "verification_date": blank(row.get("Verification_Date")),
            "applicable_stages_original": blank(row.get("Applicable_Stages")),
            "stage_evidence_level": "organisation",
            "record_source": "audit_2026-10-29",
            "in_chiang_mai_scope": in_cm,
            "is_exact_public_address": "yes" if exact else "no",
            "is_service_area": "yes" if service else "no",
            "is_physical_site": "yes" if physical else "no",
            "core_universe_role": "mapped_child_welfare",
            "geocode_status": "not_attempted",
            "geocode_point_kind": "",
            "geocode_display_name": "",
            "level1_org_eligible": "yes" if in_cm == "yes" else "no",
            "level1_site_eligible": "yes" if physical and include == "Yes" else "no",
            "level1_point_eligible": "no",
            "level1_district_join_eligible": dist["district_join_eligible"] if in_cm == "yes" and include == "Yes" else "no",
            "notes": blank(row.get("Notes")),
        }
        if site["latitude"] and site["longitude"] and exact and include == "Yes" and in_cm == "yes":
            site["geocode_status"] = "audit_supplied"
            site["level1_point_eligible"] = "yes"
        log_change(
            site["marker_id"], site["organisation"], "district_code",
            blank(row.get("District")), site["district_code"] or "(non-join)",
            "Mapped audit district label onto DOPA 5001–5025; non-district phrases stay non-joins.",
            "district_crosswalk",
        )
        sites.append(site)

    # Geocode exact public addresses that still lack a usable point.
    to_geocode = [
        s for s in sites
        if s["is_exact_public_address"] == "yes"
        or s["location_precision"] == "Exact published address — status unresolved"
    ]
    for s in to_geocode:
        if s["geocode_status"] == "audit_supplied":
            continue
        queries = [s["map_location"], s["address_english"], s["address_thai"]]
        queries.extend(LANDMARK_QUERIES.get(s["marker_id"], []))
        result = geocode_address(queries, cache)
        if result["ok"]:
            apply_geocode_result(s, result, log_change)
        else:
            s["geocode_status"] = "failed"
            s["geocode_query_used"] = result.get("queries_tried", "")
            log_change(
                s["marker_id"], s["organisation"], "geocode_status",
                "empty", "failed",
                f"Nominatim returned no hit. Tried: {result['queries_tried']}",
                "nominatim",
            )

    # Add four public directory sites.
    next_marker = 69
    next_org = 54
    for pub in public_sites():
        marker_id = f"CM-{next_marker:03d}"
        org_id = f"ORG-{next_org:03d}"
        next_marker += 1
        next_org += 1
        dist = map_district(pub["district_en"])
        queries = [
            pub["address_th"] + " ประเทศไทย",
            f"{pub['address_th']}",
        ]
        # House numbers 63/1, 63/3, 63/4 share one campus; still query each.
        extra = LANDMARK_QUERIES.get(marker_id, [])
        result = geocode_address(queries + extra, cache)
        juvenile = pub["core_universe_role"] == "juvenile_justice_separately_labelled"
        site = {
            "marker_id": marker_id,
            "org_id": org_id,
            "organisation": pub["facility_name_en"],
            "organisation_th": pub["facility_name_th"],
            "site_or_marker": pub["facility_name_en"],
            "parent_or_network": "Thailand public child-welfare / justice directory 2025",
            "site_type": pub["facility_type_en"],
            "map_location": pub["address_th"],
            "address_thai": pub["address_th"],
            "address_english": "",
            "province_original": "Chiang Mai",
            **dist,
            "latitude_original": "",
            "longitude_original": "",
            "latitude": f"{result['lat']:.6f}" if result["ok"] else "",
            "longitude": f"{result['lon']:.6f}" if result["ok"] else "",
            "location_precision": "Exact public street address" if result.get("point_kind") == "building_or_house" else "Public directory street address — geocode pending or coarse",
            "public_or_protected": "Public exact site",
            "approximation_method": "",
            "verified_physical_site": "Directory address; geocode as noted",
            "multi_site_flag": "Campus with adjacent public facilities" if "Don Kaeo" in pub["campus_note"] or "ดอนแก้ว" in pub.get("campus_note", "") or "Don Kaeo" in pub["campus_note"] else "No",
            "operational_status": "Listed as operating in 2025 public directory",
            "scope_status": "In scope — Chiang Mai Province",
            "include_in_map": "Yes",
            "confidence": "High",
            "primary_source_url": "",
            "verification_date": TODAY,
            "applicable_stages_original": "",
            "stage_evidence_level": "directory_category",
            "record_source": "public_directory_2025",
            "in_chiang_mai_scope": "yes",
            "is_exact_public_address": "yes",
            "is_service_area": "no",
            "is_physical_site": "yes",
            "core_universe_role": pub["core_universe_role"],
            "geocode_status": "ok" if result["ok"] else "failed",
            "geocode_point_kind": result.get("point_kind", ""),
            "geocode_display_name": result.get("display_name", ""),
            "geocode_query_used": result.get("query_used") or result.get("queries_tried", ""),
            "level1_org_eligible": "no" if juvenile else "yes",
            "level1_site_eligible": "no" if juvenile else "yes",
            "level1_point_eligible": "yes" if (result["ok"] and result["point_kind"] == "building_or_house" and not juvenile) else "no",
            "level1_district_join_eligible": "yes",
            "notes": pub["campus_note"],
        }
        if result["ok"] and result["point_kind"] != "building_or_house":
            site["geocode_status"] = "ok_coarse"
        sites.append(site)
        org_id_by_name[pub["facility_name_en"]] = org_id
        log_change(
            marker_id, pub["facility_name_en"], "record_added",
            "", marker_id,
            f"Added from 2025 public directory as {pub['facility_type']}. Juvenile stays separately labelled."
            if juvenile else f"Added from 2025 public directory as {pub['facility_type']}. Not in 29 Oct audit.",
            "public_childrens_homes_2025.csv",
        )
        if result["ok"]:
            log_change(
                marker_id, pub["facility_name_en"], "latitude,longitude",
                "", f"{site['latitude']},{site['longitude']}",
                f"Nominatim {result['point_kind']}",
                f"nominatim:{result['query_used']}",
            )
        else:
            log_change(
                marker_id, pub["facility_name_en"], "geocode_status",
                "empty", "failed",
                f"Nominatim returned no hit. Tried: {result['queries_tried']}",
                "nominatim",
            )

    # Don Kaeo public campus: 63/1, 63/3, 63/4. Nominatim resolved the reception
    # shelter; do not invent separate points for the two welfare homes.
    by_id = {s["marker_id"]: s for s in sites}
    campus = by_id.get("CM-071")
    if campus and campus.get("latitude"):
        for mid in ("CM-069", "CM-070"):
            s = by_id.get(mid)
            if not s:
                continue
            old_latlon = f"{s.get('latitude', '')},{s.get('longitude', '')}"
            s["latitude"] = campus["latitude"]
            s["longitude"] = campus["longitude"]
            s["geocode_status"] = "campus_shared_with_CM-071"
            s["geocode_point_kind"] = campus.get("geocode_point_kind", "")
            s["geocode_display_name"] = campus.get("geocode_display_name", "")
            s["level1_point_eligible"] = "no"
            if "not a separate nearest-neighbour" not in blank(s.get("notes")):
                s["notes"] = (
                    blank(s.get("notes")) + " Coordinates shared with CM-071 (same Don Kaeo campus); "
                    "not a separate nearest-neighbour observation."
                ).strip()
            log_change(
                mid, s["organisation"], "latitude,longitude",
                old_latlon, f"{s['latitude']},{s['longitude']}",
                "Same Don Kaeo public campus as CM-071. Shared campus coordinate; not an extra point.",
                "campus_share:CM-071",
            )

    # Organisations
    orgs = []
    for o in org_sum:
        name = o["Organisation"]
        cl = class_by_name.get(name, {})
        in_cm = "no" if o.get("Out_of_Scope_or_Excluded") and name in {
            "Homestead of Hope", "Unity Villa", "The Family Forge",
        } else "yes"
        # Building Stronger Families / INEB / Asia's Hope remain in-province organisations.
        if name in {"Homestead of Hope", "Unity Villa", "The Family Forge"}:
            in_cm = "no"
        site_rows = [s for s in sites if s["organisation"] == name]
        orgs.append({
            "org_id": org_id_by_name[name],
            "organisation": name,
            "organisation_raw": cl.get("organisation_raw", name),
            "record_source": "audit_2026-10-29",
            "in_chiang_mai_scope": in_cm,
            "core_universe_role": "mapped_child_welfare",
            "n_site_records": len(site_rows),
            "n_level1_sites": sum(1 for s in site_rows if s["level1_site_eligible"] == "yes"),
            "n_level1_points": sum(1 for s in site_rows if s["level1_point_eligible"] == "yes"),
            "multi_site_flag": blank(o.get("Multi_Site_Flag")),
            "operational_status": blank(o.get("Operational_Status")),
            "out_of_scope_or_excluded_flag": o.get("Out_of_Scope_or_Excluded") or 0,
            "stages_from_final": "; ".join(cl.get("stages", [])),
            "any_final_tick": cl.get("any_tick", False),
            "level1_org_eligible": "yes" if in_cm == "yes" else "no",
            "key_location_note": blank(o.get("Key_Location_Note")),
        })
    for pub in public_sites():
        name = pub["facility_name_en"]
        juvenile = pub["core_universe_role"] == "juvenile_justice_separately_labelled"
        site_rows = [s for s in sites if s["organisation"] == name]
        orgs.append({
            "org_id": org_id_by_name[name],
            "organisation": name,
            "organisation_th": pub["facility_name_th"],
            "organisation_raw": pub["facility_name_th"],
            "record_source": "public_directory_2025",
            "in_chiang_mai_scope": "yes",
            "core_universe_role": pub["core_universe_role"],
            "n_site_records": len(site_rows),
            "n_level1_sites": sum(1 for s in site_rows if s["level1_site_eligible"] == "yes"),
            "n_level1_points": sum(1 for s in site_rows if s["level1_point_eligible"] == "yes"),
            "multi_site_flag": "Campus with adjacent public facilities" if "campus" in pub["campus_note"].lower() else "No",
            "operational_status": "Listed in 2025 public directory",
            "out_of_scope_or_excluded_flag": 0,
            "stages_from_final": "",
            "any_final_tick": False,
            "level1_org_eligible": "no" if juvenile else "yes",
            "key_location_note": pub["campus_note"],
        })

    # Site-stage table. Audit stages are organisation-level. Public directory types are labelled separately.
    stage_rows = []
    for s in sites:
        if s["record_source"] == "public_directory_2025":
            if s["core_universe_role"] == "public_welfare":
                stages = [("Residential and Institutional Care", "public_directory_category")]
            elif s["core_universe_role"] == "public_reception":
                stages = [("Short-term Intervention", "public_directory_category")]
            else:
                stages = [("Juvenile justice — separately labelled", "public_directory_category")]
        else:
            raw = s["applicable_stages_original"]
            stages = [(p.strip(), "organisation_from_audit") for p in raw.split(";") if p.strip()]
            if not stages:
                cl = class_by_name.get(s["organisation"], {})
                stages = [(st, "organisation_from_final_checkbox") for st in cl.get("stages", [])]
        if not stages:
            stages = [("", "none")]
        for st, src in stages:
            stage_rows.append({
                "marker_id": s["marker_id"],
                "org_id": s["org_id"],
                "organisation": s["organisation"],
                "stage": st,
                "stage_source": src,
                "stage_evidence_level": s["stage_evidence_level"],
                "level1_site_eligible": s["level1_site_eligible"],
                "note": "Stage-sheet repeats are not extra sites. Do not count this row as an additional organisation.",
            })

    crosswalk_rows = []
    seen = set()
    for label, (code, th, en, scope) in DISTRICT_CROSSWALK.items():
        if label in seen:
            continue
        seen.add(label)
        crosswalk_rows.append({
            "audit_district_label": label,
            "district_code": code,
            "district_th": th,
            "district_en": en,
            "province_scope": scope,
            "join_eligible": "yes" if scope == "chiang_mai" and code else "no",
        })
    for label in sorted(NON_JOIN_DISTRICTS):
        crosswalk_rows.append({
            "audit_district_label": label,
            "district_code": "",
            "district_th": "",
            "district_en": "",
            "province_scope": "chiang_mai_non_join",
            "join_eligible": "no",
        })

    site_fields = [
        "marker_id", "org_id", "organisation", "organisation_th", "site_or_marker",
        "parent_or_network", "site_type", "map_location", "address_thai", "address_english",
        "district_label_original", "district_code", "district_th", "district_en",
        "district_join_eligible", "province_scope", "province_original",
        "latitude_original", "longitude_original", "latitude", "longitude",
        "location_precision", "public_or_protected", "approximation_method",
        "verified_physical_site", "multi_site_flag", "operational_status",
        "scope_status", "include_in_map", "confidence", "primary_source_url",
        "verification_date", "record_source", "core_universe_role",
        "in_chiang_mai_scope", "is_exact_public_address", "is_service_area",
        "is_physical_site", "geocode_status", "geocode_point_kind",
        "geocode_display_name", "geocode_query_used",
        "level1_org_eligible", "level1_site_eligible", "level1_point_eligible",
        "level1_district_join_eligible", "stage_evidence_level",
        "applicable_stages_original", "notes",
    ]
    org_fields = [
        "org_id", "organisation", "organisation_th", "organisation_raw", "record_source",
        "in_chiang_mai_scope", "core_universe_role", "n_site_records", "n_level1_sites",
        "n_level1_points", "multi_site_flag", "operational_status",
        "out_of_scope_or_excluded_flag", "stages_from_final", "any_final_tick",
        "level1_org_eligible", "key_location_note",
    ]
    write_csv(OUT / "sites.csv", sites, site_fields)
    write_csv(OUT / "organisations.csv", orgs, org_fields)
    write_csv(OUT / "site_stages.csv", stage_rows, [
        "marker_id", "org_id", "organisation", "stage", "stage_source",
        "stage_evidence_level", "level1_site_eligible", "note",
    ])
    write_csv(OUT / "change_log.csv", log, [
        "timestamp_utc", "marker_id", "organisation", "field", "old_value",
        "new_value", "reason", "source",
    ])
    write_csv(OUT / "district_crosswalk.csv", crosswalk_rows, [
        "audit_district_label", "district_code", "district_th", "district_en",
        "province_scope", "join_eligible",
    ])

    summary = {
        "raw_audit_sha256": sha256(RAW_AUDIT),
        "source_copy": str(SOURCE_COPY.relative_to(ROOT)),
        "n_sites": len(sites),
        "n_organisations": len(orgs),
        "n_from_audit": sum(1 for s in sites if s["record_source"] == "audit_2026-10-29"),
        "n_from_public_directory": sum(1 for s in sites if s["record_source"] == "public_directory_2025"),
        "level1_orgs": sum(1 for o in orgs if o["level1_org_eligible"] == "yes"),
        "level1_sites": sum(1 for s in sites if s["level1_site_eligible"] == "yes"),
        "level1_points": sum(1 for s in sites if s["level1_point_eligible"] == "yes"),
        "geocode_ok_house": sum(1 for s in sites if s.get("geocode_point_kind") == "building_or_house"),
        "geocode_ok_coarse": sum(1 for s in sites if s["geocode_status"] == "ok_coarse"),
        "geocode_failed": sum(1 for s in sites if s["geocode_status"] == "failed"),
        "chiang_rai_excluded": [
            s["marker_id"] for s in sites if s["province_scope"] == "chiang_rai"
        ],
        "rule": (
            "Level 1 unique organisations use level1_org_eligible. Unique physical sites use "
            "level1_site_eligible. Nearest-neighbour points use only level1_point_eligible "
            "(exact public house/building geocodes in Chiang Mai). Service-area markers and "
            "protected approximations are not points. Juvenile justice is labelled but not in "
            "the family-support site count."
        ),
    }
    (OUT / "cleaning_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
