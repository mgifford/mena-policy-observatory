# MENA Policy Observatory

Trilingual (English/French/Arabic), GitHub Pages-ready static research catalogue.

## Run

```sh
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 framework/build.py --region mena
python3 framework/check_html.py
python3 research-toolkit/scripts/validate_packets.py research-toolkit/examples/valid-packet.json
python3 -m unittest discover -s research-toolkit/tests -p 'test_*.py' -v
python3 research-toolkit/scripts/report_queue.py research-toolkit/backlog/tasks.jsonl research-toolkit/backlog/cross-domain-tasks.jsonl research-toolkit/backlog/tasks-tranche-02.jsonl
python3 research-toolkit/scripts/import_tranche.py --check
python3 research-toolkit/scripts/registry.py --check
python3 research-toolkit/scripts/instruments.py --check
python3 framework/change_events.py --check
python3 research-toolkit/scripts/manifest.py research-toolkit --output research-toolkit/MANIFEST.json --check
python3 -m http.server 8000 --directory dist
```

Start at `http://localhost:8000/`. GitHub Actions publishes `dist/` on pushes to `main` after test checks. In GitHub repository Settings > Pages choose **GitHub Actions**.

Automated accessibility checks:

```sh
npm ci --no-audit --no-fund
npx playwright install chromium
npm run test:a11y
```

`npm run test:a11y` rebuilds `dist/` first and checks every generated HTML page: axe-core, keyboard skip-link focus, 320 CSS pixel reflow, unique titles, `hreflang` alternates, and language-switch equivalence. See `ACCESSIBILITY.md` for remaining gaps.

## Trilingual content

Interface and homepage strings live in `regions/mena/i18n/en.json`, `fr.json` and `ar.json`. Policy records can also record optional language expressions (original, additional authoritative, official translation, research translation, machine draft, pending, unavailable or unresolved) with per-text authority, method and review provenance. Candidate terminology lives in `regions/mena/data/terminology.json` and is explicitly draft, not a legal glossary. The build fails if the three catalogues declare different keys, and unit tests check placeholders and value hygiene. French and Arabic page copy are drafts pending native-speaker review. Policy record fields have no French or Arabic translation; on those pages they are shown in their source language with `lang`/`dir` marking and an explicit notice.

The root page detects the browser language for supported locales and sends French and Arabic visitors to the matching localized homepage; English visitors see the English chooser. Unsupported languages fall back to the English chooser, and `?lang=en`, `?lang=fr` or `?lang=ar` overrides detection. The localized URLs remain stable; the redirect is progressive enhancement and the chooser stays usable without JavaScript.

## Research coverage views

The site publishes trilingual (EN/FR/AR) coverage views generated from recorded evidence only. Tranche 02 is imported through `research-toolkit/scripts/import_tranche.py`, which is deterministic and idempotent and writes a reconciliation report:

- **Jurisdictions** (`countries.json`): the 24-entry geographic scope registry, with provisional Arabic names, group labels and scope notes, and reconciled aliases.
- **Policy areas** (`domains.json`): eight research domains grouped into five themes, with subtopics. English identifiers are canonical; Arabic labels are provisional drafts.
- **Coverage matrix**: one cell per jurisdiction and policy area, showing derived research status.
- **Research queue**: discovery and review tasks from `research-toolkit/backlog/`, including the 14 verification tasks supplied with tranche 02.
- **Candidate sources**: unreviewed discovery leads from `research-toolkit/sources/candidate-sources.json`, shown as link-and-metadata only, with the reported instrument identity, publisher host, publisher-registry status, version dates, captured-version state (metadata and checksum only), retrieval outcome, source freshness, legal-verification state, and any recorded source-change observation with its human review status and task. Types and numbers are parsed from reported titles and are not verified. Without a recorded retrieval, freshness is reported as not established rather than assumed, and legal verification stays unreviewed. No change observation means none was recorded by this project, not that legislation is unchanged.
- **Comparison**: recorded provisions flattened for side-by-side reading.

`framework/coverage.py` loads and validates the registries, derives every status from recorded evidence, and separates candidate discovery from source verification. Status vocabulary is about research activity, not compliance: `not_started`, `source_discovery`, `candidate_sources_identified`, `evidence_captured`, `provision_extraction`, `legal_review_pending`, `reviewed_findings`, `blocked`. An empty or not-started cell means this repository has not researched the combination; it is not evidence that no law or policy exists.

A candidate source lead is never promoted to a verified source or a legal finding by a successful build. Public pages mark every lead as an unreviewed discovery lead, link only, with no source text reproduced. Human review of all 23 current leads is still pending: nine from the earlier inventory and 14 imported from research tranche 02.

`reviewed_findings` requires recorded review evidence, not just an empty question list: a confirmed `legal_effect`, a complete `review` entry in `research.json` (reviewer, ISO date, scope) and no open interpretation question. A confirmed effect without that entry fails validation.

