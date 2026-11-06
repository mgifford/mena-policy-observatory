# Roadmap

**Status:** proposal for authorization. The active milestone (`docs/CURRENT-MILESTONE.md`) is implementation-complete; the milestones below are **not authorized**. Each requires an explicit instruction, its own milestone document and a human-reviewed pull request.

**Direction:** the observatory documents and explains law and policy that already exist. Proposed or hypothetical rules are a separate, labelled capability and never appear as current obligations.

## Milestone 1 — Trilingual research foundation

**Priority:** next. Extend the existing bilingual infrastructure rather than building a parallel site.

- English, French and Arabic interface languages with equivalent navigation, titles, empty states and language switching.
- Source-language metadata kept separate from interface translation: original language, official translation, human-reviewed research translation, machine-assisted draft, unavailable or unresolved.
- Translation provenance and review records per text, without inventing legal translations to fill gaps.
- Accessible LTR/RTL handling, including embedded Latin identifiers, URLs and dates in Arabic text, and keyboard/reflow behaviour for the new locale.
- Terminology governance for recurring legal and technical concepts, with jurisdiction-specific meanings where they differ.

**Completion evidence:** three-locale key parity, French content marked provisional until native review, language-switch equivalence in automated tests, and samples of mixed-direction text.

## Milestone 2 — Authoritative legislation tracking

- Official publisher registry per jurisdiction: gazettes, consolidated portals, parliaments, ministries, regulators and standards bodies.
- Legal instrument identity and versions: work, expression and captured item; publication, adoption, commencement and repeal dates; amendments and consolidations.
- Source monitoring and change detection that separates source health from legal change.
- Human review tasks for suspected changes, with stale-source warnings and preserved historical evidence.

**Dependencies:** Milestone 1 for source-language metadata; a bounded pilot on a small number of publishers before any broad registry.

## Milestone 3 — Existing public digital policy research

Research programmes on digital procurement, open-source software, digital sovereignty, and environmental sustainability and climate requirements, using authoritative existing instruments.

- Candidate leads first; unreviewed packets before reviewed findings.
- No rankings or scores without a reviewed methodology.
- Procurement and contracting data, and sustainability frameworks, remain evidence about implementation or good practice, not sources of legal obligation.

## Milestone 4 — Reviewed Rules as Code

- Select one provision with reliable primary evidence, a verified version, reviewed interpretation and deterministic conditions.
- Pin the engine version, record reviewer and interpretation basis, and test positive, negative, boundary and indeterminate cases.
- Source-linked decision visualizations with accessible linear equivalents.
- Historical rule comparison, and hypothetical simulation only as a clearly labelled separate capability.

## Sequencing and gates

1. Manual accessibility and native-language review remain release conditions for every milestone; automated scans never establish conformance.
2. No executable rule before source, version and interpretation review.
3. No new domain or country expansion without an authorized milestone.
4. Any stacked pull requests must include an explicit promotion step to `main`; a merge into a feature branch does not complete a milestone.
