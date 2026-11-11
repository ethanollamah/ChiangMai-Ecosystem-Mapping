"""Build a localhost briefing preview from finished Level 2 tables.

Writes:
  preview/data/briefing.json
  preview/data/districts.geojson

Does not recompute travel times. Does not pack into the ChatGPT handoff.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "preview" / "data"
FAMILY = ROOT / "outputs" / "step6" / "comparison_family_support.csv"
EDU = ROOT / "outputs" / "step6" / "comparison_educational_reengagement.csv"
ACCESS = ROOT / "outputs" / "step5" / "district_access.csv"
DEST = ROOT / "outputs" / "step5" / "destinations.csv"
CENTROIDS = ROOT / "outputs" / "step5" / "district_centroids.csv"
BOUNDARIES = ROOT / "raw" / "boundaries" / "geoBoundaries-THA-ADM2_simplified.geojson"

PRESENCE = ROOT / "outputs" / "step4" / "district_presence.csv"
SITES = ROOT / "outputs" / "step2" / "sites.csv"
SITE_ROLES = ROOT / "outputs" / "step4" / "site_presence_role.csv"

# Districts that appear in any insight emphasis set (default highlight fallback).
FOCUS_CODES = {
    "5001",  # Mueang
    "5002",  # Chom Thong
    "5003",  # Mae Chaem
    "5005",  # Doi Saket
    "5009",  # Fang
    "5012",  # San Pa Tong
    "5014",  # San Sai
    "5015",  # Hang Dong
    "5016",  # Hot
    "5018",  # Omkoi
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(value: str | None) -> float | int | None:
    if value is None or value == "":
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return None


def minutes_label(minutes: float | None) -> str:
    if minutes is None:
        return "unknown"
    if minutes < 60:
        return f"{minutes:.0f} minutes" if minutes == int(minutes) else f"{minutes:.1f} minutes"
    hours = int(minutes // 60)
    rem = minutes - hours * 60
    if rem < 0.5:
        return f"{hours} hour" if hours == 1 else f"{hours} hours"
    return f"{hours} hour {rem:.0f} minutes" if hours == 1 else f"{hours} hours {rem:.0f} minutes"


def join_districts() -> dict[str, dict]:
    family = {r["district_code"]: r for r in read_csv(FAMILY)}
    edu = {r["district_code"]: r for r in read_csv(EDU)}
    access = {r["district_code"]: r for r in read_csv(ACCESS)}
    centroids = {r["district_code"]: r for r in read_csv(CENTROIDS)}

    districts: dict[str, dict] = {}
    for code, f in family.items():
        e = edu[code]
        a = access[code]
        c = centroids[code]
        car = num(a["private_vehicle_minutes"])
        walk = num(a["walk_minutes_same_destination"])
        valhalla = num(a["valhalla_auto_minutes_same_pair"])
        districts[code] = {
            "district_code": code,
            "district_en": f["district_en"],
            "district_th": f["district_th"],
            "shape_id": c["shape_id"],
            "in_focus": code in FOCUS_CODES,
            "centroid": {
                "lat": float(a["origin_latitude"]),
                "lon": float(a["origin_longitude"]),
            },
            "family": {
                "thai_reg_age_0_17": num(f["thai_reg_age_0_17_context_only"]),
                "n_family_support_sites": num(f["n_current_family_support_sites"]),
                "family_support_organisations": f["family_support_organisations"],
                "n_delivery_or_mixed": num(f["n_current_delivery_or_mixed"]),
                "n_approximated": num(f["n_of_those_approximated"]),
                "sites_per_10k": num(f["family_support_sites_per_10k_context"]),
                "tpmap_target_poor": num(f["tpmap_target_poor_people"]),
                "tpmap_rate_percent": num(f["tpmap_target_poor_rate_percent"]),
                "nearest_marker_id": f["nearest_family_support_site"],
                "nearest_organisation": f["nearest_family_support_organisation"],
                "car_minutes": car,
                "walk_minutes": walk,
                "valhalla_minutes": valhalla,
                "under_30_both_engines": f["under_30_min_on_both_engines"] == "yes",
                "rule_zero_and_poor": f["rule_zero_sites_and_target_poor_at_or_above_median"] == "yes",
                "rule_zero_and_children": f["rule_zero_sites_and_children_at_or_above_median"] == "yes",
                "rule_sites_and_poor_q3": f["rule_sites_present_and_target_poor_at_or_above_q3"] == "yes",
            },
            "education": {
                "dole_total": num(e["dole_total_records"]),
                "home_not_found": num(e["dole_home_not_found"]),
                "consented": num(e["dole_consented_info"]),
                "already_enrolled": num(e["dole_already_enrolled"]),
                "moved_away": num(e["dole_moved_away"]),
                "help_wanted": num(e["dole_help_wanted"]),
                "never_studied": num(e["dole_never_studied"]),
                "n_after_school": num(e["n_after_school_programme_sites"]),
                "after_school_organisations": e["after_school_organisations"],
                "n_school_campus": num(e["n_school_campus_sites"]),
                "school_campus_organisations": e["school_campus_organisations"],
                "rule_home_not_found": e["rule_home_not_found_at_or_above_q3"] == "yes",
                "rule_consented": e["rule_consented_at_or_above_q3"] == "yes",
                "rule_help_wanted": e["rule_help_wanted_at_or_above_q3"] == "yes",
                "rule_never_studied": e["rule_never_studied_at_or_above_q3"] == "yes",
            },
            "access": {
                "nearest_marker_id": a["nearest_marker_id"],
                "nearest_organisation": a["nearest_organisation"],
                "nearest_district_en": a["nearest_district_en"],
                "car_minutes": car,
                "car_km": num(a["private_vehicle_km"]),
                "walk_minutes": walk,
                "valhalla_minutes": valhalla,
                "valhalla_status": a["valhalla_status"],
                "under_30_both_engines": a["under_30_on_both_engines"] == "yes",
                "line_note": (
                    "These minutes are the modelled road trip from the district "
                    "centre to this public family-support address. They are not a "
                    "child's journey and not a trip to an after-school site."
                ),
            },
        }
        districts[code]["insight_ids"] = []
        districts[code]["action_sentence"] = factual_sentence(districts[code])
    return districts


def factual_sentence(d: dict) -> str:
    fam = d["family"]
    n = fam["n_family_support_sites"] or 0
    car = fam["car_minutes"]
    org = fam["nearest_organisation"] or "the nearest public service provider"
    if n == 0:
        return (
            f"This list has no family-support site in {d['district_en']}. "
            f"The modelled drive from the district centre to {org} is {minutes_label(car)}."
        )
    if n == 1:
        return (
            f"{d['district_en']} has 1 family-support site on this list. "
            f"The modelled drive from the district centre to {org} is {minutes_label(car)}."
        )
    return (
        f"{d['district_en']} has {n} family-support sites on this list. "
        f"The modelled drive from the district centre to {org} is {minutes_label(car)}."
    )


def special_sentences(districts: dict[str, dict]) -> None:
    """Override a few districts with the briefing sentences."""
    ds = districts["5005"]  # Doi Saket
    ds["action_sentence"] = (
        "Doi Saket has 7 delivery sites recorded only as the district and 0 in the "
        "family-support category. Homes are known to exist here. There is no "
        "family-support street address on this list yet."
    )

    ds = districts["5010"]  # Mae Ai
    ds["action_sentence"] = (
        "Mae Ai has 3 Kid's Ark after-school sites on the list, and the school list "
        f"shows {districts['5010']['education']['home_not_found']} houses not found and "
        f"{districts['5010']['education']['consented']} households who agreed to share "
        "information. The 177-minute drive ends at the Mae Rim family shelter. No drive "
        "to the after-school sites was estimated."
    )

    ds = districts["5012"]  # San Pa Tong
    ds["action_sentence"] = (
        "San Pa Tong has no family-support site inside the district. The modelled drive "
        f"to Radion in Hang Dong is {minutes_label(ds['family']['car_minutes'])} "
        "from the district centre."
    )

    ds = districts["5003"]  # Mae Chaem
    ds["action_sentence"] = (
        f"Mae Chaem has {ds['family']['tpmap_target_poor']:,} people in the poverty count, "
        "no mapped family-support site, and a drive of about 3 hours from the district "
        "centre."
    )

    ds = districts["5018"]  # Omkoi
    ds["action_sentence"] = (
        "Omkoi has no mapped family-support site and the longest modelled drive "
        f"({minutes_label(ds['family']['car_minutes'])}). The school list already has "
        f"{ds['education']['consented']} households who agreed to share information and "
        f"{ds['education']['help_wanted']} help-wanted flags."
    )

    ds = districts["5022"]  # Mae Wang
    ds["action_sentence"] = (
        "Mae Wang has one named family-support organisation, Daughters Rising, beside "
        f"{ds['family']['tpmap_target_poor']:,} people in the poverty count."
    )

    ds = districts["5001"]  # Mueang
    ds["action_sentence"] = (
        f"Mueang has {ds['family']['n_family_support_sites']} family-support sites, a poverty "
        f"count of {ds['family']['tpmap_target_poor']} out of 52,312 surveyed, and "
        f"{ds['education']['home_not_found']} houses not found on the school list. "
        "The known organisations are here. The school-list houses-not-found count is still large."
    )

    ds = districts["5009"]  # Fang
    ds["action_sentence"] = (
        f"Fang has {ds['education']['home_not_found']:,} houses the surveyor could not find. "
        "This is a finding-people track, not a follow-up-on-contact track."
    )

    ds = districts["5014"]  # San Sai
    ds["action_sentence"] = (
        f"San Sai has {ds['family']['n_family_support_sites']} family-support sites, the "
        "largest footprint in the province."
    )

    ds = districts["5016"]  # Hot
    ds["action_sentence"] = (
        f"Hot is quiet on the poverty count ({ds['family']['tpmap_target_poor']}) and loud "
        f"on contact ({ds['education']['consented']} consented, "
        f"{ds['education']['help_wanted']} help-wanted). It belongs with the follow-up track."
    )

    ds = districts["5007"]  # Mae Rim
    ds["action_sentence"] = (
        "Mae Rim's trip to its own shelter is "
        f"{minutes_label(ds['family']['car_minutes'])} on the main car model, "
        f"{minutes_label(ds['family']['valhalla_minutes'])} on the second, and "
        f"{minutes_label(ds['family']['walk_minutes'])} on foot. Write every access claim "
        "as a named trip, with and without a car."
    )

    ds = districts["5020"]  # Wiang Haeng
    ds["action_sentence"] = (
        f"Wiang Haeng's {ds['education']['dole_total']:,} school-list records include "
        f"{ds['education']['moved_away']:,} marked moved away. Build the caseload from the "
        "specific columns after setting those aside."
    )

    ds = districts["5002"]  # Chom Thong
    ds["action_sentence"] = (
        f"Chom Thong has {ds['family']['tpmap_target_poor']:,} people in the poverty count, "
        "no mapped family-support site, and a drive of about "
        f"{minutes_label(ds['family']['car_minutes'])}."
    )


def concentration_stats() -> dict:
    presence = read_csv(PRESENCE)
    total_level1 = sum(int(r["n_level1_sites"] or 0) for r in presence)
    trio_codes = {"5001", "5014", "5005"}
    trio_level1 = sum(
        int(r["n_level1_sites"] or 0)
        for r in presence
        if r["district_code"] in trio_codes
    )
    zero_delivery = sum(
        1 for r in presence if int(r["n_current_delivery_or_mixed"] or 0) == 0
    )
    return {
        "trio_level1_sites": trio_level1,
        "province_level1_sites": total_level1,
        "zero_delivery_districts": zero_delivery,
        "n_districts": len(presence),
    }


def build_insights(districts: dict[str, dict]) -> list[dict]:
    omkoi = districts["5018"]
    mae_chaem = districts["5003"]
    chom = districts["5002"]
    conc = concentration_stats()

    insights = [
        {
            "id": "concentration",
            "title": "Mapped services concentrate around the city",
            "problem": (
                f"Mueang Chiang Mai, San Sai and Doi Saket hold "
                f"{conc['trio_level1_sites']} of {conc['province_level1_sites']} "
                f"district-joined Level 1 sites. "
                f"{conc['zero_delivery_districts']} of {conc['n_districts']} "
                "districts have zero mapped current delivery or mixed sites."
            ),
            "action": (
                "Before building new facilities, test lower-cost reach: outreach from "
                "existing organisations, delivery through schools or government offices "
                "in zero-site districts, and formal cross-district referral. Ask whether "
                "city-fringe organisations already serve surrounding districts."
            ),
            "district_codes": ["5001", "5014", "5005"],
            "emphasis_codes": ["5001", "5014", "5005"],
            "dim_mode": "emphasis",
            "show_pins": "all_delivery",
            "show_trips": False,
            "trip_district_codes": [],
            "panel_fields": "family",
            "default_district": "5014",
            "track_accents": None,
        },
        {
            "id": "poverty-access",
            "title": "Poverty without local family-support access",
            "problem": (
                f"Mae Chaem has zero mapped family-support sites and "
                f"{mae_chaem['family']['tpmap_target_poor']:,} TPMAP target-poor people "
                f"({mae_chaem['family']['tpmap_rate_percent']:.2f}%), with a modelled "
                f"{minutes_label(mae_chaem['family']['car_minutes'])} drive to the "
                f"nearest public service provider. Chom Thong has zero sites, "
                f"{chom['family']['tpmap_target_poor']:,} target-poor "
                f"({chom['family']['tpmap_rate_percent']:.2f}%), and a "
                f"{minutes_label(chom['family']['car_minutes'])} drive."
            ),
            "action": (
                "These districts combine strong poverty signals, no mapped locations, "
                "and substantial travel. Partnership talks should explore a locally "
                "delivered family-preservation model — not only a longer referral trip."
            ),
            "district_codes": ["5003", "5002"],
            "emphasis_codes": ["5003", "5002"],
            "dim_mode": "emphasis",
            "show_pins": "family_public",
            "show_trips": True,
            "trip_district_codes": ["5003", "5002"],
            "panel_fields": "family",
            "default_district": "5003",
            "track_accents": None,
            "chip": "Family-support reading",
        },
        {
            "id": "omkoi-dual",
            "title": "Omkoi: family-support distance and education contact pressure",
            "problem": (
                f"Omkoi has {omkoi['family']['thai_reg_age_0_17']:,} registered Thai "
                f"children 0–17, zero mapped family-support sites, "
                f"{omkoi['family']['tpmap_target_poor']:,} target-poor people, and the "
                f"longest modelled family-support journey "
                f"({minutes_label(omkoi['family']['car_minutes'])}). The school list "
                f"shows {omkoi['education']['consented']} consented, "
                f"{omkoi['education']['help_wanted']} help-wanted, and "
                f"{omkoi['education']['never_studied']} never-studied records, with no "
                "mapped after-school programme."
            ),
            "action": (
                "Omkoi is not only remote. A substantial group has already signalled "
                "contact or help interest. Investigate an integrated local partnership "
                "that links family support with educational re-engagement."
            ),
            "district_codes": ["5018"],
            "emphasis_codes": ["5018"],
            "dim_mode": "emphasis",
            "show_pins": "family_public",
            "show_trips": True,
            "trip_district_codes": ["5018"],
            "panel_fields": "both",
            "default_district": "5018",
            "track_accents": None,
            "chip": "Family support + education",
        },
    ]

    for insight in insights:
        for code in insight["district_codes"]:
            if insight["id"] not in districts[code]["insight_ids"]:
                districts[code]["insight_ids"].append(insight["id"])
    return insights


def destinations() -> list[dict]:
    rows = []
    for r in read_csv(DEST):
        rows.append(
            {
                "marker_id": r["marker_id"],
                "organisation": r["organisation"],
                "district_code": r["district_code"],
                "district_en": r["district_en"],
                "lat": float(r["latitude"]),
                "lon": float(r["longitude"]),
                "presence_role": r["presence_role"],
                "pin_set": "family_public",
            }
        )
    return rows


def delivery_pins() -> list[dict]:
    """Exact-coordinate sites for the concentration map (subset of Level 1)."""
    roles = {r["marker_id"]: r for r in read_csv(SITE_ROLES)}
    pins = []
    for r in read_csv(SITES):
        lat, lon = r.get("latitude"), r.get("longitude")
        if not lat or not lon:
            continue
        role = roles.get(r["marker_id"], {})
        if role.get("district_join_eligible") != "yes":
            continue
        if r.get("district_code") in ("", None):
            continue
        pins.append(
            {
                "marker_id": r["marker_id"],
                "organisation": r["organisation"],
                "district_code": r["district_code"],
                "district_en": r.get("district_en") or "",
                "lat": float(lat),
                "lon": float(lon),
                "presence_role": role.get("presence_role") or "",
                "pin_set": "all_delivery",
                "is_family_support": role.get("counts_as_family_support_relevant")
                == "yes",
            }
        )
    return pins


def write_districts_geojson(districts: dict[str, dict]) -> None:
    shape_ids = {d["shape_id"]: d for d in districts.values()}
    with BOUNDARIES.open(encoding="utf-8") as f:
        raw = json.load(f)

    features = []
    for feat in raw["features"]:
        sid = feat["properties"].get("shapeID")
        if sid not in shape_ids:
            continue
        d = shape_ids[sid]
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "district_code": d["district_code"],
                    "district_en": d["district_en"],
                    "district_th": d["district_th"],
                    "in_focus": d["in_focus"],
                    "shape_id": sid,
                },
                "geometry": feat["geometry"],
            }
        )

    if len(features) != 25:
        raise SystemExit(f"Expected 25 district polygons, got {len(features)}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "districts.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    districts = join_districts()
    special_sentences(districts)
    insights = build_insights(districts)
    write_districts_geojson(districts)
    dest = destinations()
    pins = delivery_pins()

    bundle = {
        "title": "Chiang Mai partnership briefing",
        "generated_note": (
            "Built from finished Level 2 tables. Travel times are not recomputed. "
            "Private preview for localhost only."
        ),
        "data_as_of": "10 November 2026",
        "audience": "Private briefing for TSA and invited partners. Do not re-share without authorisation.",
        "sources": [
            "DOPA December 2025 — registered Thai children aged 0–17",
            "DOLE Zero Dropout retrieved 10 November 2026",
            "TPMAP 2569 metric 11111 with welfare card มีบัตร",
            "FINAL checkbox classification",
            "FOSSGIS car and foot routing 10 November 2026; Valhalla auto check",
        ],
        "reading_rules": [
            "Current delivery means a site where a programme is running, such as a home, campus, school programme, or shelter. Mixed means one address that is both an office and a place where the programme runs. Counts of current delivery or mixed include both, and only sites that are still operating. Offices and closed sites are left out of that count.",
            "A mapped site is presence in this sample, not capacity or children served.",
            "TPMAP target-poor people are all-age welfare-card counts, not poor children.",
            "DOLE columns are separate situations. The headline total includes people who moved away or who are already enrolled.",
            "Travel minutes are from the district centre to one of eight public family-support service providers.",
            "No score and no recommended pilot district.",
            "Zero mapped sites is not proof that no provider exists.",
        ],
        "legend": {
            "selected": "Selected district",
            "compare": "Compare district",
            "emphasis": "Named in this insight",
            "finding": "Finding-people track (Fang)",
            "follow_up": "Follow-up-on-contact track (Omkoi / Hot)",
            "dimmed": "Other districts (dimmed when highlight is on)",
            "door": "Public family-support service provider",
            "site": "Mapped site with exact coordinates",
            "centre": "District centre (trip start)",
            "trip": "Modelled car trip to nearest public service provider",
        },
        "focus_district_codes": sorted(FOCUS_CODES),
        "insights": insights,
        "destinations": dest,
        "delivery_pins": pins,
        "districts": list(districts.values()),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "briefing.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {OUT / 'briefing.json'}")
    print(f"wrote {OUT / 'districts.geojson'}")
    print(
        f"districts {len(districts)} destinations {len(dest)} "
        f"delivery_pins {len(pins)} insights {len(insights)}"
    )


if __name__ == "__main__":
    main()
