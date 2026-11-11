# Chiang Mai geographical analysis — working plan

Last updated: 10 November 2026 (Singapore time)
Project: Thrive TSA Partnerships
Status: Steps 1–6 complete except optional/blocked items and local partner validation. The 29 October audit is unchanged. Level 2C is two unranked comparisons in `outputs/step6/`: family-support/prevention, and educational re-engagement. There is no combined score.

## 1. Objective and scope

Produce two linked levels of analysis for Chiang Mai Province:

1. **Basic geographical concentration and dispersion:** where mapped organisations and physical sites are concentrated, spread out, clustered or isolated, overall and by the seven value-chain stages.
2. **Higher-value analysis:** (a) provider distribution relative to population and need; (b) accessibility and travel time; (c) potential outreach or pilot locations for TSA-led partnerships.

Keep observations, calculated results, assumptions and recommendations visibly separate. Do not interpret few mapped providers as proof of unmet need, or proximity as proof of access. No causal claims about family separation from geographic associations alone.

Out of scope for this phase: disability/specialist-needs analysis, actual referral-network performance, individual family-to-placement journeys, and comprehensive organisational capacity/financial resilience analysis.

## 2. Established user decisions

- Chiang Mai Province only. Note boundary effects where relevant; do not silently add providers outside the province.
- Use `landscape mapping (FINAL).xlsx`, sheet `CM Mapping (checkbox)`, as the seven-stage classification. Confirmed by the user on 10 November 2026. Do not substitute an older workbook, the SharePoint-linked `CM mapping 2.0 - updated.xlsx`, or the separately available Supply Side Scan. The checkbox sheet still contains external-link formulas pointing at that SharePoint file; analysis uses the cached checkbox values stored in FINAL, including the advocacy-for-family-placement ticks for ZOE Foundation Thailand and Daughters Rising / Chai Lai Orchid Foundation.
- Use the existing geographical audit as a starting point, not an already validated coordinate dataset. Resolve and read its current version before editing.
- Repeat organisations across applicable My Maps stage layers, but do not count these repeated map entries as additional organisations or sites.
- Exact locations only for suitable publicly disclosed sites. For non-public/sensitive sites, use documented, safeguarding-appropriate approximations. Record method, evidence and reasoning. Never infer confidential residences.
- Prefer Thai official/organisation sources; retain Thai names and original labels alongside English interpretation.
- Flag organisations with multiple verified physical sites. Keep offices, service-delivery sites and programme areas distinct.
- Do not use the blocked poor/extremely poor student dataset at `data.go.th/dataset/69_48`.
- Treat TPMAP as a view-and-record workflow; do not make a download a prerequisite.
- Google Maps/Earth are useful for inspection and selected route checks. An OpenStreetMap download is optional, not a prerequisite.
- Preserve the source workbook's visual design if later edits are requested; build analysis tables separately unless agreed otherwise.

## 3. Source register and acquisition approach

### A. Population — DOPA December 2025

- Source: https://stat.bora.dopa.go.th/new_stat/file/6812/6812cc50.txt
- Official schema: https://stat.bora.dopa.go.th/new_stat/webPage/statByAge.php
- Status: Converted and geography-validated on 10 November 2026. Use `outputs/step1/dopa_district_totals.csv` as district denominators. Do **not** use อำเภอ-labelled rows as whole-district totals.
- Format: UTF-8 BOM, pipe-delimited, no header. 334 rows. Each row is one area label plus 219 numbers (102 male/female age pairs, interleaved, ages 0–100 and 101 = over 100) then TDOB, XHOUSE, OTHER_NAT, MOVE, and sex/overall totals. Trailing empty field after the last pipe.
- Official identity, passed for all 334 rows: `MALE_TOT` = male ages 0–101 + male TDOB + male XHOUSE + male OTHER_NAT + male MOVE (same for female).
- File order: province; then all 25 districts each followed by residual tambons; then 54 municipalities each followed by their tambon fragments. No district row appears after the first municipality.
- **Geography (this is the critical check):** an `อำเภอ…` row is the **registration-office residual**, not the administrative district. Municipalities are listed separately. Residual Mueang Chiang Mai is only 15,068 people (ตำบลช้างเผือก 2,040 + ตำบลสันผีเสื้อ 13,028). Chiang Mai City (`เทศบาลนครเชียงใหม่`) is 111,809 and is not inside that residual row. Whole Mueang = residual 15,068 + nine assigned municipalities 205,216 = **220,284**.
- Tambon names are not unique IDs. `ตำบลช้างเผือก` appears three times: residual 2,040; เทศบาลตำบลช้างเผือก 8,636; a fragment inside the City 13,097. Those are mutually exclusive registration slices of the same Thai tambon. Adding same-name fragments reconstructs the tambon; collapsing them as duplicates would undercount.
- Do not sum province + district + municipality + tambon rows together. The 254 tambon-labelled rows already partition the province (they sum to 1,798,588). The 25 อำเภอ rows sum only to 1,127,147.
- Whole-district reconstruction: residual district row + municipalities assigned in `outputs/step1/dopa_municipality_assignment.csv`. All 54 municipalities assigned; reconstructed 25 districts sum to the province total 1,798,588. Four districts have no municipality in this file (Wiang Haeng, Mae On, Doi Lo, Galyani Vadhana) — their residual row *is* the whole district.
- **Population coverage:** single-year ages are **Thai nationals on ordinary house registration only**. Province Thai registered ages 0–17 = **279,076** (0–5: 72,267; 6–11: 99,326; 12–17: 107,483). Non-Thai 156,898 is all-age only; do not infer an age-specific migrant child count. TDOB (lunar birth year), XHOUSE (central house register) and MOVE (in process of moving) also have no single-year ages. Registered population is not necessarily resident population.
- Proposed child denominator for area rates: `thai_reg_age_0_17` in `dopa_district_totals.csv`, always with the coverage note attached. Programme-specific bands (0–5, 6–11, 12–17) are in the same file.
- Worked example rows: `outputs/step1/dopa_worked_example.csv`. Validation log: `outputs/step1/dopa_validation.json`.

