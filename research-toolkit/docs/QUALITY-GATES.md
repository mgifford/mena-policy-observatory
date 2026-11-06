# Quality gates and evaluation design

## Layered release decisions
**G0 tooling:** reproducible deterministic build, schema tests, accessibility checks and CI passing.
**G1 discovery:** official-looking source lead with type and query provenance; may be shown as unreviewed discovery only.
**G2 source:** exact authority, source language, version, capture details and locator validated.
**G3 interpretation:** human review recorded; competing readings documented; legal effect separate from evidence strength.
**G4 encoding:** pinned Axiom compiler passes and adversarial, negative, boundary, missing-data and temporal cases pass.
**G5 publication:** independent substantive review, Arabic/English parity review, accessible rendering; update and correction mechanism.

## Proposed benchmark (targets, not measured performance)
Prepare at least 30 independently annotated examples from 3+ jurisdictions and 3+ instrument types. Include negatives: draft law, repealed clause, false amendment, inaccessible PDF, conflicting Arabic/English text, retroactive effect, ambiguous scope, and nonexistent citation.

Measure:
- citation correctness (exact URL + page/article); invalid citations count separately;
- clause extraction precision and recall;
- date/threshold extraction exactness;
- correctly identified ambiguous cases (recall);
- false legal-effect elevation (must be zero for publication);
- rule execution discrepancies vs separate reviewer-provided fixtures;
- translation adequacy and terminology exceptions;
- human correction time and accepted research throughput;
- full CI reproducibility and human manual accessibility results.

An LLM's self-rating or agreement between two models is not independent legal validation.

## Failure policies
Invalid source hash, missing locator for a legal claim, unresolved critical ambiguity in a purportedly reviewed rule, or fabricated review metadata must block publication. Network/source unavailability should mark a source stale, not automatically delete a previously verified record.
