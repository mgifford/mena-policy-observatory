# Phase 2: source and provision data architecture

Read AGENTS.md and merged Phase 0/1 output. Build additive machine-readable provision, source, ambiguity and relationship schemas. Preserve all existing seven policy IDs and their Markdown source artifacts. Never migrate or rewrite legal text silently.

Each provision must link to one or more authoritative source records with jurisdiction, issuer, original-language metadata, exact clause locator, archival URL when available, effective/publication dates or `unknown`, document version, and source capture information (SHA-256 only if actual captured bytes exist). Track translation status separately from source authentication and legal-effect verification.

Add explicit tri-state or richer judgments (e.g., applies, does not apply, indeterminate), but never map missing evidence to a negative legal conclusion. Interpretation questions have persistent IDs, alternatives, review state, reason and references. Distinguish instrument relations such as cites, amends, supersedes, transposes, implements, incorporates and guidance-for.

Implement validation: schema, unique IDs, references resolve, allowed statuses, dates and temporal consistency, file existence, orphaned provisions, relationship cycles where inappropriate, source excerpt attribution, and unreviewed claims. Test positive and negative fixtures. Generated HTML pages must show provision, permitted original excerpt or complete licensed text, reviewed/unreviewed translation, related documents, uncertainty, and candidate rule status.

Deliver one PR with migration summary, backward compatibility checks, fixtures, accessibility checks, clear description of unverified research fields. Do not invent missing source excerpts or approvals.
