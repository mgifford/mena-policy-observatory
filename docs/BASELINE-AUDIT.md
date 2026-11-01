# Baseline audit: MENA Policy Observatory

**Phase:** 0 (repository reconnaissance, documentation only)  
**Audit date:** 2026-11-01  
**Audit branch:** `docs/baseline-audit`, created from `docs/agent-handoff` at `4f869c7`  
**Default branch at audit time:** `main` at `ec05358`  
**Published site inspected:** <https://mgifford.github.io/mena-policy-observatory/mena/en/>  
**Scope:** repository structure, build, data model, English/Arabic output, provenance handling, Axiom scaffolds, and automated accessibility tests.  
**Out of scope:** new legal research, verification of legal effect, new translations, and changes to policy claims. No legal interpretation is added by this document.

> This audit records what the repository currently contains and what its own build produces. It does not verify any legal source, legal status, translation, or country coverage. A source being linked is not evidence that an obligation exists, is in force, or applies to any organisation.

---

## 1. Executive summary

The repository is a working, static, bilingual **catalogue** with a reproducible build and a live deployment. It is not yet the evidence-based observatory described in `AGENTS.md`.

Confirmed strengths:

- The build is deterministic: rebuilding produced **zero Git diff** against committed `dist/`.
- The published site is **byte-identical** to the committed `dist/` for the four pages sampled.
- All 17 generated pages have one `<h1>` and valid `lang`/`dir`; the two index pages have captioned tables; all 17 have **zero axe-core violations** under the default rule set.
- Skip links work on all 16 locale pages; the root page is the single exception.
- No horizontal page overflow was detected at 320 CSS px on any of the 17 pages.
- No broken local links were found across all 17 pages.
- Dynamic text is passed through `html.escape(..., quote=True)` throughout the renderer; no client-side JavaScript, no runtime service, and no obvious HTML-injection path was found.
- The Axiom scaffolds are honestly marked non-executable, with empty `rules: []` arrays and warning comments.

Confirmed shortcomings that block the stated mission:

1. **Arabic is an interface shell, not an equal-priority experience.** Every Arabic record page renders English titles, authorities, scopes, notes, and raw machine tokens (`not_legally_assessed`, `national_policy`) without `lang`/`dir` marking. No policy record has an Arabic title, summary, or scope.
2. **Page identity is broken.** All 9 English pages share the title `MENA Policy Observatory`; all 8 Arabic pages share one Arabic title. Record pages are indistinguishable in browser tabs, history, and screen-reader page announcements (WCAG 2.4.2).
3. **The root page skip link does not work.** Focus remains on `<body>` after activation because `dist/index.html` has no focusable target.
4. **Primary-source artifacts are offered as raw Markdown/JSON/YAML downloads**, not rendered as accessible HTML with clause locators, language, review state, and related records — contrary to `AGENTS.md`.
5. **The published data model is record-level only.** There is no active provision model, no source register, no stable provision-to-source link, no capture timestamp or checksum, and no translation provenance. A second, unrendered provision tree exists for 4 of 7 records and is not validated or published.
6. **The validation layer is largely decorative.** The JSON Schema is unused and every record violates it (`additionalProperties: false` plus six undeclared fields; `source_identified` is not an allowed status). `validate.py` checks file existence and a URL prefix, not legal or provenance semantics.
7. **The automated accessibility gate covers 2 of 17 pages and 4 assertions.** `ACCESSIBILITY.md` claims checks that are not implemented (detail pages, 320 px overflow, heading order, scope semantics). Green CI therefore does not support the accessibility claims made in the repository.
8. **Provenance labels overstate what is held.** Four `SOURCE.md` files have a heading `Source text (verified, short excerpt)`; two of those say `Not transcribed yet` in the body. None records a capture timestamp, checksum, reviewer, or exact page locator.

No fabricated quotations, reviewer identities, or checksums were found. The issue is unsupported labelling, not proven invention. Accuracy of the linked external sources and the correctness of the paraphrases were **not** verified in this phase.

**Verdict:** safe to keep publishing as a clearly labelled research catalogue; not yet safe to describe as clause-level, bilingual, or provenance-complete. Phase 1 should not broaden legal claims. The first implementation work should make the site truthful about what it holds, then fix page identity and Arabic parity, then build the provision/source model.

---

## 2. Repository inventory

Tracked files: **214**. Generated HTML pages: **17**. Committed generated files under `dist/`: **102**.