### B. Optional Chiang Mai public-health population cross-check

- Landing page: https://www.chiangmaihealth.go.th/detail_article2.php?info_id=670
- Public Excel endpoint identified previously: https://www.chiangmaihealth.go.th/document/260710178365889530.xlsx
- User reports an IP block. On this turn the web reader recognised an Excel content type at the endpoint but could not parse it; no workbook bytes or contents were validated.
- Only use ordinary authorised public access. Do not bypass IP restrictions, rotate proxies, spoof identity or repeatedly probe a denied endpoint. If unavailable, proceed with DOPA and document the limitation, or request a copy from the publisher/user.
- This is an optional alternative/cross-check, not a dependency. Do not mix midyear and December observations as if they share a reference date. Previously identified health-office tables exclude foreign residents; verify the downloaded file's own notes.

### C. TPMAP — poverty and disadvantage

- Source: https://www.tpmap.in.th/ (Mueang live check: https://www.tpmap.in.th/2569/5001)
- Status: District evidence table written 10 November 2026. Packed CSVs are year 2569, metric `11111` (all five MPI dimensions), welfare-card filter **มีบัตร**. Official column/indicator labels from `raw/tpmap/TPMAP_datadict_plan13.xlsx`. Outputs: `outputs/step1/tpmap_district_evidence.csv`, `tpmap_glossary.csv`, `tpmap_capture_log.json`.
- Page last update shown: 3 April 2569. The 2569 page states the underlying sources are **จปฐ 2568** integrated with **State Welfare Card 2565**. The data-dictionary column text still mentions welfare-card year 2560; prefer the live page's 2565/2568 note.
- **Mueang (5001) zeros:** live page displays 0 target-poor people out of 52,312 JPT-surveyed people and 24,044 surveyed households (rate 0.00%). That matches the packed CSV. The same district is also 0 under the `all` and `nocard` 11111 files. Mueang is the **only** Chiang Mai district with 0 target poor in this view. Do **not** treat this as missing data, and do **not** treat it as proof of no poverty or no need. Urban JPT/welfare-card coverage may be incomplete.
- Highest target-poor count in this view: Mae Chaem (5003) 8,309 people (19.85% of 41,850 surveyed). Dimension counts overlap; do not add the five MPI dimensions as unique people.
- Poverty is an area-level need indicator, not evidence that a particular family should separate or that a particular child needs residential care. Target poor is not a child-only count.

### D. DOLE Zero Dropout — educational outreach/re-engagement

- Source: https://zerodropout.dole.go.th/
- Status: Thai labels inspected. Province-wide and all 25 district aggregates retrieved on 10 November 2026 (UTC) from the public dashboard endpoint `https://dbzerodropout.dole.go.th/api/dashboard_68.php` (province_id=50; district_id blank for the province, 5001–5025 for districts; subdistrict_id blank). Raw JSON, SHA-256 hashes and an acquisition log are in `raw/dole/`. A flattened table and Thai–English glossary are in `outputs/step1/`.
- Snapshot: dashboard footer © 2026.04.28, Version 2.0.0; header describes 2025 child/youth records for survey in 2026. District totals sum to the province total (27,140). The ten screening outcomes also sum to each area's total (mutually exclusive). The dashboard field `survey.notfound` (186 province-wide) is the deceased count, not “home not found”; home-not-found is the screening category `หาบ้านไม่พบ` (4,385). The four age-band totals sum to 28,377, which exceeds the record total, so they must not be added as unique children.
- Header inspected: 2025 child/youth records for survey in 2026. Record the selected geographic filters and snapshot date for every extraction.
- Translate Thai labels directly, with an English glossary; do not rely on Google Translate alone.
- Maintain distinctions: total records in system; surveyed; remaining to survey; person located; person not located; consent to information collection; prior schooling; already enrolled; assistance requested.
- Do not treat all records as confirmed current dropouts, an unlocated person as outside education, or already-enrolled children as unresolved cases.
- Identify each percentage's denominator and whether answer categories overlap. Check age range, nationality coverage, residency basis and survey completion before comparing areas.
- Separate two implications: poor survey completion/unlocated records may justify verification outreach; verified current exclusion and reported barriers may justify re-engagement support. These are different priorities.

