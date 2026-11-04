# Accessibility acceptance criteria

Target WCAG 2.2 AA, without implying automated checks prove conformance.

## Automated pull request gates (implemented)
- Validate record structure: unique IDs, secure official source URLs, required research artifacts, allowed execution status.
- Run unit tests for the structure validator with valid and invalid fixtures.
- Run unit tests for the bilingual string catalogues: matching keys and placeholders, no empty values, no HTML in values, and no unmarked Latin text in Arabic UI strings.
- Lint every generated HTML page for document language/direction, one `main` landmark with `tabindex="-1"`, one `h1`, heading order, a working skip link, unique descriptive titles, `dir` on foreign-language elements, table captions and `th` scope, resolvable local links, and non-empty link names.
- Rebuild the site and fail if committed `dist/` differs from generated output.
- Run Playwright + axe-core on all 17 generated HTML pages, plus keyboard skip-link focus, 320 CSS pixel reflow, unique titles, `hreflang` alternates, and language-switch equivalence for every page.

The 320 CSS pixel check approximates the WCAG 1.4.10 reflow requirement at 1280 px width and 400% zoom. It is not a substitute for testing real browser zoom.

## Known automation gaps
These are required before making conformance claims and are not yet checked in CI:
- Raw research artifacts are still linked as `.md`, `.json`, and `.yaml` files rather than rendered as accessible HTML with locators and review state.
- JSON Schema validation of policy records; see `docs/BASELINE-AUDIT.md` §4.3.
- External link liveness, real browser zoom and text spacing, forced colours, touch targets, print layout, and manual screen-reader behaviour.
- Arabic record content is still the source-language text, marked as English. No Arabic record translation exists, and the Arabic interface text is a draft pending native review.
- No automated check can decide whether wording is meaningful, whether a translation is accurate, or whether a legal-effect label is correct.

## Manual release checklist
- [ ] Keyboard-only navigation, language switch, table region, and source links.
- [ ] Screen reader: NVDA/Firefox and VoiceOver/Safari; verify table row and column announcements.
- [ ] Browser zoom 200% and 400%; text spacing and reflow.
- [ ] RTL Arabic, embedded Latin identifiers, Arabic punctuation, screen reader language announcements.
- [ ] Forced colors, high contrast, reduced motion and touch targets.
- [ ] Native Arabic review for meaning and terminology; record the reviewer with consent.
- [ ] User testing with disabled contributors, including cognitive accessibility and authoring workflow.

CI is a minimum gate, not a replacement for this checklist. Any exception requires a documented issue, owner, and expiry.
