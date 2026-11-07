#!/usr/bin/env python3
"""Validate and statically render reviewed rule-presentation artifacts.

A rule presentation is a read-only, pre-reviewed description of a decision
structure. It is not an execution engine and it cannot change a policy
record's legal effect. The renderer uses only the standard library and emits
semantic HTML plus one decorative/informative SVG; the node list and linear
explanation are the accessible equivalents.

This module does not attach anything to the public site. A future build step
must gate attachment on the review fields validated here.
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path

try:  # imported as framework.rule_presentation
    from .schema_lite import Validator
except ImportError:  # run as a script
    from schema_lite import Validator

FORMAT = 'rule-presentation/v1'
LANGUAGES = ('en', 'fr', 'ar')
DIRECTIONS = {'en': 'ltr', 'fr': 'ltr', 'ar': 'rtl'}
REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / 'regions' / 'mena' / 'schemas' / 'rule-presentation.schema.json'
I18N_DIR = REPO_ROOT / 'regions' / 'mena' / 'i18n'

UI_KEYS = (
    'skip',
    'rule.presentation.graph',
    'rule.presentation.graph_summary',
    'rule.presentation.nodes',
    'rule.presentation.node',
    'rule.presentation.kind',
    'rule.presentation.input',
    'rule.presentation.constant',
    'rule.presentation.computed',
    'rule.presentation.depends',
    'rule.presentation.citation',
    'rule.presentation.ladder',
    'rule.presentation.step',
    'rule.presentation.condition',
    'rule.presentation.if_true',
    'rule.presentation.if_false',
    'rule.presentation.text',
    'rule.presentation.explanation',
    'rule.presentation.sources',
    'rule.presentation.unsupported',
    'rule.presentation.effective',
    'rule.presentation.synthetic',
    'rule.presentation.reviewed',
    'rule.presentation.limits',
    'rule.presentation.provenance',
    'rule.presentation.engine',
    'rule.presentation.version',
    'rule.presentation.artifact',
    'rule.presentation.review_status',
    'rule.presentation.none',
    'rule.presentation.no_artifact',
    'rule.presentation.record',
    'rule.presentation.tests',
    'rule.presentation.unknown',
    'rule.presentation.source_language',
)

CITATION = re.compile(r'^[A-Z]{2,10}-[0-9]+$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
HOST = re.compile(r'^https://([^/]+)')


def _host(url: str) -> str:
    match = HOST.match(url or '')
    return (match.group(1).lower() if match else '')


def load_catalogues(root: Path | None = None) -> dict[str, dict]:
    base = Path(root) if root else I18N_DIR
    return {lang: json.loads((base / f'{lang}.json').read_text(encoding='utf-8'))
            for lang in LANGUAGES}


def _shape_errors(data: object) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    return Validator(SCHEMA_PATH.parent).validate(data, schema)


def _cycle_errors(nodes: list[dict]) -> list[str]:
    graph = {node['id']: list(node['depends']) for node in nodes}
    visiting: set[str] = set()
    visited: set[str] = set()
    errors: list[str] = []

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append(f'nodes: dependency cycle includes {node}')
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)
    return errors


def _valid_date(value: str) -> bool:
    if not isinstance(value, str) or not DATE.match(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def validate_presentation(data: object) -> list[str]:
    """Return shape and cross-field errors for one presentation artifact."""
    errors = _shape_errors(data)
    if errors:
        return errors
    assert isinstance(data, dict)

    synthetic = data['synthetic']
    review = data['review']
    record = data['record']
    provenance = data['provenance']

    if synthetic:
        if review['status'] != 'synthetic_fixture':
            errors.append('review: a synthetic presentation must use status synthetic_fixture')
        if record is not None:
            errors.append('record: a synthetic presentation must not be attached to a record')
        for source in data['sources']:
            if _host(source['url']) != 'example.org':
                errors.append(f"source {source['id']}: synthetic sources must use example.org")
    else:
        if review['status'] != 'reviewed':
            errors.append('review: a non-synthetic presentation must be reviewed')
        if not isinstance(record, dict):
            errors.append('record: a non-synthetic presentation needs an observatory record chain')
        elif not all(str(record.get(field, '')).strip() for field in (
                'instrument_id', 'source_id', 'provision_id', 'legal_version',
                'reviewed_interpretation_id')):
            errors.append('record: the full instrument/source/provision/version/interpretation chain is required')
        if not str(review.get('reviewer_role') or '').strip():
            errors.append('review: reviewer_role is required for a reviewed presentation')
        if not _valid_date(review.get('reviewed_at') or ''):
            errors.append('review: reviewed_at must be a valid ISO date')
        if not isinstance(provenance.get('artifact_sha256'), str) or not SHA256.match(provenance['artifact_sha256']):
            errors.append('provenance: a reviewed presentation needs an artifact SHA-256')
        for source in data['sources']:
            if _host(source['url']) == 'example.org':
                errors.append(f"source {source['id']}: example.org is not a real reviewed source")

    source_ids = [source['id'] for source in data['sources']]
    if len(source_ids) != len(set(source_ids)):
        errors.append('sources: duplicate source id')
    source_set = set(source_ids)

    node_ids = [node['id'] for node in data['nodes']]
    if len(node_ids) != len(set(node_ids)):
        errors.append('nodes: duplicate node id')
    node_set = set(node_ids)
    for node in data['nodes']:
        for dependency in node['depends']:
            if dependency not in node_set:
                errors.append(f"node {node['id']}: unknown dependency {dependency}")
            if dependency == node['id']:
                errors.append(f"node {node['id']}: cannot depend on itself")
        if node['citation'] not in source_set:
            errors.append(f"node {node['id']}: unknown citation {node['citation']}")
        if node['kind'] == 'constant' and not str(node.get('value') or '').strip():
            errors.append(f"node {node['id']}: constants need a value")
    errors.extend(_cycle_errors(data['nodes']))

    steps = data['ladder']
    step_numbers = [step['step'] for step in steps]
    if step_numbers != list(range(1, len(steps) + 1)):
        errors.append('ladder: steps must be numbered consecutively from 1')
    for step in steps:
        if step['citation'] not in source_set:
            errors.append(f"ladder step {step['step']}: unknown citation {step['citation']}")

    for lang in LANGUAGES:
        if len(data['text']['steps'][lang]) != len(steps):
            errors.append(f"text.steps.{lang}: needs one explanation per ladder step")
    if not _valid_date(data['effective_period']['from']):
        errors.append('effective_period.from must be a valid ISO date')
    to = data['effective_period']['to']
    if to is not None:
        if not _valid_date(to):
            errors.append('effective_period.to must be null or a valid ISO date')
        elif to < data['effective_period']['from']:
            errors.append('effective_period.to cannot be before from')

    if not str(provenance.get('encoding_id') or '').strip():
        errors.append('provenance: encoding_id is required')
    if not str(provenance.get('engine') or '').strip():
        errors.append('provenance: engine is required')
    if not str(provenance.get('engine_version') or '').strip():
        errors.append('provenance: engine_version is required')
    return errors


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _loc(value: dict, lang: str) -> str:
    return str(value[lang])


def _style() -> str:
    return r"""
