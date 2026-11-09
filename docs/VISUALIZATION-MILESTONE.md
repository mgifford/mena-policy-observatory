# Authorized work package: public legislative visualizations

**Status:** prototype implementation complete; manual legal, language and accessibility review deliberately deferred by the project owner on 2026-11-07. Not authoritative. It does **not** mark the three-source monitoring pilot complete and does **not** authorize executable real legislation.

## Why this is separate

The active milestone in `docs/CURRENT-MILESTONE.md` is the three-source verification and monitoring pilot. That pilot prohibits Axiom/RuleSpec implementation and broad research expansion, and it still has outstanding legal and native-language review gates.

This work package is a separate, bounded visualization layer. It may:

- publish **source structure** assembled only from existing recorded research metadata;
- publish **candidate interpretation questions** clearly marked as not legally reviewed;
- publish the existing **synthetic** Axiom/L4 demonstration as education;
- add static visualization routes, navigation and accessible text equivalents.

It may not:

- encode new real legislation or infer missing articles;
- publish a real reviewed executable rule;
- change legal-effect, review or translation status;
- use an execution engine at runtime;
- begin policy simulation, new jurisdictions or new domains;
- merge autonomously.

## Three public states

1. **Source structure — research in progress.** Instrument, recorded provisions, questions and related documents from existing `research.json`. Evidence status and uncertainty are shown. No missing structure is inferred.
2. **Candidate interpretation — not legally reviewed.** Existing unresolved questions, observations, alternatives and required review are shown as questions, not a settled decision tree.
3. **Reviewed executable logic — gated.** No real reviewed executable presentation is available. The synthetic demo is explicitly not legislation and not a reviewed rule. A future publication gate must resolve repository evidence before any real reviewed presentation is shown.

## Selected real records

| Record | Jurisdiction | Why selected | Evidence limits |
|---|---|---|---|
| `ae-moe-accessibility` | UAE | Two recorded provisions and three questions | No excerpt or bytes captured; dates unknown; no related documents recorded |
| `ae-mof-accessibility` | UAE | One recorded provision and two questions | No excerpt or bytes captured; dates unknown; one question has no provision link |
| `ae-national-digital-accessibility` | UAE | Five provisions, five open questions, four recorded links, two excerpts; March 2024 policy | English PDF plus full Arabic PDF; legal status and Arabic/English authority unresolved |
| `ae-federal-law-29-2006` | UAE | Five provisions, four questions, three recorded links, one Arabic excerpt; official English translation expression | Digital scope, Article 23 implementing instrument and consolidated amendment unresolved |
| `qa-eaccessibility-2011` | Qatar | One provision, two questions, four related documents including a proposed successor, temporal uncertainty | No excerpt or bytes captured; dates unknown; current standing unresolved |
| `qa-eaccessibility-2025-upcoming` | Qatar | Two draft provisions, two questions, two related documents | Draft/not in force; no excerpt or bytes; dates unknown; relations unreviewed |
| `sa-dga-web-accessibility-guide` | Saudi Arabia | Two provisions, two questions, one technical-standard link | No excerpt or bytes; dates unknown; guideline normativity unresolved |
| `sa-mep-accessibility` | Saudi Arabia | Three provisions, three questions, qualifier/scope uncertainty | No excerpt or bytes captured; dates unknown; no related documents recorded |
| `mena-t02-001` | Algeria | Law 18-07; 3 provisions, 3 questions, 2 recorded links, 1 excerpt | French Gazette edition; Arabic/French authority unresolved; 2025 amendment not consolidated |
| `jo-personal-data-2023` | Jordan | Law 24/2023; 3 provisions, 3 questions, 1 recorded link, 1 excerpt | Official English translation; publication/commencement and Arabic authority unresolved |
| `ma-personal-data-09-08` | Morocco | Law 09-08; 3 provisions, 3 questions, 2 recorded links, 1 excerpt | French legal-database text; Arabic authority and implementing decree reconciliation unresolved |

The initial three records were selected for depth; four more existing records were added on 2026-11-07, bringing the total to seven. Batch B (Algeria, Jordan, Morocco) was authorized on 2026-11-07 as a prototype expansion. The UAE federal law record was added on 2026-11-07 as authorized evidence gathering, bringing the total to eleven. The three-source monitoring pilot instruments are not used because complete text/provision structure is not captured.

