# MENA Policy Observatory

Bilingual (English/Arabic), GitHub Pages-ready static research catalogue.

## Run

```sh
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 framework/build.py --region mena
python3 framework/check_html.py
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

## Bilingual content

Interface and homepage strings live in `regions/mena/i18n/en.json` and `regions/mena/i18n/ar.json`. The build fails if the two catalogues declare different keys, and unit tests check placeholders and value hygiene. Arabic page copy is a draft pending native-speaker review. Policy record fields have no Arabic translation; on Arabic pages they are shown in English with `lang`/`dir` marking and an explicit notice.

## Structured research data

Each policy directory contains a `research.json` alongside its Markdown artifacts. The file records sources, candidate provisions, interpretation questions and instrument relations in a machine-readable form. It never replaces the Markdown research notes, and it never records a legal conclusion: unknown values stay `"unknown"` or `null`, and unresolved questions stay unresolved.

`framework/validate.py` checks the file against `regions/mena/schemas/research-record.schema.json` and then applies semantic checks that a schema cannot express: reference integrity, ISO dates, excerpt and summary attribution to the Markdown artifacts, capture/checksum consistency, translation provenance, and review-state gates. Valid and invalid fixtures live in `tests/fixtures/research/`. See `docs/RESEARCH-MODEL.md`.

Record pages render the structured fields: recorded source metadata (issuer, jurisdiction, dates, version, capture state and translation state), any permitted excerpt with its locator, a provisions table with recorded locators, effect assessment and encoding status; the open interpretation questions with risk and what review they need; and recorded related instruments with their review state.

## Evidence limits

Country scope does not imply reviewed law. Source identification does not establish binding legal effect. RuleSpec files are non-executable research scaffolds with empty rule arrays. No conformance or legal-certification claims are made. Translations are research drafts pending qualified review. See `docs/BASELINE-AUDIT.md` for the current repository audit.

## Expansion

Add primary sources to `regions/mena/policies/` and maintain records in `regions/mena/data/policies.json`. Preserve original-language source text where licensing permits and link all claims to exact clauses. See `ACCESSIBILITY.md`, `CONTRIBUTING.md`, and `MIGRATION.md`.

## Research expansion (October 2026)

This version has seven policy records: four original national/guidance records, and three additional agency policy records (UAE Ministry of Education, UAE Ministry of Finance, Saudi Ministry of Economy and Planning). Each record now links to `PROVISIONS.md` research notes and a structured ambiguity register in its original artifacts.

The expansion does **not** create legally approved RuleSpec. Official source pages are linked; full primary-source transcriptions and native-language legal reviews are still needed. The regional UN ESCWA report is a secondary comparison source, not a substitute for legislation.

The next editorial phase should cover Egypt, Oman, Jordan, Morocco and Bahrain, but should only add findings once specific official instruments are independently verified.
