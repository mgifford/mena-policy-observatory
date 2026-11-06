# Accessibility and multilingual acceptance checks

WCAG 2.2 AA is the test target; passing axe-core is not conformance certification.

## English/Arabic UI
- Separate route for each locale, `html lang="en" dir="ltr"` or `lang="ar" dir="rtl"`.
- Source excerpts preserve source language with `lang` and `dir`; use `<bdi>` for unknown-direction inline user strings where appropriate.
- Maintain stable provision IDs and exact locale-equivalent links, with `hreflang`.
- Arabic legal translations must disclose `machine_draft`, `human_draft` or `reviewed`; avoid silent fallbacks.
- Test visual bidi for numerals, dates, citations, code, file paths and punctuation.
- For French, Persian, Hebrew or Somali source excerpts, mark actual source language; don't automatically translate into English.

## Comparison UI
- Use real table captions and `th scope` row/column cells; table scroll must be keyboard accessible.
- Disclose source, legal status and ambiguity in visible text, not color-only markers.
- Graphs and maps require equivalent accessible lists/data tables.
- No default country quality rankings.
- Show 'not researched', 'not located in documented search', 'legal status uncertain' distinctly.

## Checks
Automated: existing Playwright/axe suite, unique titles, language-switch parity, skip links, responsive 320px, forced-colors smoke test if added.
Manual: NVDA/Firefox, VoiceOver/Safari, Arabic screen reader speech, zoom 200/400%, keyboard, text spacing, reduced motion, cognitive readability, native Arabic language review, disabled contributors testing research workflow.

See existing repository `ACCESSIBILITY.md`; do not replace it.
