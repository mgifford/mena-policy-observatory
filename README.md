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

`npm run test:a11y` rebuilds `dist/` first and covers the two MENA landing pages only. See `ACCESSIBILITY.md` for remaining gaps.

## Evidence limits

Country scope does not imply reviewed law. Source identification does not establish binding legal effect. RuleSpec files are non-executable research scaffolds with empty rule arrays. No conformance or legal-certification claims are made. Translations are research drafts pending qualified review. See `docs/BASELINE-AUDIT.md` for the current repository audit.

## Expansion

Add primary sources to `regions/mena/policies/` and maintain records in `regions/mena/data/policies.json`. Preserve original-language source text where licensing permits and link all claims to exact clauses. See `ACCESSIBILITY.md`, `CONTRIBUTING.md`, and `MIGRATION.md`.

## Research expansion (October 2026)

This version has seven policy records: four original national/guidance records, and three additional agency policy records (UAE Ministry of Education, UAE Ministry of Finance, Saudi Ministry of Economy and Planning). Each record now links to `PROVISIONS.md` research notes and a structured ambiguity register in its original artifacts.

The expansion does **not** create legally approved RuleSpec. Official source pages are linked; full primary-source transcriptions and native-language legal reviews are still needed. The regional UN ESCWA report is a secondary comparison source, not a substitute for legislation.

The next editorial phase should cover Egypt, Oman, Jordan, Morocco and Bahrain, but should only add findings once specific official instruments are independently verified.
