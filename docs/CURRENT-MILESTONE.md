# Current Milestone: MENA Research Coverage Integration

**Status:** In progress  
**Working branch:** `feat/coverage-integration` (verify before use)  
**Priority:** P0  
**Next milestone:** Rules as Code proof of concept, not yet authorized

## Objective

Complete the existing research coverage integration and incorporate Research Tranche 02 into the MENA Policy Observatory.

Deliver a reproducible, accessible, bilingual research coverage interface with validated candidate sources, research tasks, and accurate status reporting.

This milestone is focused on completing existing work, not expanding project functionality.

## Authorized work

- Complete country and domain coverage implementation.
- Integrate `research-toolkit/incoming/tranche-02/`.
- Reconcile duplicate candidate sources and research tasks.
- Preserve source provenance and original research artifacts.
- Validate jurisdiction and domain identifiers.
- Display candidate sources and research status accurately.
- Maintain English and Arabic navigation.
- Fix implementation defects.
- Complete automated tests.
- Document manual accessibility and translation review requirements.
- Prepare the implementation for human review.

## Prohibited work during this milestone

Do not:

- Implement new executable Axiom RuleSpec.
- Introduce new Axiom runtime dependencies.
- Build policy simulation or impact modeling functionality.
- Conduct unrelated new legal research.
- Add unrelated policy domains.
- Refactor unrelated infrastructure.
- Invent legal interpretations, translations, review approvals, or source metadata.
- Treat candidate sources as verified legal findings.
- Merge PRs autonomously.
- Begin the next milestone without authorization.

Existing research evidence and non-executable RuleSpec scaffolds must be preserved.

## Research integration requirements

Research Tranche 02 contains 14 unreviewed source leads and 14 tasks across nine jurisdictions.

The package is located at:

`research-toolkit/incoming/tranche-02/`

Validate it using:

```bash
python3 research-toolkit/incoming/tranche-02/validate.py
```

Integrate candidate sources without changing their legal-review status.

The integration must be idempotent. Repeated imports must not create duplicates.

Maintain separate status dimensions for:

- Research progress.
- Source verification.
- Legal effect.
- Translation review.
- Provision extraction.
- Rules as Code implementation.

Unknown or unreviewed values must not be converted into negative legal findings.

## Accessibility requirements

Target WCAG 2.2 AA.

Required automated checks include:

- Semantic HTML structure.
- Correct document languages and text direction.
- Keyboard skip links.
- Unique page titles.
- Accessible tables.
- Reflow.
- English/Arabic navigation equivalence.
- Automated axe-core checks.

Manual keyboard, screen-reader, zoom, forced-colour, and Arabic-language reviews must be documented separately.

Automated tests do not establish full WCAG conformance.

## Completion checklist

- [ ] Current implementation functionality completed.
- [ ] Country registry reconciled.
- [ ] Domain registry validated.
- [ ] Tranche 02 integrated or explicitly deferred with documented justification.
- [ ] Duplicate source and task handling tested.
- [ ] Candidate sources remain unreviewed.
- [ ] Existing published research records preserved.
- [ ] Country and domain coverage pages generated.
- [ ] Research statuses displayed accurately.
- [ ] English and Arabic navigation works.
- [ ] Automated accessibility tests pass.
- [ ] Python validation and unit tests pass.
- [ ] Static site builds reproducibly.
- [ ] Documentation matches implemented behavior.
- [ ] Pull request prepared for human review.

## Required verification commands

```bash
python3 research-toolkit/incoming/tranche-02/validate.py
python3 framework/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s research-toolkit/tests -p 'test_*.py' -v
python3 framework/build.py --region mena
python3 framework/check_html.py
npm run test:a11y
git diff --check
```

Report any checks that could not be completed.

## Deliverables

The final report must include:

1. Baseline commit and branch.
2. Completed implementation work.
3. Files changed and why.
4. Source and research task reconciliation results.
5. Data migrations and compatibility concerns.
6. Test results.
7. Accessibility review status.
8. Translation limitations.
9. Legal claims changed, if any.
10. Outstanding blockers.
11. Pull request URL.
12. Rollback instructions.
13. Recommended next milestone.

## Stop condition

Once implementation and validation are complete, prepare the PR and stop.

Do not begin Rules as Code, policy simulation, new legal research, or another implementation phase.

Wait for explicit authorization.

**Success means a complete, reviewable implementation, not a larger quantity of unverified research.**