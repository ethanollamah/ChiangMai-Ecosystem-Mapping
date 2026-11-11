# Chiang Mai geographical analysis — read this first

Packed: 10 November 2026, 20:17 +08
Project: Thrive TSA Partnerships — Chiang Mai geographical analysis
Purpose of this pack: continue the work in ChatGPT (or another agent) without the Cursor workspace.

If you are ChatGPT, treat this file as the briefing. Then open `01_Chiang_Mai_Geographical_Analysis_Plan.md`. Steps 1–6 are on disk. The 29 October geographic audit was **not edited**. Level 2C is two unranked comparisons in `outputs/step6/`. Do not collapse them into one score. Partner validation is deferred. The questions in the section below are for TSA and district partners later. Do not answer them from these files.

To refresh this pack after further Cursor work, run `python scripts/build_chatgpt_handoff.py`. It overwrites `export/chatgpt_handoff/` and `export/Chiang_Mai_ChatGPT_Handoff.zip`, and copies the zip to the TSA Mapping folder.

## How to use this pack in ChatGPT

1. Create or open the ChatGPT project “Thrive TSA Partnerships” (or a new project).
2. Upload **either** the zip `Chiang_Mai_ChatGPT_Handoff.zip` **or** the files in this folder. Prefer the zip if the file-count limit is tight.
3. Pin or attach `00_READ_ME_FIRST.md` and `01_Chiang_Mai_Geographical_Analysis_Plan.md`.
4. If Excel uploads fail, use `02_classification_FINAL_checkbox.json` plus the CSVs. The xlsx files are still the source of truth.
5. Verify checksums in `FILE_MANIFEST.csv` if a file looks truncated.

Relative paths only. Do not depend on `/Users/ethan/...` machine paths.

## Confirmed decisions (do not reopen unless the user does)

- Chiang Mai Province only. Note boundary effects; do not silently add providers outside the province.
- Classification source: `landscape mapping (FINAL).xlsx`, sheet `CM Mapping (checkbox)`. Extracted copy: `02_classification_FINAL_checkbox.json`. Includes advocacy-for-family-placement ticks for ZOE Foundation Thailand and Daughters Rising / Chai Lai Orchid Foundation.
- Do not substitute older workbooks, the SharePoint-linked `CM mapping 2.0 - updated.xlsx`, or the Supply Side Scan.
- Core analysis universe: existing mapped child-welfare organisations plus relevant public welfare/reception facilities. Private childcare is a **separate supplementary layer**, not the core nonprofit count.
- Juvenile-justice facilities stay separately labelled.
- Pilot purpose: family-support/prevention and educational re-engagement through TSA-led partnerships — not new residential-care sites.
- Keep observations, calculations, assumptions and recommendations visibly separate.
- Do not treat few mapped providers as unmet need, or proximity as access.
- No causal claims about family separation from geographic associations alone.
- Exact coordinates only for suitable publicly disclosed sites. Never infer confidential residences.
- Do not use `data.go.th/dataset/69_48`.
- Do not bypass IP blocks, rotate proxies, or spoof identity.
- Do not contact facilities without authorisation.
- Preserve the source workbook’s visual design if later edits are requested; build analysis tables separately.
- Repeat organisations across My Maps stage layers, but do not count repeats as extra organisations or sites.

## What is done

### Classification
53 organisation rows from FINAL checkbox. 39 have at least one tick. 14 have no ticks (including INEB, OneSky, Care for Children, Interact Asia, and several family-style names). The checkbox sheet still contains external-link formulas to SharePoint; analysis uses the **cached values stored in FINAL**.

### Geographic audit and Step 2 cleaning
Raw file: `04_Chiang_Mai_Organisation_Location_Audit.xlsx` (29 October 2026). **Do not edit it.** Dated copy plus analysis tables: `outputs/step2/`. 72 sites (68 audit + 4 public directory), 57 organisations. Level 1 family-support numerators: **53 organisations**, **57 physical sites**, **12 nearest-neighbour points**. Chiang Rai CM-060/061/062 excluded. Juvenile CM-072 geocoded (18.889962, 98.965311) and **not** in those counts. Don Kaeo CM-069/070 share CM-071 and are not extra points. 17 exact addresses had no Nominatim house hit; they stay sites without points. Non-district phrases are non-joins. Wiang Pa Pao is Chiang Rai.

