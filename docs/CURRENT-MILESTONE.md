# Current Milestone: MENA Research Coverage Integration

**Status:** Implementation complete — manual and professional review outstanding\
**Working branch:** delivered on `main` (commit `4b3c13a`); see the completion record below\
**Priority:** P0\
**Next milestone:** trilingual research foundation (proposed in `docs/ROADMAP.md`; not authorized)

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

- [x] Current implementation functionality completed.
- [x] Country registry reconciled.
- [x] Domain registry validated.
- [x] Tranche 02 integrated.
- [x] Duplicate source and task handling tested.
- [x] Candidate sources remain unreviewed.
- [x] Existing published research records preserved.
- [x] Country and domain coverage pages generated.
- [x] Research statuses displayed accurately.
- [x] English and Arabic navigation works.
- [x] Automated accessibility tests pass.
- [x] Python validation and unit tests pass.
- [x] Static site builds reproducibly.
- [x] Documentation matches implemented behavior.
- [x] Pull request prepared for human review and merged.

## Implementation completion record

- **Completed:** 2026-11-06.
- **`main` commit:** `4b3c13a` (merge of PR #12).
- **Delivered by:** PR #8 (coverage layer), PR #9 (review gate and Arabic labels), PR #10 (tranche 02), promoted to `main` by PR #12; PR #11 committed these instructions.
- **Research data:** 23 candidate leads (14 imported from tranche 02, all unreviewed), 54 queued tasks, 3 unreviewed reported relationships.
- **Generated site:** 93 HTML pages; `research-toolkit/MANIFEST.json` covers 59 files.
- **Verification on `main`:** tranche-02 validator PASS; `framework/validate.py` exit 0; 124 repository tests and 15 toolkit tests pass; `import_tranche.py --check` current; `build.py` and `check_html.py` pass for all 93 pages; Playwright/axe 281 pass; rebuilding leaves `dist/` unchanged.
- **Deployment:** GitHub Pages run `42259556896` succeeded; sampled English and Arabic pages are byte-identical to committed `dist/`. Two earlier `main` runs (for #11 and #8) failed in `actions/deploy-pages@v5` after successful builds; the final deployment succeeded.
- **Not claimed:** legal effect, source verification, translation quality or WCAG conformance.

## Outstanding manual and professional review

These are release conditions, not implementation gaps. Ticking the checklist above does not satisfy them.

- [ ] Manual keyboard-only walkthrough.
- [ ] Screen reader: NVDA/Firefox and VoiceOver/Safari, including table and description-list navigation.
- [ ] Browser zoom 200% and 400%; text spacing and reflow.
- [ ] Forced colours, reduced motion and touch targets.
- [ ] Native-Arabic review of interface strings, including the new candidate metadata labels.
- [ ] Human verification of all 23 candidate leads: official source, issuing authority, legal scope, authoritative language and publication permissions.

## Next milestone

Proposed in `docs/ROADMAP.md`: **Milestone 1 — trilingual research foundation** (English, French and Arabic). It is not authorized by this milestone and must not begin without an explicit instruction.

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