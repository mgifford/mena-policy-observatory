# MENA Policy Observatory: Agentic Research Toolkit

**Status:** Additive research toolkit. Not a legal database, authoritative translation, approved Axiom encoding, or deployable replacement website.

Prepared for: https://github.com/mgifford/mena-policy-observatory (repository inspected 2026-11-05).

## Start here

1. Read `docs/OPERATING-MANUAL.md` and `docs/REPO-INTEGRATION.md`.
2. Copy this toolkit into a NEW feature branch under `research-toolkit/` (recommended). Do not overwrite `AGENTS.md`, `framework/`, `regions/mena/policies/`, or existing schemas.
3. Run `python3 research-toolkit/scripts/validate_packets.py research-toolkit/examples/valid-packet.json` and `python3 -m unittest discover -s research-toolkit/tests -v`.
4. Give your local agent `agents/00-controller.md` and exactly ONE task from `backlog/tasks.jsonl`, plus `agents/01-source-discovery.md` or the matching stage prompt.
5. Keep any discovered documents in `research-toolkit/work/` (not tracked without review). Submit source pointers and citations, not invented legal assertions.
6. Produce **candidate** packets and open PRs. Reviewers, not agents, authorize legal-effect or translation claims.

## What's inside

- `agents/`: staged, bounded prompts with hard-stop and handoff contracts.
- `backlog/`: 24 proposed geographic entries, domain inventory, prioritised tasks, and small starter queue for all recorded jurisdictions.
- `sources/`: previous official-site **candidate leads** and authoritative research portals, not verified law.
- `templates/`: source, interpretation, relationship, Axiom, review, PR and research packet scaffolds.
- `schemas/`: standalone packet JSON Schema, deliberately not replacing the existing `regions/mena/schemas/` model.
- `scripts/`: offline packet validator, output manifest, and queue summaries. Network/model calls are intentionally excluded.
- `tests/`: positive and negative test fixtures.
- `docs/`: methodology, provenance, quality gates, accessible site patterns, privacy, threat modeling, internationalization, comparison and modeling.

## Critical boundaries

- A source lead is **not** proof that a law exists, is current, binding, or applicable.
- A generated Markdown transcription is **not** an authenticated original until checked against captured bytes by a reviewer.
- No invented legal citations, translations, source hashes, date claims, reviewers, or approvals.
- No auto-publishing, no autonomous merging, no raw personal case details, no unsupported country rankings.
- LLM outputs can vary. Preserve input hashes, model identifiers, prompts, exact outputs, review history and deterministic validator results.
- The included RuleSpec file is an empty, explicitly non-executable scaffold. Do not infer compliance from it.

## Quick commands

```sh
python3 scripts/validate_packets.py examples/valid-packet.json
python3 -m unittest discover -s tests -v
python3 scripts/report_queue.py backlog/tasks.jsonl
python3 scripts/manifest.py . --output /tmp/mena-toolkit-manifest.json
```

See `docs/REPO-INTEGRATION.md` before merging any of this into an existing repository.