### DOPA December 2025
Schema and registration geography are validated. Use `outputs/step1/dopa_district_totals.csv` as district denominators. **Do not** use อำเภอ-labelled rows as whole-district totals (they are residuals). Worked example: `outputs/step1/dopa_worked_example.csv`. Proposed child denominator: 279,076 Thai nationals aged 0–17 on ordinary house registration. Non-Thai 156,898 is all-age only. Registered is not resident.

### DOLE Zero Dropout
Public aggregate endpoint pulled once per area on 10 November 2026, no retries:
- Province 50: 27,140 records
- 25 districts 5001–5025; district totals **sum to 27,140**
- Ten screening categories are mutually exclusive and also sum to each area total
- Dashboard field `survey.notfound` (186) is **deceased**, not “home not found”
- Home not found = screening `หาบ้านไม่พบ` (4,385)
- Age bands sum to 28,377 > 27,140 — do not add them as unique children
- Do not treat all records as current dropouts

Files: `outputs/step1/dole_zero_dropout_by_district.csv`, `dole_glossary.csv`, `raw/dole/`.

### Private childcare directory
PDF dated 16 October 2025 (`สถานรับเลี้ยงเด็กเอกชน`). Extracted 148 numbered rows. The PDF’s own summary says 149 operating facilities; that mismatch is in the source. Thai “า” is often rendered as “ำ” in the PDF font; extraction applies a documented correction. Row 147 district overflow “งเชียงดาว” is treated as เชียงดาว.

### Accommodation check (public web, 10 November 2026)
Every numbered row has a logged result. Licence category is **not** the operating model.

| evidenced_model | n |
|---|---|
| day_only | 68 |
| unresolved | 55 |
| identity_not_confirmed | 24 |
| occasional_overnight_or_respite | 1 |
| recurring_boarding / long_term_residential / mixed_provision | 0 |

The one overnight flag: row 35, นิวซุปเปอร์คิดส์เนอสเซอรี่ / New Superkids Nursery, ฟ้าฮ่าม. Facebook-mirror copy claims 24-hour opening and an overnight-stay hashtag. Other directories list daytime hours. Medium confidence. Partner verification required.

Limitations (must stay attached to any use of these counts):
- Most day-only calls rest on third-party directory hours, not the facility’s own site.
- Facebook pages were largely unread (timeouts or name-only, no URL).
- Overnight-keyword searches were not run for every row.
- Lack of a keyword is not proof of absence.
- This does **not** establish that residential provision is absent.
- 80 rows are on the watch list (`outputs/step1/accommodation_unresolved_cases.csv`).
- Do not add ordinary daycare to the core charitable count.

Related leads, **not** added to the core count: Mission Power Foundation dormitory for hill-tribe secondary students associated with Hana Christian (row 128); San Phi Suea municipality notice of applicant private welfare home มูลนิธิบ้านร่มไม้ชายคา. A separate private residential-welfare-home directory is still not confirmed to exist.

### Public children's homes (2025 directory)
Four sites, all Mae Rim, added in Step 2 as CM-069–072. Two welfare homes and one reception shelter on the Don Kaeo campus (63/1, 63/3, 63/4); juvenile observation/protection centre at Mae Sa. None were in the 29 October audit. Juvenile-justice stays separately labelled.

### Level 1 concentration / dispersion
Tables in `outputs/step3/`. Mapped sample, not a census. Mueang 15 sites, San Sai 9, Doi Saket 8; 12 of 25 districts have zero mapped eligible sites (not proof of absence). NN among 12 public house points: min 0.875 km, median 2.78 km, max 6.18 km; descriptive only, no clustering test. FINAL stage counts: short-term 27 orgs, residential 24, kinship 0. Audit stages that disagree with FINAL are in `stage_source_disagreement.csv` and are not counted.

