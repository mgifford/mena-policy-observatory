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
import textwrap
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


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _localized_values(obj: object):
    if not isinstance(obj, dict):
        return []
    return [obj.get(lang) for lang in LANGUAGES]


def _check_localized(obj: object, path: str, errors: list[str]) -> None:
    if not isinstance(obj, dict):
        return
    present = [lang for lang in LANGUAGES if _has_text(obj.get(lang))]
    if not present:
        errors.append(f'{path}: at least one language expression is required')


def _validate_mappings(data: dict, errors: list[str]) -> None:
    mappings = data.get('mappings')
    if not mappings:
        return
    node_ids = {node['id'] for node in data['nodes']}
    step_numbers = {step['step'] for step in data['ladder']}
    outcomes = list(data.get('outcomes') or [])
    if not outcomes:
        errors.append('mappings: an outcomes list is required when mappings are present')
    if len(outcomes) != len(set(outcomes)):
        errors.append('outcomes: duplicate outcome id')
    outcome_set = set(outcomes)
    seen_pairs = set()
    mapped: dict[str, list[int]] = {}
    for item in mappings['node_steps']:
        node, step = item['node'], item['step']
        if node not in node_ids:
            errors.append(f'mappings.node_steps: unknown node {node}')
        if step not in step_numbers:
            errors.append(f'mappings.node_steps: unknown step {step}')
        if (node, step) in seen_pairs:
            errors.append(f'mappings.node_steps: duplicate {node}/{step}')
        seen_pairs.add((node, step))
        mapped.setdefault(node, []).append(step)
    for node in data['nodes']:
        if node['id'] not in mapped:
            errors.append(f'mappings.node_steps: node {node["id"]} is not mapped')
    for node in data['nodes']:
        target = max(mapped.get(node['id'], [0]))
        for dependency in node['depends']:
            source = max(mapped.get(dependency, [0]))
            if source > target:
                errors.append(f'mappings.node_steps: dependency {dependency} is downstream of {node["id"]}')
    branch_steps = []
    for branch in mappings['branches']:
        step = branch['step']
        branch_steps.append(step)
        if step not in step_numbers:
            errors.append(f'mappings.branches: unknown step {step}')
        if branch['true'] == branch['false']:
            errors.append(f'mappings.branches: step {step} has the same true and false target')
        for value in (branch['true'], branch['false']):
            if value != 'continue' and value not in outcome_set:
                errors.append(f'mappings.branches: step {step} has unknown target {value}')
        if step < len(data['ladder']) and 'continue' not in (branch['true'], branch['false']):
            errors.append(f'mappings.branches: step {step} cannot reach the next step')
    if sorted(branch_steps) != sorted(step_numbers):
        errors.append('mappings.branches: each ladder step needs exactly one branch record')
    test_ids = []
    for test in mappings['tests']:
        test_ids.append(test['id'])
        if test['expected'] != 'error' and test['expected'] not in outcome_set:
            errors.append(f'mappings.tests: {test["id"]} has unknown expected outcome {test["expected"]}')
    if len(test_ids) != len(set(test_ids)):
        errors.append('mappings.tests: duplicate test id')