### E. User-supplied 2025 directories

- `Chiang Mai Private Childcare facilities 2025.pdf` — current Library ID: `libfile_b6f8e57cf8348191a655a5f2791f1e4a`.
- `Chiang Mai Public Children's homes 2025.pdf` — current Library ID: `libfile_12cc669dc244819188145fd0e8dacc1c`.
- Initial inspection: the private file is a licensed private childcare directory (`สถานรับเลี้ยงเด็กเอกชน`), dated 16 October 2025, not a private residential-welfare-home directory. This administrative label does NOT establish that every listed facility provides only daytime care. Preserve its provider types, attendance arrangements, age eligibility, operating/licence status and any listed fees when extracting.
- The public file separately lists welfare homes, a reception facility and a juvenile observation/protection facility. These are not interchangeable service types.
- Private directory extracted on 10 November 2026 to `outputs/step1/private_childcare_directory_2025.csv` (148 numbered data rows, pages 2–13; original Thai retained; page references kept). The PDF summary states 149 operating facilities in 2568; the numbered table has 148 rows. That mismatch is in the source document. Thai “า” is often rendered as “ำ” in the PDF font; extraction applies a documented correction. Row 147's district cell overflowed as “งเชียงดาว”; treated as เชียงดาว.
- Public directory extracted 10 November 2026 to `outputs/step1/public_childrens_homes_2025.csv` (one-page PDF; four sites, all in Mae Rim). Two public welfare homes and one reception/family shelter sit on an adjacent Don Kaeo campus (63/1, 63/3, 63/4 หมู่ 4 ต.ดอนแก้ว). The juvenile observation/protection centre is a separate Mae Sa site. **None of the four names appear in the 29 October audit.** Added in Step 2 as CM-069–072 / ORG-054–057. Welfare/reception join the core public layer; the juvenile centre stays separately labelled. Don Kaeo 63/1 and 63/3 share the 63/4 reception coordinate and are not extra nearest-neighbour points.
- Do not interpret private daycare availability as free, affordable, charitable or residential care. Do not automatically add all entries to the core nonprofit count or assign value-chain stages solely from facility titles.
- Verify whether a separate private residential-welfare-home directory is still needed. Do not assume these two files cover the whole care ecosystem.

#### Required accommodation check — added by user on 10 November 2026

- Screen every listed private childcare facility for actual overnight accommodation, recurring boarding or long-term residential care, including mixed provision. Do not assume actual services from the licence category or English name.
- Inspect directory fields and visually check ambiguous Thai/OCR. Then check Thai provider websites, official social pages and credible official/independent sources, matching identity and locality. Log a result for every facility, including unavailable evidence; lack of a keyword is not proof of absence.
- Search terms may include รับเลี้ยงเด็กค้างคืน, รับเลี้ยงเด็กประจำ, พักประจำ, อยู่ประจำ, กินนอน and 24 ชั่วโมง, with the facility's Thai name. Extended hours or a 24-hour service claim alone does not establish long-term residence.
- Distinguish day-only care; occasional overnight/respite care; recurring boarding; long-term residential care; mixed provision; and unresolved status. Record original Thai evidence, English interpretation, source/date, length and pattern of stays where available, and confidence.
- Keep administrative/licence category separate from evidenced operating model. Do not infer unlawful operation from a discrepancy. Historical provision is not proof of current practice.
- Where residential operation is substantiated, flag it for the relevant residential analysis while retaining its original category and preventing duplicate counts. Do not automatically classify ordinary daycare as a core charitable provider.
- If public evidence cannot settle duration or current operation, mark for user/partner verification. Do not contact facilities without authorisation or expose confidential residences.
- Facility-by-facility public-web check completed 10 November 2026 for all 148 numbered directory rows. Combined register: `outputs/step1/accommodation_register.json` and `.csv`; unresolved/watch cases: `outputs/step1/accommodation_unresolved_cases.csv`. Administrative licence category kept separate from evidenced operating model. None of the 148 were classified as recurring boarding, long-term residential or mixed provision. One facility (row 35, นิวซุปเปอร์คิดส์เนอสเซอรี่ / New Superkids Nursery, ฟ้าฮ่าม) is `occasional_overnight_or_respite` at medium confidence from Facebook-mirror copy claiming 24-hour opening and an overnight-stay hashtag; other directories list daytime hours only — partner verification required. Counts: day_only 68; unresolved 55; identity_not_confirmed 24; occasional_overnight_or_respite 1. Most day_only calls rest on third-party directory hours, not the facility's own site; Facebook pages were largely unread because fetches timed out or were name-only. Overnight-keyword searches were not run for every row. This does not prove residential provision is absent. Rows needing partner verification remain in the unresolved-case file.
- Related leads found while searching, not in this directory: Mission Power Foundation dormitory for hill-tribe secondary students associated with Hana Christian (row 128); San Phi Suea municipality notice of an applicant private child welfare home มูลนิธิบ้านร่มไม้ชายคา. Neither was added to the core count. A separate private residential-welfare-home directory is still not confirmed to exist.

