# Authorized work package: public legislative visualizations

**Status:** implementation complete pending human review — bounded visualization work package authorized by the repository owner on 2026-11-07. It does **not** mark the three-source monitoring pilot complete and does **not** authorize executable real legislation.

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
| `ae-national-digital-accessibility` | UAE | Three recorded provisions, three open questions, two related documents, one recorded excerpt | Source bytes not stored; dates and authoritative language unknown; relations unreviewed |
| `qa-eaccessibility-2011` | Qatar | One provision, two questions, four related documents including a proposed successor, temporal uncertainty | No excerpt or bytes captured; dates unknown; current standing unresolved |
| `sa-mep-accessibility` | Saudi Arabia | Three provisions, three questions, qualifier/scope uncertainty | No excerpt or bytes captured; dates unknown; no related documents recorded |

The three-source monitoring pilot instruments are not used because complete text/provision structure is not captured.

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
- `dist/mena/{en,fr,ar}/visualizations/qa-eaccessibility-2011.html`
- `dist/mena/{en,fr,ar}/visualizations/sa-mep-accessibility.html`
- `dist/mena/{en,fr,ar}/visualizations/synthetic.html`

The navigation includes **Visualizations** in every locale, and each selected record page links to its canonical visualization. The synthetic example is a separate, prominently labelled section and is not mixed into the real-record catalogue.

Screenshots (1280 px browser width, full page):

- [Visualization catalogue](visualizations/catalogue.png)
- [Recorded source structure](visualizations/source-structure.png)
- [Synthetic demonstration](visualizations/synthetic.png)

Automated verification at the time of this work:

- `python3 framework/validate.py` — pass.
- `python3 -m unittest discover -s tests` — 305 tests, pass.
- `python3 -m unittest discover -s research-toolkit/tests` — 15 tests, pass.
- registry, instruments, import and manifest checks — current.
- `python3 framework/build.py --region mena` — 154 pages.
- `python3 framework/check_html.py` — pass.
- `npm run test:a11y` — 464 Playwright/axe checks passed (154 pages × 3 checks, plus unique-title/language tests).
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
