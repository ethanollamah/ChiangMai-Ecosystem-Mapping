"""Step 3 — Level 1 concentration and dispersion.

Reads the cleaned Step 2 tables. Does not edit the 29 October audit.
Unique organisations, unique physical sites and nearest-neighbour points are
three different numerators. Juvenile justice is labelled and excluded from
family-support counts. No clustering significance test is run.
"""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP2 = ROOT / "outputs" / "step2"
DOPA = ROOT / "outputs" / "step1" / "dopa_district_totals.csv"
OUT = ROOT / "outputs" / "step3"

STAGE_ORDER = [
    "Identification & Routing",
    "Parent Capability Building",
    "Short-term Intervention",
    "Residential and Institutional Care",
    "Foster Care / Adoption",
    "Kinship Care",
    "Reintegration, Reunification and Adoption",
]
EARTH_KM = 6371.0088
NON_JOIN = "(in Chiang Mai; district not joinable)"


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)


def yn(value: str) -> bool:
    return str(value).strip().lower() == "yes"


def as_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def stages_of(org: dict) -> list[str]:
    raw = org.get("stages_from_final") or ""
    return [p.strip() for p in raw.split(";") if p.strip()]


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(h)))


def median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return float("nan")
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sites = load_csv(STEP2 / "sites.csv")
    orgs = load_csv(STEP2 / "organisations.csv")
    stages = load_csv(STEP2 / "site_stages.csv")
    dopa = load_csv(DOPA)

    l1_orgs = [o for o in orgs if yn(o["level1_org_eligible"])]
    l1_sites = [s for s in sites if yn(s["level1_site_eligible"])]
    l1_points = [s for s in sites if yn(s["level1_point_eligible"])]
    juvenile = [s for s in sites if s["core_universe_role"] == "juvenile_justice_separately_labelled"]
    chiang_rai = [s for s in sites if s["province_scope"] == "chiang_rai"]
    public_core = [o for o in l1_orgs if o["core_universe_role"] in {"public_welfare", "public_reception"}]
    mapped_orgs = [o for o in l1_orgs if o["core_universe_role"] == "mapped_child_welfare"]
    ticked = [o for o in mapped_orgs if as_bool(o["any_final_tick"])]
    unticked = [o for o in mapped_orgs if not as_bool(o["any_final_tick"])]
    join_sites = [s for s in l1_sites if yn(s["level1_district_join_eligible"]) and s["district_code"]]
    nonjoin_sites = [s for s in l1_sites if s not in join_sites]
    campus_shared = [s for s in sites if s["geocode_status"] == "campus_shared_with_CM-071"]

    overall = [
        {
            "measure": "level1_organisations",
            "n": len(l1_orgs),
            "definition": "Unique organisations in Chiang Mai family-support universe (mapped child-welfare + public welfare/reception). Excludes Chiang Rai and juvenile justice.",
        },
        {
            "measure": "of_which_mapped_child_welfare",
            "n": len(mapped_orgs),
            "definition": "From the 29 October audit, in Chiang Mai, include-in-map organisations.",
        },
        {
            "measure": "of_which_with_final_stage_tick",
            "n": len(ticked),
            "definition": "Mapped child-welfare organisations with at least one FINAL checkbox tick.",
        },
        {
            "measure": "of_which_no_final_stage_tick",
            "n": len(unticked),
            "definition": "Mapped child-welfare organisations with no FINAL tick. Still in the overall organisation count.",
        },
        {
            "measure": "of_which_public_welfare_or_reception",
            "n": len(public_core),
            "definition": "Added from the 2025 public directory. Not in FINAL checkbox.",
        },
        {
            "measure": "level1_physical_sites",
            "n": len(l1_sites),
            "definition": "Unique eligible physical sites. Service-area markers, out-of-scope, and 'no verified site' records are excluded. Juvenile excluded.",
        },
        {
            "measure": "level1_sites_district_joinable",
            "n": len(join_sites),
            "definition": "Level 1 sites mapped onto a DOPA district 5001–5025.",
        },
        {
            "measure": "level1_sites_district_not_joinable",
            "n": len(nonjoin_sites),
            "definition": "In Chiang Mai but province-wide, undisclosed, or otherwise not a district join.",
        },
        {
            "measure": "level1_nearest_neighbour_points",
            "n": len(l1_points),
            "definition": "Exact public house/building points in Chiang Mai. Don Kaeo campus counted once (CM-071). Juvenile not included. Coarse street/locality geocodes not included.",
        },
        {
            "measure": "don_kaeo_campus_sites_not_extra_points",
            "n": len(campus_shared),
            "definition": "CM-069 and CM-070 share CM-071 coordinates and are not extra nearest-neighbour observations.",
        },
        {
            "measure": "juvenile_justice_labelled_not_in_family_support_counts",
            "n": len(juvenile),
            "definition": "Chiang Mai Juvenile Observation and Protection Centre. Coordinates stored; excluded from organisation, site and point numerators.",
        },
        {
            "measure": "chiang_rai_boundary_note_not_in_counts",
            "n": len(chiang_rai),
            "definition": "Wiang Pa Pao markers CM-060/061/062. Nearby provision note only.",
        },
    ]
    write_csv(OUT / "counts_overall.csv", overall, ["measure", "n", "definition"])

    # Organisations by FINAL stage (mapped child-welfare only).
    org_stage_rows = []
    for stage in STAGE_ORDER:
        members = [o for o in mapped_orgs if stage in stages_of(o)]
        org_stage_rows.append({
            "stage": stage,
            "n_organisations": len(members),
            "share_of_level1_orgs": round(len(members) / len(l1_orgs), 4) if l1_orgs else "",
            "share_of_mapped_child_welfare": round(len(members) / len(mapped_orgs), 4) if mapped_orgs else "",
            "classification_source": "landscape mapping (FINAL) checkbox",
            "note": "Organisation may appear in more than one stage. Shares use unique organisations, not stage-rows.",
        })
    org_stage_rows.append({
        "stage": "(mapped child-welfare; no FINAL tick)",
        "n_organisations": len(unticked),
        "share_of_level1_orgs": round(len(unticked) / len(l1_orgs), 4) if l1_orgs else "",
        "share_of_mapped_child_welfare": round(len(unticked) / len(mapped_orgs), 4) if mapped_orgs else "",
        "classification_source": "landscape mapping (FINAL) checkbox",
        "note": "Present in the mapped universe; not assigned to a value-chain stage.",
    })
    org_stage_rows.append({
        "stage": "(public welfare / reception — directory category, not FINAL)",
        "n_organisations": len(public_core),
        "share_of_level1_orgs": round(len(public_core) / len(l1_orgs), 4) if l1_orgs else "",
        "share_of_mapped_child_welfare": "",
        "classification_source": "2025 public children's-homes directory",
        "note": "Not in FINAL checkbox. Welfare homes treated as residential-care category; reception as short-term category in site_stages only.",
    })
    write_csv(OUT / "orgs_by_stage.csv", org_stage_rows, [
        "stage", "n_organisations", "share_of_level1_orgs", "share_of_mapped_child_welfare",
        "classification_source", "note",
    ])

    overlap_rows = []
    for n_st in range(0, 8):
        members = [o for o in mapped_orgs if len(stages_of(o)) == n_st]
        overlap_rows.append({
            "n_final_stages": n_st,
            "n_organisations": len(members),
            "note": "Counts unique organisations. Multi-stage overlap is not extra organisations.",
        })
    write_csv(OUT / "org_stage_overlap.csv", overlap_rows, [
        "n_final_stages", "n_organisations", "note",
    ])

    # Sites by stage: FINAL ticks of the owning organisation, plus public-directory category.
    # Audit Applicable_Stages can disagree with FINAL (e.g. kinship at Kid's Ark); FINAL wins.
    org_by_id = {o["org_id"]: o for o in orgs}
    site_ids_by_stage = defaultdict(set)
    for s in l1_sites:
        if s["record_source"] == "public_directory_2025":
            if s["core_universe_role"] == "public_welfare":
                site_ids_by_stage["Residential and Institutional Care"].add(s["marker_id"])
            elif s["core_universe_role"] == "public_reception":
                site_ids_by_stage["Short-term Intervention"].add(s["marker_id"])
            continue
        for st in stages_of(org_by_id.get(s["org_id"], {})):
            if st in STAGE_ORDER:
                site_ids_by_stage[st].add(s["marker_id"])
    site_stage_rows = []
    for stage in STAGE_ORDER:
        n = len(site_ids_by_stage[stage])
        site_stage_rows.append({
            "stage": stage,
            "n_sites": n,
            "share_of_level1_sites": round(n / len(l1_sites), 4) if l1_sites else "",
            "stage_evidence": "FINAL checkbox of the owning organisation, except public welfare/reception (directory category). Not independently verified at each site.",
            "note": "Do not sum across stages. Stage-sheet repeats are not extra sites.",
        })
    write_csv(OUT / "sites_by_stage.csv", site_stage_rows, [
        "stage", "n_sites", "share_of_level1_sites", "stage_evidence", "note",
    ])

    disagreement = []
    seen_dis = set()
    for row in stages:
        if not yn(row["level1_site_eligible"]):
            continue
        if row["stage_source"] != "organisation_from_audit":
            continue
        st = row["stage"]
        if st not in STAGE_ORDER:
            continue
        final = set(stages_of(org_by_id.get(row["org_id"], {})))
        if st in final:
            continue
        key = (row["marker_id"], st)
        if key in seen_dis:
            continue
        seen_dis.add(key)
        disagreement.append({
            "marker_id": row["marker_id"],
            "organisation": row["organisation"],
            "audit_site_stage": st,
            "final_org_stages": org_by_id.get(row["org_id"], {}).get("stages_from_final", ""),
            "used_in_level1_site_stage_count": "no",
            "note": "FINAL checkbox is the classification source. Audit Applicable_Stages listed this stage; it is not counted.",
        })
    write_csv(OUT / "stage_source_disagreement.csv", disagreement, [
        "marker_id", "organisation", "audit_site_stage", "final_org_stages",
        "used_in_level1_site_stage_count", "note",
    ])

    # District tables: all 25 DOPA districts, including zeros.
    sites_by_dist = defaultdict(list)
    for s in join_sites:
        sites_by_dist[s["district_code"]].append(s)
    orgs_by_dist = defaultdict(set)
    for s in join_sites:
        orgs_by_dist[s["district_code"]].add(s["org_id"])
    points_by_dist = defaultdict(list)
    for s in l1_points:
        if s["district_code"]:
            points_by_dist[s["district_code"]].append(s)

    district_rows = []
    for d in dopa:
        code = d["district_code"]
        n_sites = len(sites_by_dist.get(code, []))
        n_orgs = len(orgs_by_dist.get(code, []))
        n_pts = len(points_by_dist.get(code, []))
        district_rows.append({
            "district_code": code,
            "district_th": d["district_th"],
            "district_en": d["district_en"],
            "n_level1_organisations": n_orgs,
            "n_level1_sites": n_sites,
            "share_of_level1_sites": round(n_sites / len(l1_sites), 4) if l1_sites else "",
            "share_of_joinable_sites": round(n_sites / len(join_sites), 4) if join_sites else "",
            "n_level1_points": n_pts,
            "thai_reg_age_0_17": d["thai_reg_age_0_17"],
            "population_note": "Child count is registered Thai 0–17 (DOPA Dec 2025), not a need rate. Rates belong in Level 2A.",
            "zero_is_not_absent": "yes" if n_sites == 0 else "no",
        })
    district_rows.append({
        "district_code": "",
        "district_th": "",
        "district_en": NON_JOIN,
        "n_level1_organisations": len({s["org_id"] for s in nonjoin_sites}),
        "n_level1_sites": len(nonjoin_sites),
        "share_of_level1_sites": round(len(nonjoin_sites) / len(l1_sites), 4) if l1_sites else "",
        "share_of_joinable_sites": "",
        "n_level1_points": sum(1 for s in l1_points if not s["district_code"]),
        "thai_reg_age_0_17": "",
        "population_note": "Do not allocate these sites to a district denominator.",
        "zero_is_not_absent": "no",
    })
    write_csv(OUT / "sites_by_district.csv", district_rows, [
        "district_code", "district_th", "district_en",
        "n_level1_organisations", "n_level1_sites", "share_of_level1_sites",
        "share_of_joinable_sites", "n_level1_points", "thai_reg_age_0_17",
        "population_note", "zero_is_not_absent",
    ])

    point_rows = []
    coords = {}
    for s in l1_points:
        lat = float(s["latitude"])
        lon = float(s["longitude"])
        coords[s["marker_id"]] = (lat, lon)
        point_rows.append({
            "marker_id": s["marker_id"],
            "org_id": s["org_id"],
            "organisation": s["organisation"],
            "district_code": s["district_code"],
            "district_en": s["district_en"],
            "latitude": s["latitude"],
            "longitude": s["longitude"],
            "geocode_status": s["geocode_status"],
            "geocode_point_kind": s["geocode_point_kind"],
            "core_universe_role": s["core_universe_role"],
            "in_nearest_neighbour": "yes",
        })
    for s in juvenile:
        if s.get("latitude") and s.get("longitude"):
            point_rows.append({
                "marker_id": s["marker_id"],
                "org_id": s["org_id"],
                "organisation": s["organisation"],
                "district_code": s["district_code"],
                "district_en": s["district_en"],
                "latitude": s["latitude"],
                "longitude": s["longitude"],
                "geocode_status": s["geocode_status"],
                "geocode_point_kind": s["geocode_point_kind"],
                "core_universe_role": s["core_universe_role"],
                "in_nearest_neighbour": "no",
            })
    write_csv(OUT / "level1_points.csv", point_rows, [
        "marker_id", "org_id", "organisation", "district_code", "district_en",
        "latitude", "longitude", "geocode_status", "geocode_point_kind",
        "core_universe_role", "in_nearest_neighbour",
    ])

    nn_rows = []
    nn_distances = []
    for s in l1_points:
        a = coords[s["marker_id"]]
        best = None
        for other in l1_points:
            if other["marker_id"] == s["marker_id"]:
                continue
            d = haversine_km(a, coords[other["marker_id"]])
            if best is None or d < best[0]:
                best = (d, other)
        if best is None:
            continue
        nn_distances.append(best[0])
        nn_rows.append({
            "marker_id": s["marker_id"],
            "organisation": s["organisation"],
            "nearest_marker_id": best[1]["marker_id"],
            "nearest_organisation": best[1]["organisation"],
            "distance_km": round(best[0], 3),
        })
    nn_rows.sort(key=lambda r: r["distance_km"])
    write_csv(OUT / "nearest_neighbour.csv", nn_rows, [
        "marker_id", "organisation", "nearest_marker_id", "nearest_organisation", "distance_km",
    ])

    geojson = {
        "type": "FeatureCollection",
        "name": "Chiang Mai Level 1 points",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(r["longitude"]), float(r["latitude"])],
                },
                "properties": {k: r[k] for k in r if k not in {"latitude", "longitude"}},
            }
            for r in point_rows
            if r["latitude"] and r["longitude"]
        ],
    }
    (OUT / "level1_points.geojson").write_text(
        json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Offline SVG scatter (linear lon/lat; not a cartographic projection).
    svg_pts = [
        {
            "id": r["marker_id"],
            "lon": float(r["longitude"]),
            "lat": float(r["latitude"]),
            "nn": r["in_nearest_neighbour"] == "yes",
            "label": r["marker_id"],
        }
        for r in point_rows
        if r["latitude"] and r["longitude"]
    ]
    if svg_pts:
        lons = [p["lon"] for p in svg_pts]
        lats = [p["lat"] for p in svg_pts]
        pad = 0.02
        minx, maxx = min(lons) - pad, max(lons) + pad
        miny, maxy = min(lats) - pad, max(lats) + pad
        w, h, m = 720, 640, 48

        def xy(lon, lat):
            x = m + (lon - minx) / (maxx - minx) * (w - 2 * m)
            y = m + (maxy - lat) / (maxy - miny) * (h - 2 * m)
            return x, y

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
            '<rect width="100%" height="100%" fill="#fafafa"/>',
            '<text x="24" y="28" font-family="sans-serif" font-size="14">'
            "Level 1 public points (blue) and juvenile centre (orange, not in NN)</text>",
        ]
        for p in svg_pts:
            x, y = xy(p["lon"], p["lat"])
            fill = "#1d4ed8" if p["nn"] else "#c2410c"
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{fill}"/>')
            parts.append(
                f'<text x="{x + 8:.1f}" y="{y + 4:.1f}" font-family="sans-serif" font-size="11" fill="#111">'
                f'{p["label"]}</text>'
            )
        parts.append("</svg>")
        (OUT / "level1_points.svg").write_text("\n".join(parts), encoding="utf-8")

    n_zero = sum(1 for r in district_rows if r["district_code"] and int(r["n_level1_sites"]) == 0)
    top_sites = sorted(
        [r for r in district_rows if r["district_code"]],
        key=lambda r: int(r["n_level1_sites"]),
        reverse=True,
    )[:3]
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_level1_orgs": len(l1_orgs),
        "n_level1_sites": len(l1_sites),
        "n_level1_points": len(l1_points),
        "n_joinable_sites": len(join_sites),
        "n_nonjoin_sites": len(nonjoin_sites),
        "n_mapped_with_final_tick": len(ticked),
        "n_mapped_without_final_tick": len(unticked),
        "n_public_welfare_reception_orgs": len(public_core),
        "n_audit_vs_final_stage_disagreements": len(disagreement),
        "n_districts_with_zero_mapped_sites": n_zero,
        "top_districts_by_sites": [
            {
                "district_code": r["district_code"],
                "district_en": r["district_en"],
                "n_sites": int(r["n_level1_sites"]),
                "share_of_level1_sites": r["share_of_level1_sites"],
            }
            for r in top_sites
        ],
        "nearest_neighbour": {
            "n": len(nn_distances),
            "min_km": round(min(nn_distances), 3) if nn_distances else None,
            "median_km": round(median(nn_distances), 3) if nn_distances else None,
            "mean_km": round(sum(nn_distances) / len(nn_distances), 3) if nn_distances else None,
            "max_km": round(max(nn_distances), 3) if nn_distances else None,
            "method": "great-circle kilometres, WGS84, Earth radius 6371.0088 km",
            "not_a_clustering_test": True,
        },
        "limitations": [
            "This is the mapped sample, not a census of all child-welfare provision in Chiang Mai.",
            "Unique organisations, unique physical sites and nearest-neighbour points are different numerators.",
            "Only 12 sites have an exact public house/building point. District counts use 57 sites, of which some have no point.",
            "Shared district or tambon centroids were not used as points, so they cannot manufacture clusters.",
            "Don Kaeo 63/1 and 63/3 share the reception-shelter coordinate and are not extra NN observations.",
            "Juvenile justice is stored and labelled, not pooled into family-support counts.",
            "Stage assignment is the FINAL checkbox. Audit Applicable_Stages that disagree with FINAL (kinship at Kid's Ark; foster at Connie's Home) are logged and not counted.",
            "Public welfare/reception are directory categories, not FINAL ticks.",
            "Zero mapped sites in a district is not evidence of no provision.",
            "Nearest-neighbour distances are descriptive. No Clark-Evans or other clustering test is reported; study-area choice would dominate any such index.",
            "Chiang Rai Wiang Pa Pao sites are a boundary note only.",
        ],
        "rule": (
            "Do not read few mapped providers as unmet need, or proximity as access. "
            "No causal claims. Population denominators are shown for later Level 2A rates, not used as need ranks here."
        ),
    }
    (OUT / "level1_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
