#!/usr/bin/env python3
"""Build static, evidence-led visualizations for existing research records.

This module is deliberately separate from the executable-rule renderer. It
visualises only what is already recorded in research.json: the instrument,
candidate provisions, open interpretation questions and recorded related
documents. It never infers missing articles, legal effect or a settled
interpretation.
"""
from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path

try:  # imported as framework.research_visualization
    from .research import load_research
    from .rule_presentation import render_fragment
    from .rules_examples import code_excerpts
except ImportError:  # run as a script
    from research import load_research
    from rule_presentation import render_fragment
    from rules_examples import code_excerpts

SELECTED_RECORDS = (
    'ae-moe-accessibility',
    'ae-mof-accessibility',
    'ae-national-digital-accessibility',
    'qa-eaccessibility-2011',
    'qa-eaccessibility-2025-upcoming',
    'sa-dga-web-accessibility-guide',
    'sa-mep-accessibility',
    'ae-federal-law-29-2006',
    'mena-t02-001',
    'jo-personal-data-2023',
    'ma-personal-data-09-08',
)
SYNTHETIC_FIXTURE = Path('regions/mena/data/visualizations/synthetic-procurement.json')
LANGUAGES = ('en', 'fr', 'ar')
LANGUAGE_NAMES = {
    'en': {'en': 'English', 'fr': 'French', 'ar': 'Arabic'},
    'fr': {'en': 'anglais', 'fr': 'français', 'ar': 'arabe'},
    'ar': {'en': 'الإنجليزية', 'fr': 'الفرنسية', 'ar': 'العربية'},
}
DOMAINS_PATH = Path(__file__).resolve().parents[1] / 'regions' / 'mena' / 'data' / 'domains.json'


