# Structured research model

This document describes the machine-readable research layer added in Phase 2. It is a research record, not a legal opinion and not an executable rule set.

## Why it exists

The Markdown artifacts (`SOURCE.md`, `PROVISIONS.md`, `INTERPRETATION.md`, `RELATED.md`) remain the narrative research record. They are written for people and are hard to check mechanically. `research.json` adds a parallel, structured form so the site can render provisions, open questions and related instruments, and so the validator can detect breakage.

Nothing is migrated out of the Markdown. The JSON points at it, and the validator requires that quoted material still appears there verbatim.

## Files

- `regions/mena/policies/<record-id>/research.json` — one file per policy record. The validator requires one for every record listed in `data/policies.json`.
- `regions/mena/schemas/source-record.schema.json`
- `regions/mena/schemas/provision.schema.json`
- `regions/mena/schemas/interpretation-question.schema.json`
- `regions/mena/schemas/instrument-relation.schema.json`
- `regions/mena/schemas/research-record.schema.json` — combines the four.
- `framework/schema_lite.py` — dependency-free JSON Schema subset.
- `framework/research.py` — semantic checks beyond schema shape.
- `tests/test_research.py` and `tests/fixtures/research/` — positive and mutation fixtures.

`research-record.schema.json` declares `additionalProperties: false` throughout, so an accidental new field fails validation rather than being silently ignored.

## Sources

A source record carries the fields the phase requires: title, official URL, jurisdiction, issuer, instrument type, language, whether the consulted copy is the authoritative language (`yes`/`no`/`unknown`), publication and effective dates, document version, archival URL, capture information, excerpt, and translation state.

Deliberate limits:

- **Dates** are an ISO date or the literal `"unknown"`. Free text such as "sometime in 2011" is rejected. An unknown date is not treated as absent, late or invalid law.
- **Capture** records `bytes_stored`. A SHA-256 is only allowed when captured bytes actually exist in the repository, and stored bytes require a checksum and timestamp. No checksum is invented for a document that was only linked.
- **Excerpts** are copied from one of the declared Markdown artifacts, and the validator requires the exact text to still occur in that file. `excerpt_status` must agree with whether an excerpt is present: `recorded`, `not_recorded` or `not_permitted`.
- **Translation** is a separate axis with its own status and review state. A source can be authenticated and still untranslated, or translated and still not legally reviewed. A named translation needs recorded provenance; `native_reviewed` without provenance is rejected.

A recorded source means the research located the document. It does not mean the legal effect was verified.

## Provisions

A provision has a stable ID (`P-01`), heading, locator (section, article, clause, page, paragraph, annex, document, or `unknown`), one or more source IDs, a recorded interpretation, an effect assessment and an encoding status.

- `effect_assessment` is one of `not_assessed`, `draft_not_in_force`, `in_force_confirmed`, `not_in_force_confirmed`, `indeterminate`. "Not assessed" and "indeterminate" are distinct from any negative finding.
- `encoding_status` is one of `blocked`, `candidate`, `tested`, `reviewed`.
- `reviewed` is refused unless the effect assessment is a confirmed one and every linked question is resolved.

Provision IDs, headings and recorded interpretations must match `PROVISIONS.md`: an entry in either place without the other is an error, and the interpretation text must appear in the file verbatim.

## Interpretation questions

Each question has a persistent ID, an optional provision link, a statement, the recorded observation, alternatives, risk, category, status, resolution, what review it needs, and reviewer metadata.

- `unresolved` is not a negative legal finding. It means this research has not settled the question.
- A resolved question requires a resolution, a reviewer and a review date.
- A resolution without `status: resolved` is rejected, so the two cannot drift apart.
- An alternative cannot claim `reviewed` yet, because no separate evidence trail for alternatives is recorded. The validator rejects the claim rather than accepting an unsupported one.

Question IDs and statements must match `INTERPRETATION.md` in the same way as provisions.

## Instrument relations

Relations use the vocabulary `cites`, `amends`, `supersedes`, `transposes`, `implements`, `incorporates` and `guidance_for`.

