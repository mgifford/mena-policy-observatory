# Accessibility acceptance criteria

Target WCAG 2.2 AA, without implying automated checks prove conformance.

## Automated pull request gates (implemented)
- Validate record structure: unique IDs, secure official source URLs, required research artifacts, allowed execution status.
- Run unit tests for the structure validator with valid and invalid fixtures.
- Lint generated HTML for document language/direction, one `main` landmark, one `h1`, skip-link presence, and `th` scope.
- Rebuild the site and fail if committed `dist/` differs from generated output.
- Run Playwright + axe-core for the two MENA landing pages (`/mena/en/`, `/mena/ar/`) when Node dependencies are installed.

## Known automation gaps
These are required before making conformance claims and are not yet checked in CI:
- Root, record, and raw-artifact pages are not covered by axe tests.
- Page-title uniqueness, heading order, mixed-language marking, 320 CSS pixel overflow, local-link resolution, language-switch equivalence, and accessible artifact rendering.
- JSON Schema validation of policy records; see `docs/BASELINE-AUDIT.md` §4.3.

## Manual release checklist
- [ ] Keyboard-only navigation, language switch, table region, and source links.
- [ ] Screen reader: NVDA/Firefox and VoiceOver/Safari; verify table row and column announcements.
- [ ] Browser zoom 200% and 400%; text spacing and reflow.
- [ ] RTL Arabic, embedded Latin identifiers, Arabic punctuation, screen reader language announcements.
- [ ] Forced colors, high contrast, reduced motion and touch targets.
- [ ] Native Arabic review for meaning and terminology.
- [ ] User testing with disabled contributors, including cognitive accessibility and authoring workflow.

CI is a minimum gate, not a replacement for this checklist. Any exception requires a documented issue, owner, and expiry.
