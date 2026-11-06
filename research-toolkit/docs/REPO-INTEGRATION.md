# Integrate safely with existing mena-policy-observatory

Repository inspected on 2026-11-05:
- `AGENTS.md`: agent work boundaries, branch-first, human-reviewed PR.
- `docs/WORKFLOW.md`: existing phases and reviewer handoff.
- `framework/validate.py`, `framework/research.py`: semantic validation.
- `regions/mena/schemas/research-record.schema.json`: active structured research contract.
- `regions/mena/policies/<id>/research.json`: record unit.
- `regions/mena/i18n/{en,ar}.json`: UI catalogues.
- `tests/accessibility.spec.mjs`: Playwright + axe tests.
- `dist/`: committed generated output.

**This toolkit is not a new implementation of those files.** Its `schemas/candidate-packet.schema.json` is a *pre-publication interchange*. Agent packets must be reviewed and transformed into the existing `research.json` contract. Do not rename existing policy IDs or infer that a discovery candidate satisfies the full schema.

## Suggested branch commands
```sh
git status --short --branch
git switch -c research/toolkit-v1
mkdir -p research-toolkit
# Copy extracted toolkit contents to research-toolkit/ without overwriting repo files.
python3 research-toolkit/scripts/validate_packets.py research-toolkit/examples/valid-packet.json
python3 -m unittest discover -s research-toolkit/tests -v
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 framework/build.py --region mena
python3 framework/check_html.py
npm ci --no-audit --no-fund
npx playwright install chromium
npm run test:a11y
```

If tests need network/browser installation, report inability honestly; don't claim they passed. No automatic pushes or merges.

## Integration PR sequence
1. Tooling docs and packet schema only.
2. Offline candidate-source inventory + status pages (no legal findings).
3. Source-capture command with rate-limits, user agent, official-domain allowlist, licensing checks and human approval.
4. Clause research and source-to-evidence conversion into existing `research.json`.
5. Comparison UI, accessible bilingual templates, manual QA.
6. One reviewed Axiom engine-pinned executable rule, with negative/boundary tests.
7. Optional Europe region config after MENA schemas are stable.

## Differences and omissions
- **Changed:** adds an intermediate candidate packet, specialized agent prompts and stricter publication review.
- **Preserved:** existing canonical research records and region config.
- **Omitted:** auto-scraping, API calls, public-facing LLM, bulk source reproduction and legal determinations without human review.
- **Reason:** legality, privacy, provenance and reproducibility cannot be inferred from a successful build.

## Current integration status (PR 1)

The toolkit is now integrated additively; no existing policy record or legal conclusion was changed.

- `framework/coverage.py` loads `regions/mena/data/countries.json`, `regions/mena/data/domains.json`, `research-toolkit/sources/candidate-sources.json` and both backlog files. It validates registry consistency, derives research status from recorded evidence, and builds the public view model.
- `framework/validate.py` runs coverage validation after the existing record checks.
- `framework/build.py` emits bilingual jurisdiction, policy-area, coverage-matrix, task, candidate-source and comparison pages. Candidate displays are filtered to safe HTTPS, credential-free, non-IP, link-only leads with recorded display review metadata.
- `.github/workflows/pages.yml` runs the toolkit validator, toolkit tests, queue summary and `manifest.py --check` before building the site.
- `research-toolkit/tests/test_toolkit.py` covers the new validator, queue and manifest behavior.

Status vocabulary used by the coverage views is research activity only: `not_started`, `source_discovery`, `candidate_sources_identified`, `evidence_captured`, `provision_extraction`, `legal_review_pending`, `reviewed_findings`, `blocked`. It never asserts legal effect or compliance.

## Tranche 02 integration

Tranche 02 is imported through `research-toolkit/scripts/import_tranche.py`. The import is deterministic and idempotent and writes `research-toolkit/reconciliation/tranche-02-report.json`.

- **Inputs:** `incoming/tranche-02/candidate-sources.json`, `incoming/tranche-02/tasks.jsonl`, the canonical candidate inventory, policy records, jurisdiction and domain registries.
- **Outputs:** additions to `sources/candidate-sources.json`, `backlog/tasks-tranche-02.jsonl`, and the reconciliation report.
- **Result:** 14 candidates and 14 tasks imported; no matches, possible duplicates or conflicts against the existing inventory. The canonical inventory now holds 23 candidates; the combined queue holds 54 tasks.
- **Duplicate detection:** canonical URL first, then jurisdiction plus the primary instrument number, then jurisdiction plus title. A possible duplicate is held out of the import for human review and listed in the report. Title similarity alone never merges or drops a lead.
- **Legal status:** every imported candidate keeps `legal_effect: not_assessed`, `capture_status: not_captured` and `display_review.human_reviewed: false`. No capture, transcription, translation or review is claimed.
- **Relationships:** the reported 2025 amendment to Algeria's 2018 data protection law, the reported 2024 amendment to Iraq's 2013 disability law, and Somalia's reported 2026 regulations approval are stored as unreviewed candidate relations. They are not legal findings.
- **Provenance:** each imported record keeps the package path, incoming identifier, recorded date, source status, discovery note and the tranche's evidence reference. Turn-style evidence references are labelled as not independently checkable rather than presented as verification.
- **Language mapping:** `disability_rights` maps to the canonical `disability_inclusion` domain; all other domains and every source kind are mapped explicitly. Unmapped values block the import.

Run and verify:

```sh
python3 research-toolkit/incoming/tranche-02/validate.py
python3 research-toolkit/scripts/import_tranche.py
python3 research-toolkit/scripts/import_tranche.py --check
```

CI runs the package validator and the `--check` command, so a stale import or a package whose checksums no longer match fails the build.

## Evidence currency (work package 1)

The next milestone's first work package adds an explicit currency layer without fetching anything.

- `research-toolkit/sources/publishers.json` derives one entry per host cited by a candidate or policy record. Publisher name, authority type and verification status stay `null`/`unknown`/`unverified` until a human records them; the generator preserves human values.
- `research-toolkit/sources/source-checks.json` derives one check per candidate, initially `not_checked` with no date, HTTP status, final URL or content type. A check records retrieval health only.
- `research-toolkit/scripts/registry.py` regenerates both files deterministically and supports `--check`; CI runs it.
- Freshness is computed from the fixed `as_of` and `stale_after_days`, never from the build date, so generated output stays reproducible. A source without a recorded check is `not_checked`, not stale and not current.
- The sources page publishes publisher host, registry status, health state and last check date, with a notice that currency is unknown. Arabic labels are provisional.
- Out of scope for this package: live retrieval, change detection, instrument versions, French interface. Those remain separate work packages.

Run:

```sh
python3 research-toolkit/scripts/registry.py
python3 research-toolkit/scripts/registry.py --check
```

## CI recommendation
Add an isolated job for toolkit validator and unit tests, then fold selected checks into the repository's existing build after review. Do not make incomplete candidate sources appear as published legal records.

Status: applied in the repository workflow. The positive fixture is validated in CI; the intentionally invalid fixture is exercised by unit tests only. Tranche 02 is integrated and gated by the package validator plus `import_tranche.py --check`.