def _domain_label(topic: str, lang: str) -> str:
    try:
        data = json.loads(DOMAINS_PATH.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return topic
    def walk(value):
        if isinstance(value, dict):
            if value.get('id') == topic:
                return value.get(f'label_{lang}') or value.get('label_en') or topic
            for child in value.values():
                found = walk(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child)
                if found:
                    return found
        return None
    return walk(data) or topic
DIRECTIONS = {'en': 'ltr', 'fr': 'ltr', 'ar': 'rtl', 'fa': 'rtl', 'he': 'rtl', 'ur': 'rtl', 'tr': 'ltr'}
EFFECT_KEYS = {
    'not_assessed': 'record.effect.not_assessed',
    'draft_not_in_force': 'record.effect.draft_not_in_force',
    'in_force_confirmed': 'record.effect.in_force_confirmed',
    'not_in_force_confirmed': 'record.effect.not_in_force_confirmed',
    'indeterminate': 'record.effect.indeterminate',
}
ENCODING_KEYS = {
    'blocked': 'record.encoding.blocked', 'candidate': 'record.encoding.candidate',
    'tested': 'record.encoding.tested', 'reviewed': 'record.encoding.reviewed',
}
RISK_KEYS = {
    'critical': 'record.risk.critical', 'high': 'record.risk.high',
    'medium': 'record.risk.medium', 'low': 'record.risk.low', 'unknown': 'record.risk.unknown',
}
REQUIRES_KEYS = {
    'qualified_legal_review': 'record.requires.qualified_legal_review',
    'qualified_accessibility_review': 'record.requires.qualified_accessibility_review',
    'source_capture': 'record.requires.source_capture',
    'authority_confirmation': 'record.requires.authority_confirmation',
    'translation_review': 'record.requires.translation_review',
}
QUESTION_STATUS_KEYS = {'unresolved': 'record.status.unresolved', 'resolved': 'record.status.resolved'}
AUTHORITATIVE_KEYS = {
    'yes': 'record.source.authoritative.yes', 'no': 'record.source.authoritative.no',
    'unknown': 'record.source.authoritative.unknown',
}
LEGAL_STATUS_KEYS = {
    'not_legally_assessed': 'record.legal.not_assessed',
    'current_status_requires_confirmation': 'record.legal.requires_confirmation',
    'draft_not_confirmed_in_force': 'record.legal.draft',
    'binding_confirmed': 'record.legal.binding',
    'nonbinding_confirmed': 'record.legal.nonbinding',
}
INSTRUMENT_KEYS = {
    'national_policy': 'instrument.national_policy',
    'government_guideline': 'instrument.government_guideline',
    'draft_policy': 'instrument.draft_policy', 'agency_policy': 'instrument.agency_policy',
    'legislation': 'instrument.legislation', 'regulation': 'instrument.regulation',
    'technical_standard': 'instrument.technical_standard', 'other': 'instrument.other',
}


def _label(strings: dict, mapping: dict, value: object, fallback: str = '') -> str:
    key = mapping.get(str(value))
    if key and key in strings:
        return strings[key]
    return fallback or str(value or 'unknown')


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _foreign(value: str, page_lang: str, value_lang: str = 'en') -> str:
    if not value:
        return ''
    if value_lang == page_lang:
        return esc(value)
    direction = DIRECTIONS.get(value_lang, 'ltr')
    return f'<span lang="{esc(value_lang)}" dir="{direction}">{esc(value)}</span>'


def _source_link(source: dict, page_lang: str, locator: str | None = None) -> str:
    title = _foreign(source.get('title', ''), page_lang, source.get('language', 'en'))
    link = f'<a href="{esc(source.get("url", "#"))}">{title}</a>'
    if locator:
        link += f' — <span class="meta">{esc(locator)}</span>'
    return link


def _date(value: object, strings: dict) -> str:
    return esc(value) if isinstance(value, str) and value != 'unknown' else esc(strings['visualizations.dates_unknown'])


def selected_records(base: Path) -> list[tuple[dict, dict]]:
    policies = json.loads((base / 'data' / 'policies.json').read_text(encoding='utf-8'))
    by_id = {record['id']: record for record in policies}
    result = []
    for record_id in SELECTED_RECORDS:
        record = by_id.get(record_id)
        if record is None:
            continue
        research = load_research(base / 'policies' / record_id)
        result.append((record, research))
    return result


def build_structure(record: dict, research: dict) -> dict:
    """Return a source-structure model from recorded evidence only."""
    sources = research.get('sources') or []
    if not sources:
        raise ValueError(f'{record["id"]}: no source record')
    source = sources[0]
    source_lang = source.get('language', record.get('language', 'en'))
    instrument_id = f'record:{record["id"]}'
    nodes = [{
        'id': instrument_id,
        'type': 'instrument',
        'label': source.get('title') or record.get('title') or record['id'],
        'source_ref': source.get('id'),
        'evidence_status': 'recorded_source_metadata',
        'language': source_lang,
        'version': source.get('document_version'),
        'review_state': 'unreviewed',
        'uncertainty': [
            f'Publication date: {source.get("publication_date") or "unknown"}',
            f'Effective date: {source.get("effective_date") or "unknown"}',
            f'Authoritative language: {source.get("authoritative_language") or "unknown"}',
        ],
        'url': source.get('url'),
        'source_ids': [source.get('id')],
    }]
    edges = []
    provision_by_id = {}
    for provision in research.get('provisions') or []:
        provision_id = provision.get('id')
        provision_by_id[provision_id] = provision
        locator = (provision.get('locator') or {}).get('value') or 'unknown'
        nodes.append({
            'id': provision_id,
            'type': 'provision',
            'label': provision.get('heading', ''),
            'source_ref': (provision.get('source_ids') or [source.get('id')])[0],
            'source_ids': provision.get('source_ids') or [],
            'locator': locator,
            'evidence_status': 'recorded_provision_metadata',
            'language': source_lang,
            'version': source.get('document_version'),
            'review_state': 'unreviewed',
            'effect_assessment': provision.get('effect_assessment'),
            'encoding_status': provision.get('encoding_status'),
            'uncertainty': [f'Effect assessment: {provision.get("effect_assessment")}'],
            'summary': provision.get('summary', ''),
        })
        edges.append({
            'id': f'contains:{provision_id}',
            'source': instrument_id,
            'target': provision_id,
            'type': 'contains',
            'evidence_ref': provision_id,
            'review_state': 'recorded_metadata',
        })

    question_by_id = {}
    for question in research.get('interpretations') or []:
        question_id = question.get('id')
        question_by_id[question_id] = question
        provision_id = question.get('provision_id')
        nodes.append({
            'id': question_id,
            'type': 'question',
            'label': question.get('statement', ''),
            'source_ref': provision_id or source.get('id'),
            'source_ids': [source.get('id')],
            'evidence_status': 'candidate_interpretation',
            'language': record.get('language', source_lang),
            'version': source.get('document_version'),
            'review_state': question.get('status') or 'unresolved',
            'uncertainty': [
                f'Risk: {question.get("risk") or "unknown"}',
                f'Requires: {question.get("requires") or "unknown"}',
            ],
            'statement': question.get('statement', ''),
            'observation': question.get('observation'),
            'alternatives': question.get('alternatives') or [],
            'risk': question.get('risk'),
            'requires': question.get('requires'),
            'provision_id': provision_id,
        })
        edges.append({
            'id': f'question:{question_id}',
            'source': provision_id if provision_id in provision_by_id else instrument_id,
            'target': question_id,
            'type': 'raises_question',
            'evidence_ref': question_id,
            'review_state': question.get('status') or 'unresolved',
        })

    for relation in research.get('relations') or []:
        relation_id = relation.get('id')
        target = relation.get('target') or {}
        nodes.append({
            'id': relation_id,
            'type': 'related',
            'label': target.get('title', ''),
            'source_ref': relation_id,
            'source_ids': [source.get('id')],
            'evidence_status': 'recorded_relation',
            'language': 'unknown',
            'version': None,
            'review_state': relation.get('review_state') or 'unreviewed',
            'uncertainty': [
                f'Recorded label: {relation.get("recorded_label") or "unknown"}',
                'Legal relation is not established' if relation.get('relation') == 'unspecified' else '',
            ],
            'url': target.get('url'),
            'record_id': target.get('record_id'),
            'recorded_label': relation.get('recorded_label'),
            'relation': relation.get('relation'),
        })
        edges.append({
            'id': f'relation:{relation_id}',
            'source': instrument_id,
            'target': relation_id,
            'type': 'records_relation',
            'evidence_ref': relation_id,
            'review_state': relation.get('review_state') or 'unreviewed',
        })

    model = {
        'format': 'source-structure/v1',
        'record_id': record['id'],
        'title': source.get('title') or record.get('title'),
        'jurisdiction': record.get('country'),
        'source': source,
        'record': record,
        'nodes': nodes,
        'edges': edges,
        'questions': list(question_by_id.values()),
        'provisions': list(provision_by_id.values()),
        'relations': list(research.get('relations') or []),
    }
    return model


def validate_structure(model: dict) -> list[str]:
    errors: list[str] = []
    node_ids = [node.get('id') for node in model.get('nodes', [])]
    if len(node_ids) != len(set(node_ids)):
        errors.append('duplicate node id')
    required = ('id', 'type', 'label', 'source_ref', 'evidence_status',
                'language', 'review_state', 'uncertainty')
    for node in model.get('nodes', []):
        for field in required:
            if field not in node:
                errors.append(f'node {node.get("id")}: missing {field}')
        if node.get('type') not in ('instrument', 'provision', 'question', 'related'):
            errors.append(f'node {node.get("id")}: unknown type')
    node_set = set(node_ids)
    edge_ids = [edge.get('id') for edge in model.get('edges', [])]
    if len(edge_ids) != len(set(edge_ids)):
        errors.append('duplicate edge id')
    for edge in model.get('edges', []):
        if edge.get('source') not in node_set or edge.get('target') not in node_set:
            errors.append(f'edge {edge.get("id")}: unresolved endpoint')
        if edge.get('type') not in ('contains', 'raises_question', 'records_relation'):
            errors.append(f'edge {edge.get("id")}: unknown type')
    if not any(node.get('type') == 'instrument' for node in model.get('nodes', [])):
        errors.append('missing instrument node')
    return errors


def _short(label: str, width: int = 26) -> list[str]:
    lines = textwrap.wrap(label, width=width)
    if len(lines) > 2:
        lines = lines[:2]
        lines[-1] = lines[-1][:width - 1] + '…'
    return lines or ['']


def _svg(model: dict, strings: dict, page_lang: str) -> str:
    layers = {
        'instrument': [n for n in model['nodes'] if n['type'] == 'instrument'],
        'provision': [n for n in model['nodes'] if n['type'] == 'provision'],
        'question': [n for n in model['nodes'] if n['type'] == 'question'],
        'related': [n for n in model['nodes'] if n['type'] == 'related'],
    }
    width, height, gap_x, gap_y, margin = 190, 68, 30, 64, 44
    bottom = layers['question'] + layers['related']
    rows = [layers['instrument'], layers['provision'], bottom]
    max_count = max(len(row) for row in rows) or 1
    view_width = max_count * width + (max_count - 1) * gap_x + margin * 2
    view_height = 3 * height + 2 * gap_y + margin * 2
    pos = {}
    for row_index, row in enumerate(rows):
        total = len(row) * width + max(0, len(row) - 1) * gap_x
        start = (view_width - total) / 2
        for index, node in enumerate(row):
            pos[node['id']] = (start + index * (width + gap_x), margin + row_index * (height + gap_y))
    style = {
        'contains': 'stroke-width:3;stroke-dasharray:none',
        'raises_question': 'stroke-width:2;stroke-dasharray:2 6',
        'records_relation': 'stroke-width:2;stroke-dasharray:9 5',
    }
    edges = []
    for edge in model['edges']:
        sx, sy = pos[edge['source']]
        tx, ty = pos[edge['target']]
        mid = (sy + height + ty) / 2
        edges.append(
            f'<path class="edge edge-{edge["type"]}" d="M {sx + width / 2:.1f} {sy + height:.1f} '
            f'C {sx + width / 2:.1f} {mid:.1f}, {tx + width / 2:.1f} {mid:.1f}, {tx + width / 2:.1f} {ty:.1f}" '
            f'style="{style[edge["type"]]}" marker-end="url(#struct-arrow)" />')
    shapes = []
    for node in model['nodes']:
        x, y = pos[node['id']]
        cls = f"node-{node['type']}"
        lang = node.get('language') if node.get('language') not in (None, 'unknown') else 'en'
        direction = DIRECTIONS.get(lang, 'ltr')
        lines = _short(f"{node['id']} · {node['label']}" if node['type'] != 'instrument' else node['label'])
        text = ''.join(
            f'<tspan x="{x + width / 2:.1f}" dy="{0 if i == 0 else 17}">{esc(line)}</tspan>'
            for i, line in enumerate(lines))
        shapes.append(
            f'<g class="{cls}"><rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" />'
            f'<text x="{x + width / 2:.1f}" y="{y + 24}" text-anchor="middle" lang="{lang}" dir="{direction}">{text}</text></g>')
    title = f"{esc(model['title'])} — {strings['visualizations.structure_heading']}"
    return f"""
<svg viewBox="0 0 {view_width:.0f} {view_height:.0f}" role="img" aria-labelledby="struct-title" aria-describedby="struct-desc" focusable="false" direction="ltr">
  <title id="struct-title">{title}</title>
  <desc id="struct-desc">{esc(strings['visualizations.structure_caption'])}</desc>
  <defs><marker id="struct-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#4d5966" /></marker></defs>
  {''.join(edges)}
  {''.join(shapes)}
</svg>"""


def _legend(strings: dict) -> str:
    return f"""
<div class="legend" role="group" aria-label="{esc(strings['visualizations.legend'])}">
  <span><span class="line solid" aria-hidden="true"></span>{esc(strings['visualizations.edge_contains'])}</span>
  <span><span class="line dotted" aria-hidden="true"></span>{esc(strings['visualizations.edge_question'])}</span>
  <span><span class="line dashed" aria-hidden="true"></span>{esc(strings['visualizations.edge_relation'])}</span>
</div>"""


def _evidence(source: dict, strings: dict, page_lang: str, record_id: str, legal_effect: object) -> str:
    capture = source.get('capture') or {}
    if capture.get('bytes_stored'):
        capture_text = (f"{strings['visualizations.capture_stored']} — "
                        f"<code lang=\"en\" dir=\"ltr\">{esc(capture.get('sha256') or '')}</code>")
    else:
        capture_text = strings['visualizations.capture_none']
    if source.get('excerpt_status') == 'recorded' and source.get('excerpt'):
        excerpt = source['excerpt']
        excerpt_html = (
            f'<blockquote lang="{esc(excerpt.get("language", "en"))}" dir="ltr">{esc(excerpt.get("text", ""))}</blockquote>'
            f'<p class="meta">{esc(strings["record.table.locator"])}: <span lang="{esc(excerpt.get("language", "en"))}" dir="ltr">{esc(excerpt.get("locator", ""))}</span></p>')
    else:
        excerpt_html = f'<p>{esc(strings["visualizations.excerpt_none"])}</p>'
    excerpt_link = ''
    if source.get('excerpt_status') == 'recorded':
        excerpt_link = (f'<p><a href="../records/artifacts/{esc(record_id)}/SOURCE.md">'
                        f'{esc(strings["visualizations.excerpt_artifact"])}</a></p>')
    return f"""
<section aria-labelledby="evidence-h">
  <h2 id="evidence-h">{esc(strings['visualizations.source_evidence_heading'])}</h2>
  <dl>
    <dt>{esc(strings['record.source'])}</dt><dd>{_source_link(source, page_lang)}</dd>
    <dt>{esc(strings['record.authority'])}</dt><dd>{_foreign(source.get('issuer', ''), page_lang)}</dd>
    <dt>{esc(strings['visualizations.source_language'])}</dt><dd><code lang="en" dir="ltr">{esc(source.get('language', 'unknown'))}</code></dd>
    <dt>{esc(strings['record.source.authoritative'])}</dt><dd>{esc(_label(strings, AUTHORITATIVE_KEYS, source.get('authoritative_language'), 'unknown'))}</dd>
    <dt>{esc(strings['visualizations.publication_date'])}</dt><dd>{_date(source.get('publication_date'), strings)}</dd>
    <dt>{esc(strings['visualizations.effective_date'])}</dt><dd>{_date(source.get('effective_date'), strings)}</dd>
    <dt>{esc(strings['visualizations.document_version'])}</dt><dd>{esc(source.get('document_version') or strings['visualizations.dates_unknown'])}</dd>
    <dt>{esc(strings['record.legal'])}</dt><dd>{esc(_label(strings, LEGAL_STATUS_KEYS, legal_effect))}</dd>
    <dt>{esc(strings['visualizations.evidence'])}</dt><dd>{capture_text}</dd>
    <dt>{esc(strings['visualizations.excerpt_recorded'] if source.get('excerpt_status') == 'recorded' else strings['visualizations.excerpt_none'])}</dt><dd>{excerpt_html}{excerpt_link}</dd>
  </dl>
  <p class="notice">{esc(strings['visualizations.structure_notice'])}</p>
</section>"""


def visualization_body(strings: dict, lang: str, record: dict, research: dict) -> str:
    model = build_structure(record, research)
    errors = validate_structure(model)
    if errors:
        raise ValueError(f'{record["id"]}: ' + '; '.join(errors))
    source = model['source']
    title = _foreign(model['title'], lang, source.get('language', 'en'))
    provisions = [n for n in model['nodes'] if n['type'] == 'provision']
    questions = [n for n in model['nodes'] if n['type'] == 'question']
    related = [n for n in model['nodes'] if n['type'] == 'related']

    text_items = []
    instrument = next(n for n in model['nodes'] if n['type'] == 'instrument')
    text_items.append(
        f"{esc(strings['visualizations.node_instrument'])}: <code lang=\"en\" dir=\"ltr\">{esc(instrument['id'])}</code> — "
        f"{title} — {_source_link(source, lang)}")
    for edge in model['edges']:
        if edge['type'] == 'contains':
            provision = next(n for n in provisions if n['id'] == edge['target'])
            text_items.append(
                f"{esc(strings['visualizations.edge_contains'])}: {esc(provision['id'])} — "
                f"{_foreign(provision['label'], lang, source.get('language', 'en'))}; "
                f"{esc(strings['record.table.locator'])}: {_foreign(provision.get('locator', 'unknown'), lang, source.get('language', 'en'))}. "
                f"{esc(strings['visualizations.locator_note'])}")
        elif edge['type'] == 'raises_question':
            question = next(n for n in questions if n['id'] == edge['target'])
            text_items.append(
                f"{esc(strings['visualizations.edge_question'])}: {esc(question['id'])} — "
                f"{_foreign(question['label'], lang)}; {esc(strings['visualizations.candidate_notice'])}")
        else:
            relation = next(n for n in related if n['id'] == edge['target'])
            text_items.append(
                f"{esc(strings['visualizations.edge_relation'])}: {esc(relation['id'])} — "
                f"{_foreign(relation['label'], lang)}; {esc(relation.get('recorded_label') or '')}; "
                f"{esc(strings['record.relation_review.unreviewed'])}")

    provision_items = []
    for provision in provisions:
        questions_for = [q for q in questions if q.get('provision_id') == provision['id']]
        question_links = ', '.join(
            f'<a href="#question-{esc(q["id"])}"><code lang="en" dir="ltr">{esc(q["id"])}</code></a>'
            for q in questions_for) or esc(strings['record.questions_none'])
        provision_items.append(
            f'<li id="provision-{esc(provision["id"])}"><h3><code lang="en" dir="ltr">{esc(provision["id"])}</code> — '
            f'{_foreign(provision["label"], lang, source.get("language", "en"))}</h3>'
            f'<p>{_foreign(provision.get("summary", ""), lang, source.get("language", "en"))}</p>'
            f'<p class="meta"><a href="{esc(source.get("url", "#"))}">{esc(strings["visualizations.open_source"])}</a> — '
            f'{esc(strings["record.table.locator"])}: {_foreign(provision.get("locator", "unknown"), lang, source.get("language", "en"))}. '
            f'{esc(strings["visualizations.locator_note"])}</p>'
            f'<p>{esc(strings["visualizations.evidence_status"])}: {esc(strings["visualizations.evidence.recorded_provision"])}; '
            f'{esc(strings["record.table.legal_effect"])}: {esc(_label(strings, EFFECT_KEYS, provision.get("effect_assessment"), "unknown"))}; '
            f'{esc(strings["record.table.encoding"])}: {esc(_label(strings, ENCODING_KEYS, provision.get("encoding_status"), "unknown"))}; '
            f'{esc(strings["record.table.review_state"])}: {esc(strings["record.relation_review.unreviewed"])}. '
            f'{esc(strings["record.questions_heading"])}: {question_links}</p></li>')

    question_items = []
    for question in questions:
        alternatives = question.get('alternatives') or []
        alternatives_html = ''
        if alternatives:
            alternatives_html = f'<p><strong>{esc(strings["visualizations.alternatives"])}:</strong></p><ul>' + ''.join(
                f'<li>{_foreign(item, lang)}</li>' for item in alternatives) + '</ul>'
        provision_link = (f'<p><a href="#provision-{esc(question["provision_id"])}">'
                          f'{esc(strings["record.table.provision"])} {esc(question["provision_id"])}</a></p>'
                          if question.get('provision_id') else '')
        observation_html = ''
        if question.get('observation'):
            observation_html = (f'<p><strong>{esc(strings["visualizations.observation"])}:</strong> '
                                f'{_foreign(question.get("observation"), lang)}</p>')
        question_items.append(
            f'<li id="question-{esc(question["id"])}"><h3><code lang="en" dir="ltr">{esc(question["id"])}</code></h3>'
            f'<p>{_foreign(question["statement"], lang)}</p>'
            f'{observation_html}{alternatives_html}{provision_link}'
            f'<p class="meta">{esc(strings["visualizations.evidence_status"])}: {esc(strings["visualizations.evidence.candidate"])}; '
            f'{esc(strings["record.question_risk"])}: {esc(_label(strings, RISK_KEYS, question.get("risk"), "unknown"))}; '
            f'{esc(strings["record.question_status"])}: {esc(_label(strings, QUESTION_STATUS_KEYS, question.get("review_state"), "unresolved"))}; '
            f'{esc(strings["record.question_requires"])}: {esc(_label(strings, REQUIRES_KEYS, question.get("requires"), "unknown"))}.</p></li>')

    relation_items = []
    for relation in related:
        target = ''
        if relation.get('record_id'):
            target = (f'<a href="../records/{esc(relation["record_id"])}.html">'
                      f'{_foreign(relation["label"], lang)}</a>')
        elif relation.get('url'):
            target = f'<a href="{esc(relation["url"])}">{_foreign(relation["label"], lang)}</a>'
        else:
            target = _foreign(relation['label'], lang)
        relation_items.append(
            f'<li><code lang="en" dir="ltr">{esc(relation["id"])}</code> — {target} '
            f'<span class="meta">(<span lang="en" dir="ltr">{esc(relation.get("recorded_label") or "unreviewed")}</span>; '
            f'{esc(strings["visualizations.evidence.recorded_relation"])}; '
            f'{esc(strings["record.relation_review.unreviewed"])})</span></li>')

    return '\n'.join([
        f'<h1>{title}</h1>',
        f'<p class="notice"><strong>{esc(strings["visualizations.prototype_notice"])}</strong></p>',
        f'<p class="notice">{esc(strings["visualizations.structure_notice"])}</p>',
        f'<p class="record-id">{esc(strings["record.record_id"])}: <code>{esc(record["id"])}</code> — '
        f'{esc(strings["home.table.jurisdiction"])}: {esc(record.get("country", ""))}</p>',
        f'<section aria-labelledby="structure-h"><h2 id="structure-h">{esc(strings["visualizations.structure_heading"])}</h2>'
        f'<figure>{_svg(model, strings, lang)}<figcaption>{esc(strings["visualizations.structure_caption"])}</figcaption></figure>'
        f'{_legend(strings)}'
        f'<h3>{esc(strings["visualizations.text_heading"])}</h3><ol>{"".join(f"<li>{item}</li>" for item in text_items)}</ol></section>',
        f'<section aria-labelledby="provisions-h"><h2 id="provisions-h">{esc(strings["visualizations.provisions_heading"])}</h2>'
        f'<p class="notice">{esc(strings["visualizations.provision_notice"])}</p>'
        f'<ul class="structure-list">{"".join(provision_items)}</ul></section>' if provision_items
        else f'<section><h2>{esc(strings["visualizations.provisions_heading"])}</h2><p>{esc(strings["visualizations.no_provisions"])}</p></section>',
        f'<section aria-labelledby="questions-h"><h2 id="questions-h">{esc(strings["visualizations.questions_heading"])}</h2>'
        f'<p class="notice"><strong>{esc(strings["visualizations.candidate_notice"])}</strong></p>'
        f'<ul class="questions">{"".join(question_items)}</ul></section>' if question_items
        else f'<section><h2>{esc(strings["visualizations.questions_heading"])}</h2><p>{esc(strings["record.questions_none"])}</p></section>',
        f'<section aria-labelledby="relations-h"><h2 id="relations-h">{esc(strings["visualizations.relations_heading"])}</h2>'
        f'<ul>{"".join(relation_items)}</ul></section>' if relation_items
        else f'<section><h2>{esc(strings["visualizations.relations_heading"])}</h2><p>{esc(strings["visualizations.related_none"])}</p></section>',
        _evidence(source, strings, lang, record["id"], record.get("legal_effect")),
        f'<section aria-labelledby="reviewed-h"><h2 id="reviewed-h">{esc(strings["visualizations.reviewed_heading"])}</h2>'
        f'<p class="notice">{esc(strings["visualizations.reviewed_notice"])}</p>'
        f'<p>{esc(strings["visualizations.reviewed_none"])}</p></section>',
        f'<p><a href="index.html">{esc(strings["visualizations.back"])}</a></p>',
    ])


def _card(strings: dict, lang: str, record: dict, research: dict) -> str:
    source = (research.get('sources') or [{}])[0]
    title = _foreign(record.get('title', record['id']), lang, source.get('language', 'en'))
    evidence = (strings['visualizations.excerpt_recorded'] if source.get('excerpt_status') == 'recorded'
                else strings['visualizations.excerpt_none'])
    return f"""
<article class="vis-card">
  <h3><a href="{esc(record['id'])}.html">{title}</a></h3>
  <dl>
    <dt>{esc(strings['home.table.jurisdiction'])}</dt><dd>{esc(record.get('country', ''))}</dd>
    <dt>{esc(strings['record.type'])}</dt><dd>{esc(_label(strings, INSTRUMENT_KEYS, record.get('instrument_type'), 'unknown'))}</dd>
    <dt>{esc(strings['domains.table.domain'])}</dt><dd>{esc(_domain_label(record.get('topic', ''), lang))}</dd>
    <dt>{esc(strings['visualizations.source_language'])}</dt><dd><code lang="en" dir="ltr">{esc(source.get('language', 'unknown'))}</code></dd>
    <dt>{esc(strings['visualizations.interface_languages'])}</dt><dd>{' · '.join(esc(LANGUAGE_NAMES[lang][code]) for code in LANGUAGES)}</dd>
    <dt>{esc(strings['visualizations.type'])}</dt><dd>{esc(strings['visualizations.type_source'])}</dd>
    <dt>{esc(strings['visualizations.status'])}</dt><dd>{esc(strings['visualizations.status_research'])}</dd>
    <dt>{esc(strings['visualizations.last_review'])}</dt><dd>{esc(strings['visualizations.last_review_none'])}</dd>
    <dt>{esc(strings['visualizations.evidence'])}</dt><dd>{esc(evidence)}</dd>
  </dl>
  <p><a href="{esc(record['id'])}.html">{esc(strings['visualizations.open'])}</a></p>
</article>"""


def index_body(strings: dict, lang: str, selected: list[tuple[dict, dict]]) -> str:
    cards = ''.join(_card(strings, lang, record, research) for record, research in selected)
    return '\n'.join([
        f'<h1>{esc(strings["visualizations.h1"])}</h1>',
        f'<p class="notice"><strong>{esc(strings["visualizations.prototype_notice"])}</strong></p>',
        f'<p class="lede">{esc(strings["visualizations.lede"])}</p>',
        f'<p>{esc(strings["visualizations.intro"])}</p>',
        f'<section aria-labelledby="catalogue-h"><h2 id="catalogue-h">{esc(strings["visualizations.catalogue_heading"])}</h2>'
        f'<p>{esc(strings["visualizations.catalogue_note"])}</p>'
        f'<div class="vis-grid">{cards}</div></section>',
        f'<section aria-labelledby="synthetic-h"><h2 id="synthetic-h">{esc(strings["visualizations.synthetic_heading"])}</h2>'
        f'<div class="vis-card synthetic-card"><p class="notice">{esc(strings["visualizations.synthetic_notice"])}</p>'
        f'<h3><a href="synthetic.html">{esc(strings["visualizations.synthetic_page_title"])}</a></h3>'
        f'<p>{esc(strings["visualizations.synthetic_demo_notice"])}</p>'
        f'<p><a href="synthetic.html">{esc(strings["visualizations.synthetic_link"])}</a></p></div></section>',
        f'<section aria-labelledby="reviewed-state-h"><h2 id="reviewed-state-h">{esc(strings["visualizations.reviewed_heading"])}</h2>'
        f'<p class="notice">{esc(strings["visualizations.reviewed_none"])}</p>'
        f'<p>{esc(strings["visualizations.reviewed_gate"])}</p></section>',
    ])


def synthetic_page_body(strings: dict, lang: str, fixture: dict, catalogues: dict) -> str:
    fragment = render_fragment(fixture, lang, catalogues[lang])
    excerpts = code_excerpts()
    output_source = next(
        (item for item in fixture.get('sources', []) if item.get('id') == 'SP-3'),
        {'label': {}, 'url': 'https://example.org/synthetic-procurement-policy#s3'},
    )
    output_label = output_source.get('label', {})
    output_label = output_label.get(lang) or output_label.get('en') or 'SP-3'
    output_url = output_source.get('url', 'https://example.org/synthetic-procurement-policy#s3')
    axiom_url = ('https://github.com/mgifford/mena-policy-observatory/blob/main/'
                 'research/rules-visualization/axiom/procurement.rulespec.yaml')
    l4_url = ('https://github.com/mgifford/mena-policy-observatory/blob/main/'
              'research/rules-visualization/l4/procurement.l4')

    def code_card(heading_key, note_key, code, url, source_key):
        return (
            f'<article class="code-card"><h3>{esc(strings[heading_key])}</h3>'
            f'<p>{esc(strings[note_key])}</p>'
            f'<div class="code-scroll" role="region" aria-label="{esc(strings[heading_key])}" tabindex="0">'
            f'<pre><code lang="en" dir="ltr">{esc(code)}</code></pre></div>'
            f'<p><a href="{url}">{esc(strings[source_key])}</a></p></article>'
        )

    return '\n'.join([
        f'<h1>{esc(strings["visualizations.synthetic_page_title"])}</h1>',
        f'<p class="notice"><strong>{esc(strings["visualizations.prototype_notice"])}</strong></p>',
        f'<p class="notice"><strong>{esc(strings["visualizations.synthetic_notice"])}</strong></p>',
        f'<p>{esc(fixture["summary"][lang])}</p>',
        f'<p>{esc(strings["visualizations.synthetic_demo_notice"])}</p>',
        f'<nav class="workbench-nav" aria-label="{esc(strings["visualizations.workbench_label"])}"><ul>'
        f'<li><a href="#rules-machine-h">{esc(strings["visualizations.workbench_machine"])}</a></li>'
        f'<li><a href="#rule-graph-h">{esc(strings["visualizations.workbench_graph"])}</a></li>'
        f'<li><a href="#rule-ladder-h">{esc(strings["visualizations.workbench_ladder"])}</a></li>'
        f'<li><a href="#synthetic-results-h">{esc(strings["visualizations.workbench_run"])}</a></li>'
        f'</ul></nav>',
        f'<section aria-labelledby="rules-machine-h"><h2 id="rules-machine-h">{esc(strings["visualizations.rules_machine_heading"])}</h2>'
        f'<p>{esc(strings["visualizations.code_excerpt_note"])}</p><div class="code-grid">'
        + code_card('visualizations.axiom_code_heading', 'visualizations.axiom_code_note',
                    excerpts['axiom'], axiom_url, 'visualizations.synthetic_source_axiom')
        + code_card('visualizations.l4_code_heading', 'visualizations.l4_code_note',
                    excerpts['l4'], l4_url, 'visualizations.synthetic_source_l4')
        + '</div></section>',
        f'<section class="rule-inspector" aria-labelledby="rule-inspector-h">'
        f'<h2 id="rule-inspector-h">{esc(strings["visualizations.rule_inspector_heading"])}</h2>'
        f'<div class="inspector-grid"><div><h3>{esc(strings["visualizations.rule_inspector_heading"])} — <code lang="en" dir="ltr">N9</code></h3>'
        f'<p><strong>{esc(strings["visualizations.built_from"])}:</strong> '
        f'{(" " + "·" + " ").join("<code lang=\"en\" dir=\"ltr\">" + esc(item) + "</code>" for item in ["N1","N2","N3","N4","N5","N6","N7","N8"])}</p>'
        f'<dl><dt>{esc(strings["visualizations.used_by"])}</dt><dd>{esc(strings["visualizations.final_result"])}</dd>'
        f'<dt>{esc(strings["visualizations.entity"])}</dt><dd><code lang="en" dir="ltr">Procurement</code></dd>'
        f'<dt>{esc(strings["visualizations.value_type"])}</dt><dd><code lang="en" dir="ltr">Text</code></dd>'
        f'<dt>{esc(strings["visualizations.verification_status"])}</dt><dd>{esc(strings["visualizations.synthetic_not_reviewed"])}</dd>'
        f'<dt>{esc(strings["visualizations.source"])}</dt><dd><a href="{esc(output_url)}">SP-3 — {esc(output_label)}</a></dd>'
        f'<dt>{esc(strings["visualizations.effective_period"])}</dt><dd><span lang="en" dir="ltr">2026-01-01 – —</span></dd></dl>'
        f'<p><a href="#synthetic-results-h">{esc(strings["visualizations.jump_run"])}</a></p></div>'
        f'<div><h3>{esc(strings["visualizations.synthetic_results_heading"])}</h3>'
        f'<p>{esc(strings["visualizations.smoke_summary"])}</p><p><a href="#synthetic-results-h">{esc(strings["visualizations.jump_run"])}</a></p></div></div></section>',
        f'<section id="legalese-visualization" aria-labelledby="legalese-visual-h">'
        f'<h2 id="legalese-visual-h">{esc(strings["visualizations.legalese_visual_heading"])}</h2>'
        f'<p>{esc(strings["visualizations.legalese_visual_note"])}</p>',
        fragment,
        '</section>',
        f'<section aria-labelledby="synthetic-evidence-h"><h2 id="synthetic-evidence-h">{esc(strings["visualizations.synthetic_evidence_heading"])}</h2>'
        f'<ul>'
        f'<li><a href="{axiom_url}">{esc(strings["visualizations.synthetic_source_axiom"])}</a></li>'
        f'<li><a href="{l4_url}">{esc(strings["visualizations.synthetic_source_l4"])}</a></li>'
        f'<li><a href="https://github.com/mgifford/mena-policy-observatory/blob/main/research/rules-visualization/results/axiom-cases.json">{esc(strings["visualizations.synthetic_tests"])}</a></li>'
        f'<li><a href="https://github.com/mgifford/mena-policy-observatory/blob/main/docs/RULES-ENGINE-COMPARISON.md">{esc(strings["visualizations.synthetic_comparison"])}</a></li>'
        f'</ul></section>',
        f'<section aria-labelledby="synthetic-results-h"><h2 id="synthetic-results-h">{esc(strings["visualizations.synthetic_results_heading"])}</h2>'
        f'<p>{esc(strings["visualizations.synthetic_results_note"])}</p>'
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["visualizations.smoke_caption"])}" tabindex="0">'
        f'<table><caption>{esc(strings["visualizations.smoke_caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["visualizations.synthetic_case"])}</th>'
        f'<th scope="col">{esc(strings["visualizations.synthetic_axiom"])}</th>'
        f'<th scope="col">{esc(strings["visualizations.synthetic_l4"])}</th>'
        f'</tr></thead><tbody>'
        + ''.join(_case_row(case) for case in SYNTHETIC_CASES)
        + '</tbody></table></div></section>',
        f'<section aria-labelledby="synthetic-semantics-h"><h2 id="synthetic-semantics-h">{esc(strings["visualizations.synthetic_semantics"])}</h2>'
        f'<p>{esc(strings["visualizations.synthetic_semantics_text"])}</p></section>',
        f'<p><a href="index.html">{esc(strings["visualizations.back"])}</a></p>',
    ])


SYNTHETIC_CASES = (
    ('All conditions met', 'determination = open_source_consideration_required; judgments = holds', 'OpenSourceConsiderationRequired'),
    ('Scope condition not met', 'determination = outside_scope; judgments = not_holds', 'OutsideScope'),
    ('Exception applies', 'determination = exception_applies; judgments = not_holds', 'ExceptionApplies'),
    ('Missing required input', 'error: missing input covered_body', 'Indeterminate'),
    ('Boundary USD 100,000', 'determination = open_source_consideration_required; judgments = holds', 'OpenSourceConsiderationRequired'),
    ('Facts incomplete', 'determination = indeterminate; judgments = not_holds', 'Indeterminate'),
    ('Contradictory scope and exception', 'determination = outside_scope; judgments = not_holds', 'OutsideScope'),
)


def _case_row(case: tuple[str, str, str]) -> str:
    label, axiom, l4 = case
    return (f'<tr><th scope="row" lang="en" dir="ltr">{esc(label)}</th>'
            f'<td><code lang="en" dir="ltr">{esc(axiom)}</code></td>'
            f'<td><code lang="en" dir="ltr">{esc(l4)}</code></td></tr>')
