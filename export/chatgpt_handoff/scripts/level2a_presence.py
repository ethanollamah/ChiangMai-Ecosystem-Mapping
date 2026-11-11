"""Step 4 — Level 2A: population and need indicators versus mapped presence.

Joins district-eligible Level 1 sites to DOPA (Dec 2025), DOLE Zero Dropout
(retrieved 10 Nov 2026) and TPMAP 2569. Rates are presence per 10,000 registered
Thai children aged 0–17. They are not coverage, capacity or quality.

DOLE screening categories, DOLE age bands, TPMAP dimensions and DOPA age bands
are kept side by side. They are not added into a unique vulnerable-child total.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEP2 = ROOT / "outputs" / "step2"
DOPA = ROOT / "outputs" / "step1" / "dopa_district_totals.csv"
DOLE = ROOT / "outputs" / "step1" / "dole_zero_dropout_by_district.csv"
TPMAP = ROOT / "outputs" / "step1" / "tpmap_district_evidence.csv"
OUT = ROOT / "outputs" / "step4"

OFFICE_TYPES = {
    "Administrative / service office",
    "Administrative office",
    "Parent foundation administrative address",
    "Headquarters / programme office",
    "Coordination office",
    "National / programme office",
    "Foundation office",
    "Regional headquarters / programme office",
    "Former country office",
    "Former regional office",
    "Programme office",
    "Thailand country office",
}
DELIVERY_TYPES = {
    "Family-style residential home",
    "Protected child-protection facility",
    "After-school programme site",
    "Public children's welfare home",
    "Residential / care campus",
    "School / programme site",
    "Public social-enterprise and programme site",
    "Protected residential home network",
    "Residential and programme campus",
    "Protected foster-care and family programme marker",
    "Protected survivor-care campus",
    "Protected residential centre",
    "Corps / community programme site",
    "Residential care campus",
    "Protected residential / respite home",
    "Protected youth residential / leadership home",
    "Protected hostel network",
    "Temple-based residential / programme site",
    "Foundation / residential programme site",
    "Programme / social-enterprise site",
    "Protected group foster home",
    "Residential care site",
    "School-based after-school programme",
    "Public children's reception / family shelter",
}
MIXED_TYPES = {
    "Headquarters / programme campus",
    "Headquarters / residential and learning campus",
    "Office / programme site",
    "Office / child and family service centre",
    "Head office / programme site",
    "Youth centre / office",
}
FAMILY_STAGES = {
    "Identification & Routing",
    "Parent Capability Building",
    "Short-term Intervention",
    "Foster Care / Adoption",
    "Kinship Care",
    "Reintegration, Reunification and Adoption",
}
DOPA_NOTE = (
    "thai_reg_age_* are Thai nationals on ordinary house registration only. "
    "Non-Thai, central-register, lunar-birth-year and in-migration persons have no age split. "
    "Registered is not resident."
)
RATE_NOTE = (
    "Numerator is mapped presence in this district, not capacity and not children served. "
    "Denominator is DOPA Dec 2025 Thai nationals aged 0–17 on ordinary house registration. "
    "Unknown catchments: a site in one district may serve another. This is not a coverage rate."
)
TIMEFRAME = (
    "Sites: audit 29 Oct 2026 plus 2025 public directory. "
    "DOPA: December 2025 registration. "
    "DOLE: dashboard © 2026.04.28, records described as 2025 child/youth for survey in 2026, retrieved 10 Nov 2026. "
    "TPMAP: year 2569 page, update 3 Apr 2569, sources JPT 2568 and welfare card 2565."
)


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


def stages_of(org: dict) -> list[str]:
    return [p.strip() for p in (org.get("stages_from_final") or "").split(";") if p.strip()]


def is_former(site: dict) -> bool:
    op = (site.get("operational_status") or "").lower()
    st = (site.get("site_type") or "").lower()
    return st.startswith("former") or "closed" in op or "ceased" in op


def presence_role(site: dict) -> str:
    st = site.get("site_type") or ""
    if st in OFFICE_TYPES:
        return "office_or_headquarters"
    if st in DELIVERY_TYPES:
        return "delivery"
    if st in MIXED_TYPES:
        return "mixed_office_and_delivery"
    raise SystemExit(f"Unclassified site type for {site['marker_id']}: {st}")


def family_relevant(site: dict, org: dict) -> bool:
    if site["core_universe_role"] == "public_reception":
        return True
    if site["core_universe_role"] == "public_welfare":
        return False
    return bool(set(stages_of(org)) & FAMILY_STAGES)


def per_10k(n: int, children: int) -> str:
    if children <= 0:
        return ""
    return f"{n / children * 10000:.2f}"


def q3(values: list[float]) -> float:
    return statistics.quantiles(values, n=4, method="inclusive")[2]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sites = load_csv(STEP2 / "sites.csv")
    orgs = {o["org_id"]: o for o in load_csv(STEP2 / "organisations.csv")}
    dopa = load_csv(DOPA)
    dole_rows = load_csv(DOLE)
    tpmap = {r["district_code"]: r for r in load_csv(TPMAP)}
    dole = {r["area_code"]: r for r in dole_rows if r["area_code"] != "50"}
    if set(dole) != {r["district_code"] for r in dopa}:
        raise SystemExit("DOLE district codes do not match DOPA.")
    if set(tpmap) != {r["district_code"] for r in dopa}:
        raise SystemExit("TPMAP district codes do not match DOPA.")

    role_rows = []
    for s in sites:
        if not yn(s["level1_site_eligible"]):
            continue
        org = orgs[s["org_id"]]
        role = presence_role(s)
        former = is_former(s)
        relevant = family_relevant(s, org) and role in {"delivery", "mixed_office_and_delivery"} and not former
        prec = s.get("location_precision") or ""
        approximated = (
            "approximat" in prec.lower()
            or "locality" in prec.lower()
            or prec.lower().startswith("village")
        )
        role_rows.append({
            "marker_id": s["marker_id"],
            "org_id": s["org_id"],
            "organisation": s["organisation"],
            "district_code": s["district_code"],
            "district_en": s["district_en"],
            "district_join_eligible": s["level1_district_join_eligible"],
            "site_type": s["site_type"],
            "location_precision": prec,
            "location_is_approximated": "yes" if approximated else "no",
            "presence_role": role,
            "operational_status": s["operational_status"],
            "is_former_or_closed": "yes" if former else "no",
            "counts_as_current_delivery_or_mixed": "yes" if (
                role in {"delivery", "mixed_office_and_delivery"} and not former
            ) else "no",
            "counts_as_family_support_relevant": "yes" if relevant else "no",
            "family_support_basis": (
                "public reception directory category"
                if s["core_universe_role"] == "public_reception"
                else "FINAL stages of the owning organisation, excluding residential-only"
            ),
            "core_universe_role": s["core_universe_role"],
            "note": (
                "Office/HQ is presence of an organisation address, not a delivery site. "
                "Mixed labels keep both an office and a programme or campus. "
                "Former/closed sites stay in the Level 1 site count and out of current-delivery rates."
            ),
        })
    write_csv(OUT / "site_presence_role.csv", role_rows, list(role_rows[0].keys()))

    by_dist = defaultdict(list)
    nonjoin = []
    for row in role_rows:
        if yn(row["district_join_eligible"]) and row["district_code"]:
            by_dist[row["district_code"]].append(row)
        else:
            nonjoin.append(row)

    district_rows = []
    for d in dopa:
        code = d["district_code"]
        rows = by_dist.get(code, [])
        children = int(d["thai_reg_age_0_17"])
        current_dm = [r for r in rows if r["counts_as_current_delivery_or_mixed"] == "yes"]
        family = [r for r in rows if r["counts_as_family_support_relevant"] == "yes"]
        offices = [
            r for r in rows
            if r["presence_role"] == "office_or_headquarters" and r["is_former_or_closed"] == "no"
        ]
        mixed = [r for r in rows if r["presence_role"] == "mixed_office_and_delivery" and r["is_former_or_closed"] == "no"]
        delivery = [r for r in rows if r["presence_role"] == "delivery" and r["is_former_or_closed"] == "no"]
        former = [r for r in rows if r["is_former_or_closed"] == "yes"]
        org_ids = {r["org_id"] for r in rows}
        dl = dole[code]
        tp = tpmap[code]
        district_rows.append({
            "district_code": code,
            "district_th": d["district_th"],
            "district_en": d["district_en"],
            "thai_reg_age_0_5": d["thai_reg_age_0_5"],
            "thai_reg_age_6_11": d["thai_reg_age_6_11"],
            "thai_reg_age_12_17": d["thai_reg_age_12_17"],
            "thai_reg_age_0_17": children,
            "n_level1_sites": len(rows),
            "n_level1_organisations": len(org_ids),
            "n_current_office_or_hq": len(offices),
            "n_current_delivery": len(delivery),
            "n_current_mixed": len(mixed),
            "n_former_or_closed": len(former),
            "n_current_delivery_or_mixed": len(current_dm),
            "n_current_delivery_or_mixed_approximated": sum(
                1 for r in current_dm if r["location_is_approximated"] == "yes"
            ),
            "n_current_family_support_relevant": len(family),
            "level1_sites_per_10k_thai_0_17": per_10k(len(rows), children),
            "current_delivery_or_mixed_per_10k_thai_0_17": per_10k(len(current_dm), children),
            "family_support_relevant_per_10k_thai_0_17": per_10k(len(family), children),
            "organisations_per_10k_thai_0_17": per_10k(len(org_ids), children),
            "dole_total_records": int(dl["total_records"]),
            "dole_home_not_found": int(dl["screen_home_not_found"]),
            "dole_consented_info": int(dl["screen_consented_info"]),
            "dole_already_enrolled": int(dl["screen_already_enrolled"]),
            "dole_moved_away": int(dl["screen_moved_away"]),
            "dole_help_wanted": int(dl["help_wanted"] or 0),
            "dole_never_studied": int(dl["never_studied"] or 0),
            "tpmap_jpt_people": int(tp["jpt_people"]),
            "tpmap_target_poor_people": int(tp["target_poor_people"]),
            "tpmap_target_poor_rate_percent": tp["target_poor_rate_percent"],
            "tpmap_poor_education": int(tp["poor_education"]),
            "zero_current_delivery_is_not_absence": "yes" if len(current_dm) == 0 else "no",
            "dopa_note": DOPA_NOTE,
            "rate_note": RATE_NOTE,
            "timeframe_note": TIMEFRAME,
        })

    children_vals = [int(r["thai_reg_age_0_17"]) for r in district_rows]
    hnf_vals = [int(r["dole_home_not_found"]) for r in district_rows]
    cons_vals = [int(r["dole_consented_info"]) for r in district_rows]
    poor_vals = [int(r["tpmap_target_poor_people"]) for r in district_rows]
    child_q3 = q3(children_vals)
    hnf_q3 = q3(hnf_vals)
    cons_q3 = q3(cons_vals)
    poor_median = statistics.median(poor_vals)
    child_median = statistics.median(children_vals)
    joinable_sites = sum(int(r["n_level1_sites"]) for r in district_rows)
    province_children = sum(children_vals)

    signals = []
    for r in district_rows:
        children = int(r["thai_reg_age_0_17"])
        delivery_n = int(r["n_current_delivery_or_mixed"])
        sites_n = int(r["n_level1_sites"])
        base = {
            "district_code": r["district_code"],
            "district_en": r["district_en"],
            "thai_reg_age_0_17": children,
            "n_current_delivery_or_mixed": delivery_n,
            "n_level1_sites": sites_n,
            "confidence": "low",
            "sort_is_not_a_rank": "Rows are separate signals. Order is not a priority score.",
        }
        if delivery_n == 0 and int(r["dole_home_not_found"]) >= hnf_q3:
            signals.append({
                **base,
                "signal": "zero_current_delivery_and_dole_home_not_found_at_or_above_q3",
                "evidence": (
                    f"DOLE home-not-found {r['dole_home_not_found']} "
                    f"(Q3 threshold {hnf_q3:.0f} of 25 districts). "
                    "Unlocated records support verification outreach, not a count of children out of school."
                ),
            })
        if delivery_n == 0 and int(r["dole_consented_info"]) >= cons_q3:
            signals.append({
                **base,
                "signal": "zero_current_delivery_and_dole_consented_at_or_above_q3",
                "evidence": (
                    f"DOLE consented-to-information {r['dole_consented_info']} "
                    f"(Q3 threshold {cons_q3:.0f}). "
                    "Consented is not the same as help wanted or confirmed exclusion."
                ),
            })
        if delivery_n == 0 and int(r["tpmap_target_poor_people"]) >= poor_median:
            signals.append({
                **base,
                "signal": "zero_current_delivery_and_tpmap_target_poor_at_or_above_median",
                "evidence": (
                    f"TPMAP target-poor people {r['tpmap_target_poor_people']} "
                    f"(median {poor_median:.0f}; rate {r['tpmap_target_poor_rate_percent']}% of JPT people). "
                    "All-age welfare-card MPI view, not a child count. Mueang's displayed zero is below this cut."
                ),
            })
        if delivery_n == 0 and children >= child_median:
            signals.append({
                **base,
                "signal": "zero_current_delivery_and_thai_children_0_17_at_or_above_median",
                "evidence": (
                    f"Registered Thai children 0–17: {children} (median {child_median:.0f}). "
                    "Zero mapped delivery in the sample is not proof that no provider exists."
                ),
            })
        if joinable_sites and province_children:
            site_share = sites_n / joinable_sites
            child_share = children / province_children
            if sites_n >= 5 and child_share > 0 and site_share >= 2 * child_share:
                signals.append({
                    **base,
                    "signal": "mapped_sample_concentrated_relative_to_registered_children",
                    "evidence": (
                        f"{sites_n} Level 1 sites are {site_share:.1%} of joinable sites; "
                        f"{children} children are {child_share:.1%} of provincial registered Thai 0–17. "
                        "This is concentration of the mapped sample, not surplus provision."
                    ),
                })
        if delivery_n > 0 and (
            int(r["dole_home_not_found"]) >= hnf_q3 or int(r["tpmap_target_poor_people"]) >= q3(poor_vals)
        ):
            signals.append({
                **base,
                "signal": "has_mapped_delivery_and_high_unlocated_or_target_poor",
                "evidence": (
                    f"Current delivery or mixed sites: {delivery_n}. "
                    f"DOLE home-not-found {r['dole_home_not_found']} (Q3 {hnf_q3:.0f}); "
                    f"TPMAP target-poor {r['tpmap_target_poor_people']} "
                    f"(Q3 {q3(poor_vals):.0f}). Presence is not coverage."
                ),
            })

    district_fields = list(district_rows[0].keys())
    write_csv(OUT / "district_presence.csv", district_rows, district_fields)
    signal_fields = [
        "district_code", "district_en", "signal", "evidence",
        "thai_reg_age_0_17", "n_current_delivery_or_mixed", "n_level1_sites",
        "confidence", "sort_is_not_a_rank",
    ]
    signals.sort(key=lambda r: (-int(r["thai_reg_age_0_17"]), r["signal"]))
    write_csv(OUT / "signals_for_closer_look.csv", signals, signal_fields)

    definitions = [
        {
            "measure": "thai_reg_age_0_17",
            "numerator_or_value": "DOPA Dec 2025 Thai nationals aged 0–17 on ordinary house registration, whole district (residual + assigned municipalities).",
            "denominator": "Not a rate.",
            "do_not": "Do not treat as resident children. Do not add non-Thai, TDOB, XHOUSE or MOVE into this age count.",
        },
        {
            "measure": "level1_sites_per_10k_thai_0_17",
            "numerator_or_value": "Level 1 eligible sites joined to the district, including offices and former/closed offices.",
            "denominator": "thai_reg_age_0_17, times 10,000.",
            "do_not": "Do not read as children served or as coverage.",
        },
        {
            "measure": "current_delivery_or_mixed_per_10k_thai_0_17",
            "numerator_or_value": "Current sites whose type is delivery or mixed office-and-delivery. Excludes pure offices and former/closed sites.",
            "denominator": "thai_reg_age_0_17, times 10,000.",
            "do_not": "Do not add this to the office count. Catchment is unknown.",
        },
        {
            "measure": "organisations_per_10k_thai_0_17",
            "numerator_or_value": "Unique organisations with at least one Level 1 site in the district.",
            "denominator": "thai_reg_age_0_17, times 10,000.",
            "do_not": "Do not sum this column across districts. An organisation in two districts is counted in each.",
        },
        {
            "measure": "family_support_relevant_per_10k_thai_0_17",
            "numerator_or_value": "Current delivery or mixed sites with a FINAL family-support stage, plus the public reception shelter.",
            "denominator": "thai_reg_age_0_17, times 10,000.",
            "do_not": "Do not treat the all-delivery rate as this rate. Protected residential homes without a family-support tick stay in the delivery rate only.",
        },
        {
            "measure": "n_current_delivery_or_mixed_approximated",
            "numerator_or_value": "Current delivery or mixed sites whose location precision is an approximation, locality or village — not an exact public address.",
            "denominator": "Not a rate.",
            "do_not": "Do not treat a high delivery rate built from these rows as a cluster of exact points.",
        },
        {
            "measure": "n_current_family_support_relevant",
            "numerator_or_value": "Current delivery or mixed sites whose organisation has a FINAL family-support stage, plus the public reception shelter. Public welfare homes are delivery but not this count.",
            "denominator": "Not rated separately.",
            "do_not": "Do not treat residential-only sites as the pilot family-support numerator.",
        },
        {
            "measure": "dole_total_records",
            "numerator_or_value": "DOLE Zero Dropout records in the district extract.",
            "denominator": "Not a rate in this table.",
            "do_not": "Do not treat all records as current dropouts.",
        },
        {
            "measure": "dole_home_not_found",
            "numerator_or_value": "Screening category หาบ้านไม่พบ. Mutually exclusive with the other nine screening categories.",
            "denominator": "dole_total_records if a share is later required.",
            "do_not": "Do not read as children outside education. This is an unlocated-record signal.",
        },
        {
            "measure": "dole_consented_info",
            "numerator_or_value": "Screening category ยินดีให้ข้อมูล.",
            "denominator": "dole_total_records if a share is later required.",
            "do_not": "Do not add to home-not-found. Do not equate with help_wanted.",
        },
        {
            "measure": "dole_help_wanted",
            "numerator_or_value": "Records marked as wanting help. Not one of the ten screening categories.",
            "denominator": "Not established here as a share of total_records.",
            "do_not": "Do not add to screening categories or to never_studied.",
        },
        {
            "measure": "dole_never_studied",
            "numerator_or_value": "Prior-schooling flag.",
            "denominator": "Not established here.",
            "do_not": "Do not add the four DOLE age bands. They exceed the record total.",
        },
        {
            "measure": "tpmap_target_poor_people",
            "numerator_or_value": "TPMAP 2569 target-poor people: JPT people who are MPI-poor on all five dimensions and in the welfare-card (มีบัตร) filter.",
            "denominator": "tpmap_jpt_people for the published rate.",
            "do_not": "Do not add the five MPI dimension counts. Do not treat as poor children. Mueang zero is a displayed result.",
        },
        {
            "measure": "tpmap_poor_education",
            "numerator_or_value": "Target-poor people failing the education dimension.",
            "denominator": "Overlaps the other four dimensions.",
            "do_not": "Do not add to health, living, economy or social protection.",
        },
    ]
    write_csv(OUT / "measure_definitions.csv", definitions, [
        "measure", "numerator_or_value", "denominator", "do_not",
    ])

    def top(key: str, n: int = 3) -> list[dict]:
        return [
            {
                "district_code": r["district_code"],
                "district_en": r["district_en"],
                key: r[key],
            }
            for r in sorted(district_rows, key=lambda r: float(r[key] or 0), reverse=True)[:n]
        ]

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "province_thai_reg_age_0_17": province_children,
        "n_joinable_level1_sites": joinable_sites,
        "n_nonjoin_level1_sites": len(nonjoin),
        "n_districts_with_zero_current_delivery_or_mixed": sum(
            1 for r in district_rows if int(r["n_current_delivery_or_mixed"]) == 0
        ),
        "thresholds": {
            "dole_home_not_found_q3": hnf_q3,
            "dole_consented_q3": cons_q3,
            "tpmap_target_poor_median": poor_median,
            "tpmap_target_poor_q3": q3(poor_vals),
            "thai_children_median": child_median,
            "thai_children_q3": child_q3,
            "quartile_method": "statistics.quantiles n=4 method=inclusive",
            "concentration_rule": "Level 1 site share >= 2x share of registered Thai children 0–17, and at least 5 sites",
        },
        "highest_current_delivery_or_mixed_per_10k": top("current_delivery_or_mixed_per_10k_thai_0_17"),
        "highest_family_support_relevant_per_10k": top("family_support_relevant_per_10k_thai_0_17"),
        "highest_dole_home_not_found": top("dole_home_not_found"),
        "highest_tpmap_target_poor_people": top("tpmap_target_poor_people"),
        "n_signals": len(signals),
        "nonjoin_marker_ids": [r["marker_id"] for r in nonjoin],
        "limitations": [
            "Doi Saket's high delivery rate is seven family-style homes stored as district-level protected approximations, with no FINAL family-support tick. It is not an exact-point cluster and not a family-support presence rate.",
            "District organisation counts are not additive.",
            "Eight Level 1 sites are in Chiang Mai but not joined to a district, so they are absent from every district rate.",
            "Small districts make a single site a large per-10,000 rate. Read the count beside the rate.",
        ],
        "rule": (
            "Presence rates use mapped sites over registered Thai children 0–17. "
            "They are not unmet-need ranks. DOLE, TPMAP and DOPA stay in separate columns. "
            "Offices are not delivery sites. Zero mapped delivery is not absence of provision."
        ),
    }
    (OUT / "level2a_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
