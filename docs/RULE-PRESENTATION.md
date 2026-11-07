# Rule presentation renderer (synthetic follow-up)

**Status:** authorized follow-up to the merged rules-engine research ([PR #21](https://github.com/mgifford/mena-policy-observatory/pull/21)). **Synthetic fixture only.** The renderer is not attached to the public site, no real rule is encoded, and the active three-source pilot is unchanged.

The design recommendation in [RULES-ENGINE-COMPARISON.md](RULES-ENGINE-COMPARISON.md) was to keep the durable part of a future rules feature—the reviewed presentation contract—separate from any execution engine. This follow-up implements that part:

- `regions/mena/schemas/rule-presentation.schema.json` — the `rule-presentation/v1` shape.
- `framework/rule_presentation.py` — shape and review-gate validation, plus a standard-library static HTML/SVG renderer.
- `tests/fixtures/rule-presentation/synthetic-procurement.json` — a fictional fixture from the research prototype.
- `tests/test_rule_presentation.py` — validation, gate, rendering, trilingual and structural tests.

No Axiom/L4 runtime, dependency, API, model call or client-side execution is used. The renderer never changes a policy record or legal-effect status.

## Contract

A presentation is a read-only artifact derived from a reviewed interpretation. It has:

- identity: `format`, `id`, `version`, `synthetic`;
- review gate: `status` (`synthetic_fixture` or `reviewed`), reviewer role, review date, notes;
- record chain for non-synthetic artifacts: instrument, source, provision, legal version and reviewed-interpretation IDs;
- localized title, summary and disclaimer in English, French and Arabic;
- effective-period bounds with explicit open end;
- provenance: encoding ID, engine, engine version, artifact SHA-256 and test-results location;
- source references with localized citation/label, HTTPS URL and source language;
- nodes: input, constant or computed; dtype; value; dependencies; citation;
- ladder: ordered condition, true branch, false branch, citation and note;
- a complete localized linear explanation, unknown-state text and limits;
- explicit unsupported/out-of-scope semantics.

The schema is enforced with the repository's small schema validator. Cross-field validation additionally checks:

- synthetic artifacts cannot attach to an observatory record and must use synthetic `example.org` sources;
- reviewed artifacts require the full record chain, reviewer role, review date, real HTTPS sources and an artifact SHA-256;
- dependency targets exist, no self-dependency and no cycle;
- citations resolve to a declared source;
- ladder steps are consecutive from 1;
- every locale has one text step per ladder step;
- effective dates are valid and ordered;
- constants have values;
- duplicate nodes/sources and unknown fields fail.

A reviewed presentation is **still not legal verification**. The review fields describe an interpretation review; they do not prove the instrument's current legal effect.

## Renderer

`render_page(data, lang, strings)` produces one static HTML document. `render_all(data, out_dir, catalogues)` writes English, French and Arabic pages. UI labels come from the existing i18n catalogues; content comes from the presentation.

The page contains:

1. a dependency graph: inline SVG with a unique title/description, numbered nodes and edges; no canvas, drag or pointer-only content;
2. a node list with every label, kind, dependency and source citation — the accessible equivalent of the graph;
3. an ordered ladder with every condition and both branches;
4. the complete linear explanation, unknown-state text and limits;
5. source references and an explicit unsupported-semantics list;
6. provenance and review status.

The SVG scales with the page and carries no text alternative beyond its title/description; the node list is the complete nonvisual structure. There are no wide tables, so no horizontal scroll region is needed. The page uses no JavaScript, no external assets and no execution.

Run:

```bash
python3 framework/rule_presentation.py \
  tests/fixtures/rule-presentation/synthetic-procurement.json --check

python3 framework/rule_presentation.py \
  tests/fixtures/rule-presentation/synthetic-procurement.json --out /tmp/rule-render
```

## What is deliberately not done

- No attachment to `dist/`, the production build, policy records, source checks or public navigation.
- No automatic encoding of the 23 candidate leads or any real provision.
- No Axiom/L4 engine at render time or in the browser.
- No claim that a presentation is reviewed, current law or legally verified.
- No Arabic/French native review of the synthetic labels; they are provisional.
- No automatic derivation from a compiled artifact; a reviewed pipeline still has to produce the presentation model.

## Future attachment (not this PR)

A later, separately authorized integration would:

1. produce a `rule-presentation/v1` artifact only after the record's interpretation review is complete;
2. render it in the build only when the review gate passes;
3. link it from the reviewed record with a visible “reviewed interpretation” label and provenance;
4. add the presentation to coverage/status reporting without changing `legal_effect`;
5. keep engine execution out of the public page unless a separate security/hosting decision is made.

The synthetic fixture must never be published as a real instrument.

## Accessibility findings

Rendered fixture checked with Playwright 1.64.1 and axe-core 4.14.0 at 1280×900:

- **0 axe violations** per English/French/Arabic page; 26 passes, 1 incomplete (`color-contrast`, 9 SVG node labels in EN/FR), 38 inapplicable. The graph node text uses `#17202a` on the light node fills; manual ratios are 13.39:1–16.45:1.
- 320 CSS px: document width equals 320, no page overflow. The graph scales; the node list and linear explanation reflow.
- Keyboard: first Tab reaches the skip link; all links are ordinary links; no graph manipulation is required; focus is visible.
- `lang`/`dir` on each page; Arabic RTL; code/IDs tagged English/LTR.
- Forced colours and reduced motion: no animations; structural review only for forced colours. **Manual forced-colours/screen-reader/zoom testing was not performed.**
- No WCAG conformance claim.

## Tests

```bash
python3 -m unittest tests.test_rule_presentation
python3 -m unittest discover -s tests -p 'test_*.py'
python3 framework/validate.py
python3 framework/build.py --region mena
python3 framework/check_html.py
```

The fixture is synthetic and deliberately not in `dist/`.

## Rollback

Delete `regions/mena/schemas/rule-presentation.schema.json`, `framework/rule_presentation.py`, `tests/test_rule_presentation.py`, `tests/fixtures/rule-presentation/` and this document, and revert the i18n keys. No data migration or public page change is involved.