:root { color-scheme: light; --ink:#17202a; --muted:#4d5966; --paper:#fff; --wash:#f3f6f9; --line:#6b7785; --accent:#0b4f8a; --input:#dcecf8; --constant:#f3e8c8; --computed:#e2e8f5; }
* { box-sizing: border-box; }
html { font-family: system-ui, -apple-system, "Segoe UI", Tahoma, "Noto Sans Arabic", sans-serif; line-height: 1.55; }
body { margin: 0; color: var(--ink); background: var(--paper); }
a { color: var(--accent); text-underline-offset: .18em; }
a:focus-visible, [tabindex]:focus-visible { outline: 3px solid var(--ink); outline-offset: 3px; }
.skip { position:absolute; inset-inline-start:.5rem; inset-block-start:-4rem; background:var(--ink); color:var(--paper); padding:.6rem .9rem; z-index:5; }
.skip:focus { inset-block-start:.5rem; }
header, main, footer { max-inline-size: 68rem; margin-inline:auto; padding-inline:1rem; }
header { padding-block:1.2rem .6rem; }
.badge { display:inline-block; border:2px solid var(--ink); border-radius:.4rem; padding:.15rem .45rem; font-weight:700; font-size:.82rem; }
h1 { font-size:clamp(1.7rem,4vw,2.5rem); line-height:1.15; margin-block:.6rem .4rem; }
h2 { font-size:clamp(1.25rem,2.5vw,1.6rem); margin-block:2rem .6rem; border-block-end:2px solid var(--line); padding-block-end:.25rem; }
h3 { font-size:1.05rem; margin-block:0 .35rem; }
p, li { max-inline-size:68ch; }
.lead { font-size:1.08rem; color:var(--muted); }
.disclaimer { border-inline-start:6px solid var(--ink); background:var(--wash); padding:.8rem 1rem; }
figure { margin:1rem 0 1.25rem; }
figcaption { color:var(--muted); margin-block-start:.4rem; }
svg { display:block; inline-size:100%; block-size:auto; }
.node-input rect { fill:var(--input); stroke:var(--ink); stroke-width:2; }
.node-constant rect { fill:var(--constant); stroke:var(--ink); stroke-width:2; stroke-dasharray:6 3; }
.node-computed rect { fill:var(--computed); stroke:var(--ink); stroke-width:2; }
svg text { font-family:system-ui,-apple-system,"Segoe UI",Tahoma,"Noto Sans Arabic",sans-serif; font-size:15px; fill:var(--ink); }
.edge { fill:none; stroke:var(--muted); stroke-width:2; }
.nodes { list-style:none; padding:0; }
.nodes li { border:2px solid var(--line); border-radius:.5rem; padding:.7rem .9rem; margin-block-end:.7rem; background:var(--wash); }
.ladder { padding-inline-start:1.5rem; }
.ladder li { margin-block-end:.9rem; }
.ladder dl { display:grid; grid-template-columns:max-content minmax(0,1fr); gap:.25rem .75rem; margin-block:.4rem; }
.ladder dd { min-inline-size:0; overflow-wrap:anywhere; }
.ladder dt { font-weight:700; }
.ladder dd { margin:0; }
.cite { color:var(--muted); font-size:.92rem; }
.provenance { display:grid; grid-template-columns:max-content minmax(0,1fr); gap:.25rem .75rem; }
.provenance dd { min-inline-size:0; overflow-wrap:anywhere; }
code { overflow-wrap:anywhere; }
.provenance dt { font-weight:700; }
.provenance dd { margin:0; }
footer { border-block-start:2px solid var(--line); margin-block-start:2.5rem; padding-block:1rem 2rem; color:var(--muted); font-size:.92rem; }
@media (max-width:40rem) { header, main, footer { padding-inline:.75rem; } .provenance { grid-template-columns:1fr; } }
@media (forced-colors:active) { .nodes li, .disclaimer, .provenance dd { border-color:CanvasText; } }
"""


def _svg(data: dict, lang: str, strings: dict) -> str:
    nodes = {node['id']: node for node in data['nodes']}
    depth: dict[str, int] = {}
    visiting: set[str] = set()

    def visit(node_id: str) -> int:
        if node_id in depth:
            return depth[node_id]
        if node_id in visiting:
            return 0
        visiting.add(node_id)
        value = 0 if not nodes[node_id]['depends'] else 1 + max(visit(dep) for dep in nodes[node_id]['depends'])
        visiting.remove(node_id)
        depth[node_id] = value
        return value

    for node_id in nodes:
        visit(node_id)
    layers: dict[int, list[dict]] = {}
    for node in data['nodes']:
        layers.setdefault(depth[node['id']], []).append(node)
    width, height = 150, 56
    gap_x, gap_y, margin = 28, 50, 24
    counts = {level: len(items) for level, items in layers.items()}
    view_width = max(counts.values()) * width + (max(counts.values()) - 1) * gap_x + margin * 2
    view_height = (max(layers) + 1) * height + max(layers) * gap_y + margin * 2
    positions: dict[str, tuple[float, float]] = {}
    for level, items in layers.items():
        total = len(items) * width + (len(items) - 1) * gap_x
        start = (view_width - total) / 2
        for index, node in enumerate(sorted(items, key=lambda item: int(item['id'][1:]))):
            positions[node['id']] = (start + index * (width + gap_x), margin + level * (height + gap_y))
    edges = []
    for node in data['nodes']:
        tx, ty = positions[node['id']]
        for source_id in node['depends']:
            sx, sy = positions[source_id]
            edges.append(
                f'<path class="edge" d="M {sx + width / 2:.1f} {sy + height:.1f} '
                f'C {sx + width / 2:.1f} {(sy + height + ty) / 2:.1f}, '
                f'{tx + width / 2:.1f} {(sy + height + ty) / 2:.1f}, '
                f'{tx + width / 2:.1f} {ty:.1f}" marker-end="url(#rule-arrow)" />')
    shapes = []
    for node in data['nodes']:
        x, y = positions[node['id']]
        cls = {'input': 'node-input', 'constant': 'node-constant', 'computed': 'node-computed'}[node['kind']]
        shapes.append(
            f'<g class="{cls}"><rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" rx="9" />'
            f'<text x="{x + width / 2:.1f}" y="{y + 35:.1f}" text-anchor="middle">{_esc(node["id"])}</text></g>')
    title = f"{_loc(data['title'], lang)} — {strings['rule.presentation.graph']}"
    return f"""
<svg viewBox="0 0 {view_width:.0f} {view_height:.0f}" role="img" aria-labelledby="rule-graph-title" aria-describedby="rule-graph-desc" focusable="false">
  <title id="rule-graph-title">{_esc(title)}</title>
  <desc id="rule-graph-desc">{_esc(strings['rule.presentation.graph_summary'])}</desc>
  <defs><marker id="rule-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#4d5966" /></marker></defs>
  {''.join(edges)}
  {''.join(shapes)}
</svg>"""


def _source_link(data: dict, source_id: str, lang: str) -> str:
    source = next(item for item in data['sources'] if item['id'] == source_id)
    return (f'<a href="{_esc(source["url"])}"><span lang="{source["language"]}" dir="ltr">'
            f'{_esc(source["label"][lang])}</span></a> '
            f'<code lang="en" dir="ltr">{_esc(source_id)}</code>')


def render_page(data: dict, lang: str, strings: dict[str, str]) -> str:
    """Render one locale as a complete static HTML document."""
    errors = validate_presentation(data)
    if errors:
        raise ValueError('; '.join(errors))
    if lang not in LANGUAGES:
        raise ValueError(f'unsupported language: {lang}')
    missing = [key for key in UI_KEYS if not str(strings.get(key, '')).strip()]
    if missing:
        raise ValueError(f'missing UI strings: {", ".join(missing)}')
    direction = DIRECTIONS[lang]
    synthetic = data['synthetic']
    badge = strings['rule.presentation.synthetic'] if synthetic else strings['rule.presentation.reviewed']
    nodes = data['nodes']
    node_rows = []
    for node in nodes:
        depends = ', '.join(node['depends']) if node['depends'] else strings['rule.presentation.none']
        value = node.get('value')
        value_html = f' — {_esc(value)}' if value else ''
        node_rows.append(
            f'<li><p><strong>{_esc(strings["rule.presentation.node"])} <code lang="en" dir="ltr">{_esc(node["id"])}</code>'
            f' — {_esc(node["label"][lang])}</strong></p>'
            f'<p>{_esc(strings["rule.presentation.kind"])}: {_esc(strings["rule.presentation." + node["kind"]])}; '
            f'{_esc(strings["rule.presentation.depends"])}: <code lang="en" dir="ltr">{_esc(depends)}</code>; '
            f'{_esc(strings["rule.presentation.citation"])}: {_source_link(data, node["citation"], lang)}{value_html}</p></li>')
    steps = []
    for step in data['ladder']:
        steps.append(
            f'<li><h3>{_esc(step["condition"][lang])}</h3>'
            f'<dl><dt>{_esc(strings["rule.presentation.if_true"])}</dt><dd>{_esc(step["true"][lang])}</dd>'
            f'<dt>{_esc(strings["rule.presentation.if_false"])}</dt><dd>{_esc(step["false"][lang])}</dd></dl>'
            f'<p class="cite">{_esc(strings["rule.presentation.citation"])}: {_source_link(data, step["citation"], lang)}. {_esc(step["note"][lang])}</p></li>')
    explanations = ''.join(f'<li>{_esc(item)}</li>' for item in data['text']['steps'][lang])
    sources = ''.join(f'<li>{_source_link(data, source["id"], lang)} — {_esc(source["citation"][lang])}</li>'
                      for source in data['sources'])
    unsupported = ''.join(f'<li><strong>{_esc(item["label"][lang])}</strong>: {_esc(item["reason"][lang])}</li>'
                          for item in data['unsupported'])
    review = data['review']
    artifact_hash = data['provenance'].get('artifact_sha256')
    artifact = artifact_hash or strings['rule.presentation.no_artifact']
    test_results = data['provenance'].get('test_results') or strings['rule.presentation.none']
    period = data['effective_period']
    period_text = period['from'] + (f" — {period['to']}" if period['to'] else '')
    review_text = strings['rule.presentation.synthetic'] if synthetic else strings['rule.presentation.reviewed']
    if not synthetic and review.get('reviewer_role'):
        review_text += f" — {review['reviewer_role']} — {review['reviewed_at']}"
    record_html = ''
    if data.get('record'):
        record = data['record']
        record_html = f'<h3>{_esc(strings["rule.presentation.record"])}</h3><dl class="provenance">' + ''.join(
            f'<dt>{_esc(key)}</dt><dd><code lang="en" dir="ltr">{_esc(record[key])}</code></dd>'
            for key in ('instrument_id', 'source_id', 'provision_id', 'legal_version', 'reviewed_interpretation_id')
        ) + '</dl>'
    title = data['title'][lang]
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)} — {_esc(strings['rule.presentation.graph'])}</title>
<style>{_style()}</style>
</head>
<body>
<a class="skip" href="#main">{_esc(strings['skip'])}</a>
<header>
  <p><span class="badge">{_esc(badge)}</span></p>
  <h1>{_esc(title)}</h1>
  <p class="lead">{_esc(data['summary'][lang])}</p>
</header>
<main id="main" tabindex="-1">
  <p class="disclaimer">{_esc(data['disclaimer'][lang])}</p>

  <section aria-labelledby="rule-graph-h">
    <h2 id="rule-graph-h">{_esc(strings['rule.presentation.graph'])}</h2>
    <p>{_esc(strings['rule.presentation.graph_summary'])}</p>
    <figure>{_svg(data, lang, strings)}<figcaption>{_esc(strings['rule.presentation.graph_summary'])}</figcaption></figure>
  </section>

  <section aria-labelledby="rule-nodes-h">
    <h2 id="rule-nodes-h">{_esc(strings['rule.presentation.nodes'])}</h2>
    <ul class="nodes">{''.join(node_rows)}</ul>
  </section>

  <section aria-labelledby="rule-ladder-h">
    <h2 id="rule-ladder-h">{_esc(strings['rule.presentation.ladder'])}</h2>
    <ol class="ladder">{''.join(steps)}</ol>
  </section>

  <section aria-labelledby="rule-text-h">
    <h2 id="rule-text-h">{_esc(strings['rule.presentation.text'])}</h2>
    <h3>{_esc(strings['rule.presentation.explanation'])}</h3>
    <ol>{explanations}</ol>
    <h3>{_esc(strings["rule.presentation.unknown"])}</h3>
    <p>{_esc(data['text']['unknown'][lang])}</p>
    <p>{_esc(data['text']['limits'][lang])}</p>
  </section>

  <section aria-labelledby="rule-sources-h">
    <h2 id="rule-sources-h">{_esc(strings['rule.presentation.sources'])}</h2>
    <ul>{sources}</ul>
  </section>

  <section aria-labelledby="rule-unsupported-h">
    <h2 id="rule-unsupported-h">{_esc(strings['rule.presentation.unsupported'])}</h2>
    <ul>{unsupported}</ul>
  </section>

  <section aria-labelledby="rule-provenance-h">
    <h2 id="rule-provenance-h">{_esc(strings['rule.presentation.provenance'])}</h2>
    <dl class="provenance">
      <dt>{_esc(strings['rule.presentation.review_status'])}</dt><dd>{_esc(review_text)}</dd>
      <dt>{_esc(strings['rule.presentation.effective'])}</dt><dd><code lang="en" dir="ltr">{_esc(period_text)}</code></dd>
      <dt>{_esc(strings['rule.presentation.engine'])}</dt><dd><span lang="en" dir="ltr">{_esc(data['provenance']['engine'])}</span></dd>
      <dt>{_esc(strings['rule.presentation.version'])}</dt><dd><code lang="en" dir="ltr">{_esc(data['provenance']['engine_version'])}</code></dd>
      <dt>{_esc(strings['rule.presentation.artifact'])}</dt><dd>{'<code lang="en" dir="ltr">' + _esc(artifact) + '</code>' if artifact_hash else _esc(artifact)}</dd>
      <dt>{_esc(strings["rule.presentation.tests"])}</dt><dd><code lang="en" dir="ltr">{_esc(test_results)}</code></dd>
    </dl>
    {record_html}
  </section>

  <section aria-labelledby="rule-limits-h">
    <h2 id="rule-limits-h">{_esc(strings['rule.presentation.limits'])}</h2>
    <p>{_esc(data['text']['limits'][lang])}</p>
  </section>
</main>
<footer><p>{_esc(data['disclaimer'][lang])}</p></footer>
</body>
</html>
"""


def render_all(data: dict, out_dir: Path, catalogues: dict[str, dict] | None = None) -> list[Path]:
    """Render every locale below out_dir and return the written paths."""
    errors = validate_presentation(data)
    if errors:
        raise ValueError('; '.join(errors))
    catalogues = catalogues or load_catalogues()
    out_dir = Path(out_dir)
    paths = []
    for lang in LANGUAGES:
        target = out_dir / lang / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(data, lang, catalogues[lang]), encoding='utf-8')
        paths.append(target)
    return paths


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path, help='rule-presentation JSON file')
    parser.add_argument('--check', action='store_true', help='validate only')
    parser.add_argument('--out', type=Path, help='write en/fr/ar pages below this directory')
    args = parser.parse_args(argv)
    data = json.loads(args.artifact.read_text(encoding='utf-8'))
    errors = validate_presentation(data)
    if errors:
        for error in errors:
            print(error)
        return 1
    if args.check:
        print(f'{data["id"]}: valid {FORMAT} with {len(data["nodes"])} nodes and {len(data["ladder"])} steps')
        return 0
    if not args.out:
        parser.error('--out is required unless --check is used')
    for path in render_all(data, args.out):
        print(path)
    return 0


if __name__ == '__main__':
    sys.exit(main())