| Area | Paths | What it is | State |
|---|---|---|---|
| Instructions | `AGENTS.md`, `ACCESSIBILITY.md`, `CONTRIBUTING.md`, `MIGRATION.md`, `README.md`, `docs/WORKFLOW.md`, `prompts/00-audit.md` … `prompts/04-axiom.md` | Working rules, acceptance criteria, phase prompts | Present; some claims exceed implementation (see §5) |
| Build | `framework/build.py` (62 dense lines), `framework/site.css`, `framework/check_html.py`, `framework/validate.py` | Standard-library static generator and checks | Present; minimal |
| Axiom boundary | `framework/axiom/README.md` | Correct warning that scaffolds are not executable | Present |
| Region config | `regions/mena/region.json` | Languages, titles, five domain labels | Present; Arabic labels exist for region title and domains only |
| Record index | `regions/mena/data/policies.json` | 7 record summaries consumed by the build | Present; schema-invalid |
| Country list | `regions/mena/data/countries.json` | 21 jurisdictions, English names only | Present; stale counts (§4.3) |
| JSON Schema | `regions/mena/schemas/policy-record.schema.json` | Draft 2020-12 schema | Present but **never used**; points at a different repo ID |
| Policy artifacts | `regions/mena/policies/<id>/` — 7 dirs, 42 files | `SOURCE.md`, `PROVISIONS.md`, `INTERPRETATION.md`, `RELATED.md`, `manifest.json`, `rule.rulespec.yaml` | Present; two different manifest shapes |
| Provision layer | `regions/mena/domains/digital-accessibility/provisions/<id>/` — 4 dirs, 20 files | `ORIGINAL.md`, `record.json`, `INTERPRETATION.md`, `RELATED.md`, `rule.rulespec.yaml` | Present but **not read by build or validator**, not published |
| Domain notes | `regions/mena/domains/digital-accessibility/README.md`, `COMPARISON-QUESTIONS.md` | Research workflow and comparison questions | Present; no comparison data |
| Jurisdiction notes | `regions/mena/jurisdictions/*/RESEARCH.md` — 21 files | Per-country research stubs | Presence not audited for content |
| Example contract | `examples/research-packet.json` | Target research-packet shape | Present, placeholder only, not used or validated |
| Tests | `tests/accessibility.spec.mjs`, `playwright.config.mjs`, `package.json` | Playwright + axe | 4 tests over 2 landing pages |
| CI | `.github/workflows/pages.yml` | Validate → build → HTML lint → axe → Pages artifact/deploy | Present; no schema, link, title, or reflow checks |
| Generated | `dist/` (102 files) | 17 HTML pages, CSS, 84 raw artifact copies (7 records × 6 files × 2 locales) | Committed; currently in sync with build |

Absent, confirmed by search: `profiles.json`, `provisions.json`, `framework/validate_provisions.py`, `capture_source.py`, `docs/rules-as-code.md`, any Axiom explanatory page, `.gitignore`, committed `package-lock.json`, Python unit tests, positive/negative validator fixtures, a published accessibility statement, a methodology page, `sitemap.xml`, `robots.txt`, and a custom 404 page.

### 2.1 Corpus inventory (record level only)

All seven are digital-accessibility records. None is a verified legal determination.

| ID | Country | Instrument type (declared) | Legal-effect field | Record status | Manifest issues | Provision tree | Arabic fields |
|---|---|---|---|---|---|---|---|
| `ae-national-digital-accessibility` | AE | `national_policy` | `not_legally_assessed` | `source_verified` | 3 structured | yes (`*-scope-001`) | none |
| `sa-dga-web-accessibility-guide` | SA | `government_guideline` | `not_legally_assessed` | `source_verified` | 2 structured | yes (`*-scope-001`) | none |
| `qa-eaccessibility-2011` | QA | `national_policy` | `current_status_requires_confirmation` | `source_verified` | 2 structured | yes (`*-scope-001`) | none |
| `qa-eaccessibility-2025-upcoming` | QA | `draft_policy` | `draft_not_confirmed_in_force` | `identified` | 2 structured | yes (`*-scope-001`) | none |
| `ae-moe-accessibility` | AE | `agency_policy` | `not_legally_assessed` | `source_identified` | 3 ID-only | no | none |
| `ae-mof-accessibility` | AE | `agency_policy` | `not_legally_assessed` | `source_identified` | 2 ID-only | no | none |
| `sa-mep-accessibility` | SA | `agency_policy` | `not_legally_assessed` | `source_identified` | 3 ID-only | no | none |

Coverage is 3 of 21 listed jurisdictions for digital accessibility, and 0 for the other four advertised domains. The UI does not clearly distinguish “no record” from “not researched” at domain level; it does at country level.

---

## 3. Reproduced baseline

Environment: macOS, Python **3.15.2**, Node **24.22.0**, npm **11.19.1**, `@playwright/test` **1.64.1**, `@axe-core/playwright` **4.14.0** (caret ranges in `package.json`). CI pins Python 3.13 and Node 22.

| Command | Result | Notes |
|---|---|---|
| `python3 framework/validate.py` | exit 0 — `mena 7 records; language variants en,ar` | Checks IDs, `https://` prefix, four files, loose execution status |
| `python3 framework/build.py --region mena` | exit 0 — `Built mena: 7 research records` | `git status` immediately after: **0 changes** |
| `python3 framework/check_html.py` | exit 0 — `HTML accessibility structure checks: passed` | 17 pages; checks lang/dir, one `main`, one `h1`, skip href, `th[scope]` |
| `npm install --no-audit --no-fund` | 5 packages added | Created untracked `node_modules/`, `package-lock.json` |
| `npx playwright install chromium` | success | No browser cache existed before |
| `npm run test:a11y` | **4 passed** in 2.1 s | Only `/mena/en/` and `/mena/ar/`; axe + skip link |
| Published-site parity | **byte-identical** for `/`, `/mena/en/`, `/mena/ar/`, one record page | Live site matches committed `dist/` |