Existing manifest labels such as `normative_annex`, `technical_standard` or `proposed_successor` are kept as `recorded_label`, with `relation: "unspecified"` and `review_state: "unreviewed"`. Mapping those labels onto the legal vocabulary would be a new interpretation, so it is not done automatically.

- An asserted relation requires `review_state: "reviewed"`.
- `unspecified` requires a recorded label.
- An internal target must resolve to a known record, must not point at its own record, and must not also carry a URL.
- An external target must carry a URL.
- Internal `amends` and `supersedes` relations are checked for cycles. Cycles in citations are ordinary and are not flagged.

## Coverage layer

`framework/coverage.py` joins the research records with the toolkit's discovery inventory. It loads four registries:

- `regions/mena/data/countries.json` — the geographic scope, reconciled with the toolkit's proposed 24-entry list.
- `regions/mena/data/domains.json` — eight policy areas in five research themes, with subtopics.
- `research-toolkit/backlog/tasks.jsonl`, `cross-domain-tasks.jsonl` and `tasks-tranche-02.jsonl` — 54 queued discovery and verification tasks.
- `research-toolkit/sources/candidate-sources.json` — 23 candidate source leads (nine from the earlier inventory, 14 imported from research tranche 02).

Every research status is derived from recorded evidence; it is never stored as an independent legal conclusion. The vocabulary describes research activity only: `not_started`, `source_discovery`, `candidate_sources_identified`, `evidence_captured`, `provision_extraction`, `legal_review_pending`, `reviewed_findings`, `blocked`.

The layers stay separate. A listed jurisdiction is not a legal finding. A queued task is not evidence about the law. A candidate source lead is not a captured or verified source, and it is not a finding about legal effect. Candidate leads appear publicly only when the source URL passes a conservative HTTPS check and a recorded display review covers the required checks; even then the page labels every lead as unreviewed and reproduces no source text. Human review is still pending for all 23 current leads.

The validator rejects a candidate that asserts a confirmed legal effect, a captured source without capture metadata, an unknown domain or task stage, a duplicate logical task ID after separator normalization, or a public display record missing a required check.

### Candidate-source import

`research-toolkit/scripts/import_tranche.py` maps an unreviewed discovery package into the canonical candidate inventory. It is deterministic and idempotent: a second run produces the same files, and `--check` fails when the committed inventory is stale. It never assigns a legal effect, never stores source bytes and never edits a policy record.

