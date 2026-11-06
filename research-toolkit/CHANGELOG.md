# Toolkit change record

## v3 (2026-11-06)
- Added `scripts/import_tranche.py`: deterministic, idempotent import for unreviewed discovery packages with URL, instrument-number and title duplicate detection.
- Integrated tranche 02: 14 candidate leads and 14 verification tasks. The canonical inventory now holds 23 candidates and the combined queue 54 tasks.
- Added `reconciliation/tranche-02-report.json` and `backlog/tasks-tranche-02.jsonl`.
- Candidate records now accept `source_languages`, `verification_required`, `provenance` and unreviewed `relations`; coverage validates all four.
- CI validates the package, checks the integration with `import_tranche.py --check`, and includes the tranche task queue in the queue audit.
- No legal effect, capture, translation or review status was added; all 23 leads remain unreviewed.

## v2 (2026-11-06)
- Integrated the toolkit registries with the observatory's coverage views: 24 jurisdictions, eight policy areas, 40 queued tasks and nine unreviewed candidate source leads.
- Reconciled the proposed jurisdiction list with `regions/mena/data/countries.json`; preserved provisional Arabic names and recorded aliases.
- Normalized candidate-source domain IDs to the canonical registry and added per-record public display review metadata. Every lead remains unreviewed and link-only.
- Removed two duplicate logical tasks from `backlog/cross-domain-tasks.jsonl` after separator normalization (42 -> 40).
- Hardened `validate_packets.py` with `domain`, `source_type`, `exact_excerpt` and `proposed` checks from the packet schema.
- Added `manifest.py --check` and `.DS_Store` exclusion; `report_queue.py` now summarizes multiple files and reports logical duplicates and missing metadata without crashing.
- Added toolkit tests for the new validator, queue and manifest behavior; CI validates the positive packet fixture, toolkit tests, the combined queue and the committed manifest.

## v1 (2026-11-05)
- Added candidate-only source packet interchange and offline checks.
- Added 11 stage-specific agent prompts and human-review controls.
- Added 24-entry *proposed* scope (21 current, 3 editorial additions), 24 initial tasks and 18 domain discovery tasks.
- Carried forward 9 candidate source leads; not re-fetched or legally verified.
- Added source Markdown, interpretation, related-instrument, RuleSpec and PR/review templates.
- Added comparative policy and simulation methodology, accessibility/i18n, privacy, and Europe reuse guidance.

No edits to live repository or legal determinations. No sources captured, translated or legally approved. The toolkit does not execute Axiom or produce jurisdiction findings.
