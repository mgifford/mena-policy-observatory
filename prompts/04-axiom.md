# Phase 4: Axiom research prototype, not automated legal certification

Read AGENTS.md, current pinned Axiom documentation, source records and approved interpretation metadata. Select exactly one narrowly defined provision with unambiguous, source-verified deterministic conditions; otherwise write an explicit blockers report and do not invent a law-like rule.

Create an engine-independent policy test case contract (inputs, expected outcome incl. indeterminate, citation, scenario notes, reviewer status). Then add Axiom RuleSpec for the approved subset only. Confirm actual RuleSpec v1 schema and compiler semantics against a pinned engine commit; run compile, positive, negative, boundary, missing-input and version-date tests. Any unsupported legal semantics must remain explicit as unresolved issue IDs, not implicit defaults. Use date values only when verified; never insert dummy legal effective dates to make compilation pass.

Produce `docs/rules-as-code.md` for nontechnical readers, a machine-executable or blocked example, reproducibility instructions, and a comparison of human interpretation versus engine result. Store engine version/pin and test outputs in reviewed evidence. Do not say approved/certified without independent legal validation. Deliver PR and blockers list.