### Level 2A presence versus population and need
Tables in `outputs/step4/`. Rate denominator: 279,076 registered Thai children aged 0–17 (DOPA Dec 2025). 49 district-joined Level 1 sites. Offices, delivery sites and former offices are separate numerators. Doi Saket 6.15 delivery sites per 10,000 is seven protected district approximations with no family-support tick. San Sai 3.70 is the highest family-support presence rate (8 sites). DOLE and TPMAP are separate columns: Fang 1,326 home-not-found; Omkoi 631 consented; Mae Chaem 8,309 target-poor people. `signals_for_closer_look.csv` is a list of rules, not a score. Zero mapped delivery is not absence of provision. Presence is not coverage.

### Level 2B design decisions and why

The user accepted this design on 10 November 2026. The same four decisions are in `outputs/step5/design_decisions.csv`.

**Origins are district centroids.** There is no settlement layer and no child-location file. The optional health-office population workbook was IP-blocked, and DOPA December 2025 counts registered people without coordinates. District is already the geography used for DOPA, DOLE and TPMAP, so the travel description joins the same units as the need tables. A centroid is the centre of the district polygon. It is an administrative proxy. It is not a home, a village, or the place where the district's own services sit. Because of that, the results are travel from the proxy. They are not a percentage of children who live within 30 or 60 minutes of a site. Polygons are the simplified geoBoundaries Thailand districts (Royal Thai Survey Department / OCHA, year represented 2019). All 25 centroids fall inside their own polygons. Li, a Lamphun district, had a centroid inside the simplified Chiang Mai province outline and was left out because it is not one of the 25 Chiang Mai districts.

**Destinations are eight exact public sites.** A route needs a public house or building coordinate. The eight are Thai Freedom House (CM-004), IMEMF (CM-010), the Salvation Army (CM-022), Projects for Asia (CM-026), Wat Don Chan (CM-029), Dulabhatorn (CM-030), Radion (CM-032) and the Mae Rim children's and family shelter (CM-071). Each one is a current delivery site or a mixed office-and-delivery site, and each one is family-support relevant. Protected homes, undisclosed addresses and district-level approximations have no defensible door, so they are not destinations. Pure offices and the two former Mueang offices are organisation addresses. The juvenile centre stays in its own label and off this route.

**The primary mode is a private vehicle on a free road network. Walking is the sensitivity.** The project does not use a paid routing service. The primary times come from the FOSSGIS OpenStreetMap car profile (`routing.openstreetmap.de`), retrieved 10 November 2026. Motorbikes use the same roads, but the speed model is a car profile: it is not measured Chiang Mai traffic and it is not a motorbike profile. Walking the same pairs, on the FOSSGIS foot profile, tests what happens when a vehicle is not available. A second engine, Valhalla auto, checks whether the car times are an artefact of one router. Songthaew and bus timetables are not in the source set, so shared transport is not given a time.

**Thirty and sixty minutes are labels for reading the spread, not a definition of access.** No one has agreed a cutoff that means a family can reach a service. The report gives the minimum, median, mean and maximum, and counts how many district centroids fall at or under 30 minutes and at or under 60 minutes. Those counts are counts of centroids. They are not weighted by the 279,076 registered children.

### Level 2B results

All 25 centroids have a private-vehicle route. Primary times run from 3.9 minutes (Mueang) to 215 minutes (Omkoi, 187 km). The median is 84.5 minutes. Six centroids are at or under 30 minutes on this engine, and eleven are at or under 60. Road distance is between 1.11 and 2.05 times the straight line.

That 30-minute count moves when the engine changes. On the 16 pairs Valhalla could route, its car time is slower by a median of 16 minutes. Only Mueang and Saraphi are under 30 minutes on both engines. Nine remote centroids did not snap to Valhalla's graph; their FOSSGIS times stay the primary estimate.

San Sai shows why the centroid must not be read as the service. Its centroid, in the north of the district, is 34 minutes from the Mae Rim shelter. San Sai's own exact public sites are 36 to 40 minutes from that same point. Mae Rim's centroid is 21 minutes from the Don Kaeo shelter in Mae Rim.

