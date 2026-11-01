# Accessibility acceptance criteria

Target WCAG 2.2 AA, without implying automated checks prove conformance.

## Automated pull request gates
- Validate schema, preserve authoritative source references and unresolved interpretations.
- Lint generated HTML for document language, single main landmark, heading and scope semantics, skip navigation.
- Run Playwright + axe-core for all four regional/language landing pages and sample detail pages when Node dependencies are available.
- Test no horizontal body overflow at 320 CSS pixels; scrolling inside labelled comparison table regions may be necessary.

## Manual release checklist
- [ ] Keyboard-only navigation, language switch, table region, and source links.
- [ ] Screen reader: NVDA/Firefox and VoiceOver/Safari; verify table row and column announcements.
- [ ] Browser zoom 200% and 400%; text spacing and reflow.
- [ ] RTL Arabic, embedded Latin identifiers, Arabic punctuation, screen reader language announcements.
- [ ] Forced colors, high contrast, reduced motion and touch targets.
- [ ] Native Arabic review for meaning and terminology.
- [ ] User testing with disabled contributors, including cognitive accessibility and authoring workflow.

CI is a minimum gate, not a replacement for this checklist. Any exception requires a documented issue, owner, and expiry.
