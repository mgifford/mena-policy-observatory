# Toolkit change record

## v8 (2026-11-06)
- Added append-only source-change observations and human review decisions under `monitoring/`, plus derived `backlog/tasks-change-review.jsonl`.
- `framework/change_events.py` validates events/decisions, derives idempotent review tasks and supports `--check`.
- Technical changes, potential legal changes and reviewed conclusions remain distinct; no automatic legal-effect change.
- All files are empty until a real observation is recorded; synthetic fixtures exercise the workflow in tests.

## v7 (2026-11-06)
- Source records may carry optional language expressions with kind, BCP47 language, original language, authority, method, review state/date/role and uncertainty notes; existing records are unchanged.
- Validator rejects mismatched references, duplicate expressions, unauthorised review promotion and incomplete reviewed metadata.
- Added the draft terminology registry and validator; no concept or translation is marked reviewed.

## v6 (2026-11-06)
- Split the source-check model into retrieval outcome, freshness inputs and legal verification (`source-checks.json` version 2); legacy records migrate automatically.
- `registry.py` preserves an earlier successful retrieval when a later attempt fails and never promotes legal verification.
- Retrospective effective dates are warnings rather than validation errors; impossible calendar dates remain errors.
- Documentation and translation copy updated for the separated model. No legal status changed.

## v5 (2026-11-06)
- Added `sources/instruments.json`: one reported instrument identity per candidate, with parsed type/number/year, explicit null authority and version dates, expression label and uncertainty notes.
- Added `scripts/instruments.py`: deterministic derivation with `--check`; preserves human-entered authority, dates, expression language and review state.
- Coverage validates instrument identity against the candidate title, jurisdiction and reported publication date; invented capture, promoted review state and non-ISO dates are rejected.
- The sources page shows reported instrument type/number/year, version dates and captured-version state. No identity or date is verified.

## v4 (2026-11-06)
- Added `sources/publishers.json`: 25 cited hosts with jurisdiction, citation links and explicit unknown publisher identity.
- Added `sources/source-checks.json`: one `not_checked` health record per candidate; no check is inferred.
- Added `scripts/registry.py`: deterministic derivation of both files with `--check`; preserves human-entered publisher fields and recorded checks.
- Coverage validates publisher identity, citation integrity, check vocabulary and date rules; the sources page shows publisher host, registry status and source health.
- CI checks that the registry is current. No legal effect or currency claim is introduced.

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
