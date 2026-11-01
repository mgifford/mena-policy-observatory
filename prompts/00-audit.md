# Phase 0: repository reconnaissance (no implementation)

You are taking over https://github.com/mgifford/mena-policy-observatory. Read AGENTS.md and README.md fully. Examine the current default branch, git status, framework, region data, CI, accessibility tests, and deployed output. This project is a bilingual English/Arabic policy observatory; seven existing digital-accessibility document records are an initial corpus, not legally verified executable rules.

Tasks:
1. Produce a factual inventory of all source/data/build/test files, generated outputs, and existing country/provision coverage. Confirm presence or absence of `profiles.json`, `provisions.json`, `validate_provisions.py`, `capture_source.py`, and the Axiom explanatory page. Do not assume any file is present because an earlier chat mentions it.
2. Reproduce current build/tests. Record versions, commands, output, failures and missing dependencies. Confirm GitHub Pages link paths and both language directions.
3. Identify concrete defects, especially language switch from nested pages, homepage explanation, inaccessible Markdown-only links, ambiguous provenance states, XSS/HTML escaping, inconsistent data, and unsupported legal-status claims.
4. Propose a prioritized issue backlog with dependencies and measurable acceptance criteria. Distinguish verified defects from hypotheses. Assess whether a simple standard-library generator remains adequate.
5. Create a branch and a documentation-only PR: `docs/BASELINE-AUDIT.md`, no unrelated implementation changes. Do not merge.

Report: existing branch SHA, paths inspected, factual findings, risks, and recommended next PR. Do not research new national laws in this phase.
