# Axiom RuleSpec evidence

**Synthetic only.** This is not a real procurement policy and has no legal effect.

- `procurement.rulespec.yaml` — source compiled by Axiom 0.2.2, commit `d41d29d251b6eb0de6542f5899a93d317f3f0dcf`.
- `procurement.compiled.json` — actual format-3 artifact (`engine_build.dirty: false`; source-closure digest `sha256:855c7317f34bc53563e60efc0bac528d6856e3fe1a916f7ba064cd56ccbf42c1`).
- `requests/` — seven actual `ExecutionRequest` documents.
- `responses/` — actual responses; `missing_fact.error.txt` is the real non-zero result.

The module is placed under a canonical test root named `rulespec-xx` because the current engine requires an exact `rulespec-<country>` checkout and rejects unconfigured roots. `xx` is a synthetic namespace, not a country.

Reproduce:

```bash
# From the pinned Axiom source checkout:
cargo build --release --features fs

mkdir -p /tmp/axiom-proto/rulespec-xx/xx/policies
cp procurement.rulespec.yaml /tmp/axiom-proto/rulespec-xx/xx/policies/procurement.yaml

/path/to/axiom-rules-engine compile \
  --program /tmp/axiom-proto/rulespec-xx/xx/policies/procurement.yaml \
  --rulespec-root /tmp/axiom-proto/rulespec-xx \
  --output /tmp/axiom-proto/procurement.compiled.json

/path/to/axiom-rules-engine run-compiled \
  --artifact /tmp/axiom-proto/procurement.compiled.json \
  < requests/all_met.json
```

The policy's `facts_complete` input is a demonstration workaround, not a claim that Axiom can produce an undetermined judgment from missing input. A missing input is an execution error; see `responses/missing_fact.error.txt`.