### 3.1 Independent probes beyond the repository tests

These were run against `dist/` served locally and are **not** committed as tests.

| Probe | Coverage | Result |
|---|---|---|
| axe-core default rule set | all 17 HTML pages | 0 violations |
| One `<h1>` and document `lang`/`dir` | all 17 pages | pass |
| Heading-level sequence | all 17 pages | no skipped levels |
| Unique `<title>` | all 17 pages | **fail**: 9 English pages share one title; 8 Arabic pages share one title |
| Skip link → focus `main` | all 17 pages | **1 fail**: `/index.html` leaves focus on `<body>` |
| 320 CSS px body overflow | all 17 pages | 0 overflow |
| Local `href` resolution | all 17 pages | 0 broken local links |
| Language switch from a record page | 1 English record | **loses context**: lands on `/mena/ar/`, not the Arabic counterpart record |
| Latin-script text outside `lang="en"` | Arabic index and record pages | **fail**: policy titles, standards, status codes, scopes, authority names, country names |
| Forced-colors + reduced-motion emulation | 4 representative pages | 0 axe violations; focused skip link has 3 px solid outline |
| 200% root font size and WCAG 1.4.12 text spacing | 4 representative pages | no page overflow |
| Raw artifact links | all record pages | 6 raw `.md`/`.json`/`.yaml` links per record page, duplicated under `/en/` and `/ar/` |

**Not tested in this phase:** NVDA/Firefox, VoiceOver/Safari, native Arabic linguistic review, real Windows High Contrast mode, browser zoom at 400% (only 320 px reflow and 200% text were approximated), touch-target measurement, numeric contrast ratios beyond UA system colours and axe, external link liveness, PDF/HTML source accessibility, and verification of any legal claim.

The probes are evidence of the current state, not proof of WCAG 2.2 AA conformance. Automated scans cannot decide 1.3.1, 1.3.2, 2.4.2, 3.1.2, or translation quality.

---

## 4. Verified defects

Severity reflects user impact and mission risk, not legal importance. Each item was observed in source code, generated HTML, or the live site.

### 4.1 Accessibility and page identity

| ID | Defect | Evidence | Impact | Reference |
|---|---|---|---|---|
| A11Y-01 | Every record page reuses the region title as `<title>` | `framework/build.py:49` passes `title` (region title) to `page()`; all 17 pages yield 2 unique titles | Users cannot distinguish records in tabs, history, bookmarks, or screen-reader “page loaded” announcements | WCAG 2.4.2 |
| A11Y-02 | Root skip link does not move focus | `dist/index.html` `<main id="main">` lacks `tabindex="-1"`; probe shows focus on `BODY` | Keyboard users gain nothing from the first control on the entry page | WCAG 2.4.1 |
| A11Y-03 | Arabic record pages contain unmarked English content | H1, authority, scope, notes, `instrument_type`, `legal_effect` rendered from English-only JSON without `lang`/`dir` | Screen readers pronounce English with Arabic rules; bidi punctuation and reading order degrade; users may believe the record is translated | WCAG 3.1.2, 1.3.2 |
| A11Y-04 | Arabic index cells contain English without `lang`/`dir` | Titles, standards, status codes, and all country names are English-only | Same as A11Y-03 across the main comparison surface | WCAG 3.1.2 |
| A11Y-05 | Raw enum tokens shown as user-facing status | `not_legally_assessed`, `not_implemented`, `national_policy`, `source_verified` appear verbatim | Jargon and underscores are read literally; the distinction between “not assessed”, “draft”, and “binding” is lost to non-specialists | WCAG 3.1.1 (content clarity), mission requirement 4 |
| A11Y-06 | Record pages have no breadcrumb or equivalent-page language switch | Header has only a language link to the locale home; probe from a record lands on `/mena/ar/` | Users lose their place when switching language; no wayfinding beyond “Back to comparison” | WCAG 3.2.3/3.2.4 consistency, Phase 1 requirement |
| A11Y-07 | Primary sources are raw file downloads, not accessible HTML | Six “Open source file” links per record to `.md`, `.json`, `.yaml`; no rendered headings, `lang`, locator, review state, or related records | Screen-reader and mobile users get undifferentiated plain text; contradicts `AGENTS.md` rendering requirement | WCAG 1.3.1, 3.1.2; AGENTS “Technology and authoring” |
| A11Y-08 | Policy table uses country code as the only row header | `framework/build.py:25` puts `scope="row"` on AE/SA/QA while the document title is a `<td>`; AE has 3 records, SA 2 | Row/column announcements associate cells with a repeated code, not the document; codes are unexpanded | WCAG 1.3.1 |
| A11Y-09 | Arabic link lacks `dir` on English pages | `framework/build.py:10` sets `lang="ar"` but no `dir="rtl"`; same for `lang="en"` on Arabic pages | Inline bidi isolation is weaker than it should be; especially visible with punctuation | bidi robustness requirement |
| A11Y-10 | No alternate-language relations in document head | No `<link rel="alternate" hreflang>`, canonical URL, or per-page description | Search engines and assistive tooling cannot discover the equivalent page; language switching is only visual | i18n requirement (not a WCAG failure by itself) |
| A11Y-11 | No visible focus treatment on `main` after skip | CSS styles `a:focus-visible` and `.table-scroll:focus-visible` only | Sighted keyboard users see focus disappear after using the skip link | WCAG 2.4.7 (low severity, arguable) |

