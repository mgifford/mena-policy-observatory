# Current Milestone: Three-Source Verification and Monitoring Pilot

**Status:** In progress — evidence captured, review outstanding\
**Priority:** P0\
**Baseline:** `main` at `4257c1f`\
**Working branch:** `feat/source-verification-pilot` (verify before use)\
**Report:** `docs/PILOT-REPORT.md`\
**Later milestones:** public digital policy research, then reviewed Rules as Code. Neither is authorized.

## Objective

Verify and monitor three existing authoritative legal or policy sources already represented by candidate leads. Record real retrieval evidence, distinguish technical observations from legal conclusions, and exercise the human review workflow without performing a broad crawl or creating new legal findings.

## Authorized work

- Select three existing candidates with documented rationale.
- Record publisher identity evidence, jurisdictions, languages and retrieval constraints.
- Retrieve each source once with bounded, respectful requests; record actual HTTP outcomes, content type, length, timestamp and SHA-256.
- Record capture metadata and checksums without storing or redistributing full text unless permitted.
- Update source-health records from the actual retrieval result.
- Record real change observations only if an actual difference is observed; do not create an event for an initial capture with no prior version.
- Exercise review tasks and decisions with synthetic fixtures where no real change exists.
- Publish source health, captured version metadata and review status in the three interface languages.
- Document evidence, failures, limitations and outstanding review.

## Prohibited work

Do not:

- Add countries, domains or research questions beyond the three selected candidates.
- Crawl broadly, schedule a monitoring service, bypass access controls or ignore robots policies.
- Store or redistribute full text without a permitted basis.
- Treat a successful retrieval or byte difference as legal verification or an amendment.
- Generate legal translations, reviewer identities, approvals, dates or checksums.
- Modify a policy record's legal effect or mark a source legally reviewed.
- Implement Axiom/RuleSpec, a rules engine or policy simulation.
- Merge pull requests autonomously.
- Begin the research-expansion or Rules as Code milestones.

## Completion criteria

- [x] Three existing candidates selected with documented reasons.
- [x] Actual retrieval attempts and outcomes recorded.
- [x] Publisher identities evidenced or explicitly unresolved.
- [x] Source versions and capture metadata traceable.
- [x] Source checks updated from real outcomes; legal verification remains unreviewed.
- [ ] Human review of source adequacy, identity and legal significance.
- [x] Change detection workflow exercised with synthetic fixtures only.
- [x] Monitoring failures and limitations documented.
- [x] No source promoted to a legal finding.
- [ ] Native Arabic/French and manual accessibility review.
- [x] Static build reproducible and automated checks passing.
- [x] Focused PR prepared for review.

## Required verification commands

```bash
python3 framework/validate.py
python3 framework/change_events.py --check
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s research-toolkit/tests -p 'test_*.py' -v
python3 research-toolkit/scripts/registry.py --check
python3 research-toolkit/scripts/instruments.py --check
python3 research-toolkit/scripts/import_tranche.py --check
python3 framework/build.py --region mena
python3 framework/check_html.py
npm run test:a11y
git diff --check
```

Manual keyboard, screen-reader, zoom, forced-colour and native-language review remain separate release conditions. Automated tests do not establish WCAG conformance.

## Stop condition

Prepare the pilot PR and stop. Do not start a monitoring schedule, recapture, legal review or the next milestone without an explicit instruction.
