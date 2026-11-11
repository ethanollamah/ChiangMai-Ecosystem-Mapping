"""Step 6 — Level 2C: two unranked comparisons.

The user chose both pilot purposes, kept separate, with no weighted score:
family-support / prevention partnerships, and educational re-engagement.

District rows stay in DOPA code order. A rule hit is a yes/no on one stated
cut from Level 2A. Hits are not added up and not sorted into a priority.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRESENCE = ROOT / "outputs" / "step4" / "district_presence.csv"
ACCESS = ROOT / "outputs" / "step5" / "district_access.csv"
ROLES = ROOT / "outputs" / "step4" / "site_presence_role.csv"
SITES = ROOT / "outputs" / "step2" / "sites.csv"
THRESHOLDS = ROOT / "outputs" / "step4" / "level2a_summary.json"
OUT = ROOT / "outputs" / "step6"

ORDER_NOTE = "Listed in DOPA district-code order. This is not a rank and not a score."


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)


def yn(flag: bool) -> str:
    return "yes" if flag else "no"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    presence = load_csv(PRESENCE)
    access = {r["district_code"]: r for r in load_csv(ACCESS)}
    cuts = json.loads(THRESHOLDS.read_text(encoding="utf-8"))["thresholds"]
    poor_median = float(cuts["tpmap_target_poor_median"])
    poor_q3 = float(cuts["tpmap_target_poor_q3"])
    child_median = float(cuts["thai_children_median"])
    hnf_q3 = float(cuts["dole_home_not_found_q3"])
    cons_q3 = float(cuts["dole_consented_q3"])

    sites = {s["marker_id"]: s for s in load_csv(SITES)}
    after_school = defaultdict(list)
    school_campus = defaultdict(list)
    family_sites = defaultdict(list)
    for role in load_csv(ROLES):
        site = sites[role["marker_id"]]
        if role["district_join_eligible"] != "yes" or not role["district_code"]:
            continue
        if role["is_former_or_closed"] == "yes":
            continue
        kind = site["site_type"]
        code = role["district_code"]
        if "after-school" in kind.lower():
            after_school[code].append(role)
        elif kind == "School / programme site":
            school_campus[code].append(role)
        if role["counts_as_family_support_relevant"] == "yes":
            family_sites[code].append(role)

    help_q3 = statistics.quantiles([int(r["dole_help_wanted"]) for r in presence], n=4, method="inclusive")[2]
    never_q3 = statistics.quantiles([int(r["dole_never_studied"]) for r in presence], n=4, method="inclusive")[2]
    family_rows = []
    family_hits = []
    education_rows = []
    education_hits = []

    for row in presence:
        code = row["district_code"]
        trip = access[code]
        children = int(row["thai_reg_age_0_17"])
        poor = int(row["tpmap_target_poor_people"])
        family_n = int(row["n_current_family_support_relevant"])
        hnf = int(row["dole_home_not_found"])
        consented = int(row["dole_consented_info"])
        help_wanted = int(row["dole_help_wanted"])
        names = sorted({r["organisation"] for r in family_sites.get(code, [])})

        delivery_n = int(row["n_current_delivery_or_mixed"])
        approx_n = int(row["n_current_delivery_or_mixed_approximated"])
        other_delivery = ""
        if delivery_n:
            other_delivery = (
                f" Other mapped delivery or mixed sites, not in the family-support count: {delivery_n}"
                f", of which {approx_n} are approximated."
            )
        f_poor = family_n == 0 and poor >= poor_median
        f_children = family_n == 0 and children >= child_median
        f_present_poor = family_n > 0 and poor >= poor_q3
        family_rows.append({
            "district_code": code,
            "district_th": row["district_th"],
            "district_en": row["district_en"],
            "thai_reg_age_0_17_context_only": children,
            "n_current_family_support_sites": family_n,
            "family_support_organisations": "; ".join(names),
            "n_current_delivery_or_mixed": delivery_n,
            "n_of_those_approximated": approx_n,
            "family_support_sites_per_10k_context": row["family_support_relevant_per_10k_thai_0_17"],
            "tpmap_target_poor_people": poor,
            "tpmap_target_poor_rate_percent": row["tpmap_target_poor_rate_percent"],
            "centroid_private_vehicle_minutes": trip["private_vehicle_minutes"],
            "centroid_walk_minutes_same_destination": trip["walk_minutes_same_destination"],
            "nearest_family_support_site": trip["nearest_marker_id"],
            "nearest_family_support_organisation": trip["nearest_organisation"],
            "under_30_min_on_both_engines": trip["under_30_on_both_engines"],
            "rule_zero_sites_and_target_poor_at_or_above_median": yn(f_poor),
            "rule_zero_sites_and_children_at_or_above_median": yn(f_children),
            "rule_sites_present_and_target_poor_at_or_above_q3": yn(f_present_poor),
            "order_note": ORDER_NOTE,
            "reading_note": (
                "Family-support sites are the Level 2A family-support numerator. "
                "Residential approximations without that tick stay in the delivery count only. "
                "TPMAP target-poor people are an all-age welfare-card count, not children who should enter care. "
                "Travel time is from the district centroid to one of the eight exact public sites."
            ),
        })
        evidence = {
            "rule_zero_sites_and_target_poor_at_or_above_median": (
                f"No mapped family-support site. TPMAP target-poor people {poor} "
                f"(median cut {poor_median:.0f}; rate {row['tpmap_target_poor_rate_percent']}%). "
                f"Centroid is {trip['private_vehicle_minutes']} private-vehicle minutes from {trip['nearest_organisation']}."
                + other_delivery
            ),
            "rule_zero_sites_and_children_at_or_above_median": (
                f"No mapped family-support site. Registered Thai children 0–17: {children} "
                f"(median cut {child_median:.0f}). Zero family-support sites is not proof that no provider exists."
                + other_delivery
            ),
            "rule_sites_present_and_target_poor_at_or_above_q3": (
                f"{family_n} mapped family-support site(s): {'; '.join(names)}. "
                f"TPMAP target-poor people {poor} (Q3 cut {poor_q3:.0f}). Presence is not coverage."
            ),
        }
        for rule, hit in (
            ("rule_zero_sites_and_target_poor_at_or_above_median", f_poor),
            ("rule_zero_sites_and_children_at_or_above_median", f_children),
            ("rule_sites_present_and_target_poor_at_or_above_q3", f_present_poor),
        ):
            if hit:
                family_hits.append({
                    "district_code": code,
                    "district_en": row["district_en"],
                    "rule": rule,
                    "evidence": evidence[rule],
                    "order_note": ORDER_NOTE,
                })

        after = after_school.get(code, [])
        campus = school_campus.get(code, [])
        e_hnf = hnf >= hnf_q3
        e_cons = consented >= cons_q3
        e_help = help_wanted >= help_q3
        never_n = int(row["dole_never_studied"])
        e_never = never_n >= never_q3
        education_rows.append({
            "district_code": code,
            "district_th": row["district_th"],
            "district_en": row["district_en"],
            "thai_reg_age_0_17_context_only": children,
            "dole_total_records": int(row["dole_total_records"]),
            "dole_home_not_found": hnf,
            "dole_consented_info": consented,
            "dole_already_enrolled": int(row["dole_already_enrolled"]),
            "dole_moved_away": int(row["dole_moved_away"]),
            "dole_help_wanted": help_wanted,
            "dole_never_studied": int(row["dole_never_studied"]),
            "n_after_school_programme_sites": len(after),
            "after_school_organisations": "; ".join(sorted({r["organisation"] for r in after})),
            "n_school_campus_sites": len(campus),
            "school_campus_organisations": "; ".join(sorted({r["organisation"] for r in campus})),
            "rule_home_not_found_at_or_above_q3": yn(e_hnf),
            "rule_consented_at_or_above_q3": yn(e_cons),
            "rule_help_wanted_at_or_above_q3": yn(e_help),
            "rule_never_studied_at_or_above_q3": yn(e_never),
            "order_note": ORDER_NOTE,
            "reading_note": (
                "DOLE columns are separate. Total records are not current dropouts. "
                "Home-not-found is an unlocated-record signal. Consented is not help-wanted. "
                "Already enrolled is not an unresolved case. "
                "After-school sites are mapped programme locations, not verified DOLE re-engagement providers. "
                "No road time to an education site is estimated, because those sites are approximated and were not routed."
            ),
        })
        edu_evidence = {
            "rule_home_not_found_at_or_above_q3": (
                f"DOLE home-not-found {hnf} (Q3 cut {hnf_q3:.0f} of {row['dole_total_records']} records). "
                "This supports a check on whether the record can be located. It is not a count of children outside school."
            ),
            "rule_consented_at_or_above_q3": (
                f"DOLE consented-to-information {consented} (Q3 cut {cons_q3:.0f}). "
                "Consented is a contacted pool. It is not the same as help wanted or confirmed exclusion."
            ),
            "rule_help_wanted_at_or_above_q3": (
                f"DOLE help-wanted {help_wanted} (Q3 cut {help_q3:.0f}). "
                "This flag is not added to never-studied or to home-not-found."
            ),
            "rule_never_studied_at_or_above_q3": (
                f"DOLE never-studied {never_n} (Q3 cut {never_q3:.0f}). "
                "This flag is not added to help-wanted."
            ),
        }
        for rule, hit in (
            ("rule_home_not_found_at_or_above_q3", e_hnf),
            ("rule_consented_at_or_above_q3", e_cons),
            ("rule_help_wanted_at_or_above_q3", e_help),
            ("rule_never_studied_at_or_above_q3", e_never),
        ):
            if hit:
                education_hits.append({
                    "district_code": code,
                    "district_en": row["district_en"],
                    "rule": rule,
                    "evidence": edu_evidence[rule],
                    "order_note": ORDER_NOTE,
                })

    questions = [
        {
            "comparison": "both",
            "question": "Which providers are working in this district but absent from the mapped sample?",
            "why": "Zero mapped sites is not proof that no provider exists. The sample is the audit plus the 2025 public directory.",
        },
        {
            "comparison": "both",
            "question": "What languages do families use here, and can a TSA partner work in those languages?",
            "why": "Language is outside the geographic tables. A reachable district can still be the wrong partnership.",
        },
        {
            "comparison": "both",
            "question": "Can a family make this trip without a private vehicle, and what does it cost?",
            "why": "The travel estimate is a car-profile time from a district centroid. Fares and songthaew schedules were not modelled.",
        },
        {
            "comparison": "both",
            "question": "Does a mapped organisation have capacity to host a partnership or take a referral?",
            "why": "A mapped site is a location, not a measure of spare capacity or willingness.",
        },
        {
            "comparison": "family_support",
            "question": "Are the TPMAP target-poor households a group a prevention partnership could meet, or a feature of who the survey counted?",
            "why": "Target-poor people are an all-age welfare-card MPI count. Mueang's displayed zero is a survey result, not a finding of no need.",
        },
        {
            "comparison": "educational_reengagement",
            "question": "For home-not-found records, is the gap a missing address, a move, or a child outside school?",
            "why": "Home-not-found is an unlocated DOLE record. It becomes a re-engagement caseload only after the record is located and the schooling status is known.",
        },
        {
            "comparison": "educational_reengagement",
            "question": "Among records that consented, how many want help, and is that help about school re-entry?",
            "why": "Consented, help-wanted and never-studied are different columns. Already-enrolled records are not unresolved cases.",
        },
    ]
    outcomes = [
        {
            "comparison": "family_support",
            "outcome_to_monitor": "A local partner is named, and the partnership role is agreed in writing.",
            "why_provisional": "This records whether a partnership exists. It is not a count of children placed or separated.",
        },
        {
            "comparison": "family_support",
            "outcome_to_monitor": "Families in contact, and the referral options that exist before any placement discussion.",
            "why_provisional": "The pilot purpose is family support and prevention, not a new residential site.",
        },
        {
            "comparison": "educational_reengagement",
            "outcome_to_monitor": "Home-not-found records that are located, and the schooling status found when they are located.",
            "why_provisional": "Location comes before any claim that the child is outside education.",
        },
        {
            "comparison": "educational_reengagement",
            "outcome_to_monitor": "Among consented records, how many want help and how many enter school or alternative education.",
            "why_provisional": "Help-wanted and enrolment are separate from the size of the DOLE extract.",
        },
    ]

    write_csv(OUT / "comparison_family_support.csv", family_rows, list(family_rows[0].keys()))
    write_csv(OUT / "comparison_educational_reengagement.csv", education_rows, list(education_rows[0].keys()))
    hit_fields = ["district_code", "district_en", "rule", "evidence", "order_note"]
    write_csv(OUT / "family_support_rule_hits.csv", family_hits, hit_fields)
    write_csv(OUT / "education_rule_hits.csv", education_hits, hit_fields)
    write_csv(OUT / "local_validation_questions.csv", questions, ["comparison", "question", "why"])
    write_csv(OUT / "provisional_outcomes.csv", outcomes, ["comparison", "outcome_to_monitor", "why_provisional"])

    summary = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "decision": (
            "User chose both purposes on 10 November 2026: family-support/prevention partnerships "
            "and educational re-engagement, kept as two comparisons. No weighted score. No rank."
        ),
        "order": "DOPA district code. Not a priority order.",
        "cuts_reused_from_level2a": cuts,
        "education_flag_q3": {"dole_help_wanted": help_q3, "dole_never_studied": never_q3},
        "n_family_support_rule_hits": len(family_hits),
        "n_education_rule_hits": len(education_hits),
        "family_support_districts_with_any_rule": list(dict.fromkeys(r["district_en"] for r in family_hits)),
        "education_districts_with_any_rule": list(dict.fromkeys(r["district_en"] for r in education_hits)),
        "after_school_sites": {
            code: len(rows) for code, rows in sorted(after_school.items())
        },
        "school_campus_sites": {
            code: len(rows) for code, rows in sorted(school_campus.items())
        },
        "uncertainties": [
            "The mapped sample is not a census of providers.",
            "Catchments are unknown, so a site in one district may serve another.",
            "Centroid travel time is not a child's travel time.",
            "DOLE screening categories must not be added to each other or to TPMAP.",
            "Affordability, language, eligibility and spare capacity are validation questions, not measured values.",
        ],
    }
    (OUT / "level2c_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