- Incoming identifiers are preserved in lowercase (`MENA-T02-001` becomes `mena-t02-001`); task identifiers are preserved verbatim.
- Domains and source types are mapped through explicit tables; an unmapped value blocks the import instead of being guessed.
- Duplicates are detected by canonical URL first, then by jurisdiction plus the primary instrument number, then by jurisdiction plus title. A possible duplicate is held out of the import and listed in the reconciliation report for human review; it is not merged or silently dropped.
- A record that already exists with the same identifier but different metadata is reported as a conflict and left untouched.
- `research-toolkit/reconciliation/tranche-02-report.json` records imported records, matched records, possible duplicates, conflicts, imported tasks, outstanding verification and the mapping tables.
- Imported candidates keep their package provenance (package, incoming identifier, recorded date, source status, evidence reference) and carry `verification_required` requirements taken from the paired task. A `web_evidence_ref` that points at an AI session turn is preserved as recorded provenance and labelled as not independently checkable.
- Reported instrument relationships (for example the reported 2025 amendment to Algeria's 2018 data protection law) are stored as unreviewed candidate relations and validated. They are not legal findings.

Country entries also carry provisional Arabic group labels, scope notes and jurisdiction notes (`group_ar`, `scope_note_ar`, `jurisdiction_note_ar`, each with an `_ar_status` of `provisional` or `reviewed`). The validator requires the Arabic counterpart wherever the English editorial text exists, so an Arabic page cannot silently fall back to untranslated interface prose. `provisional` is a statement about review, not about accuracy.

### Record-level review evidence

`reviewed_findings` is a review outcome, so the coverage layer will not infer it from silence. A record is counted as reviewed only when all of the following hold:

- its `legal_effect` is `binding_confirmed` or `nonbinding_confirmed`;
- `research.json` carries a complete `review` entry with `status: "reviewed"`, a `reviewer`, an ISO `reviewed_at` date and a stated `scope`;
- no interpretation question in the record is still open.

A `review` entry with `status: "pending"` records intent only and never counts as review evidence. A confirmed legal effect without a complete review entry is a validation error, because the site would otherwise have to label the record unreviewed while the data claims a confirmed effect.

```json
"review": {
  "status": "reviewed",
  "reviewer": "Reviewer name or role, recorded with consent",
  "reviewed_at": "2026-11-06",
  "scope": "Legal effect and applicability of the reviewed instrument"
}
```

The review entry records that a review happened and what it covered. It is not a legal approval, and the schema does not verify the reviewer's independence.

### Evidence currency

Two files record what is known about source currency, separately from legal effect:

- `research-toolkit/sources/publishers.json`: one entry per host cited by a candidate or published record. It records the host, jurisdictions, citation links and explicit unknowns. `publisher_name`, `authority_type`, `languages` and `verification_status` are human-supplied; the generator preserves them but never invents them. An entry is `unverified` until a reviewer records otherwise.
- `research-toolkit/sources/source-checks.json`: one check per candidate. Statuses are `not_checked`, `reachable`, `unchanged`, `changed`, `blocked`, `failed` and `unknown`. A `not_checked` record may not carry a date, HTTP status, final URL or content type. Any other status requires an ISO `checked_at`.

A check records retrieval health only. It does not establish that a source is current, that an instrument is in force, or that its content was reviewed. A missing check is not evidence of absence.

Freshness is derived from the fixed `as_of` date and `stale_after_days`, not from the build date, so the static output is deterministic. A recorded check older than the threshold is reported as `stale`; without a recorded check the state is `not_checked`, not `stale`.

### Instrument identity and versions

`research-toolkit/sources/instruments.json` records one reported instrument identity per candidate:

- work id and candidate id (the same stable identifier until a separate work registry exists);
- reported title, parsed instrument type and instrument number, and the year parsed from the title;
- issuing authority and version dates, which stay `null` until a human records them;
- the expression label (`Reported title only`) and no captured item;
- explicit uncertainty notes and `review_state: reported`.

Types and numbers are **parsed from reported titles** and are not verified. A null publication, adoption, commencement, expiry, repeal or consolidation date means the date is unknown, not that no date exists. The reported year is not an effective date. `research-toolkit/scripts/instruments.py` derives the file deterministically, preserves human-entered authority, dates, expression language and review state, and supports `--check`.

The validator rejects a mismatch with the candidate title, jurisdiction or reported publication date; an unknown type carrying a number; a year without a number; an invented captured item; a promoted review state; a non-ISO date; and a candidate without an instrument record.

`research-toolkit/scripts/registry.py` derives both files from the existing URLs, preserves recorded checks and human-entered publisher fields, and supports `--check`. The validator rejects a cited host without a publisher, an uncited publisher, a publisher whose id does not match its host, unknown vocabularies, duplicate or unknown checks, `not_checked` records carrying dates, recorded statuses without a date, and a candidate without a check.

## Running the checks

```sh
python3 research-toolkit/scripts/registry.py --check
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

`framework/validate.py` keeps its existing record-structure checks and now also runs the research checks for every record in the region. Unit tests cover duplicate IDs, unknown references, impossible dates, invented checksums, excerpt and summary attribution, review-state gates and unsupported schema keywords.

If `schema_lite.py` meets a schema keyword it does not implement, it raises instead of ignoring it. That keeps the check honest when a schema grows.

## What this layer does not do

- It does not confirm that a provision is in force, binding or correctly interpreted.
- It does not verify that a source URL still resolves or that a captured copy matches the official text.
- It does not translate legal text, and it does not check translation accuracy.
- It does not decide whether a case of `cites` or `guidance_for` is legally correct, only whether a reviewed relation is recorded consistently.
- It does not compile or execute Axiom RuleSpec files.
- It does not replace independent legal, accessibility or native-language review.