**Prototype status:** this is a proof of concept for comparative legislation review and comparison. It is **not authoritative**. Manual legal, language and accessibility review was deliberately deferred by the project owner for this prototype stage and has **not** been performed. Do not use these pages for compliance decisions.

## Legal languages versus interface languages

The public interface is English, French and Arabic. That is not a claim that legislation in the region is written only in those languages. Official or authoritative legal languages may include Arabic, French, English, Persian, Turkish, Hebrew, Kurdish and others; source records must state the actual language rather than force a document into the interface set.

This release:

- records source language with BCP47 tags (the source-record schema now accepts tags such as `fa`, `tr`, `he` and `ar`);
- shows source-language titles, locators and excerpts with `lang`/`dir`, without inventing a translation;
- keeps interface translations separate from legal-text translations.

Persian/Turkish and other legal-language translations are **not implemented**. A future translation work package must record source language, translation type (official, human research, machine-assisted draft, pending/unavailable), authority, review state and reviewer role where appropriate. No machine output may be presented as official legal text.

## Completion criteria

- [x] Visualizations index in EN/FR/AR.
- [x] Synthetic demonstration discoverable and clearly labelled.
- [x] Source-structure pages for selected records, based only on recorded evidence.
- [x] Candidate-interpretation sections clearly labelled.
- [x] Complete accessible text equivalents and source links.
- [x] Navigation and record-page entries.
- [x] No real reviewed executable logic and no legal-effect changes.
- [x] Automated tests, 320px reflow and axe scans pass.
- [x] Manual screen-reader, zoom and native-language gaps disclosed (not performed).
- [x] Reviewable PR prepared; no autonomous merge.

## Stop condition

Deliver the visualization PR(s), report evidence and gaps, and stop. Do not extend scope to new records, real rule encoding, monitoring schedules or simulations without a new explicit instruction.


## Implementation evidence

Public routes (built statically for all three locales):

- `dist/mena/{en,fr,ar}/visualizations/index.html`
- `dist/mena/{en,fr,ar}/visualizations/ae-national-digital-accessibility.html`
- `dist/mena/{en,fr,ar}/visualizations/ae-federal-law-29-2006.html`
- `dist/mena/{en,fr,ar}/visualizations/qa-eaccessibility-2011.html`
- `dist/mena/{en,fr,ar}/visualizations/sa-mep-accessibility.html`
- `dist/mena/{en,fr,ar}/visualizations/synthetic.html`

The navigation includes **Visualizations** in every locale, and each selected record page links to its canonical visualization. The synthetic example is a separate, prominently labelled section and is not mixed into the real-record catalogue.

Screenshots (1280 px browser width, full page):

- [Visualization catalogue](visualizations/catalogue.png)
- [Recorded source structure](visualizations/source-structure.png)
- [Synthetic demonstration](visualizations/synthetic.png)
- [Rules as Code homepage section](rules-as-code-home.png)
- [Legalese-style dependency graph](legalese-graph.png)
- [Full synthetic Rules as Code page](rules-as-code-synthetic.png)

Automated verification at the time of this work:

- `python3 framework/validate.py` — pass.
- `python3 -m unittest discover -s tests` — 335 tests, pass.
- `python3 -m unittest discover -s research-toolkit/tests` — 15 tests, pass.
- registry, instruments, import and manifest checks — current.
- `python3 framework/build.py --region mena` — 190 pages.
- `python3 framework/check_html.py` — pass.
- `npm run test:a11y` — 578 Playwright/axe checks passed (190 pages × 3 checks, plus unique-title/language tests).
- 320 CSS px reflow checked for the new pages: no page-level horizontal overflow.

## Accessibility and language gaps

- Automated axe and reflow checks passed for the new pages.
- Manual screen-reader testing, real 400% browser zoom, text-spacing override, forced-colours manual inspection, print/PDF and disabled-user testing were **not** performed.
- French and Arabic interface copy is provisional; native review is outstanding. Source-language legal text is shown in English with `lang="en"` and is not presented as an official translation.
- No WCAG conformance is claimed.

## What remains deferred

- Any real reviewed executable rule or publication gate.
- New records, jurisdictions or domains.
- Inferred provisions, article numbers or relationship types.
- Runtime graph interaction, pan/zoom/editing or policy simulation.
- A general graph framework.

The source-structure pages intentionally show only recorded provisions and questions. Where an official index page was captured, the view shows that source and its recorded relationships rather than an imagined full legal structure.
