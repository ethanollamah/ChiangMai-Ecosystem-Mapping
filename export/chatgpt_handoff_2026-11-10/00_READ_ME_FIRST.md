# Chiang Mai Step 1 handoff — read this first

Packed: 10 November 2026 (Singapore time)
Project: Thrive TSA Partnerships — Chiang Mai geographical analysis
Purpose of this pack: continue the work in ChatGPT (or another agent) without the Cursor workspace.

If you are ChatGPT, treat this file as the briefing. Then open `01_Chiang_Mai_Geographical_Analysis_Plan.md`. Do not start Level 1 mapping or edit the geographic audit until the DOPA file has been explained to the user with a worked row example.

## How to use this pack in ChatGPT

1. Create or open the ChatGPT project “Thrive TSA Partnerships” (or a new project).
2. Upload **either** the zip `Chiang_Mai_Step1_ChatGPT_Handoff_2026-11-10.zip` **or** the files in this folder. Prefer the zip if the file-count limit is tight.
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

### Geographic audit (starting point only)
`04_Chiang_Mai_Organisation_Location_Audit.xlsx` (29 October 2026): 53 organisations, 68 master location records, 36 exact or named public records. Not yet cleaned or boundary-validated.

### DOLE Zero Dropout
Public aggregate endpoint pulled once per area on 10 November 2026, no retries:
- Province 50: 27,140 records
- 25 districts 5001–5025; district totals **sum to 27,140**
- Ten screening categories are mutually exclusive and also sum to each area total
- Dashboard field `survey.notfound` (186) is **deceased**, not “home not found”
- Home not found = screening `หาบ้านไม่พบ` (4,385)
- Age bands sum to 28,377 > 27,140 — do not add them as unique children
- Do not treat all records as current dropouts

Files: `05_…csv`, `06_…csv`, `07_…json`, `17_dole_raw_json/`.

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
- 80 rows are on the watch list (`10_accommodation_unresolved_cases.csv`).
- Do not add ordinary daycare to the core charitable count.

Related leads, **not** added to the core count: Mission Power Foundation dormitory for hill-tribe secondary students associated with Hana Christian (row 128); San Phi Suea municipality notice of applicant private welfare home มูลนิธิบ้านร่มไม้ชายคา. A separate private residential-welfare-home directory is still not confirmed to exist.

## What is not done

- DOPA December 2025 file is in the pack as raw text only. Schema and geography are **not** validated. Do not use district-labelled rows as denominators until parent/child/municipality geography is reconciled.
- Public children’s-homes PDF is included but **not** extracted to a table.
- TPMAP CSVs are included; indicator labels are not glossed; Mueang (5001) poverty file is all zeros and must be checked on the live page.
- Optional Chiang Mai health-office population Excel was IP-blocked; proceed with DOPA.
- Geographic audit not yet cleaned (stable IDs, duplicates, boundary check, precision flags).
- Level 1 concentration/dispersion not started.
- Level 2A–2C not started.
- Travel mode and accessibility thresholds remain undecided.

## Next action (do this next)

1. Explain the DOPA file to the user with a **small worked row example**.
2. Explain basic geographic data cleaning **before** altering the audit.
3. Only then convert DOPA into a validated population table.
4. Extract the public directory; capture TPMAP with provenance.
5. Then clean the geographic base and do Level 1 before Level 2.

Update `01_Chiang_Mai_Geographical_Analysis_Plan.md` after each completed step. Never mark an analysis complete merely because a source exists.

## File index

| File | Use |
|---|---|
| `00_READ_ME_FIRST.md` | This briefing |
| `01_Chiang_Mai_Geographical_Analysis_Plan.md` | Living working plan |
| `02_classification_FINAL_checkbox.json` | 53 organisations × seven stages |
| `03_landscape_mapping_FINAL.xlsx` | Classification workbook |
| `04_Chiang_Mai_Organisation_Location_Audit.xlsx` | Location starting point |
| `05_dole_zero_dropout_by_district.csv` | DOLE area table |
| `06_dole_glossary.csv` | DOLE Thai–English labels |
| `07_dole_acquisition_log.json` | Retrieval provenance |
| `08_private_childcare_directory_2025.csv` | Extracted private directory |
| `09_accommodation_register.csv` | 148-row check (use this for tables) |
| `10_accommodation_unresolved_cases.csv` | Partner-verification list |
| `11_accommodation_register.json` | Same register with URLs |
| `12_…Private…2025.pdf` | Private directory source |
| `13_…Public…2025.pdf` | Public homes source |
| `14_dopa_2025_12_chiang_mai.txt` | Raw population |
| `15` / `16` TPMAP CSVs | District poverty/common indicators |
| `17_dole_raw_json/` | Unflattened DOLE JSON |
| `scripts/` | How the tables were built |
| `FILE_MANIFEST.csv` | SHA-256 for every packed file |

## Intentionally omitted (not required to continue)

- Supply Side Scan and other-country workbooks
- Google My Maps layer zip (rebuild from the audit if needed)
- OpenStreetMap / road network
- ChatGPT project mirror under `~/.codex/.chatgpt-projects/…` (treat as read-only if you ever see it)
- Intermediate accommodation batch JSON (merged into files 09–11)

## Safeguarding

Do not contact listed facilities. Do not publish or infer children’s identities or confidential residences. Operator names, phones and addresses in the directory are copied from a public licensing PDF; keep them in analysis files, not in public write-ups, unless the user asks.
