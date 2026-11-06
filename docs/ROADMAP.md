# Roadmap

**Status:** the active milestone (`docs/CURRENT-MILESTONE.md`) is in progress; the milestones after it are **not authorized**. Each requires an explicit instruction, its own milestone document and a human-reviewed pull request.

**Direction:** the observatory documents and explains law and policy that already exist. Proposed or hypothetical rules are a separate, labelled capability and never appear as current obligations.

## Active milestone — Legal evidence currency and multilingual support

**Status:** authorized and in progress. This milestone makes the existing evidence current, traceable and readable across languages. It does **not** start Rules as Code, Axiom or any executable rule work.

### Legal evidence currency

- **Bounded publisher registry.** Record the official publishers already cited by the 23 candidate leads and the seven policy records: authority type, jurisdiction, languages, retrieval constraints, maintainer and review priority. No new countries or domains; no broad crawling.
- **Instrument identity and versions.** Distinguish legal work, expression and captured item. Record publication, adoption, commencement, expiry, repeal and consolidation dates where documented; keep `unknown` explicit. Record amendments and corrections as unreviewed relationships until reviewed.
- **Source checks and freshness.** Deterministic, idempotent checks that record last successful check, last failed check, last detected change and explicit unavailable/blocked states. Source health is tracked separately from legal change.
- **Change events.** Record immutable monitoring events (new instrument, amendment, repeal, consolidation, translation update, technical change, unknown) and open human review tasks. No automated legal-effect change.
- **Candidate lead currency.** Re-check the 23 existing leads and record when each was checked and against which version. A lead stays unreviewed and is never described as current law until a reviewer confirms it.
- **Boundaries.** Respect publisher terms, robots policies, rate limits and access restrictions. No authentication bypass; no private or personal data.

### Multilingual support

- **Three interface languages.** English, French and Arabic on the existing internationalisation infrastructure — navigation, titles, empty states, language switching and status labels. No parallel site.
- **Source language is not interface language.** Record original publication language, official translation, human-reviewed research translation, machine-assisted draft, translation pending, unavailable or unresolved. Never invent a legal translation to fill a gap.
- **Translation provenance.** Per text: language, source, document version, publication or translation authority, review status, review date and reviewer role where appropriate.
- **Terminology governance.** Reviewed terms for recurring legal and technical concepts, with jurisdiction-specific meanings where they differ.
- **Accessibility.** LTR and RTL layouts, mixed-direction text (URLs, identifiers, dates), keyboard operation, reflow and screen-reader language announcements. French and Arabic copy remains provisional until native review.

### Explicitly out of scope

- Axiom, RuleSpec, rules engines or any executable-rule dependency.
- Policy simulation, impact modelling or hypothetical legislative drafting.
- New legal research beyond re-checking the existing leads.
- New policy domains or countries.
- Legal-effect determinations, certification or WCAG conformance claims.
- Broad crawling, monitoring services or a database.

### Completion evidence

1. Publisher-registry entries with provenance for the bounded pilot.
2. Instrument and version records for the pilot, with unknown dates preserved.
3. Deterministic source checks and recorded change events with explicit success, failure and stale states.
4. Human review tasks opened for every detected or suspected change.
5. Three-locale key parity and language-switch equivalence in automated tests; French and Arabic marked provisional pending native review.
6. Accessibility tests for three locales, plus the documented manual accessibility and native-language review gates.
7. No candidate promoted to a verified source or legal finding.
8. Documentation and a reviewable pull request.

## Milestone 2 — Existing public digital policy research

Research programmes on digital procurement, open-source software, digital sovereignty, and environmental sustainability and climate requirements, using authoritative existing instruments.

- Candidate leads first; unreviewed packets before reviewed findings.
- No rankings or scores without a reviewed methodology.
- Procurement and contracting data, and sustainability frameworks, remain evidence about implementation or good practice, not sources of legal obligation.

## Milestone 3 — Reviewed Rules as Code

Deferred until source, version and interpretation review are operational. Axiom and comparable engines remain unselected and are not dependencies.

- Select one provision with reliable primary evidence, a verified version, reviewed interpretation and deterministic conditions.
- Pin the engine version, record reviewer and interpretation basis, and test positive, negative, boundary and indeterminate cases.
- Source-linked decision visualizations with accessible linear equivalents.
- Historical rule comparison, and hypothetical simulation only as a clearly labelled separate capability.

## Sequencing and gates

1. Manual accessibility and native-language review remain release conditions for every milestone; automated scans never establish conformance.
2. No executable rule before source, version and interpretation review.
3. No new domain or country expansion without an authorized milestone.
4. Any stacked pull requests must include an explicit promotion step to `main`; a merge into a feature branch does not complete a milestone.
