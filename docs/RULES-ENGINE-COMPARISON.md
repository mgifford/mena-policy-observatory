# Axiom RuleSpec vs Legalese L4: exploratory comparison and accessible visualization prototype

**Status:** exploratory research, isolated from production. **Not a legal opinion, not an approved encoding and not a Rules-as-Code deployment.**

**Baseline:** `main` at `4257c1f` (WP5 merged; pilot PR #20 open). The active milestone is the three-source verification and monitoring pilot (`docs/CURRENT-MILESTONE.md`). That milestone does **not** authorize Axiom integration, new legal encodings or a rules engine in the public application. This work adds the standalone report, synthetic examples and the isolated prototype under `research/rules-visualization/`. The public observatory now surfaces short excerpts of the synthetic Axiom/L4 sources and a readable Legalese-style ladder on the homepage and synthetic visualization page. Engine execution, reviewed real encodings and legal-effect changes remain out of production.

**Prototype:** [`research/rules-visualization/prototype/index.html`](../research/rules-visualization/prototype/index.html).

**Question:** whether Axiom RuleSpec, Legalese L4, or a constrained combination gives the clearest, most accessible and most defensible way to visualize existing law in this observatory.

## Executive recommendation

1. **Do not add Axiom, L4 or the Rules Visualizer as a production dependency now.** None is justified by the active milestone, and all three need a reviewed encoding pipeline that does not exist.
2. **For a future reviewed encoding layer, prefer Axiom RuleSpec as the candidate executable representation** where the task is deterministic calculation over reviewed facts. It compiled and executed deterministically, produced durable rule IDs, an explanation trace, source metadata and a reproducible artifact under a permissive MIT licence.
3. **Do not use Axiom's graph viewer as the public visualization.** It is an API-backed React/Vercel application, not an offline artifact viewer; it needs an Axiom API key and a server-side proxy. The same applies, more strongly, to the Gary Community Ventures Rules Visualizer, which needs a Python/aiohttp backend and a vendored Rust engine.
4. **Build a small neutral presentation artifact and a static accessible renderer** from a reviewed encoding. Render two views from that one model: a dependency graph and a ladder/decision view, plus a complete linear text equivalent. This prototype demonstrates the renderer. It does not automate the conversion.
5. **Keep L4 as an authoring and explanation comparator, not a second production semantics.** L4 is materially better for deontic modality and explicit `MAYBE`/indeterminate reasoning. If obligations, permissions, prohibitions or deadline consequences become central, revisit L4 seriously. Running Axiom and L4 in production would create two potentially conflicting interpretations unless one is designated authoritative and the other is only an explanation of the same reviewed encoding.
6. **A hybrid is justified only as "one authoritative encoding, two views".** The prototype's single presentation model is that shape. It is not a dual-engine runtime and must not become one by accident.

## Method and pinned sources

I inspected the current source code and documentation, not only project home pages. Clones were made on 2026-11-06/07. No external model API was used.

| Project | Revision inspected | Version | Licence |
|---|---|---|---|
| Axiom Rules Engine | `d41d29d251b6eb0de6542f5899a93d317f3f0dcf` | 0.2.2 | MIT |
| Axiom RuleSpec Graph Viewer | `880af3d8234f1eb8704bcab7f3e2fc8494556fba` | 0.0.1 | MIT |
| Legalese L4 IDE | `4c887e0db7b8a49703598531ca1199688353da30` | CLI 1.6.109 / build 109 | Apache-2.0 |
| Gary Community Ventures Rules Visualizer | `e74d607f500fe9a0d169c424f44af75726679dbe` | 0.1.0 | MPL-2.0 |

Exact source links are in the source register at the end. Status vocabulary for the matrix:

- **S** — supported and demonstrated by an actual run in this investigation.
- **D** — documented by the project but not tested here.
- **P** — partial: some support, or a workaround was required.
- **U** — unsupported.
- **?** — unknown; not enough evidence.

## Capability matrix

| Capability | Axiom RuleSpec | Legalese L4 | Rules Visualizer |
|---|---|---|---|
| 1. Conditions and exceptions | **S** — formulas with `if`, `and`, `not`, comparisons; synthetic ladder compiled and ran. Exceptions are ordinary conditions, not first-class legal exceptions. | **S** — `CONSIDER`, `IF`, `BRANCH`; the synthetic file models scope, exception and missing facts and ran. | **P** — RuleSpec model parser; graph is a view of the same conditions. |
| 2. Obligations, permissions, prohibitions | **U** — outputs are scalar/judgment/text; there is no deontic type or `MUST`/`MAY`/`SHANT`. A judgment is a proposition, not a duty. | **S** — `PARTY`, `MUST`, `MAY`, `SHANT`/`MUST NOT`, `HENCE`, `LEST`; the synthetic `open source duty` evaluated to `JUST OF (PARTY … MUST … WITHIN 30)`. | **U** — inherits RuleSpec; no deontic construct. |
| 3. Temporal applicability and amendments | **P** — `effective_from`/`effective_to` and periods are supported and compiled; `source_relation` can carry `amends`/`restates` metadata, but that is not a reviewed amendment/version graph. | **P** — dates, deadlines (`WITHIN`), `NOW`/`TODAY`; no instrument-version registry or amendment graph. | **?** — depends on the upstream artifact and external metadata; simulation for RuleSpec is documented as TBD. |
| 4. Unknown and indeterminate outcomes | **P** — three-valued `Judgment` is documented, but this RuleSpec surface had no undetermined literal/input. A missing input is an error; the demonstration uses a `facts_complete` flag and a text status, while the judgment outputs are `not_holds` when facts are incomplete. | **S** — `MAYBE` plus `CONSIDER NOTHING` produced `Indeterminate` in the actual run. | **?** — no evidence of a distinct unknown state in the visualizer. |
| 5. Traceability to source provisions | **S** — durable output IDs, `sources`/`source_url`, source-closure hashes; the compiled artifact records these. | **P** — `@ref` and `<<…>>` cite legal sources, but there is no durable research-ID/version schema in the prototype. | **P** — resolves policy-document citations from `references.json`; no observatory IDs. |
| 6. Translation and multiple source-language expressions | **U** — no language or translation layer. | **U** — no translation provenance layer. | **U** — no translation layer. |
| 7. Compilation and deterministic execution | **S** — `compile` produced a format-3 artifact; `run-compiled` executed it. | **S** — `l4 check` succeeded; `l4 run` evaluated all cases. | **P** — delegates to the Axiom binary; wrapper says it is compatible with the **0.1.0** API, while current Axiom is 0.2.2 and requires `--rulespec-root`. |
| 8. Explanation traces | **S** — `mode: explain` returned `executed_expression`, `dependencies` and `parameter_reads` for every output. | **S** — `#EVALTRACE` produced a GraphViz DOT trace of the evaluated branch. | **P/D** — execution panel and AI chat; no formal portable trace was demonstrated. |
| 9. Decision and dependency graphs | **P** — dependency data is in the artifact/trace; the standalone viewer fetches graphs from the API. No offline graph artifact is bundled. | **S** — CLI `trace` renders evaluation as DOT; the web ladder is a separate Svelte visualizer. | **D** — documented interactive node graph; not run in this investigation. |
| 10. Browser/static-site deployment | **P** — native Rust binary; a WASM crate exists but was not evaluated; the graph viewer needs an API. | **P** — native CLI and WASM/LSP builds exist; GraphViz is needed for SVG; the ladder is a Svelte app. | **U** — aiohttp server + Vite frontend, not a static GitHub Pages artifact. |
| 11. Security and privacy | **S** — local CLI, no network required for compile/run; the WASM crate claims no filesystem, environment or clock access. | **S** — local CLI for check/run/trace; cloud deployment is optional. | **P** — local server; optional AI path uses LangChain/OpenRouter and needs configuration. |
| 12. Accessibility | **P/?** — graph viewer uses React Flow, tabs and a canvas-like pan/zoom graph; no complete accessible table equivalent was found. Not browser/AT tested. | **P/?** — ladder visualizer is an interactive Svelte app; GraphViz output still needs a text equivalent. Not browser/AT tested. | **?** — React UI; no evidence of an accessible linear equivalent. Not tested. |
| 13. Licensing and maintainability | **S** — MIT; active Rust project with tests and a versioned artifact format. | **P** — Apache-2.0; Haskell/TypeScript monorepo, GHC 9.10.2 + Cabal + Node + GraphViz; heavy for this Python static site. | **P** — MPL-2.0; Python/Rust/React stack, vendored engine, LangChain/OpenRouter dependencies and a backend. |
| 14. Testability and reproducibility | **S** — pinned source build, Cargo tests, compiled artifact, actual requests/responses committed. | **S** — `l4 check`, JSON run envelope and DOT trace committed; release binary provenance recorded. | **P** — tests exist, but the engine wrapper targets an older API and the app was not run. |
| 15. Compatibility with research identifiers | **S** — durable IDs such as `xx:policies/procurement#procurement_obligation`. | **P** — names and `@ref` citations; no observatory instrument/source/version IDs. | **P** — parser emits its own Model JSON; no observatory IDs. |

## Existing visualization approaches

### A. Axiom RuleSpec Graph Viewer

- **How graphs are produced:** the viewer fetches `GET /v1/runtime/packages/{jurisdiction}/{program_id}/graph` through a same-origin proxy; it does not build graphs client-side and bundles no graph artifact (S5).
- **Offline generation:** not provided by this viewer. The engine can compile a local artifact and the explain trace contains dependencies, but the viewer's graph shape is an API response.
- **Public API required:** yes in the documented architecture; the proxy injects `AXIOM_API_KEY` server-side. A local Axiom API instance is an option, but that is still a service.
- **Authentication:** an API key is required server-side; the browser does not hold it.
- **Citations:** the viewer has citation/detail code; the README describes a detail panel with source citation and cross-jurisdiction restatement citations. This is a display feature, not a verification.
- **GitHub Pages:** not directly. A pre-fetched graph JSON plus a new static renderer could work, but that is a new implementation, not the existing viewer. The viewer's Vercel function/proxy is not a GitHub Pages artifact.
- **Accessibility:** React Flow is a pan/zoom graph canvas with ARIA on some toolbar tabs. I found no complete table/text equivalent in the source review. It is **not tested** with a keyboard or screen reader here; do not treat the presence of `aria-label` as sufficient.

### B. Legalese L4 visualization

- **Ladder/evaluation traces:** `#EVALTRACE` and `l4 trace` produce GraphViz `dot`; `--format svg|png` requires GraphViz installed. The actual DOT trace is committed at `research/rules-visualization/l4/procurement.trace.dot`.
- **Static output:** yes in principle; DOT/SVG is a static artifact. The CLI can write SVG with `--format svg -o DIR` if `dot` is available. No SVG was rendered here because GraphViz is not installed.
- **Citations and versions:** `@ref` annotates legal sources; the trace itself does not carry an instrument-version timeline. Citations are source annotations, not a verified legal-version graph.
- **Obligations, exceptions, deadlines:** deontic constructs exist and the synthetic duty evaluated. Deadlines are `WITHIN`; the trace showed `WITHIN 30`.
- **RTL/accessibility:** the interactive ladder is a Svelte package; GraphViz SVG output has no automatic text equivalent, and RTL was not tested. The DOT trace is evidence, not a public accessible visualization.

### C. Gary Community Ventures Rules Visualizer

- **RuleSpec features:** README describes RuleSpec libraries, inputs, constants, computed nodes, citations and execution; the parser walks imports and emits a visualizer Model. It is a RuleSpec visualizer, not a deontic editor.
- **Engine compatibility:** `axiom_engine.py` explicitly says it is compatible with the **0.1.0** API and calls `compile --program … --output …` without the current required `--rulespec-root`. Current Axiom 0.2.2 requires `--rulespec-root` and rejects unconfigured roots. The build script clones `TheAxiomFoundation/rac`, not the current engine repository name. This is a real compatibility/maintenance risk, not a theoretical one.
- **Static hosting:** no. It runs an aiohttp Python backend plus a Vite/React frontend, compiles rules with a vendored Rust binary, and documents a WebSocket reload path. GitHub Pages cannot run that backend.
- **Reusable graph components:** possible in principle because the frontend is React and the model is JSON, but the graph is embedded in a large app with many Radix/Tailwind dependencies and MPL-2.0 file-level obligations; reuse would not be a small component extraction.
- **Non-AI operation:** the core parser/server may run without an AI key, but the project includes LangChain/LangGraph/OpenRouter dependencies and an AI assistant. I did not run it, so I do not claim the non-AI path is independent in practice.
- **Read-only public demonstration:** a local read-only demo is plausible, but not a purely static public page. The README's own "developer tool" framing and the server architecture point away from GitHub Pages.

## Synthetic demonstration

The policy is fictional and labelled in every artifact. It has five conditions and one threshold:

- `facts_complete`;
- `covered_body`;
- `contract_scope_met`;
- `exception_applies`;
- `contract_value >= USD 100,000`.

Axiom RuleSpec and L4 implement the same intended decision table. The complete source is in `research/rules-visualization/axiom/procurement.rulespec.yaml` and `research/rules-visualization/l4/procurement.l4`.

### What was actually executed

**Axiom 0.2.2** was built from the pinned commit with `cargo build --release --features fs`. The RuleSpec compiled to a format-3 artifact with source-closure digest `sha256:855c…`. Seven `run-compiled` requests were executed; responses are committed. The engine reported `missing input` as a non-zero execution error for the missing-fact case.

**L4 1.6.109** was not built from Haskell source because no GHC/Cabal toolchain was installed. The official `l4-vscode-darwin-arm64-1.6.109.vsix` release (`l4-ide-build-109`, commit `4c887e0`) was downloaded; its `l4` CLI was extracted and run. `l4 check` succeeded; `l4 run --json` evaluated all cases; `l4 trace --format dot` produced the committed DOT trace. No GraphViz SVG was rendered because `dot` is not installed.

**Rules Visualizer and the Axiom Graph Viewer were not run.** They require a backend/API and a substantial dependency install; static source review was sufficient to establish the hosting and compatibility constraints. Their matrix cells are marked accordingly.

### Actual outputs

| Case | Axiom RuleSpec | Legalese L4 |
|---|---|---|
| All conditions met (USD 150,000) | `determination = open_source_consideration_required`; both judgments `holds` | `OpenSourceConsiderationRequired` |
| Scope condition false | `determination = outside_scope`; both judgments `not_holds` | `OutsideScope` |
| Exception true | `determination = exception_applies`; both judgments `not_holds` | `ExceptionApplies` |
| Missing `covered_body` | **error:** `missing input … covered_body` | `Indeterminate` |
| Boundary USD 100,000 | `open_source_consideration_required`; both `holds` | `OpenSourceConsiderationRequired` |
| `facts_complete = false` | `determination = indeterminate`; both judgments `not_holds` | `Indeterminate` |
| Scope false and exception true | `determination = outside_scope`; both `not_holds` | `OutsideScope` |

The exact requests/responses are in `research/rules-visualization/axiom/requests/` and `responses/`; L4's JSON envelope is `l4/procurement.run.json`.

### Semantic differences that must not be flattened

- **Axiom judgments are not duties.** `procurement_obligation` is a proposition that holds or not; it cannot express “the contracting authority MUST consider open source”. L4 can.
- **Missing input is an error in Axiom; `NOTHING` is a first-class indeterminate value in L4.** The Axiom demonstration uses a synthetic `facts_complete` flag and a text status to represent the unknown; it cannot make the judgment itself undetermined through this surface. That is a modelling workaround, not equivalence.
- **Axiom's determination text duplicates the decision logic.** The duplicate text rule exists only to expose an indeterminate status; in a production encoding it would be an isomorphism risk, not a second source of truth.
- **Contradictory facts are not detected.** Both engines applied the ladder/condition order and returned `outside_scope`; neither reported an inconsistency. The ladder order is therefore part of the legal interpretation and must be reviewed.
- **Boundary is inclusive** in both (`>= 100000` and `AT LEAST`).
- **The two engines use different source languages of expression.** The comparison does not claim semantic equivalence beyond the tested table.

## Prototype and the intermediate presentation model

`research/rules-visualization/model/presentation.json` has:

- nodes (inputs, constants, computed outputs), dependencies, dtypes, values and citations;
- an ordered ladder with true/false branches and notes;
- outcomes, synthetic source references, effective period, test results;
- an explicit **unsupported semantics** list: deontic modality, amendment/version history, translation provenance, real text/citation verification and contradiction detection.

The generator renders the same model as:

1. a numbered dependency graph (SVG `role="img"`, title/description, no canvas, no drag);
2. a ladder/decision view (ordered HTML list with true/false branches and citations);
3. a complete linear text equivalent, plus the node/dependency table, test table and source register.

Node numbers in the SVG are a visual shorthand; the table supplies every label and dependency. The graph is not the only route to any content.

### Can one model support both Axiom and L4-style views?

For this synthetic policy, **yes at the presentation layer**, because the model is curated. The dependency view and ladder view read the same conditions, branches, outcomes and citations. This is the useful result.

**Automatic Axiom-to-ladder conversion was not demonstrated as faithful.** The Axiom artifact exposes expressions and dependency edges, not an explicit legal branch order or an exception object. Turning `not exception_applies` into a ladder step requires a semantic mapping and a reviewer decision about evaluation order. L4's `CONSIDER` provides an explicit order, but it is a different authored source. A converter that silently discarded the exception or reordered branches would be legally misleading.

Therefore:

- keep one **reviewed** presentation model as the source for both views;
- derive it from a reviewed encoding with an explicit, checked mapping;
- retain unsupported semantics in the model rather than dropping them;
- keep separate renderers until the mapping is validated against source provisions and tests;
- never run both engines as competing authorities.

## Proposed future link to observatory records

A future reviewed record could carry this chain, with each link separately reviewable:

| Link | Example field | Status rule |
|---|---|---|
| Instrument | `instrument_id` | existing reviewed instrument ID |
| Source | `source_id` + publisher/URL | existing source/provenance records |
| Provision | `provision_id` + exact locator | reviewed citation; no invented locator |
| Legal version | `legal_version` + effective period | reviewed dates or explicit unknown |
| Original-language citation | `original_citation` + language | source text/excerpt provenance |
| Reviewed interpretation | `interpretation_id` + reviewer/date | human-reviewed; not machine-inferred |
| Rule encoding | `encoding_id` + RuleSpec URL + engine version | compiled and tested against pinned engine |
| Presentation model | `presentation_id` + version | derived from encoding; unsupported semantics listed |
| Visualization artifact | static HTML/SVG/JSON + checksum | accessible equivalent included |
| Engine version | version + commit/artifact digest | exact reproducibility |
| Test results | case IDs + expected/actual + date | positive, negative, boundary, indeterminate |

The prototype uses synthetic placeholder IDs only. It does **not** modify `legal_effect`, verification state, candidate records or reviewed translations. A production link must be gated on the record's review state, show provenance and an “unreviewed/synthetic” label, and remain read-only.

## Accessibility findings

The prototype was checked with Playwright 1.64.1 and axe-core 4.14.0 against WCAG 2.0/2.1/2.2 A/AA tags:

- **Axe:** 0 violations on each of the three language pages at 1280×900; 28 passes, 1 incomplete (`color-contrast`: 18 SVG text nodes in English/French, 11 in Arabic because of label overlap), 36 inapplicable. The incomplete check is because axe cannot determine the background of SVG text on filled rectangles. Manual contrast calculation for the actual pairs is 13.39:1–16.45:1 for node text, 6.59:1 for muted text, 8.40:1 for links.
- **Forced colours + reduced motion:** 0 violations; no animation is used.
- **320 CSS px:** document width equals 320 px; no page-level horizontal overflow. The graph and tables are contained, focusable horizontal scroll regions with a visible table/text equivalent. The graph is a visual summary, not the only access route.
- **Keyboard:** first Tab reaches the skip link; next stops include language links, the graph scroll region, both table regions, ladder content and source links; focus outlines are visible (3 px). Arrow keys scroll the focused graph/table region at 320 px (English 0→120 px; Arabic RTL 0→−120 px with the opposite physical direction). No keyboard trap observed.
- **Language/direction:** `lang`/`dir` on each page; Arabic is RTL; identifiers, engine names and test codes are tagged as English/LTR where they are code. The language index links use `hreflang`.
- **Visual equivalence:** node table has every node, dependency and citation; ladder has every branch; linear explanation repeats every condition and outcome. The SVG has a unique title/description and is not an interactive canvas.
- **Progressive enhancement:** one small inline script enables ArrowLeft/ArrowRight scrolling in the focusable regions. Without it, all content remains in HTML and the region is still a named scroll area; no content is generated by script.

**Not tested:** real browser 400% zoom (the 320 px viewport is a layout approximation), text-spacing override, VoiceOver/NVDA, touch, print/PDF export, native French or Arabic review, and user testing with disabled people. **No WCAG conformance is claimed.**

Automated results are in `research/rules-visualization/results/accessibility.json`. The structural validator (`research/rules-visualization/validate.py`) checks language/direction, skip link, main landmark, table captions/scopes, SVG title/desc, unique IDs and local links; it is not an accessibility conformance test.

## GitHub Pages feasibility

- **This prototype:** yes. It is static HTML/CSS/SVG with relative links, no server, no external assets, no model call and no engine. It can be copied under a Pages subpath as-is.
- **Production integration:** not done. A future PR would need a generator step that copies reviewed presentation artifacts into `dist/`, a record-page attachment and review-state gating. This PR deliberately does not touch `dist/` or the production generator.
- **Axiom graph viewer:** no, not without replacing its API-backed graph source with a pre-fetched static artifact and reimplementing the renderer.
- **L4 ladder:** static SVG/DOT is possible, but the interactive Svelte ladder is not a drop-in static component; GraphViz would become a build dependency.
- **Rules Visualizer:** no; backend required.

## Licensing and dependency assessment

| Component | Licence | Implication |
|---|---|---|
| Axiom Rules Engine | MIT | Permissive; suitable for a future reviewed pipeline with attribution/licence notice. Rust engine and WASM add build/runtime choices. |
| Axiom Graph Viewer | MIT | Code is permissive, but the API-backed architecture and API key/service are the blockers, not the licence. |
| Legalese L4 | Apache-2.0 | Permissive, but the Haskell/TS monorepo and GHC/GraphViz toolchain are heavy; the CLI release used here is a prebuilt binary. |
| Rules Visualizer | MPL-2.0 | File-level copyleft; reuse requires care. It also brings aiohttp, React/Vite, vendored Rust and LangChain/OpenRouter dependencies. |
| This prototype | repository licence | Original generator/model/HTML; no third-party code copied. The Axiom RuleSpec and L4 source are synthetic examples written for this comparison. |

The Axiom engine is a native binary; a public site cannot execute it client-side without the WASM build. Axiom's WASM crate exists and claims in-browser compile/execute with no filesystem/clock/network, but it was **not** built or tested here. L4's WASM/LSP build exists; it was not tested. Neither should be put on a public page merely because a WASM artifact exists.

## Decision criteria

| Criterion | Evidence | Weight |
|---|---|---|
| Semantic fidelity | Axiom is strong for deterministic propositions but lacks deontic modality; L4 is stronger for duties and `MAYBE`; neither verifies legal meaning. | High |
| Explainability | Both trace; Axiom's `explain` is machine-readable and L4's DOT is visual; both need a human-readable equivalent. | High |
| Accessibility | Existing graph/ladder viewers are not demonstrated accessible; the neutral static renderer is. | High |
| Compatibility with MENA research | Axiom durable IDs fit better; L4 `@ref` is useful but no observatory ID schema. | High |
| Proprietary-service independence | Axiom CLI/L4 CLI local; Axiom graph viewer and Rules Visualizer AI path are service-dependent. | High |
| Static deployment | Only the neutral renderer/prototype is static; existing viewers are not. | High |
| Reproducibility | Axiom artifact + trace strongest; L4 pinned CLI + DOT strong; RV wrapper targets old API. | High |
| Maintainability | Axiom Rust engine active; L4 large Haskell/TS stack; RV large multi-stack app with stale engine binding. | Medium |
| Amendments/history | Neither provides a reviewed legal-version graph; both need observatory metadata. | High |
| Contribution by regional researchers | Axiom YAML/RuleSpec is approachable with review; L4 reads closer to legal prose but has a heavier toolchain; both need training and review. | Medium |

## Recommendation in one sentence

**Use Axiom RuleSpec as the candidate reviewed encoding/execution layer, but ship a neutral, static, accessible presentation model and renderer—not the Axiom graph viewer or the Rules Visualizer—and keep L4 as the comparator to revisit if deontic or indeterminate legal semantics become central.**

This is not an endorsement of Axiom as legally authoritative. It is a recommendation about engineering fit after a synthetic demonstration. The observatory's legal effect remains a human-reviewed research conclusion, not an engine output.

## Remaining research questions

1. Which reviewed provisions, if any, justify encoding at all, and who signs off the interpretation and test cases?
2. Does the research question need deontic duties (then L4 deserves a deeper trial) or only deterministic eligibility/calculation (then Axiom is sufficient)?
3. How should effective periods and amendments be represented so a visualization never shows a rule outside its reviewed applicability?
4. Can a RuleSpec-to-presentation mapping be validated against source provisions without silently reordering exceptions?
5. What is the minimum accessible visual vocabulary for legal conditions, branches and unknown states in Arabic RTL and French?
6. Should the observatory publish only a reviewed static artifact, or also expose an engine API? The latter adds security, hosting and reproducibility obligations.
7. How are engine builds pinned, attested and re-tested when the engine changes?
8. What licence/provenance notice is required if Axiom or L4 artifacts are redistributed?

## Proposed small follow-up PR (not this PR)

A later, separately authorized production-integration PR could:

1. define a `rule-presentation.v1` JSON schema with nodes, dependencies, ladder steps, citations, effective period, unsupported semantics and text-equivalent blocks;
2. add `framework/render_rule_presentation.py` (standard library, static HTML/SVG) with structural tests;
3. add a review-state gate so a presentation attaches only to a record with a reviewed interpretation and an explicit “synthetic/unreviewed” label;
4. add one **synthetic** fixture page under the existing test suite, not a real legal record;
5. document engine/version provenance and the accessibility/manual-review gates;
6. leave Axiom/L4 execution out of the public site until a reviewed encoding and a security/hosting decision exist.

That is intentionally smaller than embedding either engine. It tests the durable part—the presentation contract—without creating a legal decision service.

## Deliverable checklist

- [x] Source-backed comparison report (this document).
- [x] Axiom vs L4 capability matrix (and Rules Visualizer, because it was a required approach).
- [x] Review of all three visualizer approaches.
- [x] Synthetic, clearly labelled example.
- [x] Axiom RuleSpec example and compiled artifact.
- [x] L4 example.
- [x] Actual compile/run results, including a real missing-input error and a real L4 indeterminate result.
- [x] Working static graph + ladder prototype.
- [x] Accessible linear explanation.
- [x] Accessibility findings and automated results, with manual gaps.
- [x] Licensing and dependency assessment.
- [x] GitHub Pages feasibility.
- [x] Architectural recommendation.
- [x] Remaining research questions.
- [x] Proposed follow-up PR.
- [x] No production legal records, legal-effect status or active milestone changed.

## Source register

**Axiom**

- S1. Axiom Rules Engine repository and RuleSpec semantics: <https://github.com/TheAxiomFoundation/axiom-rules-engine/blob/d41d29d251b6eb0de6542f5899a93d317f3f0dcf/docs/rulespec.md>
- S2. RuleSpec expression grammar and `Judgment` three-valued type: <https://github.com/TheAxiomFoundation/axiom-rules-engine/blob/d41d29d251b6eb0de6542f5899a93d317f3f0dcf/docs/rulespec-format.md>
- S3. `JudgmentOutcome` (including `Undetermined`) in the engine source: <https://github.com/TheAxiomFoundation/axiom-rules-engine/blob/d41d29d251b6eb0de6542f5899a93d317f3f0dcf/src/spec.rs>
- S4. Axiom WASM crate (documented, not tested): <https://github.com/TheAxiomFoundation/axiom-rules-engine/blob/d41d29d251b6eb0de6542f5899a93d317f3f0dcf/wasm/README.md>
- S5. Axiom RuleSpec Graph Viewer (API/proxy, no bundled graph artifact): <https://github.com/TheAxiomFoundation/rulespec-graph-viewer/blob/880af3d8234f1eb8704bcab7f3e2fc8494556fba/README.md>
- S6. Axiom licence (MIT): <https://github.com/TheAxiomFoundation/axiom-rules-engine/blob/d41d29d251b6eb0de6542f5899a93d317f3f0dcf/LICENSE>

**Legalese L4**

- S7. L4 repository, CLI, GraphViz traces and requirements: <https://github.com/legalese/l4-ide/blob/4c887e0db7b8a49703598531ca1199688353da30/README.md>
- S8. L4 CLI reference (check/run/trace): <https://github.com/legalese/l4-ide/blob/4c887e0db7b8a49703598531ca1199688353da30/doc/tutorials/getting-started/l4-cli.md>
- S9. L4 deontic vocabulary (`PARTY`, `MUST`, `MAY`, `SHANT`, `HENCE`, `LEST`): <https://github.com/legalese/l4-ide/blob/4c887e0db7b8a49703598531ca1199688353da30/doc/reference/GLOSSARY.md>
- S10. L4 `@ref` citations: <https://github.com/legalese/l4-ide/blob/4c887e0db7b8a49703598531ca1199688353da30/doc/reference/syntax/README.md>
- S11. L4 licence (Apache-2.0): <https://github.com/legalese/l4-ide/blob/4c887e0db7b8a49703598531ca1199688353da30/LICENSE>
- S12. L4 language overview and playground: <https://legalese.com/l4> and <https://play.legalese.com/>

**Gary Community Ventures Rules Visualizer**

- S13. Repository and architecture/AI/static-server description: <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/README.md>
- S14. Python server dependencies (aiohttp, LangChain/OpenRouter): <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/packages/rac-server/pyproject.toml>
- S15. Engine build script (clones `TheAxiomFoundation/rac`): <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/scripts/build-axiom-engine.sh>
- S16. Engine wrapper says compatible with 0.1.0 API and omits `--rulespec-root`: <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/packages/rac-server/rules_visualizer_rac/axiom_engine.py>
- S17. RuleSpec parser note ("Visualizer-only"): <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/packages/rac-server/rules_visualizer_rac/rulespec_parser.py>
- S18. Licence (MPL-2.0): <https://github.com/Gary-Community-Ventures/rules-visualizer/blob/e74d607f500fe9a0d169c424f44af75726679dbe/LICENSE>

**Methodology**

- S19. Rules as Code League handbook introduction: <https://github.com/Rules-as-Code-League/RaC-Handbook/wiki/1-Introduction:-What-is-Rules-as-Code%3F>
- S20. Digital Government Hub, Rules as Code and large language models: <https://digitalgovernmenthub.org/library/rules-as-code-and-large-language-models/>

**Prototype artifacts**

- `research/rules-visualization/axiom/procurement.rulespec.yaml`
- `research/rules-visualization/axiom/procurement.compiled.json`
- `research/rules-visualization/axiom/requests/` and `responses/`
- `research/rules-visualization/l4/procurement.l4`
- `research/rules-visualization/l4/procurement.run.json` and `.trace.dot`
- `research/rules-visualization/model/presentation.json`
- `research/rules-visualization/prototype/{en,fr,ar}/index.html`
- `research/rules-visualization/results/accessibility.json`

## Rollback

This PR only adds `docs/RULES-ENGINE-COMPARISON.md` and `research/rules-visualization/`. It does not modify the production generator, `dist/`, legal records, source checks, translation catalogues or the active milestone. Revert the PR commit or delete those paths; no data migration is required.