From the Level 2A closer-look districts, primary centroid times are Chom Thong 86 minutes, Fang 135 minutes, Mae Chaem 186 minutes and Omkoi 215 minutes. Walking the same pairs is a different kind of journey: about 29 minutes from the Mueang centroid, and about 40 hours from the Omkoi centroid. For eight districts the nearest site on foot is a different site from the nearest site by car. Fares, eligibility and shared-transport schedules are listed in `gaps_not_modelled.csv` and were not turned into numbers.

### Level 2C — two unranked comparisons

On 10 November 2026 the user chose both purposes, kept separate: family-support/prevention partnerships, and educational re-engagement. There is no weighted score and no priority order. Districts are listed in DOPA code order.

`comparison_family_support.csv` puts family-support sites, TPMAP target-poor people, registered children, and centroid travel time in separate columns. `comparison_educational_reengagement.csv` keeps each DOLE flag in its own column. Home-not-found is an unlocated-record signal. Consented, help-wanted and never-studied are not added to it or to each other. After-school sites are Kid's Ark: three in Mae Ai, one in San Sai. Vineyard Methodist School in San Sai is recorded as a school campus. Road time to an education site was not estimated.

The rule-hit files repeat the Level 2A cuts as yes/no evidence. They are not a ranking. Fang is the large home-not-found district (1,326). Omkoi is the large contacted district (631 consented, 173 help-wanted, 112 never-studied) with home-not-found at 20. Mae Chaem (8,309 target-poor) and Chom Thong (3,755) have no mapped family-support site. Doi Saket's seven family-style homes are approximated and are outside the family-support count. Mae Ai has after-school sites and is also above the home-not-found and consented cuts.

Questions for partners and provisional outcomes to monitor are in `local_validation_questions.csv` and `provisional_outcomes.csv`. The questions are repeated in the next section so a future reader highlights them for partners. The user could not answer them on 10 November 2026.

### TPMAP 2569
District evidence table with glossary. Filter: 5 MPI dimensions, welfare card = มีบัตร. Underlying sources stated on the page: JPT 2568 + welfare card 2565. Mueang (5001) live page on 10 November 2026 showed **0** target-poor people out of **52,312** surveyed — matching the CSV. That is the only zero district. Do not read it as no need.

## Partner validation — ask later

Highlight this list for TSA and district partners when validation is possible. On 10 November 2026 the user could not provide these answers. Do not fill them in from the maps, DOPA, DOLE, or TPMAP tables. Do not contact facilities unless the user authorises it. There is no analysis step after this list that can run before the answers exist. When answers arrive, record what partners confirm, what they contradict, and what they cannot say. Keep the family-support comparison and the educational re-engagement comparison separate.

Full wording and the reason for each question: `outputs/step6/local_validation_questions.csv`.

Ask partners:

1. Which providers are working in a district but absent from the mapped sample?
2. What languages do families use there, and can a TSA partner work in those languages?
3. Can a family make the trip without a private vehicle, and what does it cost?
4. Does a mapped organisation have capacity to host a partnership or take a referral?
5. For family support: are the TPMAP target-poor households a group a prevention partnership could meet, or a feature of who the survey counted?
6. For educational re-engagement: when a DOLE record is home-not-found, is the gap a missing address, a move, or a child outside school?
7. For educational re-engagement: among records that consented, how many want help, and is that help about school re-entry?

## What is not done

- Optional Chiang Mai health-office population Excel was IP-blocked; proceed with DOPA.
- Partner validation is deferred. The seven questions above are unanswered. Do not invent the answers.
- 80 private-childcare rows remain on the accommodation watch list; partner verification still required.
- 17 exact public addresses did not resolve to a Nominatim house/building point.

## Next action (do this next)

paused for partner validation. When TSA or district partners can answer, highlight the seven questions in the handoff briefing. Then update this plan with what they confirm, what they contradict, and what remains unknown. Keep the two comparisons separate. Do not invent partner answers from the tables already on disk. Never mark an analysis complete merely because a source or dashboard exists.

Update `01_Chiang_Mai_Geographical_Analysis_Plan.md` after each completed step. Never mark an analysis complete merely because a source exists.

## File index

