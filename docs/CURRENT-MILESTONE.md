# Current Milestone: Legal Evidence Currency and Multilingual Support

**Status:** In progress\
**Priority:** P0\
**Working branch:** `feat/translation-provenance` (verify before use)\
**Previous milestone:** MENA research coverage integration — implementation complete on `main` at `4b3c13a` (see git history and `docs/ROADMAP.md`)\
**Later milestones:** public digital policy research, then reviewed Rules as Code. Neither is authorized.

## Objective

Make recorded legal evidence explicitly current (or explicitly not checked), traceable to an official publisher and version, and readable across English, French and Arabic — without starting Rules as Code.

The milestone is delivered in bounded work packages. Each package needs its own reviewable pull request; no package may promote a candidate lead to verified law or infer a legal effect.

## Authorized work

### Legal evidence currency

- A registry of official publishers cited by existing candidate leads and published records, recording host, jurisdiction, authority type, languages, verification status, monitoring state and retrieval notes. Unknown values stay unknown.
- Source-check records per candidate, separating retrieval outcome, source freshness and legal verification. A successful request never verifies legal effect; a failed request never erases an earlier successful retrieval.
- Explicit freshness and stale-source reporting derived from recorded checks, with a fixed `as_of` date so the static build stays deterministic.
- Instrument identity and version metadata (work, expression, captured item; publication, commencement, repeal and consolidation dates) only where documented, with unknown values preserved.
- Defect corrections in existing evidence handling: retrieval outcome, source freshness and legal verification are separate; unusual chronology such as retrospective effect is a review warning, not a hard rejection; repository instructions match the trilingual implementation.
- Immutable change events and human review tasks for detected or suspected changes. No automated legal-effect change.

### Multilingual support

- English, French and Arabic interface support on the existing internationalisation infrastructure. No parallel site.
- Source language separated from interface language; translation states (original, official translation, human-reviewed research translation, machine-assisted draft, pending, unavailable, unresolved) and translation provenance.
- Terminology governance for recurring legal and technical concepts.
- Accessible LTR/RTL layouts, mixed-direction text, keyboard operation and reflow in all three locales. French and Arabic copy remains provisional until native review.

## Prohibited work

Do not:

- Implement executable Axiom RuleSpec, Axiom runtime dependencies, rules engines or policy simulation.
- Conduct new legal research beyond re-checking the existing 23 candidate leads.
- Add policy domains, countries or jurisdictions.
- Add automated legal-effect, in-force or compliance determinations.
- Crawl broadly, bypass access controls, or store copyrighted full text or personal data.
- Invent publisher identities, authority types, dates, translations or review approvals.
- Merge pull requests autonomously.
- Begin the research-expansion or Rules as Code milestones.

## Work packages

1. **Publisher registry and source-health records** — delivered (PR #14): registry of 25 cited hosts, one not-attempted retrieval record per candidate, validator and trilingual display. Defect correction in this PR separates retrieval outcome, freshness and legal verification.
2. **Instrument identity and version metadata** — delivered in this work package: reported type/number/year, explicit null authority and version dates, captured-version state, validator and trilingual display.
3. **French interface foundation** — delivered (PR #16): French catalogue, localized country/domain labels, three-language navigation and language switching, 139-page build and three-locale tests.
4. **Translation provenance and terminology** — delivered in this work package: optional per-source language expressions, validation, draft terminology registry and accessible expression status on record pages; native review remains outstanding.
5. **Source-change review workflow** — next: change events, review tasks, stale-source warnings.

**Maintenance (this PR): defect corrections** — source-health classification, retrospective-date handling, trilingual instruction reconciliation and regression tests.

## Completion criteria

- [x] Publisher registry covers every host cited by candidates and records, with explicit unknowns.
- [x] Every candidate has a source-check record; no check is fabricated.
- [x] Retrieval outcome, freshness and legal verification are separate and freshness is derived from a fixed `as_of` date.
- [x] Instrument identity and version metadata are recorded where evidence exists.
- [ ] Change events and review tasks exist for detected changes (WP5).
- [x] English, French and Arabic navigation works; French and Arabic copy is marked provisional.
- [x] Translation states and provenance are recorded per text (WP4).
- [x] Automated accessibility tests pass for all three locales.
- [x] Python validation, unit tests and the reproducible build pass.
- [x] Documentation matches the implementation.
- [x] Work-package pull requests are prepared for human review.

## Required verification commands

```bash
python3 research-toolkit/scripts/registry.py --check
python3 research-toolkit/incoming/tranche-02/validate.py
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s research-toolkit/tests -p 'test_*.py' -v
python3 framework/build.py --region mena
python3 framework/check_html.py
npm run test:a11y
git diff --check
```

Manual keyboard, screen-reader, zoom, forced-colour and native-language review must be recorded separately. Automated tests do not establish WCAG conformance.

## Stop condition

Complete and validate one work package at a time, prepare a reviewable pull request, and stop. Do not start the next work package or a later milestone without an explicit instruction.
