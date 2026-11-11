"""Step 5 — Level 2B accessibility.

Origins are district centroids (administrative proxies). Destinations are the
eight exact public current delivery or mixed sites agreed on 10 November 2026.
Private-vehicle road time is the primary estimate. Walking is the sensitivity
check. 30 and 60 minutes are descriptive bins, not a definition of access.

Does not estimate a share of children within a time threshold.
Does not route to protected or approximated residences.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADM1 = ROOT / "raw" / "boundaries" / "geoBoundaries-THA-ADM1_simplified.geojson"
ADM2 = ROOT / "raw" / "boundaries" / "geoBoundaries-THA-ADM2_simplified.geojson"
DOPA = ROOT / "outputs" / "step1" / "dopa_district_totals.csv"
SITES = ROOT / "outputs" / "step2" / "sites.csv"
ROLES = ROOT / "outputs" / "step4" / "site_presence_role.csv"
OUT = ROOT / "outputs" / "step5"
CACHE = OUT / "routing_cache.json"

CAR_TABLE = "https://routing.openstreetmap.de/routed-car/table/v1/driving/"
FOOT_TABLE = "https://routing.openstreetmap.de/routed-foot/table/v1/foot/"
VALHALLA = "https://valhalla1.openstreetmap.de/sources_to_targets"
USER_AGENT = "ChiangMaiMapping/2.0 (Thrive TSA geographical analysis)"
AGREED_DESTINATIONS = {
    "CM-004", "CM-010", "CM-022", "CM-026", "CM-029", "CM-030", "CM-032", "CM-071",
}
EARTH_KM = 6371.0088

DECISIONS = [
    {
        "decision_id": "L2B-1",
        "topic": "Origin",
        "choice": "Geometric centroid of each Chiang Mai district polygon, flagged when the centroid falls outside the polygon and an interior point is used instead.",
        "rationale": (
            "No settlement or child-location layer is on disk. The optional health-office population Excel was IP-blocked, and DOPA December 2025 gives registration counts without coordinates. "
            "District is already the join geography for DOPA, DOLE and TPMAP. "
            "A centroid is an administrative proxy, not a child's home. "
            "Travel times describe that proxy. They are not a percentage of children within 30 or 60 minutes."
        ),
    },
    {
        "decision_id": "L2B-2",
        "topic": "Destinations",
        "choice": "Eight exact public sites that are current delivery or mixed office-and-delivery: CM-004 Thai Freedom House, CM-010 IMEMF, CM-022 Salvation Army, CM-026 Projects for Asia, CM-029 Wat Don Chan, CM-030 Dulabhatorn, CM-032 Radion, CM-071 Mae Rim children's and family shelter.",
        "rationale": (
            "Road routing is applied only where a public house or building geocode exists. "
            "Protected homes, undisclosed sites and district-level approximations have no defensible door, so they are not routed to. "
            "Pure offices and the two former Mueang offices are organisation addresses, not the delivery destinations for this estimate. "
            "The juvenile centre is stored and labelled, and it stays outside the family-support destination set. "
            "All eight included sites are family-support relevant under the Level 2A rule."
        ),
    },
    {
        "decision_id": "L2B-3",
        "topic": "Travel mode",
        "choice": "Primary: private-vehicle road distance and time from the FOSSGIS OSM car profile. Sensitivity: walking time on the FOSSGIS OSM foot profile, for the same origin-destination pairs and for the nearest walk destination when it differs. Validation: Valhalla auto time for the car pair. No paid routing service.",
        "rationale": (
            "The project default is no paid routing. "
            "A private vehicle is a common way to move between Chiang Mai districts, and motorbikes share the road network, but the speed model is a car profile, not observed traffic and not a motorbike profile. "
            "Walking tests the assumption that a vehicle is available. "
            "Songthaew and bus timetables are not in the source set, so shared transport is not modelled. "
            "A second independent engine checks whether the car times are an artefact of one router."
        ),
    },
    {
        "decision_id": "L2B-4",
        "topic": "Threshold",
        "choice": "Report the minimum, median, mean and maximum private-vehicle times, and count district centroids at or under 30 minutes and at or under 60 minutes.",
        "rationale": (
            "No partner has defined a single cutoff that means accessible. "
            "The spread keeps that choice visible. "
            "Thirty and sixty minutes are descriptive bins for reading the distribution. "
            "They are not a finding that a family can reach a service, and they are not weighted by the child population."
        ),
    },
]


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def norm_name(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_KM * math.asin(min(1.0, math.sqrt(h)))


def signed_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    if ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    a = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        cross = x1 * y2 - x2 * y1
        a += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    a *= 0.5
    if abs(a) < 1e-14:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return 0.0, sum(xs) / len(xs), sum(ys) / len(ys)
    return a, cx / (6 * a), cy / (6 * a)


def iter_polygons(geom: dict):
    if geom["type"] == "Polygon":
        yield geom["coordinates"]
    elif geom["type"] == "MultiPolygon":
        yield from geom["coordinates"]
    else:
        raise ValueError(geom["type"])


def geometry_centroid(geom: dict) -> tuple[float, float]:
    total_a = sx = sy = 0.0
    for poly in iter_polygons(geom):
        for ring in poly:
            a, cx, cy = signed_area_centroid(ring)
            total_a += a
            sx += cx * a
            sy += cy * a
    if abs(total_a) < 1e-14:
        raise ValueError("empty geometry")
    return sx / total_a, sy / total_a


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, rings: list) -> bool:
    if not point_in_ring(lon, lat, rings[0]):
        return False
    return all(not point_in_ring(lon, lat, hole) for hole in rings[1:])


def point_in_geom(lon: float, lat: float, geom: dict) -> bool:
    return any(point_in_polygon(lon, lat, poly) for poly in iter_polygons(geom))


def interior_point(geom: dict, lon: float, lat: float) -> tuple[float, float, str]:
    if point_in_geom(lon, lat, geom):
        return lon, lat, "area_centroid_inside"
    lons, lats = [], []
    for poly in iter_polygons(geom):
        for x, y in poly[0]:
            lons.append(x)
            lats.append(y)
    best = None
    for i in range(1, 40):
        x = min(lons) + (max(lons) - min(lons)) * i / 40
        for j in range(1, 40):
            y = min(lats) + (max(lats) - min(lats)) * j / 40
            if not point_in_geom(x, y, geom):
                continue
            d = (x - lon) ** 2 + (y - lat) ** 2
            if best is None or d < best[0]:
                best = (d, x, y)
    if best is None:
        raise ValueError("no interior point")
    return best[1], best[2], "interior_point_centroid_was_outside"


def fetch_json(url: str, data: bytes | None = None, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_cache() -> dict:
    if CACHE.is_file():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def osrm_table(base: str, origins: list[tuple[float, float]], dests: list[tuple[float, float]], cache: dict) -> dict:
    """origins and dests are (lat, lon). Returns durations_s and distances_m as [n_origin][n_dest]."""
    coords = origins + dests
    key = base + "|" + ";".join(f"{lat:.5f},{lon:.5f}" for lat, lon in coords)
    if key in cache:
        return cache[key]
    path = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    sources = ";".join(str(i) for i in range(len(origins)))
    destinations = ";".join(str(len(origins) + i) for i in range(len(dests)))
    url = f"{base}{path}?sources={sources}&destinations={destinations}&annotations=duration,distance"
    payload = fetch_json(url)
    if payload.get("code") != "Ok":
        raise RuntimeError(payload)
    parsed = {
        "durations_s": payload["durations"],
        "distances_m": payload["distances"],
    }
    cache[key] = parsed
    save_cache(cache)
    return parsed


def valhalla_pair(origin: tuple[float, float], dest: tuple[float, float], cache: dict) -> dict:
    """One car pair. The public server returns HTTP 400 when a path exceeds 150 km."""
    key = f"valhalla|auto|{origin[0]:.5f},{origin[1]:.5f}|{dest[0]:.5f},{dest[1]:.5f}"
    if key in cache:
        return cache[key]
    body = {
        "sources": [{"lat": origin[0], "lon": origin[1]}],
        "targets": [{"lat": dest[0], "lon": dest[1]}],
        "costing": "auto",
        "units": "kilometers",
    }
    result = {"time_s": None, "distance_km": None, "status": "no_route"}
    try:
        payload = fetch_json(VALHALLA, data=json.dumps(body).encode("utf-8"))
        cell = payload["sources_to_targets"][0][0]
        if cell.get("time") is not None:
            result = {"time_s": cell["time"], "distance_km": cell["distance"], "status": "ok"}
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        if "max distance" in message:
            result["status"] = "exceeds_150km_limit"
        else:
            result["status"] = f"http_{exc.code}"
    cache[key] = result
    save_cache(cache)
    time.sleep(0.6)
    return result


def median(values: list[float]) -> float:
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not ADM1.is_file() or not ADM2.is_file():
        raise SystemExit("District and province boundary files are missing from raw/boundaries.")

    adm1 = json.loads(ADM1.read_text(encoding="utf-8"))
    province = next(
        f for f in adm1["features"] if f["properties"].get("shapeName") == "Chiang Mai Province"
    )
    adm2 = json.loads(ADM2.read_text(encoding="utf-8"))
    dopa = load_csv(DOPA)
    by_norm = {norm_name(r["district_en"]): r for r in dopa}

    centroids = []
    excluded_neighbours = []
    for feat in adm2["features"]:
        lon, lat = geometry_centroid(feat["geometry"])
        if not point_in_geom(lon, lat, province["geometry"]):
            continue
        name = feat["properties"]["shapeName"]
        row = by_norm.get(norm_name(name))
        if row is None:
            excluded_neighbours.append(name)
            continue
        use_lon, use_lat, how = interior_point(feat["geometry"], lon, lat)
        centroids.append({
            "shape_name": name,
            "shape_id": feat["properties"].get("shapeID", ""),
            "district_code": row["district_code"] if row else "",
            "district_en": row["district_en"] if row else "",
            "district_th": row["district_th"] if row else "",
            "latitude": f"{use_lat:.6f}",
            "longitude": f"{use_lon:.6f}",
            "centroid_method": how,
            "thai_reg_age_0_17": row["thai_reg_age_0_17"] if row else "",
            "boundary_source": "geoBoundaries gbOpen THA ADM2 simplified; Royal Thai Survey Department, OCHA ROAP; year represented 2019; build Dec 2023",
            "boundary_note": "Simplified polygon. Centroid is an administrative proxy, not a child's home. Child count is context only and does not weight the travel time.",
        })
    codes = {c["district_code"] for c in centroids}
    if codes != {r["district_code"] for r in dopa} or len(centroids) != 25:
        raise SystemExit(
            "District match failed. "
            f"Kept: {[c['shape_name'] for c in centroids]}. "
            f"Excluded neighbours whose centroid fell inside the simplified province polygon: {excluded_neighbours}."
        )
    centroids.sort(key=lambda r: r["district_code"])

    roles = {r["marker_id"]: r for r in load_csv(ROLES)}
    sites = {s["marker_id"]: s for s in load_csv(SITES)}
    dest_rows = []
    for mid in sorted(AGREED_DESTINATIONS):
        site = sites[mid]
        role = roles[mid]
        if role["counts_as_current_delivery_or_mixed"] != "yes":
            raise SystemExit(f"{mid} is no longer a current delivery or mixed site.")
        if site["geocode_point_kind"] != "building_or_house" or site["geocode_status"] not in {"ok", "audit_supplied"}:
            raise SystemExit(f"{mid} no longer has an exact public house/building point.")
        dest_rows.append({
            "marker_id": mid,
            "organisation": site["organisation"],
            "district_code": site["district_code"],
            "district_en": site["district_en"],
            "latitude": site["latitude"],
            "longitude": site["longitude"],
            "presence_role": role["presence_role"],
            "geocode_status": site["geocode_status"],
            "included_because": "Agreed Level 2B destination: exact public current delivery or mixed site.",
        })
    if {r["marker_id"] for r in dest_rows} != AGREED_DESTINATIONS:
        raise SystemExit("Destination set drifted from the agreed eight.")

    cache = load_cache()
    origins = [(float(c["latitude"]), float(c["longitude"])) for c in centroids]
    dests = [(float(d["latitude"]), float(d["longitude"])) for d in dest_rows]
    car = osrm_table(CAR_TABLE, origins, dests, cache)
    foot = osrm_table(FOOT_TABLE, origins, dests, cache)

    access = []
    for i, origin in enumerate(centroids):
        car_times = car["durations_s"][i]
        car_dists = car["distances_m"][i]
        foot_times = foot["durations_s"][i]
        foot_dists = foot["distances_m"][i]
        best_car = None
        best_foot = None
        for j, dest in enumerate(dest_rows):
            if car_times[j] is not None and (best_car is None or car_times[j] < best_car[0]):
                best_car = (car_times[j], car_dists[j], j)
            if foot_times[j] is not None and (best_foot is None or foot_times[j] < best_foot[0]):
                best_foot = (foot_times[j], foot_dists[j], j)
        if best_car is None:
            access.append({
                "district_code": origin["district_code"],
                "district_en": origin["district_en"],
                "origin_latitude": origin["latitude"],
                "origin_longitude": origin["longitude"],
                "centroid_method": origin["centroid_method"],
                "route_status": "no_private_vehicle_route",
                "thai_reg_age_0_17_context_only": origin["thai_reg_age_0_17"],
            })
            continue
        j = best_car[2]
        dest = dest_rows[j]
        minutes = best_car[0] / 60
        km = best_car[1] / 1000
        straight = haversine_km(
            float(origin["latitude"]), float(origin["longitude"]),
            float(dest["latitude"]), float(dest["longitude"]),
        )
        val = valhalla_pair(
            (float(origin["latitude"]), float(origin["longitude"])),
            (float(dest["latitude"]), float(dest["longitude"])),
            cache,
        )
        val_min = None if val["time_s"] is None else val["time_s"] / 60
        foot_same_min = None if foot_times[j] is None else foot_times[j] / 60
        foot_same_km = None if foot_dists[j] is None else foot_dists[j] / 1000
        foot_nearest_id = ""
        foot_nearest_min = ""
        foot_nearest_same = ""
        if best_foot is not None:
            fj = best_foot[2]
            foot_nearest_id = dest_rows[fj]["marker_id"]
            foot_nearest_min = f"{best_foot[0] / 60:.1f}"
            foot_nearest_same = "yes" if fj == j else "no"
        access.append({
            "district_code": origin["district_code"],
            "district_en": origin["district_en"],
            "district_th": origin["district_th"],
            "origin_latitude": origin["latitude"],
            "origin_longitude": origin["longitude"],
            "centroid_method": origin["centroid_method"],
            "route_status": "ok",
            "nearest_marker_id": dest["marker_id"],
            "nearest_organisation": dest["organisation"],
            "nearest_district_en": dest["district_en"],
            "private_vehicle_minutes": f"{minutes:.1f}",
            "private_vehicle_km": f"{km:.2f}",
            "straight_line_km": f"{straight:.2f}",
            "road_to_straight_ratio": f"{(km / straight):.2f}" if straight else "",
            "bin_30_min_descriptive": "yes" if minutes <= 30 else "no",
            "bin_60_min_descriptive": "yes" if minutes <= 60 else "no",
            "under_30_on_both_engines": "yes" if (
                minutes <= 30 and val_min is not None and val_min <= 30
            ) else "no",
            "walk_minutes_same_destination": "" if foot_same_min is None else f"{foot_same_min:.1f}",
            "walk_km_same_destination": "" if foot_same_km is None else f"{foot_same_km:.2f}",
            "walk_nearest_marker_id": foot_nearest_id,
            "walk_nearest_minutes": foot_nearest_min,
            "walk_nearest_is_same_site": foot_nearest_same,
            "valhalla_auto_minutes_same_pair": "" if val_min is None else f"{val_min:.1f}",
            "valhalla_status": val["status"],
            "validation_minute_difference_valhalla_minus_fossgis": (
                "" if val_min is None else f"{(val_min - minutes):.1f}"
            ),
            "thai_reg_age_0_17_context_only": origin["thai_reg_age_0_17"],
            "engines": "Primary car and foot: routing.openstreetmap.de FOSSGIS OSRM. Validation car: valhalla1.openstreetmap.de costing auto.",
            "reading_note": "Time is from the district centroid, not from homes. 30 and 60 minutes are descriptive bins. Child count is not a weight.",
        })

    write_csv(OUT / "design_decisions.csv", DECISIONS, ["decision_id", "topic", "choice", "rationale"])
    write_csv(OUT / "district_centroids.csv", centroids, list(centroids[0].keys()))
    write_csv(OUT / "destinations.csv", dest_rows, list(dest_rows[0].keys()))
    write_csv(OUT / "district_access.csv", access, list(access[0].keys()) if access else ["district_code"])

    gaps = [
        {
            "gap": "affordability",
            "status": "not_modelled",
            "why": "Travel time does not include fares, fuel, or whether a household can pay. No fare table is in the source set.",
        },
        {
            "gap": "eligibility",
            "status": "not_modelled",
            "why": "A reachable site may not accept a referral, serve the child's age, or have a place. Reach is not eligibility.",
        },
        {
            "gap": "shared_transport",
            "status": "not_modelled",
            "why": "Songthaew and bus timetables are not in the source set. Walking is the only no-vehicle sensitivity. It is not a transit model.",
        },
    ]
    write_csv(OUT / "gaps_not_modelled.csv", gaps, ["gap", "status", "why"])

    ok = [r for r in access if r["route_status"] == "ok"]
    minutes = [float(r["private_vehicle_minutes"]) for r in ok]
    diffs = [
        float(r["validation_minute_difference_valhalla_minus_fossgis"])
        for r in ok
        if r["validation_minute_difference_valhalla_minus_fossgis"] != ""
    ]
    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "n_origins": len(centroids),
        "n_destinations": len(dest_rows),
        "n_routed": len(ok),
        "n_failed": len(access) - len(ok),
        "n_centroids_outside_polygon": sum(1 for c in centroids if c["centroid_method"] != "area_centroid_inside"),
        "excluded_neighbour_centroids_inside_simplified_province": excluded_neighbours,
        "private_vehicle_minutes": {
            "min": round(min(minutes), 1) if minutes else None,
            "median": round(median(minutes), 1) if minutes else None,
            "mean": round(sum(minutes) / len(minutes), 1) if minutes else None,
            "max": round(max(minutes), 1) if minutes else None,
            "n_centroids_at_or_under_30": sum(1 for m in minutes if m <= 30),
            "n_centroids_at_or_under_60": sum(1 for m in minutes if m <= 60),
            "n_centroids_over_60": sum(1 for m in minutes if m > 60),
            "n_under_30_on_both_engines": sum(1 for r in ok if r["under_30_on_both_engines"] == "yes"),
            "unit": "district centroids, not children",
        },
        "validation": {
            "n_pairs_compared": len(diffs),
            "n_valhalla_no_route": sum(1 for r in ok if r.get("valhalla_status") == "no_route"),
            "n_valhalla_exceeds_150km_limit": sum(1 for r in ok if r.get("valhalla_status") == "exceeds_150km_limit"),
            "median_valhalla_minus_fossgis_minutes": round(median(diffs), 1) if diffs else None,
            "max_abs_difference_minutes": round(max(abs(d) for d in diffs), 1) if diffs else None,
            "note": "Where both engines return a time, Valhalla auto is slower. A no_route from Valhalla means that centroid did not snap to Valhalla's road graph. The FOSSGIS time remains the primary estimate.",
        },
        "boundary_sha256": {
            "adm1_simplified": sha256(ADM1),
            "adm2_simplified": sha256(ADM2),
        },
        "bins_are_descriptive": True,
        "not_a_share_of_children": True,
    }
    (OUT / "level2b_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
