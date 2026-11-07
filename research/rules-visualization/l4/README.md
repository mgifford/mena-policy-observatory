# Legalese L4 evidence

**Synthetic only.** This is not a real procurement policy and has no legal effect.

- `procurement.l4` — synthetic L4 source with five outcomes and a deontic `open source duty`.
- `procurement.check.txt` — actual `l4 check` result.
- `procurement.run.json` — actual `l4 run --json` envelope.
- `procurement.run.txt` — human-readable run output.
- `procurement.trace.dot` — actual `l4 trace --format dot` output.

No Haskell toolchain was installed. The CLI was extracted from the official
`l4-vscode-darwin-arm64-1.6.109.vsix` release (`l4-ide-build-109`):

- VSIX SHA-256: `d4bd6f7f9da25526b10b5afa7811b502487b4a6db1304eeaa32cbf4286779fc9`
- CLI SHA-256: `eeb12f1e9d0ec646b6196d53a4b83c41160ada7f3959211aa50b0115652b73cb`
- `l4 --version`: `1.6.109 (main, 4c887e0, 2026-11-04)`

Reproduce:

```bash
l4 check procurement.l4
l4 run procurement.l4 --json
l4 trace procurement.l4 --format dot
```

`#EVAL` order is: all conditions met; the `#EVALTRACE` duplicate; scope false; exception true; missing covered body (`NOTHING`); boundary 100000; contradictory scope/exception; and the deontic duty. The missing-fact case is `Indeterminate`, not an error.

GraphViz (`dot`) was not installed, so `--format svg` was not run. The DOT file is the actual trace; the accessible HTML ladder is generated independently from the presentation model.