def _validate_period(data: dict, errors: list[str]) -> None:
    period = data['effective_period']
    status = period.get('status')
    from_date = period.get('from')
    to_date = period.get('to')
    if status is None:
        status = 'known' if from_date is not None else 'unknown'
    if status in ('unknown', 'unresolved'):
        if from_date is not None or to_date is not None:
            errors.append(f'effective_period: status {status} must not invent dates')
    elif status in ('known', 'conditional', 'retrospective'):
        if not _valid_date(from_date):
            errors.append(f'effective_period: status {status} needs a valid from date')
        if status == 'conditional' and not _has_text((period.get('condition') or {}).get('en')) and not any(
                _has_text(value) for value in _localized_values(period.get('condition'))):
            errors.append('effective_period: a conditional period needs a condition')
    if to_date is not None:
        if not _valid_date(to_date):
            errors.append('effective_period.to must be null or a valid ISO date')
        elif from_date is None:
            errors.append('effective_period.to needs a from date')
        elif to_date < from_date:
            errors.append('effective_period.to cannot be before from')
    if period.get('condition'):
        _check_localized(period['condition'], 'effective_period.condition', errors)
    if period.get('note'):
        _check_localized(period['note'], 'effective_period.note', errors)


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

    step_text_present = False
    for lang in LANGUAGES:
        explanations = data['text']['steps'].get(lang)
        if explanations is None:
            continue
        step_text_present = True
        if len(explanations) != len(steps):
            errors.append(f"text.steps.{lang}: needs one explanation per ladder step")
    if not step_text_present:
        errors.append('text.steps: at least one language explanation list is required')
    _validate_period(data, errors)
    _validate_mappings(data, errors)
    for path, localized in (
            ('title', data['title']), ('summary', data['summary']),
            ('disclaimer', data['disclaimer']), ('text.unknown', data['text']['unknown']),
            ('text.limits', data['text']['limits'])):
        _check_localized(localized, path, errors)
    for node in data['nodes']:
        _check_localized(node['label'], f'node {node["id"]}.label', errors)
    for step in steps:
        _check_localized(step['condition'], f'ladder {step["step"]}.condition', errors)
        _check_localized(step['true'], f'ladder {step["step"]}.true', errors)
        _check_localized(step['false'], f'ladder {step["step"]}.false', errors)
        _check_localized(step['note'], f'ladder {step["step"]}.note', errors)
    for source in data['sources']:
        _check_localized(source['citation'], f'source {source["id"]}.citation', errors)
        _check_localized(source['label'], f'source {source["id"]}.label', errors)
    for index, item in enumerate(data['unsupported']):
        _check_localized(item['label'], f'unsupported[{index}].label', errors)
        _check_localized(item['reason'], f'unsupported[{index}].reason', errors)

    if not str(provenance.get('encoding_id') or '').strip():
        errors.append('provenance: encoding_id is required')
    if not str(provenance.get('engine') or '').strip():
        errors.append('provenance: engine is required')
    if not str(provenance.get('engine_version') or '').strip():
        errors.append('provenance: engine_version is required')
    return errors


