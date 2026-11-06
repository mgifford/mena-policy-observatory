# Policy comparison and simulation contracts

## Comparison
Shared scenario inputs permit cross-country comparison only when the respective rules share a concept and explicitly compatible input definitions. Record mismatches: semantic, temporal, population, unit, evidence, legal effect, and source availability.

Example concepts:
- website_accessibility: covered organization, content scope, WCAG version/level, exceptions, effective dates;
- freedom_expression: restriction authorization, judicial/process safeguards, appeal (avoid binary 'freedom' scores);
- ai_governance: risk or sector scope, assessment duties, transparency, human oversight;
- data_centres: capacity threshold, energy/water reporting, metric units, exceptions;
- disability_inclusion: accommodation processes, built environment standards;
- immigration or SRHR: sensitive eligibility should use synthetic cases only.

## Model three separate outputs
1. **Rule application:** legal consequence conditional on a particular accepted interpretation.
2. **Coverage:** population/facility/agency share conditional on data quality and representativeness.
3. **Impact:** causal effects (environmental, economic, social) that require measured data and an explicit identification strategy. An Axiom trace is NOT causal evaluation.

## Required simulation metadata
Scenario ID, jurisdiction, as-of date, applicable rule IDs, input schema/version, non-sensitive synthetic input values or aggregate dataset URI + license/version, code/engine commit, evaluation result (permit/deny/indeterminate/not_applicable), explanation links, unresolved alternatives, assumptions, error bars/sensitivity where appropriate. For datasets record units and representativeness.

## Counterfactual comparison
A 'what if threshold changed' result is a mechanical policy change, not an estimate of behavioral response. Present uncertainty bands where data permit; no false policy quality ranking.