### 4.2 Arabic / translation

| ID | Defect | Evidence | Impact |
|---|---|---|---|
| I18N-01 | Zero policy records have Arabic content | `policies.json` has no `title_ar`, `notes_ar`, `scope_ar`, or translation object; `build.py` prints the same English strings on both locales | “Equal-priority interfaces” is not met; Arabic pages imply translation that does not exist |
| I18N-02 | No translation status is displayed per field or record | Only `SOURCE.md` says “Not a certified Arabic translation”; the UI never shows it | Readers cannot tell whether Arabic is absent, machine-drafted, or reviewed |
| I18N-03 | Arabic artifacts are byte-identical English files | `dist/mena/ar/records/artifacts/**` duplicates the English Markdown/JSON/YAML | Doubles payload and suggests Arabic versions exist |
| I18N-04 | Country names are English-only | `countries.json` has no Arabic names; Arabic coverage table shows “Algeria”, “Egypt”, … | Mixed-language RTL table; proper nouns unmarked |
| I18N-05 | UI strings are embedded in Python conditionals | `framework/build.py:10–48` contains inline `'…' if ar else '…'` pairs | No translation catalogue, no key coverage check, easy to miss a string |
| I18N-06 | `<html lang="ar">` pages can have an English H1 | Arabic record `<h1>` is `National Digital Accessibility Policy` | Document language claim is correct for chrome but the main heading is foreign and unmarked |

### 4.3 Data, schema, and provenance

| ID | Defect | Evidence | Impact |
|---|---|---|---|
| DATA-01 | JSON Schema is never executed | No `jsonschema` import; `validate.py` hand-checks 4 files; `jsonschema` is not installed | Schema cannot catch regressions |
| DATA-02 | Every record violates its own schema | Schema has `additionalProperties: false`; all 7 records add `source_markdown`, `rulespec_path`, `interpretation_path`, `related_path`, `unresolved_interpretations`, `execution_status`. Three use `source_identified`, not in the `status` enum | The schema is misleading and cannot be enabled without a breaking migration |
| DATA-03 | Two incompatible manifest shapes | Four records: `policy_id`, `source_document`, `interpretation_issues`, `reviewed_on`. Three: `id`, `source_url`, `legal_review`, `ambiguities` (ID strings only) | Consumers cannot read manifests uniformly; agency ambiguity registers have no observations/severity in JSON |
| DATA-04 | `unresolved_interpretations` counts are unbound | Agencies declare 3/2/3 issues; their manifests contain only ID strings, so counts cannot be derived or validated | Counts can drift silently |
| DATA-05 | `countries.json` counts are stale | Declared vs actual: AE 1 vs 3, SA 1 vs 2, QA 2 vs 2; all `status: not_assessed` though records exist | Any future consumer trusting the field will under-report coverage |
| DATA-06 | Two parallel provision models, one dead | `regions/mena/policies/` (7, published) and `regions/mena/domains/.../provisions/` (4, never read); `build.py`/`validate.py` contain no reference to `domains/` | Duplication and drift; `ORIGINAL.md`/`record.json` are invisible to users and CI |
| DATA-07 | No clause-level locator | Provision `legal_text.source_section` is `null` in all 4; manifest `section` is free text such as “Technical annex, section 1” | No verifiable pointer from claim to text |
| DATA-08 | No capture evidence | No `retrieved_at`, `sha256`, `archived_url`, or file bytes; “source checksum” appears only in a transcription-protocol sentence | Cannot prove what was read, or detect publisher changes |
| DATA-09 | `reviewed_on` is not a date | `"2026-10-31 (metadata snapshot, not legal approval)"` in six records; agency manifests omit it | Not sortable or validatable; mixes date and disclaimer |
| DATA-10 | Source language is contradictory | `policies.json` `language: "en"`; `SOURCE.md` says “confirm authoritative original language”; provision `legal_text.original_language: "unverified"` | Conflates “language of the copy consulted” with “authoritative language” |
| DATA-11 | “Verified” heading without evidence | 4 `SOURCE.md` files: `## Source text (verified, short excerpt)`. Two say `Not transcribed yet`. None has locator, capture time, checksum, or reviewer | Overstates provenance; the exact failure mode `AGENTS.md` forbids |
| DATA-12 | No tri-state applicability | Provision `applicability: null`; `binding_status`/`legal_effect` are assessment labels, not applies/does-not-apply/indeterminate | Cannot represent “unknown” separately from “no obligation” at field level |
| DATA-13 | Relationships are prose or loosely typed | `RELATED.md` prose plus manifest `related` with free strings (`normative_annex`, `technical_standard`); no target source IDs or cycle checks | Cannot validate citations, amendments, supersession, or implementation links |
| DATA-14 | Translation provenance absent from records | `translation` appears only in `examples/research-packet.json`; no record carries translator, reviewer, source language, or status | Arabic drafts cannot be distinguished from reviewed translations |
| DATA-15 | No stable source ID namespace | IDs are record-level and provision-level (`*-scope-001`) but a source URL is the de facto key; no `source_id` | Re-publication or URL change breaks provenance |
| DATA-16 | Record-level `status` is overloaded | `source_verified` and `source_identified` mix source capture with review progress; no definitions | Readers and validators interpret the same field differently |

