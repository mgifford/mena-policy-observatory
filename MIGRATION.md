# Migration notes

Preserved: four original MENA digital-accessibility policy records, source URLs, interpretations, related documents, RuleSpec scaffolds, and domain research under `regions/mena`.

Changed: a shared Python static renderer replaces the earlier region-specific generated HTML. The repository currently ships one region config (`mena`); there is no `regions/europe` directory. Only generated site output is rewritten.

Added (PR 1, coverage integration): a 24-entry jurisdiction registry reconciled with the toolkit's proposed scope, an eight-domain policy-area registry with provisional Arabic labels, a derived coverage view model, bilingual EN/AR coverage pages, and deterministic toolkit checks. The existing seven policy record IDs, source URLs, legal conclusions and research data are unchanged.

Follow-up (review gate and Arabic labels): every country entry gains `group_ar`, `scope_note_ar` and `jurisdiction_note_ar` (plus `_ar_status`) as additive fields; existing English fields are unchanged. `research.json` accepts an optional record-level `review` object. Coverage now requires a complete review entry before reporting `reviewed_findings`, and `framework/validate.py` rejects a confirmed legal effect without one. No existing record, source or legal-status value changes, because no record currently claims a confirmed effect.

Research layers remain separate: geographic scope, task status, candidate discovery, source verification, provision extraction, interpretation, translation, Rules as Code and publication are never collapsed into one label. Candidate source leads are displayed as unreviewed discovery leads only; no candidate has been captured, verified, translated or legally reviewed.

Omitted: old duplicated `docs/policies` tree and historical generated HTML, because they were derived outputs. No additional law or verified translation has been invented. Old scripts have not been carried forward where their behavior duplicates the new framework.
