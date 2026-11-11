"""Build preview/data/catalog.json from a Google My Maps viewer pageData dump.

The public KML/KMZ for this map has addresses but no Point coordinates.
Google geocodes them in the viewer. Capture that payload once:

  1. Open https://www.google.com/maps/d/viewer?mid=10TLIIZr41YJMf0jhPuwt3kz8mQqbcVo
  2. In the browser console: copy(JSON.parse(_pageData))
  3. Save as preview/data/mymap_pagedata.json

Or keep the existing dump and run:

  python3 scripts/import_mymap_catalog.py

Each stage folder becomes a layer. The same place is repeated once per stage,
matching the My Map. Coordinates are the ones the My Map already publishes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGEDATA = ROOT / "preview" / "data" / "mymap_pagedata.json"
OUT = ROOT / "preview" / "data" / "catalog.json"
SOURCE_MID = "10TLIIZr41YJMf0jhPuwt3kz8mQqbcVo"
SOURCE_TITLE = "Chiang Mai Child Welfare Ecosystem"


def slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def collect_fields(node, out: dict | None = None) -> dict:
    if out is None:
        out = {}
    if not isinstance(node, list):
        return out
    if node and isinstance(node[0], str) and len(node) >= 2:
        key = node[0]
        val = node[1]
        if isinstance(val, list):
            if val and all(v is None or isinstance(v, (int, float)) for v in val):
                val = next((v for v in val if v is not None), None)
            else:
                val = val[0] if val else None
        if val is not None and key not in out:
            out[key] = str(val)
        return out
    for child in node:
        collect_fields(child, out)
    return out


def coords_of(feat) -> tuple[float, float] | None:
    try:
        c = feat[1][0][0]
        return float(c[0]), float(c[1])
    except (TypeError, IndexError, ValueError):
        return None


def build_catalog(pagedata: list) -> dict:
    folders = pagedata[1][6]
    layers = []
    for folder in folders:
        stage = folder[2]
        features = folder[12][0][13][0]
        places = []
        for feat in features:
            fields = collect_fields(feat[5])
            xy = coords_of(feat)
            name = fields.get("Name") or ""
            if not xy or not name:
                continue
            lat, lon = xy
            places.append(
                {
                    "name": name,
                    "organisation": fields.get("Organisation") or "",
                    "site": fields.get("Site") or "",
                    "address": fields.get("Address") or "",
                    "stage": fields.get("Stage") or stage,
                    "subcategories": fields.get("Subcategories") or "",
                    "location_precision": fields.get("Location precision") or "",
                    "approximation_method": fields.get("Approximation method") or "",
                    "safeguarding_reason": fields.get("Safeguarding reason") or "",
                    "lat": lat,
                    "lon": lon,
                }
            )
        layers.append({"id": slug(stage), "name": stage, "places": places})
    return {
        "source_mid": SOURCE_MID,
        "source_title": SOURCE_TITLE,
        "layers": layers,
    }


def main() -> None:
    if not PAGEDATA.exists():
        raise SystemExit(
            f"Missing {PAGEDATA}. Export window._pageData from the My Maps viewer first."
        )
    pagedata = json.loads(PAGEDATA.read_text(encoding="utf-8"))
    catalog = build_catalog(pagedata)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = ", ".join(f"{layer['name']}={len(layer['places'])}" for layer in catalog["layers"])
    total = sum(len(layer["places"]) for layer in catalog["layers"])
    print(f"Wrote {OUT} — {total} placemarks ({counts})")


if __name__ == "__main__":
    main()