No evidence of fabricated quotations, reviewers, dates, or checksums was found. Accuracy of external sources and paraphrases was not assessed. The three agency `SOURCE.md` files that describe themselves as **paraphrased source records, not the original legal text** are honest and should remain the pattern for any record without a verified transcription.

### 4.4 Tooling, CI, and repository hygiene

| ID | Defect | Evidence | Impact |
|---|---|---|---|
| CI-01 | Accessibility tests cover 2 of 17 pages | `tests/accessibility.spec.mjs` loops only over locale indexes | Record pages, root, and artifact-linked pages unguarded |
| CI-02 | No test for page titles, language switching, 320 px reflow, link resolution, or mixed-language marking | Test file has 4 assertions total | All defects in §4.1 and §4.2 pass CI |
| CI-03 | `ACCESSIBILITY.md` claims gates that do not exist | Claims “all four regional/language landing pages and sample detail pages”, 320 px overflow test, heading and scope semantics | Repository documentation overstates evidence |
| CI-04 | HTML lint is shallow | `check_html.py:17–20` checks presence only; accepts a skip link that does not work; no heading order, title uniqueness, table caption, or inline language checks | False confidence |
| CI-05 | No `.gitignore` | `npm install` produced untracked `node_modules/`, `package-lock.json`, `test-results/` | Accidental commits; noisy reviews |
| CI-06 | No committed lockfile; CI uses `npm install` | `package.json` uses `^4.10.2` and `^1.56.1` | Non-reproducible test runs |
| CI-07 | No Python tests or validator fixtures | No `tests/*.py`, no fixtures | Validator regressions undetected; Phase 2 fixtures absent |
| CI-08 | Build and test are not coupled | `webServer` serves existing `dist/`; no rebuild before tests locally | Tests can pass against stale output |
| CI-09 | `dist/` is committed with no drift gate | 102 of 214 tracked files are generated; build is in sync today but CI does not prove it | Source/generated divergence risk; large diffs |
| CI-10 | `--region europe` is advertised but impossible | `build.py:58` allows `europe`; `regions/europe` does not exist. `MIGRATION.md` says “two region configs” | Misleading CLI/docs; runtime failure |
| CI-11 | Root page generation happens at import time | `build.py:61–62` writes `dist/index.html` even when building one region or importing the module | Side effect outside `build()`; hard to test |
| CI-12 | One unescaped dynamic value | `build.py:44` inserts `str(rec.get('unresolved_interpretations', 0))` without `esc()`; trusted JSON today | Defensive gap; validator should enforce integer type |

Not verified (hypotheses or external dependencies):

- Whether the five GitHub Actions versions used in `pages.yml` are all currently resolvable; CI history was not inspected.
- Whether every `source_url` still resolves or still hosts the cited document.
- Whether the two short excerpts match the publisher’s current text. This requires source-level review, which Phase 0 forbids.
- Whether “Regional additions” (Djibouti, Mauritania) matches the project’s intended MENA definition.
- Numeric contrast of `GrayText` table borders against `Canvas`; system colours adapt to user themes and were not measured.

---

## 5. Can the data model support clause-level legal provenance?

**No, not in its published form.** The current model is a catalogue of documents. The provision layer that could support clause-level provenance exists as a four-record prototype, is not validated, not built, not published, and covers only 4 of 7 records.

| `AGENTS.md` requirement | Current state | Verdict |
|---|---|---|
| Stable provision ID | 4 `record.json` IDs (`*-scope-001`); no registry; 3 records have none | Partial, duplicated |
| Jurisdiction | ISO code per record; English names in `countries.json` | Present, not localized |
| Authority | Free text | Present |
| Instrument type | Enum in schema and data; not validated | Present, weakly enforced |
| Publication / effective dates | No record-level dates; provision `effective_date: null` | Missing |
| Official URL | Present and `https://`-checked | Present; no archive |
| Source language | `language: "en"` vs `original_language: "unverified"` | Contradictory |
| Original text / excerpt | 2 short excerpts; 2 “Not transcribed yet”; 3 paraphrase-only agency records | Partial, mislabelled |
| Exact locator | `source_section: null`; free-text manifest sections | Missing |
| Capture timestamp and checksum | Absent (protocol text only) | Missing |
| Legal status | `legal_effect` labels, mostly not assessed; no evidence pointer | Present, unsupported |
| Relationships | Prose and loosely typed arrays; no source IDs | Partial, unvalidated |
| Interpretation alternatives | 4 structured manifests; 3 ID-only lists; prose registers | Inconsistent |
| Uncertainty | `severity`/`category`/`status` only in 4 manifests | Partial |
| Translation provenance | Only in the unused example packet | Missing |
| Tests | None; test fields only in the example packet | Missing |
| Review history | `reviewed_on` free text; no reviewer identity | Missing |
| Tri-state / indeterminate | `applicability: null`; no applies/does-not-apply/indeterminate enum | Missing at field level |
| Clause-level URLs | None; raw files only | Missing |

