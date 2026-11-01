# Working with a coding agent and a research reviewer

1. Coding agent starts at `prompts/00-audit.md`; do not ask it to perform every phase in one context window.
2. Agent works on a branch. CI and a human reviewer check each PR. Do not merge automatically.
3. After Phase 1, complete Phase 2 before asking for any actual executable legal rules.
4. Research reviewer produces a clause-specific evidence packet in `examples/research-packet.json` shape, separately from code edits; include exact official source, locator, translation provenance and unresolved issues.
5. Legal/domain reviewer resolves or documents ambiguity; the coding agent handles schema, rendering and tests but cannot set review state to approved by itself.
6. Axiom changes require a pinned engine, compiler run and explicit test evidence; an empty `rules:` list is not a working rule.

## Agent report template
- Baseline commit SHA and branch
- Changes made and intentionally omitted (with reasons)
- Files added/changed/deleted
- Evidence and primary source URLs for every legal claim
- Automated tests (commands, results); manual tests performed/not performed
- Accessibility of Arabic/English pages
- Unresolved questions and risk
- PR link and rollback procedure