## Source verification pilot

Three existing candidates have recorded retrieval evidence in `research-toolkit/monitoring/source-captures.jsonl`: Algeria Law 25-11 (Official Gazette PDF), Bahrain Law 30/2018 (Legislation and Legal Opinion Commission landing page) and Oman's National Digital Accessibility Policy (MTCIT policy page). Bytes were hashed and not stored; no legal effect, authenticity or currency is established. See `docs/PILOT-REPORT.md` for selection reasons, checksums, limitations and outstanding review.

## Legislative visualizations

The public [visualizations](https://mgifford.github.io/mena-policy-observatory/mena/en/visualizations/) section shows recorded source structure for eleven existing research records and a clearly labelled synthetic Axiom/L4 demonstration. **This is a proof of concept for comparative legislation review, not authoritative.** Manual legal, language and accessibility review was deferred and has not been performed. Source structure is research in progress; candidate interpretation is not legally reviewed; no real reviewed executable rule is published. See [docs/VISUALIZATION-MILESTONE.md](docs/VISUALIZATION-MILESTONE.md).

## UAE accessibility deep dive

A source-linked briefing for the UAE conversation is in [docs/UAE-ACCESSIBILITY-DEEPDIVE.md](docs/UAE-ACCESSIBILITY-DEEPDIVE.md). It distinguishes federal law, policy, technical guidance, self-description and the observatory's candidate records. It is a prototype, not legal advice.

## Rules as Code

The homepage now includes a visible **Rules as Code** section with short, exact excerpts from the synthetic Axiom RuleSpec and Legalese L4 sources, plus a three-step Legalese-style evaluation ladder. The full synthetic page adds the machine-readable sources, dependency graph, complete ladder, accessible text equivalent and recorded engine outputs. The navigation exposes **Rules as Code** on every page.

This is still synthetic only. No real instrument has an approved executable encoding, Axiom has not been selected as a permanent engine, and Axiom/L4 semantics are not interchangeable. See [docs/RULES-ENGINE-COMPARISON.md](docs/RULES-ENGINE-COMPARISON.md).

## Rule presentation (synthetic only)

`framework/rule_presentation.py` validates and statically renders a reviewed `rule-presentation/v1` artifact. It is intentionally not attached to the public site; the only artifact is a synthetic fixture. See [docs/RULE-PRESENTATION.md](docs/RULE-PRESENTATION.md).

## Structured research data

Each policy directory contains a `research.json` alongside its Markdown artifacts. The file records sources, candidate provisions, interpretation questions and instrument relations in a machine-readable form. It never replaces the Markdown research notes, and it never records a legal conclusion: unknown values stay `"unknown"` or `null`, and unresolved questions stay unresolved.

`framework/validate.py` checks the file against `regions/mena/schemas/research-record.schema.json` and then applies semantic checks that a schema cannot express: reference integrity, ISO dates, excerpt and summary attribution to the Markdown artifacts, capture/checksum consistency, translation provenance, and review-state gates. Valid and invalid fixtures live in `tests/fixtures/research/`. See `docs/RESEARCH-MODEL.md`.

Record pages render the structured fields: recorded source metadata (issuer, jurisdiction, dates, version, capture state and translation state), any permitted excerpt with its locator, a provisions table with recorded locators, effect assessment and encoding status; the open interpretation questions with risk and what review they need; and recorded related instruments with their review state.

## Evidence limits

Country scope does not imply reviewed law. Source identification does not establish binding legal effect. RuleSpec files are non-executable research scaffolds with empty rule arrays. No conformance or legal-certification claims are made. Translations are research drafts pending qualified review. See `docs/BASELINE-AUDIT.md` for the current repository audit.

## Expansion

Add primary sources to `regions/mena/policies/` and maintain records in `regions/mena/data/policies.json`. Preserve original-language source text where licensing permits and link all claims to exact clauses. See `ACCESSIBILITY.md`, `CONTRIBUTING.md`, and `MIGRATION.md`.

## Research records and homepage discovery

This version has eleven policy records across six jurisdictions and three policy areas. They include national and agency records from the UAE, Saudi Arabia and Qatar, plus records for Algeria, Jordan and Morocco. Each record links to `PROVISIONS.md` research notes and a structured ambiguity register in its original artifacts.

The homepage derives its research snapshot from `policies.json`, `countries.json`, `domains.json` and the coverage model. It does not duplicate the full jurisdiction table; that table remains on the coverage pages. The expansion does **not** create legally approved RuleSpec. Official source pages are linked; full primary-source transcriptions and native-language legal reviews are still needed. The regional UN ESCWA report is a secondary comparison source, not a substitute for legislation.

The next editorial phase should cover Egypt, Oman, Jordan, Morocco and Bahrain, but should only add findings once specific official instruments are independently verified.