The existing wording is cautious in most places, which is a real asset. The gap is structural: there is nowhere to put a clause, a quotation, a capture hash, a translator, a reviewer, a relationship edge, or a tri-state outcome, and no validator to enforce any of them.

---

## 6. How the Axiom RuleSpec scaffolds are represented

- **11 scaffold files** exist: 7 under `regions/mena/policies/*/rule.rulespec.yaml` and 4 under `regions/mena/domains/.../provisions/*/rule.rulespec.yaml`.
- Every file declares `format: rulespec/v1`, a `module.title`, and **`rules: []`**. There is no substantive rule, no source binding, no `effective_from`, no engine version, no test case, and no compiled artefact.
- The 7 policy scaffolds carry comments listing unresolved interpretation IDs. The 4 provision scaffolds carry a shorter placeholder warning. Wording differs, so the two sets will drift.
- `framework/axiom/README.md` correctly states that the scaffolds are not executable and that a future encoder must compile, test, and legally review independently.
- The published UI mentions Axiom only as the label “Axiom RuleSpec scaffold” on a raw-file link. There is **no explanatory page** for Rules as Code, no `docs/rules-as-code.md`, and no page explaining engine versus human interpretation.
- There is no pinned Axiom engine, no `validate_provisions.py`, no compiler run, and no positive/negative/boundary/indeterminate test evidence. Whether `format: rulespec/v1` and the `module` shape match the current Axiom schema was **not** verified; this audit did not fetch or pin an engine.

**Assessment:** the representation is honest in intent (empty rules plus warnings) but duplicated, unvalidated, and not user-explicable. It must not be described as Axiom-conformant or executable. Phase 4’s blocker requirement is likely to apply to most or all seven records.

---

## 7. Proposed architecture improvements (incremental)

No framework change is justified. The standard-library generator remains adequate for a static catalogue of this size. Improve the model and the checks, not the stack.

1. **Keep one published model, not two.** Retire the orphan `domains/.../provisions/` tree by migrating its 4 records into the canonical data directory, or document explicitly why it is retained. Do not silently delete research.
2. **Separate the axes that are currently one `status` field:**
   - `source_capture_status`: `not_captured | url_only | captured`
   - `original_language_status`: `unverified | verified`
   - `translation_status`: `not_available | draft | reviewed`
   - `interpretation_status`: `not_started | open | reviewed`
   - `legal_effect_status`: `not_assessed | requires_confirmation | draft_not_in_force | binding_confirmed | nonbinding_confirmed`
   - `rule_status`: `not_encoded | scaffold | candidate | tested | reviewed`
   A single field must never imply progress on another axis.
3. **Add a source register and a provision register:**
   - `regions/mena/data/sources.json` with stable `source_id`, issuer, instrument title/type, official URL, archived URL, authoritative language, capture time, SHA-256 **only when bytes are stored**, reuse status, and version.
   - `regions/mena/data/provisions.json` with stable `provision_id`, `policy_id`, `source_id`, structured `locator` (`section`, `page`, `paragraph`, `quote`), original excerpt path, language, tri-state applicability, exceptions, interpretation issue IDs, related provision IDs, and per-field review state.
   - Keep the existing policy IDs and URLs unchanged; migration must be additive and covered by compatibility tests.
4. **Render Markdown as escaped, structured HTML at build time** using a restricted standard-library renderer (headings, lists, blockquotes, tables, emphasis, links). No raw HTML pass-through. Keep a secondary “download original file” link with media type and size. The published page must show source URL, locator, language, review state, and related records.
5. **Use structured relationships with validation:** `cites | amends | supersedes | transposes | implements | incorporates | guidance_for | related`, each with source and target IDs, plus cycle detection where a relation must be acyclic.
6. **Externalize UI strings** to `regions/mena/i18n/{en,ar}.json` (or a small Python catalogue) and fail the build on missing keys for any locale. Never generate English prose inside Arabic chrome; wrap foreign text in `lang` and `dir`.
7. **Publish only reviewed Arabic.** Where Arabic is absent, show an explicit localized “Arabic translation not available” status and the English text with `lang="en" dir="ltr"`. Do not machine-draft legal text into the Arabic UI without a recorded `draft` status and human review.
8. **Keep `dist/` either out of Git or guarded.** The publish workflow already uses an Actions artifact, so committing `dist/` is optional. If it stays, add a CI drift check (`build` then `git diff --exit-code dist`). Removing it is a separate, documented decision.
9. **Add a validator that fails closed:** schema, unique IDs, reference resolution, enum values, ISO dates, temporal consistency, file existence, orphan provisions, relationship cycles, excerpt attribution, translation status, and required reviewer fields. Prefer a small stdlib validator over a new dependency; if `jsonschema` is used, add a pinned dev requirement.
10. **Keep the Axiom boundary explicit:** one pinned engine commit, one contract, one blocked-or-candidate provision, and published test evidence. An empty `rules:` array is never “a rule”.

---

## 8. Accessible interface priorities

