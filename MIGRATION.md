# Migration notes

Preserved: four original MENA digital-accessibility policy records, source URLs, interpretations, related documents, RuleSpec scaffolds, and domain research under `regions/mena`.

Changed: a shared Python static renderer replaces the earlier region-specific generated HTML. The repository currently ships one region config (`mena`); there is no `regions/europe` directory. Only generated site output is rewritten.

Added (PR 1, coverage integration): a 24-entry jurisdiction registry reconciled with the toolkit's proposed scope, an eight-domain policy-area registry with provisional Arabic labels, a derived coverage view model, bilingual EN/AR coverage pages, and deterministic toolkit checks. The existing seven policy record IDs, source URLs, legal conclusions and research data are unchanged.

Follow-up (review gate and Arabic labels): every country entry gains `group_ar`, `scope_note_ar` and `jurisdiction_note_ar` (plus `_ar_status`) as additive fields; existing English fields are unchanged. `research.json` accepts an optional record-level `review` object. Coverage now requires a complete review entry before reporting `reviewed_findings`, and `framework/validate.py` rejects a confirmed legal effect without one. No existing record, source or legal-status value changes, because no record currently claims a confirmed effect.

Tranche 02 integration (additive): `research-toolkit/sources/candidate-sources.json` grows from 9 to 23 candidates and `research-toolkit/backlog/tasks-tranche-02.jsonl` adds 14 tasks (combined queue 54). Incoming identifiers are preserved in lowercase; no existing candidate, task, policy record or legal-status field is renamed or removed. Imported records carry package provenance and `verification_required` fields; three reported instrument relationships are stored as unreviewed candidate relations. The import is reproducible with `python3 research-toolkit/scripts/import_tranche.py --check`.

Evidence-currency work package (additive): `research-toolkit/sources/publishers.json` records the 25 hosts cited by the 23 candidates and seven policy records, with publisher identity fields left unknown; `research-toolkit/sources/source-checks.json` records 23 `not_checked` source-health records. No existing candidate, task, policy record or legal-status field changes. Both files are reproducible with `python3 research-toolkit/scripts/registry.py --check`.

Instrument-identity work package (additive): `research-toolkit/sources/instruments.json` adds one reported instrument identity per candidate, with parsed type/number/year, explicit null dates and uncertainty notes. No existing candidate, task, policy record or legal-status field changes. Reproducible with `python3 research-toolkit/scripts/instruments.py --check`.

Source-health defect correction (non-breaking data migration): `research-toolkit/sources/source-checks.json` moves to version 2 fields. Legacy `status`/`checked_at` records migrate to `retrieval_status`, `attempted_at` and `last_successful_retrieval`, and gain a separate `legal_verification` object. All 23 current records are `not_attempted` and `unreviewed`; no retrieval, freshness or verification claim is created. `registry.py --check` reproduces the file. Retrospective effective dates now produce a validation warning instead of an error; no source date is changed.

Translation-provenance work package (additive): source records may carry an optional `expressions` array for language expressions and translations. No existing research record is changed or required to add one; records without expressions remain valid and show an explicit "no expression record" state. Added `regions/mena/data/terminology.json` (15 draft concepts) and terminology validation. No source text, translation, reviewer or legal claim is fabricated.

Research layers remain separate: geographic scope, task status, candidate discovery, source verification, provision extraction, interpretation, translation, Rules as Code and publication are never collapsed into one label. Candidate source leads are displayed as unreviewed discovery leads only; no candidate has been captured, verified, translated or legally reviewed.

Omitted: old duplicated `docs/policies` tree and historical generated HTML, because they were derived outputs. No additional law or verified translation has been invented. Old scripts have not been carried forward where their behavior duplicates the new framework.
