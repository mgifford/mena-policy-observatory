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

## CI recommendation
Add an isolated job for toolkit validator and unit tests, then fold selected checks into the repository's existing build after review. Do not make incomplete candidate sources appear as published legal records.

Status: applied in the repository workflow. The positive fixture is validated in CI; the intentionally invalid fixture is exercised by unit tests only.
