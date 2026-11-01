# Phase 1: understandable and accessible homepage

Read AGENTS.md and docs/BASELINE-AUDIT.md. Implement a substantial, plain-language bilingual explanation of the project on the root landing page and `/mena/en/`, `/mena/ar/` without changing policy claims.

Content requirements: explain what the observatory is, why readers should use it, what Rules as Code means, how Axiom/RuleSpec relates to laws and human interpretation, how source -> clause -> interpretation -> candidate rule -> test -> independent review works, and why empty or uncertain findings do not establish no law. Name current pilot: UAE, Saudi Arabia, Qatar. Clearly state that no current machine-executable rule has legal certification unless independently documented. Link to repository, methodology, source records, and accessible comparison.

Implementation requirements: accessible navigation and breadcrumbs; persistent language switching between equivalent pages; correct `lang`/`dir`; proper mixed-language markup; responsive layout; structured explanation rather than jargon; no CSS-only content; no inferred country ranking. Move locale strings into maintained translation files where practical.

Validation: run both-language Playwright/axe checks; keyboard navigation; 320 px reflow; 200/400% zoom; automated checks for broken local links, heading order and accessible names; manual test checklist. Do not claim tests that were not run.

Deliver one narrow PR with screenshots, test evidence, unchanged legal record counts, and accessibility review notes. No new legal claims.