### P0 — truthfulness and equal access (before Phase 1 content expansion)

1. Unique, descriptive `<title>` per page, including record ID and document title (2.4.2).
2. Fix the root skip link target and keep it working on every page (2.4.1).
3. Mark every foreign-language span with `lang` and `dir`; stop rendering English record content inside Arabic pages without an explicit untranslated status (3.1.2, 1.3.2).
4. Replace raw enum tokens with human-readable, localized status labels. Never use colour alone; include text (1.3.1, 3.1.1).
5. Add consistent site navigation and breadcrumbs, and make the language switch land on the equivalent record (3.2.3, 3.2.4, 2.4.4).
6. Render source and provision Markdown as accessible HTML with locators and review state; keep raw files as secondary downloads (1.3.1, 3.1.2).

### P1 — structural quality

7. Correct table header association: document/provision as row header, country as a cell with a full localized name (1.3.1).
8. Add `<link rel="alternate" hreflang>`, canonical URLs, and per-page descriptions.
9. Verify 400% zoom, print layout, touch targets, and text spacing; add a print stylesheet.
10. Provide a visible focus treatment for the skip target and any scrollable region.

### P2 — trust and maintenance

11. Publish an accessibility statement with a feedback route and known limitations.
12. Add `sitemap.xml`, `robots.txt`, and a local 404 page.
13. Stop duplicating English artifacts under `/ar/`; use one canonical artifact URL with language metadata.

---

## 9. Sequenced implementation backlog

Each PR is intentionally narrow and must preserve all seven existing policy IDs, source URLs, and research text. None may add a legal conclusion. Dependencies are explicit.

### PR-1 — This audit (documentation only)

**Scope:** `docs/BASELINE-AUDIT.md`; no code or generated changes.  
**Acceptance:** all baseline commands reproduced and reported; defects separated from hypotheses; no new legal or translation claims; `git diff` contains only this file.

### PR-2 — Repo hygiene and truthful guardrails (no UI change)

**Scope:** add `.gitignore` (`node_modules/`, `test-results/`, local caches); commit `package-lock.json`; switch CI to `npm ci`; rebuild before tests; add a `dist` drift check in CI; add Python unit tests for `validate.py`; correct `ACCESSIBILITY.md`, `README.md`, and `MIGRATION.md` so they list only implemented gates; fix or remove the `--region europe` path; move root-page generation out of import time.  
**Dependencies:** none.  
**Acceptance:** fresh clone + `npm ci` leaves no untracked build artifacts; `validate.py` unit tests pass and fail on a deliberately broken fixture; CI runs build before tests and fails on `dist` drift; documentation contains no claim of an unimplemented test; site HTML is unchanged.

### PR-3 — Page identity, navigation, and skip-link correctness

**Scope:** unique page titles; root skip target; breadcrumb and site navigation; language switch to equivalent record URL; `hreflang` alternates; wrap foreign text in `lang`/`dir`; replace raw status tokens with human-readable English labels. Do not invent Arabic record translations.  
**Dependencies:** PR-2.  
**Acceptance:** 17/17 pages have unique, descriptive titles; 17/17 skip links focus `main`; every record page links to the equivalent record in the other locale; Arabic pages contain no Latin-script text outside a `lang="en" dir="ltr"` element; axe 0 on all pages; new Playwright checks cover all generated pages and fail if any of these regress.

### PR-4 — Bilingual string catalogue and honest Arabic status

**Scope:** move all UI chrome into `regions/mena/i18n/{en,ar}.json`; add Arabic labels only where reviewed or plainly structural; add a per-record translation status badge (`not available`, `draft`, `reviewed`); add Arabic country names only when sourced/reviewed, otherwise show the English name with `lang="en"`; remove duplicated English artifacts under `/ar/`.  
**Dependencies:** PR-3.  
**Acceptance:** build fails on a missing key in either locale; Arabic pages show no untranslated UI chrome; every non-Arabic string on an Arabic page is marked; native Arabic reviewer sign-off is recorded in the PR; no legal or explanatory prose is invented.

### PR-5 — Clause-level source and provision model + validator

**Scope:** add `sources.json`, `provisions.json`, and schemas; migrate the 4 orphan provision records into the canonical model; add structured locators, source IDs, tri-state applicability, translation provenance, typed relationships, and per-axis review status; add `validate_provisions.py` with positive and negative fixtures. Do not invent missing excerpts, dates, or reviewers.  
**Dependencies:** PR-2.  
**Acceptance:** all 7 policy IDs and URLs preserved; validator rejects duplicate IDs, unresolved references, invalid enums/dates, missing files, orphan provisions, and inappropriate cycles; both fixture suites pass; existing published pages remain valid; a migration report lists every field added and every unknown left `null`/`not_researched`.

### PR-6 — Accessible rendering of sources and provisions

**Scope:** restricted Markdown → HTML renderer; record/provision pages show title, jurisdiction, authority, instrument type, official URL, locator, original-language excerpt, translation status, interpretation issues, relationships, and review state; raw files become secondary downloads.  
**Dependencies:** PR-5.  
**Acceptance:** no raw Markdown is the primary representation; every rendered page has correct `lang`/`dir` for quotations and translations; heading order and table semantics pass; axe 0 on all pages; escaping tests prove script/attribute injection cannot pass through; original artifact bytes remain unchanged.

