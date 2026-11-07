# Rules-visualization prototype (isolated)

**Status:** exploratory research, synthetic only. This directory is intentionally outside the production generator, data model and legal records. Nothing here is legal advice, existing law, or an approved encoding.

This prototype compares how Axiom RuleSpec and Legalese L4 represent one fictional procurement policy, then renders the same presentation model as static, accessible HTML.

## Read these first

- [`docs/RULES-ENGINE-COMPARISON.md`](../../docs/RULES-ENGINE-COMPARISON.md) — source-backed comparison, capability matrix, visualizer review, accessibility findings and recommendation.
- [`prototype/`](prototype/) — English, French and Arabic static pages.
- [`results/`](results/) — actual engine outputs, test cases and accessibility checks.
- [`axiom/`](axiom/) — RuleSpec source, compiled artifact (Axiom 0.2.2) and requests/responses.
- [`l4/`](l4/) — L4 source, run output and GraphViz DOT trace.
- [`model/presentation.json`](model/presentation.json) — small intermediate model used by both views.

## Synthetic policy

All facts are fictional:

- a public body may be covered;
- a contract may be in scope;
- an exception may apply;
- an open-source consideration threshold is USD 100,000;
- missing required facts produce an indeterminate outcome.

The citations point to `example.org/synthetic-procurement-policy` and are labelled fictional. No real instrument, provision, date, reviewer or legal effect is represented.

## Reproduce the engine evidence

### Axiom Rules Engine

The compiled artifact was produced with the source build at commit
`d41d29d251b6eb0de6542f5899a93d317f3f0dcf` (version 0.2.2):

```bash
cd /path/to/axiom-rules-engine
cargo build --release --features fs

# The engine requires an absolute canonical checkout named rulespec-<country>.
mkdir -p /tmp/axiom-proto/rulespec-xx/xx/policies
cp procurement.rulespec.yaml /tmp/axiom-proto/rulespec-xx/xx/policies/procurement.yaml

/tmp/axiom-target/release/axiom-rules-engine compile \
  --program /tmp/axiom-proto/rulespec-xx/xx/policies/procurement.yaml \
  --rulespec-root /tmp/axiom-proto/rulespec-xx \
  --output /tmp/axiom-proto/procurement.compiled.json

/tmp/axiom-target/release/axiom-rules-engine run-compiled \
  --artifact /tmp/axiom-proto/procurement.compiled.json \
  < axiom/requests/all_met.json
```

The committed `procurement.compiled.json` is the actual format-3 artifact from that build. `axiom/requests/` and `axiom/responses/` record all seven cases. The missing-input case is a real non-zero engine result, not a mock.

### Legalese L4

No Haskell toolchain was installed in the prototyping environment. The CLI was extracted from the official `l4-vscode-darwin-arm64-1.6.109.vsix` release
(`l4-ide-build-109`, commit `4c887e0db7b8a49703598531ca1199688353da30`, CLI 1.6.109):

```bash
l4 check l4/procurement.l4
l4 run l4/procurement.l4 --json
l4 trace l4/procurement.l4 --format dot
```

`l4/procurement.run.json` is the actual JSON envelope. `l4/procurement.trace.dot` is the actual GraphViz DOT trace. GraphViz (`dot`) was not installed, so no SVG/PNG was rendered.

### Prototype pages

```bash
python3 generate.py
python3 validate.py
```

The generator uses only the Python standard library and the checked-in presentation model. There is no graph library, framework, build step or external service.

## Files

| Path | Purpose |
|---|---|
| `generate.py` | Renders four static pages from `model/presentation.json`. |
| `validate.py` | Structural checks: language/direction, skip link, table captions/headers, SVG title/desc, unique IDs, local links. Not a WCAG conformance test. |
| `prototype/en|fr|ar/index.html` | Generated English, French and Arabic pages. |
| `prototype/index.html` | Language index. |
| `axiom/` | Synthetic RuleSpec, compiled artifact, requests/responses. |
| `l4/` | Synthetic L4 file, check/run output and DOT trace. |
| `results/` | Actual case results and accessibility evidence. |

## Deliberate limits

- The demonstration model is curated by hand. It is **not** automatically derived from the Axiom artifact.
- Axiom RuleSpec has no deontic modality; L4 does. The prototype does not pretend they are semantically identical.
- The Axiom missing-input case is an error; L4 models `NOTHING` as `Indeterminate`.
- No real legislation is encoded and no observatory record is attached.
- Manual screen-reader, real 400% browser zoom and native Arabic/French review were not performed.
