# Chiang Mai geographical analysis — working plan

Last updated: 10 November 2026 (Singapore time)
Project: Thrive TSA Partnerships
Status: Step 1 source preparation in progress. Classification workbook resolved to `landscape mapping (FINAL).xlsx`. DOLE district aggregates and the private-childcare accommodation register are on disk. DOPA conversion, TPMAP evidence table, public-directory extraction and geographic-base cleaning have not started. Substantive geographical analyses have not started.

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
- Status: Raw text and official schema inspected on 10 November 2026. Not yet converted into a validated analytical table.
- Format: pipe-delimited text without a header row. Area label first; alternating male/female age fields follow. The final fields include special registration categories and overall totals.
- Next: obtain an ordinary public download; retain original bytes; decode Thai correctly; add documented English column names; validate field counts and totals.
- Critical geography check: establish whether district-labelled rows cover the whole administrative district or registration-office residual areas with municipalities listed separately. Do not use those rows as district denominators until the geography is reconciled. Do not sum province totals, parent rows and child rows together.
- Critical population check: establish the coverage of the single-age fields versus non-Thai and special-registration totals. Do not infer age-specific migrant populations from all-age totals. Registered population is not necessarily resident population.
- Proposed child denominator: ages 0–17, subject to confirmation and data coverage. Programme-specific age groups should be reported separately where needed.

### B. Optional Chiang Mai public-health population cross-check

- Landing page: https://www.chiangmaihealth.go.th/detail_article2.php?info_id=670
- Public Excel endpoint identified previously: https://www.chiangmaihealth.go.th/document/260710178365889530.xlsx
- User reports an IP block. On this turn the web reader recognised an Excel content type at the endpoint but could not parse it; no workbook bytes or contents were validated.
- Only use ordinary authorised public access. Do not bypass IP restrictions, rotate proxies, spoof identity or repeatedly probe a denied endpoint. If unavailable, proceed with DOPA and document the limitation, or request a copy from the publisher/user.
- This is an optional alternative/cross-check, not a dependency. Do not mix midyear and December observations as if they share a reference date. Previously identified health-office tables exclude foreign residents; verify the downloaded file's own notes.

### C. TPMAP — poverty and disadvantage

- Source: https://www.tpmap.in.th/ (example Chiang Mai page: https://www.tpmap.in.th/2569/501301)
- Method: inspect Thai public pages; record selected year, area, welfare-card filter, indicator, numerator, denominator, displayed result, URL and capture date in a structured evidence table.
- Validate a sample of transcriptions against the page. If interactive values cannot be read reliably, request screenshots or an authorised browser view; do not substitute blank placeholders for zeros.
- Capture both counts and rates. Preserve the survey denominator and underlying observation years, not just the dashboard year. Overlapping dimensions are not separate people.
- Poverty is an area-level need indicator, not evidence that a particular family should separate or that a particular child needs residential care.

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
- Private directory extracted on 10 November 2026 to `outputs/step1/private_childcare_directory_2025.csv` (148 numbered data rows, pages 2–13; original Thai retained; page references kept). The PDF summary states 149 operating facilities in 2568; the numbered table has 148 rows. That mismatch is in the source document. Thai “า” is often rendered as “ำ” in the PDF font; extraction applies a documented correction. Row 147's district cell overflowed as “งเชียงดาว”; treated as เชียงดาว. Public directory not yet fully extracted into an analysis table. Reconcile both directories with existing organisation and site records before counting.
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

- Explain the DOPA file with a small worked row example; create a readable population table only after validating its schema and registration geography.
- Explain basic geographic data cleaning to the user before applying changes.
- Translate the directories and DOLE labels; extract available area-level evidence from DOLE/TPMAP with provenance.
- Completion: source register records what is available, excluded, inaccessible or still unverified; no invented values.

### Step 2 — clean and validate the geographic base

- Preserve raw data and a change log. Standardise Thai/English organisation and place names; assign stable organisation and site IDs; resolve duplicates and parent–child relationships.
- Validate coordinates against sources and Chiang Mai boundaries. Record exact/approximate precision, approximation method, address evidence and date.
- Keep unknowns distinct from zero. Separate offices from delivery sites and broad operating areas from physical points.
- Validate stage assignments at site level where possible; label organisation-level-only evidence. Maintain separate organisation, site and site–stage tables.
- Completion: documented analysis-ready population/need joins and site eligibility rules. Sensitive and uncertain records are not silently discarded or treated as exact.

### Step 3 — Level 1: concentration and dispersion