| File | Use |
|---|---|
| `01_Chiang_Mai_Geographical_Analysis_Plan.md` | Living working plan. Update after each completed step. |
| `02_classification_FINAL_checkbox.json` | Seven-stage ticks extracted from landscape mapping (FINAL).xlsx / CM Mapping (checkbox). |
| `03_landscape_mapping_FINAL.xlsx` | Confirmed classification workbook. Do not substitute an older copy. |
| `04_Chiang_Mai_Organisation_Location_Audit.xlsx` | 29 Oct 2026 geographic audit. Starting point; not yet cleaned. |
| `outputs/step1/accommodation_register.csv` | Merged overnight/boarding check for all 148 private-childcare rows. |
| `outputs/step1/accommodation_register.json` | Same register with evidence URLs and search logs. |
| `outputs/step1/accommodation_unresolved_cases.csv` | Watch list: unresolved, identity_not_confirmed, and the overnight flag. |
| `outputs/step1/dole_glossary.csv` | Thai–English glossary of DOLE dashboard labels. |
| `outputs/step1/dole_zero_dropout_by_district.csv` | DOLE Zero Dropout province + 25 districts. |
| `outputs/step1/dopa_district_totals.csv` | Whole-district denominators (residual + assigned municipalities). |
| `outputs/step1/dopa_municipality_assignment.csv` | Which municipality was assigned to which district. |
| `outputs/step1/dopa_province_summary.csv` | Province totals and child-denominator coverage note. |
| `outputs/step1/dopa_rows.csv` | Every DOPA registration row with geography slice and age bands. Do not sum parent+child. |
| `outputs/step1/dopa_schema.csv` | Official DOPA field meanings. |
| `outputs/step1/dopa_validation.json` | Identity and geography reconciliation checks. |
| `outputs/step1/dopa_worked_example.csv` | Mueang / Nakhon / Chang Phueak worked example rows. |
| `outputs/step1/private_childcare_directory_2025.csv` | 148 numbered rows from the 16 Oct 2025 private childcare PDF. |
| `outputs/step1/public_childrens_homes_2025.csv` | Four public sites from the 2025 directory: two welfare homes, one reception shelter, one juvenile centre. Juvenile stays separately labelled. |
| `outputs/step1/tpmap_2569_mueang_5001.png` | Screenshot of https://www.tpmap.in.th/2569/5001 on 10 Nov 2026: 0 target poor / 52,312 surveyed. |
| `outputs/step1/tpmap_capture_log.json` | Live-page check of Mueang 5001 and how to use the TPMAP table. |
| `outputs/step1/tpmap_district_evidence.csv` | 2569 district TPMAP headline measures with provenance. Mueang zeros are live-page confirmed. |
| `outputs/step1/tpmap_glossary.csv` | TPMAP column and 38-indicator labels from the official Plan 13 data dictionary. |
| `outputs/step2/change_log.csv` | Every district, geocode and public-directory addition. Raw 29 Oct file was not edited. |
| `outputs/step2/cleaning_summary.json` | Step 2 counts and eligibility rule. |
| `outputs/step2/district_crosswalk.csv` | Audit district labels onto DOPA 5001–5025. Non-district phrases are non-joins. Wiang Pa Pao is Chiang Rai. |
| `outputs/step2/geocode_cache.json` | Nominatim response cache. Reproducible geocodes; not a finding. |
| `outputs/step2/organisations.csv` | Step 2 organisations (57). level1_org_eligible is the unique-org numerator. |
| `outputs/step2/site_stages.csv` | Organisation-level stage evidence copied to sites. FINAL checkbox remains the classification source. |
| `outputs/step2/sites.csv` | Step 2 cleaned sites (72). Use level1_*_eligible flags; do not treat every row as a point. |
| `outputs/step2/source_copy/Chiang_Mai_Organisation_Location_Audit_2026-10-29.xlsx` | Dated copy of the 29 Oct audit. The raw snapshot is also packed as 04_. |
| `outputs/step3/counts_overall.csv` | Level 1 numerators: 53 orgs, 57 sites, 12 points, with definitions. |
| `outputs/step3/level1_points.csv` | The 12 NN points plus the juvenile centre (in_nearest_neighbour=no). |
| `outputs/step3/level1_points.geojson` | Same points as GeoJSON. |
| `outputs/step3/level1_points.svg` | Offline scatter of the public points. Linear lon/lat, not a map projection. |
| `outputs/step3/level1_summary.json` | Level 1 headline counts, NN summary and limitations. |
| `outputs/step3/nearest_neighbour.csv` | Descriptive great-circle NN among 12 public house/building points. Not a clustering test. |
| `outputs/step3/org_stage_overlap.csv` | How many FINAL stages each mapped organisation has. |
| `outputs/step3/orgs_by_stage.csv` | Unique organisations by FINAL stage. Do not add across stages. |
| `outputs/step3/sites_by_district.csv` | All 25 DOPA districts including zeros, plus a non-join row. Zero mapped is not absent. |
| `outputs/step3/sites_by_stage.csv` | Eligible sites by FINAL stage of the owning organisation. |
| `outputs/step3/stage_source_disagreement.csv` | Audit Applicable_Stages that disagree with FINAL; not used in Level 1 stage counts. |
| `outputs/step4/district_presence.csv` | Level 2A: one row per DOPA district. Presence per 10,000 registered Thai children 0–17. DOLE and TPMAP stay in separate columns. |
| `outputs/step4/level2a_summary.json` | Level 2A thresholds, headline rates, and limitations. |
| `outputs/step4/measure_definitions.csv` | Numerator, denominator, and what must not be added. |
| `outputs/step4/signals_for_closer_look.csv` | Separate rule hits. Not a priority score and not an unmet-need ranking. |
| `outputs/step4/site_presence_role.csv` | Each Level 1 site as office, delivery, or mixed. Former/closed flagged. |
| `outputs/step5/design_decisions.csv` | Level 2B origin, destination, mode and threshold, each with the reason it was chosen. |
| `outputs/step5/destinations.csv` | The eight exact public delivery or mixed sites used as route destinations. |
| `outputs/step5/district_access.csv` | Private-vehicle time and distance from each centroid, walking sensitivity, and Valhalla check. |
| `outputs/step5/district_centroids.csv` | 25 district centroids used as administrative proxies. Not children's homes. |
| `outputs/step5/gaps_not_modelled.csv` | Affordability, eligibility and shared transport were not given numbers. |
| `outputs/step5/level2b_summary.json` | Level 2B spread of times, descriptive bins, and engine comparison. |
| `outputs/step5/routing_cache.json` | Cached FOSSGIS and Valhalla responses. Reproducible routes; not a finding. |
| `outputs/step6/comparison_educational_reengagement.csv` | Unranked educational re-engagement comparison. DOLE flags stay in separate columns. |
| `outputs/step6/comparison_family_support.csv` | Unranked family-support comparison, DOPA code order. Not a score. |
| `outputs/step6/education_rule_hits.csv` | Separate yes/no rule hits for DOLE flags. Not a rank. |
| `outputs/step6/family_support_rule_hits.csv` | Separate yes/no rule hits for family support. Not a rank. |
| `outputs/step6/level2c_summary.json` | Level 2C decision, cuts, and uncertainties. |
| `outputs/step6/local_validation_questions.csv` | Questions for TSA and local partners. Not measured answers. |
| `outputs/step6/provisional_outcomes.csv` | Outcomes to monitor if a partnership proceeds. Not targets. |
| `FILE_MANIFEST.csv` | SHA-256 for every packed file except `00_READ_ME_FIRST.md` |
| `00_READ_ME_FIRST.md` | This briefing |

## Intentionally omitted (not required to continue)

- Supply Side Scan and other-country workbooks
- Google My Maps layer zip (rebuild from the audit if needed)
- OpenStreetMap / road network
- ChatGPT project mirror under `~/.codex/.chatgpt-projects/…` (treat as read-only if you ever see it)
- Intermediate accommodation batch JSON (merged into the accommodation register)

## Safeguarding

Do not contact listed facilities. Do not publish or infer children’s identities or confidential residences. Operator names, phones and addresses in the directory are copied from a public licensing PDF; keep them in analysis files, not in public write-ups, unless the user asks.