def validate_publication(data: dict, root: Path | None = None) -> list[str]:
    """Resolve a non-synthetic presentation against repository evidence.

    This is deliberately separate from syntactic validation. It does not prove
    legal correctness; it verifies that the named record, source, provision,
    interpretation, encoding artifact and test evidence exist and agree.
    Synthetic artefacts are exempt because they are explicitly fictional.
    """
    errors = validate_presentation(data)
    if errors or data.get('synthetic'):
        return errors
    base = Path(root) if root else REPO_ROOT
    record = data.get('record') or {}
    provenance = data.get('provenance') or {}
    try:
        policies = json.loads((base / 'regions/mena/data/policies.json').read_text(encoding='utf-8'))
        policy = next((item for item in policies if item.get('id') == record.get('instrument_id')), None)
        if policy is None:
            return [f'publication: unknown instrument_id {record.get("instrument_id")!r}']
        research = json.loads((base / 'regions/mena/policies' / record['instrument_id'] / 'research.json').read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return [f'publication: cannot resolve record evidence: {exc}']
    sources = {item.get('id'): item for item in research.get('sources', [])}
    provisions = {item.get('id'): item for item in research.get('provisions', [])}
    interpretations = {item.get('id'): item for item in research.get('interpretations', [])}
    source = sources.get(record.get('source_id'))
    if source is None:
        errors.append(f'publication: unknown source_id {record.get("source_id")!r}')
    provision = provisions.get(record.get('provision_id'))
    if provision is None:
        errors.append(f'publication: unknown provision_id {record.get("provision_id")!r}')
    elif record.get('source_id') not in (provision.get('source_ids') or []):
        errors.append('publication: the provision does not reference the named source')
    interpretation = interpretations.get(record.get('reviewed_interpretation_id'))
    if interpretation is None:
        errors.append(f'publication: unknown interpretation {record.get("reviewed_interpretation_id")!r}')
    else:
        if interpretation.get('status') != 'resolved' or interpretation.get('resolution') is None:
            errors.append('publication: the reviewed interpretation is not resolved')
        if not str(interpretation.get('reviewer') or '').strip() or not _valid_date(interpretation.get('reviewed_at') or ''):
            errors.append('publication: the interpretation needs a reviewer and review date')
    review = research.get('review') or {}
    if review.get('status') != 'reviewed':
        errors.append('publication: the research record itself is not reviewed')
    if source is not None:
        versions = {source.get('document_version'), source.get('effective_date'), source.get('publication_date')}
        versions.discard(None)
        versions.discard('unknown')
        if not versions:
            errors.append('publication: no recorded legal version exists for the source')
        elif record.get('legal_version') not in versions:
            errors.append('publication: legal_version does not match the recorded source version')
    artifact_path = provenance.get('artifact_path')
    tests_path = provenance.get('tests_path')
    if not isinstance(artifact_path, str) or not artifact_path:
        errors.append('publication: artifact_path is required')
    if not isinstance(tests_path, str) or not tests_path:
        errors.append('publication: tests_path is required')
    if isinstance(artifact_path, str) and artifact_path:
        path = (base / artifact_path).resolve()
        if not path.is_relative_to(base.resolve()):
            errors.append('publication: artifact_path escapes the repository root')
        elif not path.is_file():
            errors.append('publication: encoding artifact does not exist')
        else:
            import hashlib
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != provenance.get('artifact_sha256'):
                errors.append('publication: artifact checksum does not match')
            try:
                artifact = json.loads(path.read_text(encoding='utf-8'))
                if artifact.get('engine_version') not in (None, provenance.get('engine_version')):
                    errors.append('publication: artifact engine version does not match provenance')
            except (OSError, json.JSONDecodeError):
                errors.append('publication: encoding artifact is not valid JSON')
    if isinstance(tests_path, str) and tests_path:
        path = (base / tests_path).resolve()
        if not path.is_relative_to(base.resolve()):
            errors.append('publication: tests_path escapes the repository root')
        elif not path.is_file():
            errors.append('publication: test evidence does not exist')
        else:
            try:
                evidence = json.loads(path.read_text(encoding='utf-8'))
                results = evidence.get('results') if isinstance(evidence, dict) else None
                if not isinstance(results, list) or not results:
                    errors.append('publication: test evidence has no results')
                elif any(not isinstance(item, dict) or item.get('status') != 'passed' for item in results):
                    errors.append('publication: test evidence contains a non-passing result')
            except (OSError, json.JSONDecodeError):
                errors.append('publication: test evidence is not valid JSON')
    return errors


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _resolve(value: object, lang: str) -> tuple[str, str]:
    if isinstance(value, dict):
        for code in (lang, 'en', 'fr', 'ar'):
            candidate = value.get(code)
            if _has_text(candidate):
                return str(candidate), code
    return '', lang


def _text_raw(value: object, lang: str) -> str:
    return _resolve(value, lang)[0]


def _text_html(value: object, lang: str) -> str:
    text, used = _resolve(value, lang)
    if used != lang:
        direction = DIRECTIONS.get(used, 'ltr')
        return f'<span lang="{used}" dir="{direction}">{_esc(text)}</span>'
    return _esc(text)


def _steps_for(data: dict, lang: str) -> tuple[list[str], str]:
    for code in (lang, 'en', 'fr', 'ar'):
        value = data['text']['steps'].get(code)
        if isinstance(value, list) and value:
            return value, code
    return [], lang


def _needs_fallback(data: dict, lang: str) -> bool:
    localized = [data['title'], data['summary'], data['disclaimer'],
                 data['text']['unknown'], data['text']['limits']]
    localized += [node['label'] for node in data['nodes']]
    localized += [step['condition'] for step in data['ladder']]
    localized += [step['true'] for step in data['ladder']]
    localized += [step['false'] for step in data['ladder']]
    localized += [step['note'] for step in data['ladder']]
    localized += [source['citation'] for source in data['sources']]
    localized += [source['label'] for source in data['sources']]
    localized += [item['label'] for item in data['unsupported']]
    localized += [item['reason'] for item in data['unsupported']]
    if data['effective_period'].get('condition'):
        localized.append(data['effective_period']['condition'])
    for value in localized:
        if isinstance(value, dict) and not _has_text(value.get(lang)) and any(
                _has_text(value.get(code)) for code in LANGUAGES):
            return True
    return not _has_text(data['text']['steps'].get(lang)) and any(
        isinstance(data['text']['steps'].get(code), list) and data['text']['steps'].get(code)
        for code in LANGUAGES)


def _period_text(data: dict, lang: str, strings: dict) -> str:
    period = data['effective_period']
    status = period.get('status') or ('known' if period.get('from') else 'unknown')
    if status in ('unknown', 'unresolved'):
        return strings[f'rule.presentation.effective_{status}']
    text = str(period.get('from') or '')
    if status == 'conditional' and period.get('condition'):
        text += f" ({strings['rule.presentation.effective_conditional']}: {_text_raw(period['condition'], lang)})"
    if status == 'retrospective':
        text += f" ({strings['rule.presentation.effective_retrospective']})"
    if period.get('to'):
        text += f" — {period['to']}"
    return text


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
    width, height = 170, 76
    gap_x, gap_y, margin = 30, 52, 24
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
        label, used = _resolve(node.get('label'), lang)
        lines = textwrap.wrap(label, width=24)[:2]
        if len(textwrap.wrap(label, width=24)) > 2:
            lines[-1] = lines[-1][:23] + '…'
        label_spans = ''.join(
            f'<tspan x="{x + width / 2:.1f}" dy="{0 if index == 0 else 15}">{_esc(line)}</tspan>'
            for index, line in enumerate(lines or ['']))
        shapes.append(
            f'<g class="{cls}"><rect x="{x:.1f}" y="{y:.1f}" width="{width}" height="{height}" rx="9" />'
            f'<text x="{x + width / 2:.1f}" y="{y + 20:.1f}" text-anchor="middle">{_esc(node["id"])}</text>'
            f'<text x="{x + width / 2:.1f}" y="{y + 38:.1f}" text-anchor="middle" lang="{used}" dir="{DIRECTIONS.get(used, "ltr")}">{label_spans}</text></g>')
    title = f"{_text_raw(data['title'], lang)} — {strings['rule.presentation.graph']}"
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
    return (f'<a href="{_esc(source["url"])}">{_text_html(source["label"], lang)}</a> '
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
            f' — {_text_html(node["label"], lang)}</strong></p>'
            f'<p>{_esc(strings["rule.presentation.kind"])}: {_esc(strings["rule.presentation." + node["kind"]])}; '
            f'{_esc(strings["rule.presentation.depends"])}: <code lang="en" dir="ltr">{_esc(depends)}</code>; '
            f'{_esc(strings["rule.presentation.citation"])}: {_source_link(data, node["citation"], lang)}{value_html}</p></li>')
    steps = []
    for step in data['ladder']:
        steps.append(
            f'<li><h3>{_text_html(step["condition"], lang)}</h3>'
            f'<dl><dt>{_esc(strings["rule.presentation.if_true"])}</dt><dd>{_text_html(step["true"], lang)}</dd>'
            f'<dt>{_esc(strings["rule.presentation.if_false"])}</dt><dd>{_text_html(step["false"], lang)}</dd></dl>'
            f'<p class="cite">{_esc(strings["rule.presentation.citation"])}: {_source_link(data, step["citation"], lang)}. {_text_html(step["note"], lang)}</p></li>')
    explanation_values, explanation_lang = _steps_for(data, lang)
    explanations = ''.join(
        f'<li><span lang="{explanation_lang}" dir="{DIRECTIONS.get(explanation_lang, "ltr")}">{_esc(item)}</span></li>'
        if explanation_lang != lang else f'<li>{_esc(item)}</li>'
        for item in explanation_values)
    sources = ''.join(f'<li>{_source_link(data, source["id"], lang)} — {_text_html(source["citation"], lang)}</li>'
                      for source in data['sources'])
    unsupported = ''.join(f'<li><strong>{_text_html(item["label"], lang)}</strong>: {_text_html(item["reason"], lang)}</li>'
                          for item in data['unsupported'])
    review = data['review']
    artifact_hash = data['provenance'].get('artifact_sha256')
    artifact = artifact_hash or strings['rule.presentation.no_artifact']
    test_results = data['provenance'].get('test_results') or strings['rule.presentation.none']
    period_text = _period_text(data, lang, strings)
    period_html = (f'<code lang="en" dir="ltr">{_esc(period_text)}</code>'
                   if data['effective_period'].get('from') else _esc(period_text))
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
    title = _text_raw(data['title'], lang)
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
  <h1>{_text_html(data['title'], lang)}</h1>
  {f'<p class="notice">{_esc(strings["rule.presentation.translation_fallback"])}</p>' if _needs_fallback(data, lang) else ''}
  <p class="lead">{_text_html(data["summary"], lang)}</p>
</header>
<main id="main" tabindex="-1">
  <p class="disclaimer">{_text_html(data["disclaimer"], lang)}</p>

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
    <p>{_text_html(data["text"]["unknown"], lang)}</p>
    <p>{_text_html(data["text"]["limits"], lang)}</p>
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
      <dt>{_esc(strings['rule.presentation.effective'])}</dt><dd>{period_html}</dd>
      <dt>{_esc(strings['rule.presentation.engine'])}</dt><dd><span lang="en" dir="ltr">{_esc(data['provenance']['engine'])}</span></dd>
      <dt>{_esc(strings['rule.presentation.version'])}</dt><dd><code lang="en" dir="ltr">{_esc(data['provenance']['engine_version'])}</code></dd>
      <dt>{_esc(strings['rule.presentation.artifact'])}</dt><dd>{'<code lang="en" dir="ltr">' + _esc(artifact) + '</code>' if artifact_hash else _esc(artifact)}</dd>
      <dt>{_esc(strings["rule.presentation.tests"])}</dt><dd><code lang="en" dir="ltr">{_esc(test_results)}</code></dd>
    </dl>
    {record_html}
  </section>

  <section aria-labelledby="rule-limits-h">
    <h2 id="rule-limits-h">{_esc(strings['rule.presentation.limits'])}</h2>
    <p>{_text_html(data["text"]["limits"], lang)}</p>
  </section>
</main>
<footer><p>{_text_html(data["disclaimer"], lang)}</p></footer>
</body>
</html>
"""


def render_fragment(data: dict, lang: str, strings: dict[str, str]) -> str:
    """Return the main content only, for embedding in an existing site page.

    The fragment contains the disclaimer and all presentation sections, but no
    header, site navigation or footer. It is generated by rendering the full
    document and extracting its main landmark, which keeps one rendering path.
    """
    page = render_page(data, lang, strings)
    start_marker = '<main id="main" tabindex="-1">'
    start = page.index(start_marker) + len(start_marker)
    end = page.index('</main>')
    fragment = page[start:end].strip()
    return '\n'.join(line.rstrip() for line in fragment.splitlines()).strip()


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