- Report unique organisations and unique physical sites separately, overall and by stage.
- Compare counts and shares by district; use subdistrict detail only when reliable. Include land-area density if valid boundaries are available.
- For sufficiently precise physical sites, calculate descriptive nearest-neighbour distances and spatial spread using appropriate distance calculations. Report the number of eligible observations.
- Use approximate records for appropriate area-level summaries; do not let shared district/tambon centroids manufacture artificial point clusters. Compare conclusions with/without uncertain locations.
- Interpret multi-stage overlap without double counting. No claim of statistically significant clustering without an explicit test and defensible reference model.
- Output: mapped distribution, compact summary tables and cautious findings about the mapped sample—not a complete census unless validated as one.

### Step 4 — Level 2A: population/need versus provision

- Join validated child population, TPMAP and DOLE measures to the same geography and compatible timeframes.
- Calculate provider-presence rates, for example unique eligible sites per 10,000 children, with explicit numerator/denominator definitions. Counts are not capacity or quality measures.
- Compare both absolute need and rates; retain survey coverage and data gaps. Do not combine overlapping vulnerable populations into a unique-child total.
- Separate verified delivery locations from organisation headquarters. Where service catchments are unknown, describe presence rather than actual coverage.
- Output: areas warranting closer investigation, with evidence and confidence—not definitive unmet-need rankings.

### Step 5 — Level 2B: accessibility

- Agree the origin unit, relevant destination services, travel mode and practical thresholds before calculation.
- Use meaningful settlement/population origins where available. An administrative centroid is a proxy, not a child's home; disclose any approximation.
- Estimate road distance/time to eligible services; test alternative travel assumptions. Do not route to confidential or broadly approximated residences as if exact.
- Do not estimate a percentage of children within a travel-time threshold from coarse district totals without a justified population-allocation method.
- Output: modelled accessibility, sensitivity checks and selected route validation. Show affordability, eligibility and transport-availability gaps separately.

### Step 6 — Level 2C: outreach/pilot shortlist

- Combine evidence on need, existing provision and accessibility with potential partners and TSA's feasible role.
- Confirmed focus: shortlist family-support/prevention and educational re-engagement locations through TSA-led partnerships, not new residential-care sites. Specify the particular intervention before final location ranking.
- Compare options transparently; no arbitrary composite weights hidden in a score. Seek agreement before using a weighted ranking and test sensitivity.
- Validate shortlisted areas with TSA/local partners, including affordability, language, referral options and actual operational capacity.
- Output: a reasoned shortlist and rationale, uncertainties, local-validation questions and provisional pilot outcomes to monitor.

## 5. Confirmed decisions and remaining method choices

1. **Provider universe — accepted:** core analysis = existing mapped child-welfare organisations plus relevant public welfare/reception facilities; private childcare/daycare forms a separate supplementary layer (`outputs/step1/accommodation_register.csv`; none of 148 classified as long-term residential on public evidence; one occasional-overnight flag). Juvenile-justice facilities are separately labelled, not pooled into ordinary family-support provision. Additional user requirement: check whether any private childcare entries actually provide long-term accommodation or function as residential facilities, following Section 3E — public-web pass completed; partner verification still required for unresolved and overnight-flagged rows.
2. **Pilot purpose — confirmed:** initial shortlist = family-support/prevention and educational re-engagement through TSA-led partnerships; not residential expansion.

Working defaults to review later: district-first comparisons with subdistrict drill-down where valid; children aged 0–17 with programme-specific exceptions; 2025 baseline where possible and clearly labelled newer dashboard snapshots; no paid routing services. Travel mode and thresholds remain undecided until the accessibility design step.

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
- [x] Packed a ChatGPT-ready handoff (10 November 2026): `export/Chiang_Mai_Step1_ChatGPT_Handoff_2026-11-10.zip` (copy also in the TSA Mapping folder). Start with `00_READ_ME_FIRST.md` inside the zip.
- [ ] Convert/validate DOPA; explain the file and basic geographic cleaning in detail.
- [ ] Fully extract/translate the public children's-homes directory; capture TPMAP area evidence with provenance (DOLE area table already extracted).
- [ ] Validate geographic base, then complete Level 1 before Level 2.

Next action: explain the DOPA file with a worked row example and basic geographic cleaning, then convert it to a validated population table without mixing parent/child geography. Do not alter the geographic audit until that explanation is given. Update this same plan after each completed step with outputs, limitations, decisions and the next action. Never mark an analysis complete merely because a source or dashboard exists.