### F. Roads, routes and administrative boundaries

- Optional road source: https://download.geofabrik.de/asia/thailand.html
- Optional structured Google route alternative: https://developers.google.com/maps/documentation/routes/compute_route_matrix
- Viewing roads and calculating consistent journeys across many origin–destination pairs are different tasks. Use selected Google route checks for a small shortlist; choose a structured routing approach only if scale requires it.
- Do not purchase API services, activate billing or download large road datasets before choosing the method and obtaining any required authorisation.
- Obtain suitable administrative boundaries/codes for district/subdistrict joins and area calculations. Verify vintage and alignment with population geography.
- Routes need connected road-network data and travel assumptions, not just road lines. Record mode, date/time assumptions, speeds, seasonal limitations and route failures. No implied access to private vehicles or suitable public transport.

## 4. Execution sequence and completion checks

### Step 1 — source preparation and explanation

- Explain the DOPA file with a small worked row example; create a readable population table only after validating its schema and registration geography. **Done 10 November 2026.** See Section 3A and `outputs/step1/dopa_district_totals.csv`.
- Explain basic geographic data cleaning to the user before applying changes. **Explained and applied 10 November 2026** to a dated copy. Raw 29 October file untouched. See Step 2 below.
- Translate the directories and DOLE labels; extract available area-level evidence from DOLE/TPMAP with provenance. **Done 10 November 2026** (DOLE, private directory, public directory, TPMAP).
- Completion: source register records what is available, excluded, inaccessible or still unverified; no invented values.

### Step 2 — clean and validate the geographic base

**Explanation (given before any edit of the 29 October audit).** Cleaning means making the existing location workbook analysis-ready without changing its visual design or silently dropping uncertain records. The 29 October file stays the raw starting point; a copy plus a change log is used.

**Applied 10 November 2026.** Raw SHA-256 `a6a0219320a0535d46f6a78896efeabe7b9d7e4e9f5c0bb46ff8f39e4021b07c` unchanged. Dated copy: `outputs/step2/source_copy/Chiang_Mai_Organisation_Location_Audit_2026-10-29.xlsx`. Analysis tables: `sites.csv`, `organisations.csv`, `site_stages.csv`, `change_log.csv`, `district_crosswalk.csv`, `cleaning_summary.json`. Script: `scripts/clean_geographic_base.py`.

Resulting universe: 72 site records (68 audit + 4 public directory); 57 organisations (53 audit + 4 public). Level 1 family-support counts: **53 organisations**, **57 physical sites**, **12 nearest-neighbour points**. Chiang Rai CM-060/061/062 excluded. Juvenile CM-072 labelled, geocoded to the OSM named facility (18.889962, 98.965311), **not** in those three numerators. Don Kaeo CM-069/070 share CM-071 (18.857521, 98.968210) and are not extra points. 17 exact public addresses had no Nominatim house/building hit; they remain sites without points, not zeros. 3 geocodes were street-level only (`ok_coarse`) and are not NN points. Audit-supplied points kept: Child's Dream CM-042, Interact Asia CM-047. Non-district phrases stay non-joins. Wiang Pa Pao maps to Chiang Rai, not a 26th Chiang Mai district.

What the current audit already contains, and what cleaning will do with it:

1. **Preserve raw + changelog.** Keep `raw/project_snapshot/Chiang_Mai_Organisation_Location_Audit.xlsx` untouched. Work on a dated copy. Every coordinate, district, precision or inclusion change gets a log row (marker ID, field, old, new, reason, source, date).
2. **Stable IDs.** Marker IDs `CM-001`… already exist (68 master records, 53 organisations). Keep them. Add a separate organisation ID only if one organisation must own several markers; do not renumber.
3. **Names.** Standardise Thai/English organisation and place names for joins, retaining the original strings. District labels in the audit are mixed English (`Mueang Chiang Mai`, `San Sai`) and non-district phrases (`Undisclosed in Chiang Mai Province`, `Province-wide / multiple districts`). Cleaning will map named districts onto the 25 DOPA district names/codes and keep non-district phrases as non-joins, not as a 26th district.
4. **Duplicates and parent–child.** Flag multi-site organisations, parent offices versus delivery sites, and network markers that are not extra organisations. Stage sheets intentionally repeat organisations; those repeats are not additional sites.
5. **Coordinates.** Only 2 of 68 master records currently store latitude/longitude (Child's Dream `CM-042`, Interact Asia `CM-047`). “Exact public street address” (30 records) is not yet a point on the map. Geocoding will be applied only to publicly disclosed exact sites, checked against Chiang Mai boundaries, and logged. Protected/approximate records will **not** be geocoded to a fake point.
6. **Precision versus points.** Existing `Location_Precision` values already distinguish exact addresses, district/province approximations, service areas, and “no verified site”. Descriptive nearest-neighbour work in Level 1 may use exact public points only. Shared district centroids must not be treated as clusters.
7. **Unknown versus zero.** Empty coordinates, “district confirmed; premises not geolocated”, and “no verified Chiang Mai site” stay distinct from a count of zero providers. Out-of-scope is not the same as absent.
8. **Boundary / scope.** Three markers are Chiang Rai, Wiang Pa Pao (`CM-060` Homestead of Hope, `CM-061` Unity Villa, `CM-062` The Family Forge) and are already `Out of scope — Chiang Rai Province` / `Include_in_Map = No`. They illustrate the boundary-effect rule: do not silently add them to Chiang Mai counts; they may be noted as nearby provision. Six organisation-summary rows have an out-of-scope/excluded flag; the Excluded & Review sheet has eight records (alternate address, no local site, former offices, Asia's Hope network, plus the three Chiang Rai sites). Cleaning will apply explicit inclusion rules before Level 1 counts.
9. **Offices, delivery sites, service areas.** `Site_Type` is already heterogeneous (administrative office, residential campus, service-area marker, protected home). Level 1 will count unique organisations and unique eligible physical sites separately; service-area markers are not physical sites.
10. **Stages.** Organisation-level ticks from FINAL remain the classification source. Site-level stage evidence will be labelled when it is only organisation-level. Do not copy stage-sheet repeats into a unique-site count.
11. **Safeguarding.** Non-public child residential and high-risk sites stay approximated. Do not infer confidential residences or publish hidden addresses. Do not contact facilities.
12. **Joins to DOPA/DOLE/TPMAP.** After names and districts are standardised, eligible sites can be joined to `dopa_district_totals.csv` (and later TPMAP) on district code/name. Do not join residual อำเภอ DOPA rows. Do not allocate province-wide or undisclosed sites to a district denominator.

Completion when applied: documented analysis-ready population/need joins and site eligibility rules. Sensitive and uncertain records are not silently discarded or treated as exact. **Met 10 November 2026.**

### Step 3 — Level 1: concentration and dispersion

- Report unique organisations and unique physical sites separately, overall and by stage.
- Compare counts and shares by district; use subdistrict detail only when reliable. Include land-area density if valid boundaries are available.
- For sufficiently precise physical sites, calculate descriptive nearest-neighbour distances and spatial spread using appropriate distance calculations. Report the number of eligible observations.
- Use approximate records for appropriate area-level summaries; do not let shared district/tambon centroids manufacture artificial point clusters. Compare conclusions with/without uncertain locations.
- Interpret multi-stage overlap without double counting. No claim of statistically significant clustering without an explicit test and defensible reference model.
- Output: mapped distribution, compact summary tables and cautious findings about the mapped sample—not a complete census unless validated as one.

**Done 10 November 2026.** Script: `scripts/level1_concentration.py`. Outputs: `outputs/step3/`.

Headline counts (family-support universe): **53 organisations**, **57 physical sites**, **12 NN points**. Of the 53 organisations: 50 mapped child-welfare (39 with a FINAL tick, 11 with none) plus 3 public welfare/reception. 8 of 57 sites are in Chiang Mai but not joinable to a district. 49 join to DOPA 5001–5025. 12 of 25 districts have **zero** mapped eligible sites — that is not evidence of no provision.

District concentration of mapped sites: Mueang Chiang Mai 15 (26% of 57), San Sai 9, Doi Saket 8. Those three hold 32 of 57 sites. Mae Rim has the three public campus sites (one NN point). Doi Saket’s 8 sites have **no** house-level points. Child population is shown on the district table for later Level 2A rates, not as a need ranking here.

FINAL organisation-stage counts (unique orgs; do not add across stages): Short-term Intervention 27; Residential and Institutional Care 24; Parent Capability Building 17; Identification & Routing 15; Reintegration, Reunification and Adoption 15; Foster Care / Adoption 2; Kinship Care **0**. 32 of 50 mapped organisations have two or more FINAL stages; 11 have none. Site-stage counts copy FINAL ticks to eligible sites (plus directory category for the three public facilities). Audit `Applicable_Stages` that disagree with FINAL (including kinship at Kid’s Ark and foster at Connie’s Home) are logged in `stage_source_disagreement.csv` and not counted.

Nearest-neighbour (n=12 public house/building points; great-circle km): min 0.875 (Friends for All Children — Child’s Dream), median 2.78, mean 3.14, max 6.18 (Mae Rim reception shelter — Salvation Army). All 12 points sit in the central basin (Mueang, San Sai, Hang Dong, Saraphi, Mae Rim). Descriptive only. No clustering test: a whole-province CSR index would be dominated by study-area choice. Coarse street geocodes and shared campus copies were not treated as extra points, so they cannot manufacture clusters.

Limitations that stay attached: this is the mapped sample, not a census; organisations, sites and points are different numerators; proximity is not access; few mapped sites is not unmet need; no causal claims.

### Step 4 — Level 2A: population/need versus provision

- Join validated child population, TPMAP and DOLE measures to the same geography and compatible timeframes.
- Calculate provider-presence rates, for example unique eligible sites per 10,000 children, with explicit numerator/denominator definitions. Counts are not capacity or quality measures.
- Compare both absolute need and rates; retain survey coverage and data gaps. Do not combine overlapping vulnerable populations into a unique-child total.
- Separate verified delivery locations from organisation headquarters. Where service catchments are unknown, describe presence rather than actual coverage.
- Output: areas warranting closer investigation, with evidence and confidence—not definitive unmet-need rankings.

**Done 10 November 2026.** Script: `scripts/level2a_presence.py`. Outputs: `outputs/step4/`.

Denominator for every rate: DOPA December 2025 Thai nationals aged 0–17 on ordinary house registration. Province total **279,076**, equal to the sum of the 25 reconstructed districts. Registered is not resident. Non-Thai, TDOB, XHOUSE and MOVE stay out of the age denominator.

Numerators, kept separate: Level 1 sites joined to a district (**49**); current delivery or mixed sites; current offices; former/closed offices (Care for Children, Interact Asia, both Mueang); family-support-relevant sites (FINAL family-support stage, or the public reception shelter). Public welfare homes count as delivery and not as family-support. Eight Level 1 sites have no district join and are in no district rate. Rates are mapped presence per 10,000 registered Thai children 0–17. Catchments are unknown, so this is not coverage, capacity or children served.

Twelve districts have zero current delivery or mixed sites. That is not evidence of no provision.

Doi Saket’s delivery rate is **6.15 per 10,000** (7 sites). Those seven are family-style homes stored as district-level protected approximations, and none has a FINAL family-support tick. The family-support rate there is **0**. San Sai is the highest family-support presence rate at **3.70** (8 sites, 21,649 children). Mae Wang’s **1.84** is one site over 5,436 children; read the count beside the rate. Mueang has 15 Level 1 sites, of which 9 are current offices and 2 are former offices; current delivery or mixed is 4 (**1.44 per 10,000**).

DOLE and TPMAP stay in their own columns. They are not added to each other or to the child denominator. DOLE home-not-found is an unlocated-record signal (Fang 1,326; Mueang 990; Mae Ai 533). DOLE consented-to-information is a different screening category (Omkoi 631). TPMAP target-poor people are an all-age welfare-card MPI count (Mae Chaem 8,309, 19.85% of 41,850 JPT people; Chom Thong 3,755; Mae Taeng 2,872). Mueang’s target-poor count remains the displayed **0**. The five TPMAP dimensions overlap. DOLE age bands are not used.

`signals_for_closer_look.csv` has 27 rows. Each row is one stated rule (quartile or median cut, published in `level2a_summary.json`). A district can appear more than once. The file is not a priority score. Low confidence on every row. Separate signals that warrant a closer look, still inside this mapped sample: Fang (1,326 unlocated DOLE records, zero mapped delivery, 18,203 registered Thai children 0–17); Omkoi (631 consented, 2,831 target-poor, zero mapped delivery); Mae Chaem (8,309 target-poor, zero mapped delivery); Chom Thong (3,755 target-poor, zero mapped delivery). Mueang, Mae Ai and Mae Rim have mapped delivery and still have high home-not-found counts: presence is not coverage.

### Step 5 — Level 2B: accessibility

- Agree the origin unit, relevant destination services, travel mode and practical thresholds before calculation.
- Use meaningful settlement/population origins where available. An administrative centroid is a proxy, not a child's home; disclose any approximation.
- Estimate road distance/time to eligible services; test alternative travel assumptions. Do not route to confidential or broadly approximated residences as if exact.
- Do not estimate a percentage of children within a travel-time threshold from coarse district totals without a justified population-allocation method.
- Output: modelled accessibility, sensitivity checks and selected route validation. Show affordability, eligibility and transport-availability gaps separately.

**Agreed and calculated 10 November 2026.** The user accepted the recommended design. Rationales are also in the handoff briefing. Script: `scripts/level2b_access.py`. Outputs: `outputs/step5/`.

1. **Origins — district centroids.** No settlement or child-location layer is on disk, and DOPA has counts without coordinates. District is already the join for DOPA, DOLE and TPMAP. The centroid is an administrative proxy, not a child's home. Polygons are geoBoundaries gbOpen Thailand ADM2, simplified, Royal Thai Survey Department / OCHA, year represented 2019. All 25 centroids fall inside their polygons. Li (Lamphun) had a centroid inside the simplified Chiang Mai province outline and was excluded because it is not one of the 25 districts.
2. **Destinations — eight exact public delivery or mixed sites.** Routing needs a public house or building geocode. Protected approximations, undisclosed sites, pure offices, former offices and the juvenile centre stay off the route. The eight are CM-004, CM-010, CM-022, CM-026, CM-029, CM-030, CM-032 and CM-071. All eight are family-support relevant.
3. **Mode — private-vehicle road time, with walking as the sensitivity.** No paid router. Primary engine: FOSSGIS OSM car profile at `routing.openstreetmap.de`, retrieved 10 November 2026. The speed model is a car profile on shared roads; it is not observed traffic and not a separate motorbike profile. Walking uses the FOSSGIS foot profile on the same pairs. Valhalla auto checks the car pair. Songthaew and bus timetables are not in the source set.
4. **Threshold — the spread, with 30 and 60 minutes as descriptive bins.** No partner defined a cutoff that means accessible. Bins count district centroids. They are not a share of children.

**Results.** All 25 centroids returned a private-vehicle route. Primary times: minimum 3.9 minutes (Mueang), median 84.5, mean 88.0, maximum 215.4 (Omkoi, 187 km). Six centroids are at or under 30 minutes on the primary engine (Mueang, Saraphi, Hang Dong, Mae Rim, San Kamphaeng, San Pa Tong). Eleven are at or under 60. Fourteen are over 60. Road distance is 1.11 to 2.05 times the straight line.

The 30-minute bin is engine-sensitive. On the 16 pairs Valhalla could route, its car time is slower by a median of 16.1 minutes (maximum difference 28). Only Mueang (3.9 and 6.8 minutes) and Saraphi (8.9 and 14.3) are under 30 minutes on both engines. Nine remote centroids, including Mae Chaem and Omkoi, did not snap to Valhalla's road graph; their FOSSGIS times remain the primary estimate.

The centroid is not the location of a district's own services. San Sai's centroid is 34 minutes from the Mae Rim shelter; San Sai's own exact public sites are 36–40 minutes from that same northern centroid. Mae Rim's centroid is 21 minutes and 17 km from the Don Kaeo shelter in the same district.

Closer-look districts from Level 2A, primary private-vehicle time from the centroid: Chom Thong 86 minutes, Fang 135 minutes, Mae Chaem 186 minutes, Omkoi 215 minutes. Walking the same pairs is a different order of magnitude (Mueang centroid about 29 minutes on foot; Omkoi about 40 hours). For 8 districts the nearest site on foot is a different site from the nearest site by car. Affordability, eligibility and shared-transport schedules are recorded as not modelled.

### Step 6 — Level 2C: outreach/pilot shortlist

- Combine evidence on need, existing provision and accessibility with potential partners and TSA's feasible role.
- Confirmed focus: shortlist family-support/prevention and educational re-engagement locations through TSA-led partnerships, not new residential-care sites. Specify the particular intervention before final location ranking.
- Compare options transparently; no arbitrary composite weights hidden in a score. Seek agreement before using a weighted ranking and test sensitivity.
- Validate shortlisted areas with TSA/local partners, including affordability, language, referral options and actual operational capacity.
- Output: a reasoned shortlist and rationale, uncertainties, local-validation questions and provisional pilot outcomes to monitor.

**Done 10 November 2026, as two unranked comparisons.** The user chose both purposes and asked that they stay separate, with no weighted score. Script: `scripts/level2c_comparisons.py`. Outputs: `outputs/step6/`. Rows are in DOPA district-code order. That order is not a priority.

Family-support comparison uses the Level 2A family-support site count, the TPMAP target-poor count, registered Thai children 0–17 as context, and the Level 2B centroid travel time to one of the eight exact public sites. Educational re-engagement uses the DOLE columns one at a time. Home-not-found, consented, help-wanted and never-studied are separate rules. After-school sites are counted on their own: three Kid's Ark sites in Mae Ai and one in San Sai. Vineyard Methodist School in San Sai is a school campus, not an after-school site. No road time to an education site was estimated, because those locations are approximated.

Cuts are the Level 2A quartiles and medians. Help-wanted and never-studied use the same quartile method on their own columns (Q3 = 5 for each). A district can appear under more than one rule. The hits are not added into a score.

Reading the two tables side by side, without combining them: Fang's DOLE signal is home-not-found (1,326) with consented below the cut. Omkoi's DOLE signal is the contacted side (631 consented, 173 help-wanted, 112 never-studied) with home-not-found at 20. Mae Chaem and Chom Thong have no mapped family-support site and target-poor counts of 8,309 and 3,755. Doi Saket has no family-support tick, and its seven family-style homes remain protected approximations in the other delivery count. Mae Ai has the three after-school sites and is also at or above the home-not-found and consented cuts, so mapped after-school presence is not treated as coverage. Mae Wang has one family-support site and target-poor people at or above the third quartile.

Local validation questions and provisional outcomes to monitor are in `local_validation_questions.csv` and `provisional_outcomes.csv`. Affordability, language, eligibility and spare capacity are questions, not measured values. On 10 November 2026 the user could not answer them. They are highlighted for future partner validation in the handoff briefing. Do not fill them from the existing tables, and do not contact facilities unless the user authorises it.

## 5. Confirmed decisions and remaining method choices

1. **Provider universe — accepted:** core analysis = existing mapped child-welfare organisations plus relevant public welfare/reception facilities; private childcare/daycare forms a separate supplementary layer (`outputs/step1/accommodation_register.csv`; none of 148 classified as long-term residential on public evidence; one occasional-overnight flag). Juvenile-justice facilities are separately labelled, not pooled into ordinary family-support provision. Additional user requirement: check whether any private childcare entries actually provide long-term accommodation or function as residential facilities, following Section 3E — public-web pass completed; partner verification still required for unresolved and overnight-flagged rows.
2. **Pilot purpose — confirmed:** initial shortlist = family-support/prevention and educational re-engagement through TSA-led partnerships; not residential expansion. On 10 November 2026 the user kept both purposes as two unranked comparisons. No weighted score.

Working defaults to review later: district-first comparisons with subdistrict drill-down where valid; children aged 0–17 with programme-specific exceptions; 2025 baseline where possible and clearly labelled newer dashboard snapshots; no paid routing services. Level 2B travel mode is now decided: private-vehicle road time, walking as the sensitivity, 30 and 60 minutes as descriptive bins only. See Step 5.

## 6. Progress log and next action

- [x] Confirmed the two analysis levels and three higher-value priorities.
- [x] Recorded excluded sources and non-circumvention rules for access blocks.
- [x] Inspected the supplied DOPA text and official field schema.
- [x] Inspected DOLE's Thai dashboard labels, but not filtered Chiang Mai values.
- [x] Retrieved and flattened DOLE province + 25 district aggregates (10 November 2026); glossary written; `notfound` field interpreted as deceased, not home-not-found.
- [x] Identified the different facility categories in the two uploaded directories.
- [x] User confirmed provider universe and pilot purpose; added accommodation verification for private childcare facilities.
- [x] User confirmed `landscape mapping (FINAL).xlsx` / `CM Mapping (checkbox)` as the classification source.
- [x] Completed preliminary text screening of the private directory; this is not evidence that all facilities are non-residential.
- [x] Extracted the 148-row private childcare table with page references.
- [x] Completed facility-by-facility public-web accommodation checks for all 148 rows and merged the register; unresolved/watch cases logged. Facebook and some own websites remain unread. Not evidence that residential provision is absent.
- [x] ChatGPT handoff is a repeatable overwrite, not a one-off dated dump. Refresh after each step with `python scripts/build_chatgpt_handoff.py`. Live folder: `export/chatgpt_handoff/`. Live zip: `export/Chiang_Mai_ChatGPT_Handoff.zip` (copied to the TSA Mapping folder). A dated zip is also written under `export/`. Start with `00_READ_ME_FIRST.md`. New tables under `outputs/step1/` through `outputs/step6/` are packed automatically.
- [x] Converted and validated DOPA (10 November 2026): schema identity passed on 334 rows; อำเภอ rows are residuals; whole-district table = residual + assigned municipalities; province total 1,798,588; Thai registered ages 0–17 = 279,076. Outputs under `outputs/step1/dopa_*.csv`. Worked example: Mueang residual 15,068 vs reconstructed Mueang 220,284.
- [x] Explained basic geographic cleaning (10 November 2026). The 29 October audit has **not** been edited; cleaning used a dated copy plus a change log.
- [x] Extracted the public children's-homes directory (4 sites, all Mae Rim; none in the 29 October audit). Welfare/reception vs juvenile-justice kept distinct.
- [x] Captured TPMAP 2569 district evidence with glossary and a live check of Mueang 5001 (0 target poor / 52,312 surveyed; matches CSV).
- [x] Applied Step 2 geographic cleaning (10 November 2026): public Mae Rim sites added as CM-069–072; districts mapped to DOPA 5001–5025; Nominatim house/building geocodes only; campus-share for Don Kaeo; juvenile labelled and excluded from family-support numerators.
- [x] Completed Level 1 concentration/dispersion (10 November 2026): 53 orgs / 57 sites / 12 points; district shares; descriptive NN; FINAL stage counts. Outputs under `outputs/step3/`.
- [x] Completed Level 2A (10 November 2026): district presence rates per 10,000 registered Thai children 0–17; offices separated from delivery; DOLE and TPMAP kept as separate columns; closer-look signals are rules, not a score. Outputs under `outputs/step4/`.
- [x] Agreed and calculated Level 2B (10 November 2026): district-centroid proxies to eight exact public destinations; private-vehicle times with a walking sensitivity; 30 and 60 minutes as descriptive bins. Outputs under `outputs/step5/`. Rationales are in this plan and in the handoff briefing.
- [x] Completed Level 2C (10 November 2026) as two unranked comparisons: family-support/prevention and educational re-engagement. No weighted score. Outputs under `outputs/step6/`.
- [ ] Partner validation, deferred on 10 November 2026. The seven questions are highlighted in the handoff briefing and stored in `outputs/step6/local_validation_questions.csv`. The user could not answer them. Nothing further in this sequence can be calculated before those answers exist.

Next action: paused for partner validation. When TSA or district partners can answer, highlight the seven questions in the handoff briefing. Then update this plan with what they confirm, what they contradict, and what remains unknown. Keep the two comparisons separate. Do not invent partner answers from the tables already on disk. Never mark an analysis complete merely because a source or dashboard exists.