### PR-7 — Comparison by obligation

**Scope:** semantic comparison table for UAE, Saudi Arabia, and Qatar across the nine Phase 3 topics; each cell shows claim, legal-effect status, date/version, provenance link, and ambiguity warning; missing data reads `not researched`, never `no requirement`; native controls with labels; no-JS baseline; print styles.  
**Dependencies:** PR-5, PR-6.  
**Acceptance:** 3 × 9 matrix with a provenance link in every populated cell; no cell asserts absence without a documented negative finding; keyboard and screen-reader table tests pass; RTL and 320 px reflow pass; print output is legible; no country score or ranking exists.

### PR-8 — Rules as Code explainer and one honest Axiom attempt

**Scope:** `docs/rules-as-code.md` and a published explanatory page; select one narrowly defined provision or publish a blockers report; pin an Axiom engine commit; record a test-case contract with positive, negative, boundary, missing-input, and indeterminate cases; store compile/test evidence.  
**Dependencies:** PR-5, PR-6.  
**Acceptance:** engine commit and schema version are pinned; compile output is stored; all contract tests pass or the PR states exactly which semantics are unsupported; no rule is called approved/certified without recorded independent legal review; the page explains human interpretation versus engine output and links to source, provision, and tests.

### PR-9 — Manual accessibility and native-language evidence

**Scope:** record NVDA/Firefox and VoiceOver/Safari results; 400% zoom, forced colours, reduced motion, touch targets, and text spacing; native Arabic review of terminology and meaning; publish an accessibility statement with feedback route and known limitations; publish methodology.  
**Dependencies:** PR-3, PR-4, PR-6, PR-7.  
**Acceptance:** checklist records date, browser/AT versions, tester, pass/fail, and filed issues; every failure has an owner and target; the accessibility statement does not claim conformance from automated scans; Arabic review is attributed with consent; methodology explains evidence states and the “no record ≠ no law” rule.

---

## 10. What requires human review before any claim changes

- **Legal effect and instrument classification** of every record, including whether a policy, guideline, portal statement, or draft creates an obligation.
- **Authoritative language** of each source, especially Qatari and Saudi instruments where the consulted copy is English.
- **Exact clause locators and excerpts**, including reuse permission and whether the excerpt is a quotation or a paraphrase.
- **Arabic terminology, translation status, and bidi behaviour**, by a native Arabic reviewer.
- **Screen-reader behaviour** with NVDA and VoiceOver, including table announcements and language switching.
- **Whether any provision is deterministic enough for Axiom**, and the resulting legal interpretation.

The coding agent can build schema, rendering, tests, and accessible UI. It cannot set a review state to approved, verify a legal effect, or certify a translation.

---

## 11. Suggested PR body for this phase

- **Summary:** documentation-only baseline audit; no implementation, legal, or translation changes.
- **Files changed:** `docs/BASELINE-AUDIT.md` only.
- **Why:** establish a factual baseline before Phase 1 and prevent unsupported claims.
- **Migrations:** none.
- **Risks:** findings may be misread as legal conclusions; they are not. The audit intentionally preserves every existing research record.
- **Test commands and results:** `python3 framework/validate.py` (pass, 7 records); `python3 framework/build.py --region mena` (pass, zero diff); `python3 framework/check_html.py` (pass); `npm run test:a11y` (4 passed). Independent probes: 17 pages, 0 axe violations, 0 broken local links, 0 overflow at 320 px, 1 broken skip link, 2 unique titles across 17 pages, language switch loses context.
- **Keyboard tested:** yes, automated focus probes; no manual screen-reader session.
- **Language checks:** document `lang`/`dir` pass; mixed-language marking fails (documented).
- **Legal claims added/changed:** none.
- **Sources for legal claims:** none added.
- **Outstanding ambiguities:** source accuracy, legal effect, authoritative language, translation quality, external link liveness.
- **Screenshots / snapshots:** not applicable (documentation only); rendered-page evidence is recorded as probe output in §3.
- **Rollback:** revert this single commit; no generated files or data are touched.
- **AI-assisted:** yes. External code copied: no. External sources consulted: repository files and the published site only. Copyright concern: none known.

---

## 12. Audit method and reproducibility notes

- Repository inspected at `4f869c7` on `docs/agent-handoff`; feature branch `docs/baseline-audit` created from it. `main` was at `ec05358` and does not contain the Phase 0 prompts or `AGENTS.md`, so this audit should be reviewed against `docs/agent-handoff` unless that branch is merged first.
- All commands were run from the repository root. The build was run before the diff check and again after, with no changes.
- The live site was compared by SHA-256 for `/`, `/mena/en/`, `/mena/ar/`, and one record page; all matched the committed `dist/`.
- The independent probes used a temporary Playwright script outside the repository. No probe file, dependency, or generated output was added to the branch.
- `npm install` created `node_modules/`, `package-lock.json`, and `test-results/`; these are untracked and must not be committed. Their absence from `.gitignore` is itself a finding (CI-05).
- No external model/provider API was used for source text. No new national law was researched.
