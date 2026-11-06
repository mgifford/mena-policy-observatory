# Operating manual: human-led research, agent-supported work

## Research pipeline

1. **Discovery:** record candidate official sources and source type. Avoid declaring legal effect.
2. **Capture:** retrieve only when permitted. Store exact bytes where licensing/security permits. Hash actual captured bytes with SHA-256. Record retrieval time and content type.
3. **Transcription:** produce original-language Markdown with exact page/article/paragraph locators; distinguish quoted text from editorial annotation. Never fabricate a missing clause.
4. **Translation:** record language, approach, translator, translation version and review status. A generated draft is a draft.
5. **Extraction:** record discrete rights, obligations, restrictions, definitions, authorities, exceptions, dates and cross-references.
6. **Interpretation:** describe competing readings and unresolved questions. Explicitly indicate whether the rule is deterministic, conditional, discretionary or not codable.
7. **Challenge:** a separate review pass tests counterexamples, source disagreement, amendments, scope and missing evidence.
8. **Formalization:** only reviewed, suitably precise propositions receive candidate RuleSpec. Pin the exact engine commit. Validate the syntax independently.
9. **Independent review:** qualified region/language/legal experts record their own approval or rejection. Agents cannot set approval flags.
10. **Publication:** render accessible English/Arabic views with provenance. Human-approved PR, no direct writes to main.

## Evidence classes
- **PRIMARY_AUTHENTICATED:** exact official original sourced, captured, compared, and checked by a human.
- **PRIMARY_LOCATED:** official document lead, original bytes not yet authenticated.
- **SECONDARY:** NGO, academic, media, database, or agency summary of legislation; never substitute for legal text.
- **DERIVED:** model interpretation or extracted structured data, explicitly tied to sources.
- **OBSERVED:** independently collected implementation/case measurement; do not conflate with laws.

## Status axes (never collapse)
Source state: candidate / captured / text_verified.
Legal effect: not_assessed / indeterminate / nonbinding_confirmed / binding_confirmed / not_in_force_confirmed.
Translation: not_available / machine_draft / human_draft / reviewed.
Encoding: blocked / candidate / compiled / tested / legally_reviewed.
Research coverage: not_started / discovery / source_verified / clause_reviewed.

## Publishability conditions
- Every legal claim links to an exact source locator and explicit evidence type.
- Candidate transcription and translation are visibly labeled.
- Affected jurisdiction / organization / period are recorded; unknown is not false.
- No executable rule has unresolved critical semantics.
- No sensitive case data collected in git history.
- English/Arabic page behavior and WCAG 2.2 AA test requirements are addressed.

## Exit on uncertainty
If a source conflicts with another source, the original is inaccessible, legal authority is unclear, or translation changes normative strength, the agent stops and opens a review question. Do not guess or resolve by majority vote among models.

## Practical first run
Use `backlog/tasks.jsonl` and `agents/01-source-discovery.md` for one jurisdiction-domain. Then `agents/02-capture-transcribe.md` for a human-authorized document, `agents/03-provisions.md`, and `agents/04-challenge.md`. Only after source and interpretation review use `agents/05-axiom.md`.
