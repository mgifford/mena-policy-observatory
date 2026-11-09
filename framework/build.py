#!/usr/bin/env python3
"""Generate portable static HTML per region and locale (no runtime JS).

The generator only arranges recorded research. It does not verify legal effect,
translations, or rule behaviour, and it never marks a rule as reviewed.
"""
from pathlib import Path
import argparse
import html
import json
import shutil

try:  # imported as framework.build
    from .coverage import build_view, load_coverage
    from .research import RESEARCH_FILENAME, load_research
    from .research_visualization import (
        SELECTED_RECORDS,
        SYNTHETIC_FIXTURE,
        index_body as visualizations_index_body,
        selected_records,
        synthetic_page_body,
        visualization_body,
    )
    from .rules_examples import code_excerpts, ladder_excerpt
except ImportError:  # run as a script
    from coverage import build_view, load_coverage
    from research import RESEARCH_FILENAME, load_research
    from research_visualization import (
        SELECTED_RECORDS,
        SYNTHETIC_FIXTURE,
        index_body as visualizations_index_body,
        selected_records,
        synthetic_page_body,
        visualization_body,
    )
    from rules_examples import code_excerpts, ladder_excerpt

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_URL = 'https://github.com/mgifford/mena-policy-observatory'
WORKFLOW_URL = REPOSITORY_URL + '/blob/main/docs/WORKFLOW.md'
AUDIT_URL = REPOSITORY_URL + '/blob/main/docs/BASELINE-AUDIT.md'
RESEARCH_MODEL_URL = REPOSITORY_URL + '/blob/main/docs/RESEARCH-MODEL.md'
ACCESSIBILITY_URL = REPOSITORY_URL + '/blob/main/ACCESSIBILITY.md'
CONTRIBUTING_URL = REPOSITORY_URL + '/blob/main/CONTRIBUTING.md'
RULES_DOC_URL = REPOSITORY_URL + '/blob/main/docs/RULES-ENGINE-COMPARISON.md'
FEATURED_VISUALIZATION_ID = 'ae-national-digital-accessibility'
ESCWA_URL = ('https://www.unescwa.org/sites/default/files/pubs/pdf/'
             'technical-guidelines-digital-accessibility-empower-older-persons-english.pdf')

LEGAL_STATUS_KEYS = {
    'not_legally_assessed': 'record.legal.not_assessed',
    'current_status_requires_confirmation': 'record.legal.requires_confirmation',
    'draft_not_confirmed_in_force': 'record.legal.draft',
    'binding_confirmed': 'record.legal.binding',
    'nonbinding_confirmed': 'record.legal.nonbinding',
}
RULE_STATUS_KEYS = {
    'not_implemented': 'record.rule.not_implemented',
    'scaffold': 'record.rule.scaffold',
    'not_encoded': 'record.rule.not_encoded',
    'candidate': 'record.rule.candidate',
    'tested': 'record.rule.tested',
    'reviewed': 'record.rule.reviewed',
}
INSTRUMENT_KEYS = {
    'national_policy': 'instrument.national_policy',
    'government_guideline': 'instrument.government_guideline',
    'draft_policy': 'instrument.draft_policy',
    'agency_policy': 'instrument.agency_policy',
    'legislation': 'instrument.legislation',
    'regulation': 'instrument.regulation',
    'technical_standard': 'instrument.technical_standard',
    'other': 'instrument.other',
}
ARTIFACT_KEYS = {
    'PROVISIONS.md': 'artifact.provisions',
    'SOURCE.md': 'artifact.source',
    'INTERPRETATION.md': 'artifact.interpretation',
    'RELATED.md': 'artifact.related',
    'rule.rulespec.yaml': 'artifact.rulespec',
    'manifest.json': 'artifact.manifest',
    'research.json': 'artifact.research',
}
EFFECT_KEYS = {
    'not_assessed': 'record.effect.not_assessed',
    'draft_not_in_force': 'record.effect.draft_not_in_force',
    'in_force_confirmed': 'record.effect.in_force_confirmed',
    'not_in_force_confirmed': 'record.effect.not_in_force_confirmed',
    'indeterminate': 'record.effect.indeterminate',
}
ENCODING_KEYS = {
    'blocked': 'record.encoding.blocked',
    'candidate': 'record.encoding.candidate',
    'tested': 'record.encoding.tested',
    'reviewed': 'record.encoding.reviewed',
}
RISK_KEYS = {
    'critical': 'record.risk.critical',
    'high': 'record.risk.high',
    'medium': 'record.risk.medium',
    'low': 'record.risk.low',
    'unknown': 'record.risk.unknown',
}
QUESTION_STATUS_KEYS = {
    'unresolved': 'record.status.unresolved',
    'resolved': 'record.status.resolved',
}
REQUIRES_KEYS = {
    'qualified_legal_review': 'record.requires.qualified_legal_review',
    'qualified_accessibility_review': 'record.requires.qualified_accessibility_review',
    'source_capture': 'record.requires.source_capture',
    'authority_confirmation': 'record.requires.authority_confirmation',
    'translation_review': 'record.requires.translation_review',
}
RELATION_KEYS = {
    'cites': 'record.relation.cites',
    'amends': 'record.relation.amends',
    'supersedes': 'record.relation.supersedes',
    'transposes': 'record.relation.transposes',
    'implements': 'record.relation.implements',
    'incorporates': 'record.relation.incorporates',
    'guidance_for': 'record.relation.guidance_for',
}
RELATION_REVIEW_KEYS = {
    'unreviewed': 'record.relation_review.unreviewed',
    'reviewed': 'record.relation_review.reviewed',
}
AUTHORITATIVE_KEYS = {
    'yes': 'record.source.authoritative.yes',
    'no': 'record.source.authoritative.no',
    'unknown': 'record.source.authoritative.unknown',
}
TRANSLATION_KEYS = {
    'not_translated': 'record.translation.not_translated',
    'draft': 'record.translation.draft',
    'complete': 'record.translation.complete',
}
EXPRESSION_KIND_KEYS = {
    'original_authoritative': 'expression.kind.original_authoritative',
    'additional_authoritative': 'expression.kind.additional_authoritative',
    'official_translation': 'expression.kind.official_translation',
    'research_translation': 'expression.kind.research_translation',
    'machine_assisted_draft': 'expression.kind.machine_assisted_draft',
    'translation_pending': 'expression.kind.translation_pending',
    'translation_unavailable': 'expression.kind.translation_unavailable',
    'authority_unresolved': 'expression.kind.authority_unresolved',
}
EXPRESSION_REVIEW_KEYS = {
    'unreviewed': 'expression.review.unreviewed',
    'in_review': 'expression.review.in_review',
    'reviewed': 'expression.review.reviewed',
    'native_reviewed': 'expression.review.native_reviewed',
    'disputed': 'expression.review.disputed',
}
EXPRESSION_METHOD_KEYS = {
    'human': 'expression.method.human',
    'machine_assisted': 'expression.method.machine_assisted',
    'unknown': 'expression.method.unknown',
}
TRANSLATION_REVIEW_KEYS = {
    'not_reviewed': 'record.translation.not_reviewed',
    'native_reviewed': 'record.translation.native_reviewed',
}
RESEARCH_STATUS_KEYS = {
    status: f'coverage.status.{status}'
    for status in (
        'not_started', 'source_discovery', 'candidate_sources_identified',
        'evidence_captured', 'provision_extraction', 'legal_review_pending',
        'reviewed_findings', 'blocked',
    )
}
TASK_STATUS_KEYS = {
    'unstarted': 'task.status.unstarted',
    'in_progress': 'task.status.in_progress',
    'blocked': 'task.status.blocked',
    'complete': 'task.status.complete',
    'cancelled': 'task.status.cancelled',
}
TASK_STAGE_KEYS = {
    'source_discovery': 'task.stage.source_discovery',
    'capture': 'task.stage.capture',
    'transcription': 'task.stage.transcription',
    'provision_extraction': 'task.stage.provision_extraction',
    'interpretation': 'task.stage.interpretation',
    'challenge': 'task.stage.challenge',
    'review': 'task.stage.review',
    'publication': 'task.stage.publication',
    'formalization': 'task.stage.formalization',
}
PRIORITY_KEYS = {
    'baseline': 'task.priority.baseline',
    'pilot': 'task.priority.pilot',
    'high': 'task.priority.high',
    'medium': 'task.priority.medium',
    'low': 'task.priority.low',
}
CAPTURE_KEYS = {
    'not_captured': 'source.capture.not_captured',
    'captured': 'source.capture.captured',
    'verified': 'source.capture.verified',
}
SOURCE_TYPE_KEYS = {
    source_type: f'source.type.{source_type}'
    for source_type in (
        'official_instrument', 'official_index', 'official_summary',
        'official_ministry_policy_listing', 'official_ministry_policy_index',
        'official_ministry_explainer', 'official_legislative_publication',
        'official_regulator_legal_index', 'official_legislation_index',
        'official_government_explainer_not_statute',
        'official_ministry_explainer_not_statute',
        'official_agency_accessibility_statement', 'secondary', 'unknown',
    )
}


def esc(value):
    return html.escape(str(value), quote=True)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_i18n(base, languages=('en', 'fr', 'ar')):
    """Load locale catalogues and fail loudly on asymmetric keys."""
    catalogues = {}
    for lang in languages:
        catalogues[lang] = load(base / 'i18n' / f'{lang}.json')
    reference = set(catalogues[languages[0]])
    for lang in languages[1:]:
        missing = sorted(reference - set(catalogues[lang]))
        extra = sorted(set(catalogues[lang]) - reference)
        if missing or extra:
            raise SystemExit(
                f'i18n catalogue {lang} does not match {languages[0]}: '
                f'missing={missing} unexpected={extra}'
            )
    return catalogues


def t(strings, key, **values):
    try:
        template = strings[key]
    except KeyError as exc:
        raise KeyError(f'missing translation key: {key}') from exc
    return template.format(**values)


def label(strings, mapping, token, fallback_key='record.not_assessed'):
    key = mapping.get(token)
    return strings[key] if key else strings[fallback_key]


def foreign(value, page_lang, value_lang='en'):
    """Mark a value written in another language, including its direction."""
    text = esc(value)
    if page_lang == value_lang:
        return text
    return f'<span lang="{value_lang}" dir="{direction(value_lang)}">{text}</span>'


LANGUAGES = ('en', 'fr', 'ar')
LANGUAGE_NAMES = {'en': 'English', 'fr': 'Français', 'ar': 'العربية'}
CONTINUE_KEYS = {'en': 'root.continue_english', 'fr': 'root.continue_french', 'ar': 'root.continue_arabic'}


def other_languages(lang):
    return [code for code in LANGUAGES if code != lang]


def direction(lang):
    return 'rtl' if lang == 'ar' else 'ltr'


def status_text(strings, status):
    return strings[RESEARCH_STATUS_KEYS.get(status, RESEARCH_STATUS_KEYS['not_started'])]


def task_status_text(strings, status):
    return strings[TASK_STATUS_KEYS.get(status, 'task.status.unstarted')]


def task_stage_text(strings, stage):
    return strings[TASK_STAGE_KEYS.get(stage, 'task.stage.source_discovery')]


def priority_text(strings, priority):
    key = PRIORITY_KEYS.get(priority)
    return strings[key] if key else strings['task.priority.unknown']


def capture_text(strings, status):
    return strings[CAPTURE_KEYS.get(status, 'source.capture.not_captured')]


def source_type_text(strings, source_type):
    key = SOURCE_TYPE_KEYS.get(source_type)
    return strings[key] if key else strings['source.type.unknown']


LEGAL_REVIEW_KEYS = {
    'not_assessed': 'source.legal_review.not_assessed',
}
RELATION_KEYS = {
    'amends': 'source.relationship.amends',
    'related': 'source.relationship.related',
    'implements': 'source.relationship.implements',
    'consolidates': 'source.relationship.consolidates',
}
VERIFICATION_KEYS = {
    requirement: f'source.verification.{requirement}'
    for requirement in (
        'official_source', 'legal_scope', 'language', 'publication_permissions',
    )
}


INSTRUMENT_TYPE_KEYS = {
    instrument_type: f'source.instrument_type.{instrument_type}'
    for instrument_type in (
        'law', 'act', 'decree_law', 'decision', 'regulation', 'ordinance', 'unknown',
    )
}
PUBLISHER_STATUS_KEYS = {
    'unverified': 'source.registry.unverified',
    'reviewed': 'source.registry.reviewed',
    'disputed': 'source.registry.disputed',
}
RETRIEVAL_KEYS = {
    status: f'source.retrieval.{status}'
    for status in ('not_attempted', 'success', 'failed', 'blocked', 'unknown')
}
FRESHNESS_KEYS = {
    state: f'source.freshness.{state}'
    for state in ('not_established', 'within_interval', 'interval_exceeded', 'unknown')
}
LEGAL_VERIFICATION_KEYS = {
    status: f'source.legal_verification.{status}'
    for status in ('unreviewed', 'in_review', 'verified', 'disputed', 'superseded')
}
CHANGE_TECHNICAL_KEYS = {
    value: f'change.technical.{value}'
    for value in ('new_content', 'bytes_changed', 'text_changed', 'metadata_changed',
                  'url_changed', 'format_changed', 'no_observed_change', 'indeterminate')
}
CHANGE_POTENTIAL_KEYS = {
    value: f'change.potential.{value}'
    for value in ('possible_new_instrument', 'possible_amendment', 'possible_repeal',
                  'possible_correction', 'possible_consolidation',
                  'possible_translation_update', 'possible_effective_date_change',
                  'relationship_unresolved', 'none')
}
CHANGE_REVIEW_KEYS = {
    value: f'change.review.{value}'
    for value in ('not_required', 'awaiting_review', 'reviewed_no_change',
                  'reviewed_substantive', 'reviewed_technical', 'further_evidence',
                  'interpretation_pending', 'translation_review', 'indeterminate')
}
CHANGE_LEGAL_KEYS = {
    value: f'change.legal.{value}'
    for value in ('confirmed_amendment', 'confirmed_repeal', 'confirmed_correction',
                  'confirmed_consolidation', 'confirmed_translation_update',
                  'no_substantive_change', 'indeterminate')
}
RETRIEVAL_ERROR_KEYS = {
    category: f'source.retrieval.error.{category}'
    for category in ('timeout', 'dns', 'tls', 'http_error', 'blocked',
                     'unsupported_content', 'other')
}


def instrument_type_text(strings, value):
    key = INSTRUMENT_TYPE_KEYS.get(value)
    return strings[key] if key else strings['source.instrument_type.unknown']


def publisher_status_text(strings, value):
    key = PUBLISHER_STATUS_KEYS.get(value)
    return strings[key] if key else strings['source.registry.unverified']


def retrieval_text(strings, value):
    key = RETRIEVAL_KEYS.get(value)
    return strings[key] if key else strings['source.retrieval.unknown']


def freshness_text(strings, value):
    key = FRESHNESS_KEYS.get(value)
    return strings[key] if key else strings['source.freshness.unknown']


def legal_verification_text(strings, value):
    key = LEGAL_VERIFICATION_KEYS.get(value)
    return strings[key] if key else strings['source.legal_verification.unreviewed']


def retrieval_error_text(strings, value):
    key = RETRIEVAL_ERROR_KEYS.get(value)
    return strings[key] if key else strings['source.retrieval.error.other']


def legal_review_text(strings, value):
    key = LEGAL_REVIEW_KEYS.get(value)
    return strings[key] if key else strings['source.legal_review.not_assessed']


def relation_text(strings, value):
    key = RELATION_KEYS.get(value)
    return strings[key] if key else strings['source.relationship.related']


def country_text(country, lang):
    if lang != 'en' and country.get(f'name_{lang}'):
        return country[f'name_{lang}']
    return country.get('name', '')


def domain_text(domain, lang):
    if lang != 'en' and domain.get(f'label_{lang}'):
        return domain[f'label_{lang}']
    return domain.get('label_en', '')


def country_name(country, lang):
    """Prefer the registry's localized name; mark English on other locales."""
    if lang != 'en' and country.get(f'name_{lang}'):
        return esc(country[f'name_{lang}'])
    return foreign(country.get('name', ''), lang)


def domain_name(domain, lang):
    if lang != 'en' and domain.get(f'label_{lang}'):
        return esc(domain[f'label_{lang}'])
    return foreign(domain.get('label_en', ''), lang)


def localized_label(item, lang):
    """Render a localized label from a group or subtopic entry."""
    if lang != 'en' and item.get(f'label_{lang}'):
        return esc(item[f'label_{lang}'])
    return foreign(item.get('label_en', ''), lang)


def country_group(country, lang):
    """Prefer the registry's provisional localized group label."""
    if lang != 'en' and country.get(f'group_{lang}'):
        return esc(country[f'group_{lang}'])
    return foreign(country.get('group', ''), lang)


def country_note(country, key, lang):
    """Render an editorial note, preferring its provisional localization."""
    english = country.get(key, '')
    if not english:
        return ''
    if lang != 'en' and country.get(f'{key}_{lang}'):
        return esc(country[f'{key}_{lang}'])
    return foreign(english, lang)


def code(value):
    return f'<code lang="en" dir="ltr">{esc(value)}</code>'


def breadcrumb_trail(items):
    parts = []
    for index, (href, label_html, current) in enumerate(items):
        if current:
            content = f'<span aria-current="page">{label_html}</span>'
        else:
            content = f'<a href="{esc(href)}">{label_html}</a>'
        separator = ('<span class="breadcrumb-separator" aria-hidden="true">/</span>'
                     if index else '')
        parts.append(f'<li>{separator}{content}</li>')
    return '<ol>' + ''.join(parts) + '</ol>'


def page(catalogues, lang, title, body, depth, alt_hrefs, description,
         breadcrumb_html=''):
    strings = catalogues[lang]
    prefix = '../' * depth
    local = '../' * (depth - 1)
    home_href = local + 'index.html'
    root_href = prefix + '../index.html'
    alternates = ''.join(
        f'<link rel="alternate" hreflang="{code}" href="{esc(href)}">\n'
        for code, href in alt_hrefs.items()
    )
    language_links = ''.join(
        f'<li><a href="{esc(href)}" hreflang="{code}" lang="{code}" '
        f'dir="{direction(code)}">{esc(LANGUAGE_NAMES[code])}</a></li>'
        for code, href in alt_hrefs.items()
    )
    breadcrumb = ''
    if breadcrumb_html:
        breadcrumb = (f'<nav class="breadcrumb" aria-label="{esc(strings["breadcrumb.label"])}">'
                      f'{breadcrumb_html}</nav>')
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
{alternates}<link rel="alternate" hreflang="x-default" href="{esc(root_href)}">
<link rel="stylesheet" href="{prefix}assets/site.css">
</head>
<body>
<a class="skip" href="#main">{esc(strings['skip'])}</a>
<header class="site-header">
<p class="brand"><a href="{home_href}">{esc(strings['site.title'])}</a></p>
<nav class="site-nav" aria-label="{esc(strings['nav.label'])}">
<ul>
<li><a href="{home_href}">{esc(strings['nav.home'])}</a></li>
<li><a href="{home_href}#method">{esc(strings['nav.method'])}</a></li>
<li><a href="{home_href}#rules-as-code">{esc(strings['nav.rules'])}</a></li>
<li><a href="{home_href}#records">{esc(strings['nav.records'])}</a></li>
<li><a href="{local}coverage/index.html">{esc(strings['nav.coverage'])}</a></li>
<li><a href="{local}countries/index.html">{esc(strings['nav.countries'])}</a></li>
<li><a href="{local}domains/index.html">{esc(strings['nav.domains'])}</a></li>
<li><a href="{local}tasks/index.html">{esc(strings['nav.tasks'])}</a></li>
<li><a href="{local}sources/index.html">{esc(strings['nav.sources'])}</a></li>
<li><a href="{local}visualizations/index.html">{esc(strings['nav.visualizations'])}</a></li>
<li><a href="{REPOSITORY_URL}">{esc(strings['nav.repository'])}</a></li>
</ul>
</nav>
<nav class="language" aria-label="{esc(strings['nav.language'])}">
<ul>{language_links}</ul>
</nav>
</header>
<main id="main" tabindex="-1">
{breadcrumb}
{body}
</main>
<footer>
<p>{esc(strings['footer.note'])}</p>
<p><a href="{REPOSITORY_URL}">{esc(strings['footer.repo'])}</a></p>
</footer>
</body>
</html>
"""


def breadcrumb_html(strings, home_href, current_label, current_is_foreign):
    label_html = (f'<span lang="en" dir="ltr">{esc(current_label)}</span>'
                  if current_is_foreign else esc(current_label))
    return (f'<ol><li><a href="{home_href}">{esc(strings["nav.home"])}</a> '
            f'<span aria-hidden="true">/</span></li>'
            f'<li><span aria-current="page">{label_html}</span></li></ol>')


def home_stats(policies, view):
    """Derive the homepage summary from the canonical coverage view."""
    countries = view.get('countries') or []
    domains = view.get('domains') or []
    covered_countries = [country for country in countries if country.get('records')]
    record_domains = [domain for domain in domains if domain.get('records')]
    candidates = view.get('candidates') or []
    successful_retrievals = sum(
        1 for candidate in candidates
        if candidate.get('retrieval_status') == 'success'
    )
    reviewed = sum(
        1 for policy in policies
        if policy.get('legal_effect') in ('binding_confirmed', 'nonbinding_confirmed')
    )
    remaining = len(countries) - len(covered_countries)
    discovery = [
        country for country in countries
        if not country.get('records') and (country.get('candidates') or country.get('tasks'))
    ]
    no_research = [
        country for country in countries
        if not country.get('records') and not country.get('candidates') and not country.get('tasks')
    ]
    return {
        'records': len(policies),
        'covered': len(covered_countries),
        'total': len(countries),
        'domains': len(record_domains),
        'candidates': len(candidates),
        'retrievals': successful_retrievals,
        'reviewed': reviewed,
        'remaining': remaining,
        'discovery': len(discovery),
        'no_research': len(no_research),
        'covered_countries': covered_countries,
        'record_domains': record_domains,
    }


def _home_country_list(countries, lang):
    return ''.join(
        f'<li><a href="countries/{esc(country.get("code"))}.html">'
        f'{country_name(country, lang)}</a></li>'
        for country in countries
    )


def _home_domain_list(domains, lang):
    return ''.join(
        f'<li><a href="domains/{esc(domain.get("id"))}.html">'
        f'{domain_name(domain, lang)}</a></li>'
        for domain in domains
    )


def home_body(catalogues, lang, cfg, policies, view, stats=None):
    """Render the homepage as a task-oriented research discovery page."""
    strings = catalogues[lang]
    stats = stats or home_stats(policies, view)
    countries_with_records = stats['covered_countries']
    domains_with_records = stats['record_domains']
    featured = next(
        (policy for policy in policies if policy.get('id') == FEATURED_VISUALIZATION_ID),
        None,
    )

    paths = (
        ('countries/index.html', 'home.paths.find.title', 'home.paths.find.body'),
        ('comparison/index.html', 'home.paths.compare.title', 'home.paths.compare.body'),
        ('visualizations/index.html', 'home.paths.visualize.title', 'home.paths.visualize.body'),
        ('sources/index.html', 'home.paths.evidence.title', 'home.paths.evidence.body'),
    )
    path_items = ''.join(
        f'<li><a href="{esc(href)}"><strong>{esc(strings[title])}</strong>'
        f'<span>{esc(strings[body])}</span></a></li>'
        for href, title, body in paths
    )

    stat_rows = (
        ('home.snapshot.total', 'total'),
        ('home.snapshot.jurisdictions', 'covered'),
        ('home.snapshot.records', 'records'),
        ('home.snapshot.domains', 'domains'),
        ('home.snapshot.candidates', 'candidates'),
        ('home.snapshot.retrievals', 'retrievals'),
        ('home.snapshot.reviewed', 'reviewed'),
    )
    stat_items = ''.join(
        f'<div class="stat"><dt>{esc(strings[label_key])}</dt>'
        f'<dd>{stats[value_key]}</dd></div>'
        for label_key, value_key in stat_rows
    )

    excerpts = code_excerpts()
    ladder = ladder_excerpt()

    def fixture_text(value):
        if isinstance(value, dict):
            text = value.get(lang) or value.get('en', '')
            return foreign(text, lang, lang if lang in value else 'en')
        return esc(value)

    def code_card(label_key, note_key, code, source_url, source_label):
        return (
            f'<article class="code-card"><h3>{esc(strings[label_key])}</h3>'
            f'<p>{esc(strings[note_key])}</p>'
            f'<div class="code-scroll" role="region" aria-label="{esc(strings[label_key])}" tabindex="0">'
            f'<pre><code lang="en" dir="ltr">{esc(code)}</code></pre></div>'
            f'<p><a href="{source_url}">{esc(source_label)}</a></p></article>'
        )

    ladder_items = ''.join(
        f'<li><strong>{esc(strings["rule.presentation.step"])} {esc(step.get("step"))}</strong> '
        f'{fixture_text(step.get("condition"))}'
        f'<p><strong>{esc(strings["rule.presentation.if_true"])}:</strong> '
        f'{fixture_text(step.get("true"))} · '
        f'<strong>{esc(strings["rule.presentation.if_false"])}:</strong> '
        f'{fixture_text(step.get("false"))}</p>'
        f'<p class="meta"><code lang="en" dir="ltr">{esc(step.get("citation", ""))}</code></p></li>'
        for step in ladder
    )
    rules_section = (
        f'<section id="rules-as-code" class="rules-code"><h2>{esc(strings["home.rules.heading"])}</h2>'
        f'<p>{esc(strings["home.rules.body"])}</p>'
        f'<div class="code-grid">'
        + code_card(
            'home.rules.axiom_label', 'home.rules.axiom_note', excerpts['axiom'],
            REPOSITORY_URL + '/blob/main/research/rules-visualization/axiom/procurement.rulespec.yaml',
            strings['visualizations.synthetic_source_axiom'],
        )
        + code_card(
            'home.rules.l4_label', 'home.rules.l4_note', excerpts['l4'],
            REPOSITORY_URL + '/blob/main/research/rules-visualization/l4/procurement.l4',
            strings['visualizations.synthetic_source_l4'],
        )
        + '</div>'
        f'<p class="meta">{esc(strings["home.rules.code_note"])}</p>'
        f'<h3>{esc(strings["home.rules.ladder_heading"])}</h3>'
        f'<ol class="ladder-preview">{ladder_items}</ol>'
        f'<p class="meta">{esc(strings["home.rules.ladder_note"])}</p>'
        f'<p><a href="visualizations/synthetic.html#legalese-visualization">{esc(strings["home.rules.visual_link"])}</a> · '
        f'<a href="{RULES_DOC_URL}">{esc(strings["home.rules.comparison_link"])}</a></p>'
        f'<p class="notice"><strong>{esc(strings["home.rules.synthetic"])}</strong> '
        f'{esc(strings["home.rules.no_real_law"])}</p>'
        f'<p>{esc(strings["home.rules.engine_note"])}</p></section>'
    )

    parts = [
        f'<h1>{esc(cfg["title"][lang])}</h1>',
        f'<p class="lede">{esc(strings["home.lede"])}</p>',
        f'<section class="start-here"><h2>{esc(strings["home.start.heading"])}</h2>'
        f'<p>{esc(strings["home.start.body"])}</p>'
        f'<p><a href="visualizations/synthetic.html">{esc(strings["home.start.rules"])}</a> · '
        f'<a href="countries/index.html">{esc(strings["home.start.research"])}</a> · '
        f'<a href="index.html#method">{esc(strings["home.start.method"])}</a></p></section>',
        f'<section><h2>{esc(strings["home.what.heading"])}</h2>'
        f'<p>{esc(strings["home.what.body"])}</p></section>',
        f'<section class="home-paths"><h2>{esc(strings["home.paths.heading"])}</h2>'
        f'<nav aria-label="{esc(strings["home.paths.label"])}"><ul>{path_items}</ul></nav></section>',
        rules_section,
        f'<section id="records"><h2>{esc(strings["home.snapshot.heading"])}</h2>'
        f'<p>{esc(strings["home.snapshot.summary"])}</p>'
        f'<dl class="stat-grid">{stat_items}</dl>'
        f'<h3>{esc(strings["home.snapshot.jurisdictions_label"])}</h3>'
        f'<ul class="inline-list">{_home_country_list(countries_with_records, lang)}</ul>'
        f'<h3>{esc(strings["home.snapshot.domains_label"])}</h3>'
        f'<ul class="inline-list">{_home_domain_list(domains_with_records, lang)}</ul>'
        f'<p>{esc(t(strings, "home.snapshot.discovery", remaining=stats["remaining"], discovery=stats["discovery"]))}</p>'
        f'<p>{esc(t(strings, "home.snapshot.no_research", none=stats["no_research"]))}</p>'
        f'<p>{esc(strings["home.snapshot.retrieval_note"])}</p>'
        f'<p>{esc(strings["home.snapshot.review_note"])}</p>'
        f'<p><a href="coverage/index.html">{esc(strings["home.snapshot.coverage_link"])}</a></p>'
        f'</section>',
    ]

    if featured is not None:
        featured_title = foreign(featured.get('title', featured.get('id')), lang,
                                 featured.get('language', 'en'))
        parts.append(
            f'<section class="feature"><h2>{esc(strings["home.featured.heading"])}</h2>'
            f'<p class="notice"><strong>{esc(strings["home.featured.status"])}</strong></p>'
            f'<h3><a href="visualizations/{esc(FEATURED_VISUALIZATION_ID)}.html">{featured_title}</a></h3>'
            f'<p>{esc(strings["home.featured.body"])}</p><ul>'
            + ''.join(
                f'<li>{esc(strings[f"home.featured.item{index}"])}</li>'
                for index in range(1, 6)
            )
            + f'</ul><p><a href="visualizations/{esc(FEATURED_VISUALIZATION_ID)}.html">'
            f'{esc(strings["home.featured.link"])}</a> · '
            f'<a href="visualizations/index.html">{esc(strings["home.featured.catalogue_link"])}</a></p></section>'
        )

    stages = ('source', 'capture', 'provision', 'interpretation', 'review', 'encoding')
    stage_items = ''.join(
        f'<li><strong>{esc(strings[f"home.stage.{key}.title"])}</strong> '
        f'<span>{esc(strings[f"home.stage.{key}.body"])}</span></li>'
        for key in stages
    )
    parts.append(
        f'<section id="method"><h2>{esc(strings["home.pipeline.heading"])}</h2>'
        f'<p>{esc(strings["home.pipeline.intro"])}</p>'
        f'<ol class="steps">{stage_items}</ol>'
        f'<p class="notice">{esc(strings["home.pipeline.note"])}</p></section>'
    )

    parts.append(
        f'<section><h2>{esc(strings["home.limits.heading"])}</h2>'
        f'<p>{esc(strings["home.limits.body"])}</p>'
        f'<p>{esc(strings["home.limits.evidence"])}</p>'
        f'<p>{esc(strings["home.missing.body"])}</p>'
        f'<ul><li><a href="coverage/index.html">{esc(strings["home.limits.coverage_link"])}</a></li>'
        f'<li><a href="countries/index.html">{esc(strings["home.limits.countries_link"])}</a></li>'
        f'<li><a href="domains/index.html">{esc(strings["home.limits.domains_link"])}</a></li>'
        f'<li><a href="tasks/index.html">{esc(strings["home.limits.tasks_link"])}</a></li>'
        f'<li><a href="sources/index.html">{esc(strings["home.limits.sources_link"])}</a></li></ul></section>'
    )

    claims = ''.join(
        f'<li>{esc(strings[f"home.claims.item{index}"])}</li>'
        for index in range(1, 7)
    )
    parts.append(
        f'<section><h2>{esc(strings["home.claims.heading"])}</h2><ul>{claims}</ul></section>'
    )

    parts.append(
        f'<section><h2>{esc(strings["home.resources.heading"])}</h2><ul>'
        f'<li><a href="{WORKFLOW_URL}">{esc(strings["home.resources.method"])}</a></li>'
        f'<li><a href="{RESEARCH_MODEL_URL}">{esc(strings["home.resources.provenance"])}</a></li>'
        f'<li><a href="{ACCESSIBILITY_URL}">{esc(strings["home.resources.accessibility"])}</a></li>'
        f'<li><a href="{CONTRIBUTING_URL}">{esc(strings["home.resources.contribution"])}</a></li>'
        f'<li><a href="{RULES_DOC_URL}">{esc(strings["home.resources.rules_doc"])}</a></li>'
        f'<li><a href="{AUDIT_URL}">{esc(strings["home.resources.audit"])}</a></li>'
        f'<li><a href="{REPOSITORY_URL}">{esc(strings["home.resources.repo"])}</a></li>'
        f'</ul></section>'
    )
    return '\n'.join(parts)


def source_sections(strings, lang, research):
    """Render recorded source metadata and permitted excerpts."""
    sources = research.get('sources') or []
    if not sources:
        return []
    items = []
    for source in sources:
        title = foreign(source.get('title', ''), lang)
        url = source.get('url')
        heading = f'<a href="{esc(url)}">{title}</a>' if url else title
        language = source.get('language', '')
        publication = source.get('publication_date')
        effective = source.get('effective_date')
        version = source.get('document_version')
        capture = source.get('capture') or {}
        translation = source.get('translation') or {}
        archival = source.get('archival_url')

        def date_value(value):
            if not value or value == 'unknown':
                return esc(strings['record.source.unknown'])
            return f'<span lang="en" dir="ltr">{esc(value)}</span>'

        if archival:
            archival_html = (f'<a href="{esc(archival)}">{esc(strings["record.source.archival"])}: '
                             f'{title}</a>')
        else:
            archival_html = esc(strings['record.source.not_recorded'])

        if capture.get('bytes_stored') and capture.get('sha256'):
            capture_html = t(
                strings, 'record.source.capture_detail',
                date=esc(capture.get('captured_at') or strings['record.source.not_recorded']),
                sha=esc(capture['sha256'][:12]),
            )
        else:
            capture_html = esc(strings['record.source.capture_none'])

        rows = [
            f'<dt>{esc(strings["record.source.issuer"])}</dt>'
            f'<dd>{foreign(source.get("issuer") or strings["record.source.not_recorded"], lang)}</dd>',
            f'<dt>{esc(strings["record.source.jurisdiction"])}</dt>'
            f'<dd><span lang="en" dir="ltr"><code>{esc(source.get("jurisdiction", ""))}</code></span></dd>',
            f'<dt>{esc(strings["record.source.instrument"])}</dt>'
            f'<dd>{esc(label(strings, INSTRUMENT_KEYS, source.get("instrument_type"), "record.not_classified"))}</dd>',
            f'<dt>{esc(strings["record.source.language"])}</dt>'
            f'<dd><span lang="en" dir="ltr"><code>{esc(language)}</code></span> — '
            f'{esc(strings["record.source.authoritative"])}: '
            f'{esc(label(strings, AUTHORITATIVE_KEYS, source.get("authoritative_language"), "record.source.authoritative.unknown"))}</dd>',
            f'<dt>{esc(strings["record.source.publication"])}</dt><dd>{date_value(publication)}</dd>',
            f'<dt>{esc(strings["record.source.effective"])}</dt><dd>{date_value(effective)}</dd>',
            f'<dt>{esc(strings["record.source.version"])}</dt><dd>{foreign(version, lang) if version else esc(strings["record.source.not_recorded"])}</dd>',
            f'<dt>{esc(strings["record.source.archival"])}</dt><dd>{archival_html}</dd>',
            f'<dt>{esc(strings["record.source.capture"])}</dt><dd>{capture_html}</dd>',
            f'<dt>{esc(strings["record.source.translation"])}</dt>'
            f'<dd>{esc(label(strings, TRANSLATION_KEYS, translation.get("status"), "record.source.not_recorded"))} — '
            f'{esc(label(strings, TRANSLATION_REVIEW_KEYS, translation.get("review_state"), "record.source.not_recorded"))}</dd>',
        ]

        expressions = source.get('expressions') or []
        if expressions:
            expression_items = []
            for expression in expressions:
                kind = esc(label(strings, EXPRESSION_KIND_KEYS, expression.get('kind'),
                                 'record.not_classified'))
                language = expression.get('language', '')
                review = esc(label(strings, EXPRESSION_REVIEW_KEYS,
                                   expression.get('review_status'), 'source.not_recorded'))
                meta = [f'{esc(strings["expression.original_language"])}: '
                        f'{code(expression.get("original_language", ""))}']
                if expression.get('authority'):
                    meta.append(f'{esc(strings["expression.authority"])}: '
                                f'{foreign(expression["authority"], lang)}')
                if expression.get('instrument_version'):
                    meta.append(f'{esc(strings["expression.version"])}: '
                                f'{foreign(expression["instrument_version"], lang)}')
                if expression.get('translation_method'):
                    meta.append(f'{esc(strings["expression.method"])}: '
                                f'{esc(label(strings, EXPRESSION_METHOD_KEYS,
                                            expression["translation_method"], "expression.method.unknown"))}')
                if expression.get('reviewed_at'):
                    meta.append(f'{esc(strings["expression.reviewed_at"])}: '
                                f'{code(expression["reviewed_at"])}')
                if expression.get('reviewer_role'):
                    meta.append(f'{esc(strings["expression.reviewer_role"])}: '
                                f'{foreign(expression["reviewer_role"], lang)}')
                if expression.get('notes'):
                    meta.append(foreign(expression['notes'], lang))
                link = ''
                if expression.get('url'):
                    link = (f'<p><a href="{esc(expression["url"])}">'
                            f'{esc(strings["expression.open"])} '
                            f'({code(language)})</a></p>')
                expression_items.append(
                    f'<li><strong>{kind}</strong> — {code(language)} — {review}'
                    f'<p class="meta">{"; ".join(meta)}</p>{link}</li>')
            rows.append(
                f'<dt>{esc(strings["record.expressions_heading"])}</dt>'
                f'<dd><ul>{"".join(expression_items)}</ul></dd>')
        else:
            rows.append(
                f'<dt>{esc(strings["record.expressions_heading"])}</dt>'
                f'<dd>{esc(strings["record.expressions_none"])}</dd>')

        excerpt = source.get('excerpt')
        if isinstance(excerpt, dict):
            excerpt_lang = excerpt.get('language', 'en')
            excerpt_html = (
                f'<h4>{esc(strings["record.source.excerpt"])}</h4>'
                f'<blockquote lang="{esc(excerpt_lang)}" dir="{direction(excerpt_lang)}">'
                f'<p>{esc(excerpt.get("text", ""))}</p></blockquote>'
                f'<p class="meta"><strong>{esc(strings["record.source.excerpt_locator"])}:</strong> '
                f'{foreign(excerpt.get("locator", ""), lang, excerpt_lang)} — '
                f'{esc(strings["record.source.excerpt_note"])} '
                f'<code lang="en" dir="ltr">{esc(excerpt.get("artifact", ""))}</code></p>'
            )
        else:
            excerpt_html = (f'<h4>{esc(strings["record.source.excerpt"])}</h4>'
                            f'<p>{esc(strings["record.source.excerpt_none"])}</p>')

        items.append(f'<article><h3>{heading}</h3><dl>{"".join(rows)}</dl>{excerpt_html}</article>')

    return [
        f'<section><h2>{esc(strings["record.sources_heading"])}</h2>'
        f'<p class="notice">{esc(strings["record.sources_notice"])}</p>'
        f'<p class="notice">{esc(strings["record.expressions_notice"])}</p>'
        f'{"".join(items)}</section>'
    ]


def research_sections(strings, lang, research):
    """Render the structured research fields. Nothing here is a legal finding."""
    if not research:
        return []
    parts = source_sections(strings, lang, research)

    provisions = research.get('provisions') or []
    rows = []
    for provision in provisions:
        locator = (provision.get('locator') or {}).get('value', '')
        rows.append(
            f'<tr><th scope="row"><code lang="en" dir="ltr">{esc(provision.get("id", ""))}</code> '
            f'{foreign(provision.get("heading", ""), lang)}</th>'
            f'<td>{foreign(locator, lang)}</td>'
            f'<td>{foreign(provision.get("summary", ""), lang)}</td>'
            f'<td>{esc(label(strings, EFFECT_KEYS, provision.get("effect_assessment")))}</td>'
            f'<td>{esc(label(strings, ENCODING_KEYS, provision.get("encoding_status")))}</td></tr>'
        )
    if rows:
        parts.append(
            f'<section><h2>{esc(strings["record.provisions_heading"])}</h2>'
            f'<p class="notice">{esc(strings["record.provisions_notice"])}</p>'
            f'<div class="table-scroll" role="region" aria-label="{esc(strings["record.provisions_heading"])}" tabindex="0">'
            f'<table><caption>{esc(strings["record.provisions_caption"])}</caption><thead><tr>'
            f'<th scope="col">{esc(strings["record.table.provision"])}</th>'
            f'<th scope="col">{esc(strings["record.table.locator"])}</th>'
            f'<th scope="col">{esc(strings["record.table.interpretation"])}</th>'
            f'<th scope="col">{esc(strings["record.table.legal_effect"])}</th>'
            f'<th scope="col">{esc(strings["record.table.encoding"])}</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
        )
    else:
        parts.append(f'<section><h2>{esc(strings["record.provisions_heading"])}</h2>'
                     f'<p>{esc(strings["record.provisions_none"])}</p></section>')

    questions = research.get('interpretations') or []
    items = []
    for question in questions:
        meta = [
            f'{esc(strings["record.question_risk"])}: {esc(label(strings, RISK_KEYS, question.get("risk")))}',
            f'{esc(strings["record.question_status"])}: {esc(label(strings, QUESTION_STATUS_KEYS, question.get("status")))}',
            f'{esc(strings["record.question_requires"])}: {esc(label(strings, REQUIRES_KEYS, question.get("requires")))}',
        ]
        category = question.get('category')
        if category and category != 'unknown':
            meta.append(f'{esc(strings["record.question_category"])}: '
                        f'<span lang="en" dir="ltr"><code>{esc(category)}</code></span>')
        items.append(
            f'<li><strong><code lang="en" dir="ltr">{esc(question.get("id", ""))}</code></strong> '
            f'<span>{foreign(question.get("statement", ""), lang)}</span>'
            f'<p class="meta">{"; ".join(meta)}</p></li>'
        )
    parts.append(
        f'<section><h2>{esc(strings["record.questions_heading"])}</h2>'
        + (f'<ul class="questions">{"".join(items)}</ul>' if items
           else f'<p>{esc(strings["record.questions_none"])}</p>')
        + '</section>'
    )

    relations = research.get('relations') or []
    rows = []
    for relation in relations:
        target = relation.get('target') or {}
        title = foreign(target.get('title', ''), lang)
        if target.get('kind') == 'internal_record':
            target_html = (f'<a href="{esc(target.get("record_id", ""))}.html">{title}</a> '
                           f'<span class="meta">({esc(strings["record.relations_internal"])})</span>')
        else:
            target_html = f'<a href="{esc(target.get("url") or "")}">{title}</a>'
        if relation.get('relation') == 'unspecified':
            relation_html = (f'<span lang="en" dir="ltr"><code>{esc(relation.get("recorded_label") or "")}</code></span>'
                             f' — {esc(strings["record.relation.unspecified"])}')
        else:
            relation_html = esc(label(strings, RELATION_KEYS, relation.get('relation')))
        review = esc(label(strings, RELATION_REVIEW_KEYS, relation.get('review_state')))
        rows.append(f'<tr><th scope="row">{target_html}</th><td>{relation_html}</td><td>{review}</td></tr>')
    if rows:
        parts.append(
            f'<section><h2>{esc(strings["record.relations_heading"])}</h2>'
            f'<div class="table-scroll" role="region" aria-label="{esc(strings["record.relations_heading"])}" tabindex="0">'
            f'<table><caption>{esc(strings["record.relations_caption"])}</caption><thead><tr>'
            f'<th scope="col">{esc(strings["record.table.target"])}</th>'
            f'<th scope="col">{esc(strings["record.table.relation"])}</th>'
            f'<th scope="col">{esc(strings["record.table.review_state"])}</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
        )
    else:
        parts.append(f'<section><h2>{esc(strings["record.relations_heading"])}</h2>'
                     f'<p>{esc(strings["record.relations_none"])}</p></section>')
    return parts


def record_body(catalogues, lang, record, base, research=None):
    strings = catalogues[lang]
    record_id = record['id']
    record_lang = record.get('language', 'en')
    title = foreign(record.get('title', record_id), lang, record_lang)
    untranslated = ''
    if lang != record_lang:
        untranslated = f'<p class="notice">{esc(strings["record.untranslated"])}</p>'
    authority = record.get('authority') or strings['record.not_verified']
    standard = record.get('standard') or '—'
    legal = label(strings, LEGAL_STATUS_KEYS, record.get('legal_effect'))
    instrument = (strings[INSTRUMENT_KEYS[record['instrument_type']]]
                  if record.get('instrument_type') in INSTRUMENT_KEYS
                  else strings['record.not_classified'])
    issues = record.get('unresolved_interpretations')
    if isinstance(issues, int):
        issues_text = t(strings, 'record.issues_count', count=issues)
    else:
        issues_text = strings['record.not_assessed']
    rule_status = label(strings, RULE_STATUS_KEYS, record.get('execution_status'), 'record.rule.not_encoded')

    parts = [
        f'<h1>{title}</h1>',
        untranslated,
        f'<p class="record-id">{esc(strings["record.record_id"])}: <code>{esc(record_id)}</code></p>',
        '<dl>',
        f'<dt>{esc(strings["record.authority"])}</dt><dd>{foreign(authority, lang, record_lang)}</dd>',
        f'<dt>{esc(strings["record.legal"])}</dt><dd>{esc(legal)}</dd>',
        f'<dt>{esc(strings["record.type"])}</dt><dd>{esc(instrument)}</dd>',
        f'<dt>{esc(strings["home.table.standard"])}</dt><dd>{foreign(standard, lang, record_lang)}</dd>',
        f'<dt>{esc(strings["record.source"])}</dt>'
        f'<dd><a href="{esc(record.get("source_url", "#"))}">{foreign(record.get("source_title") or strings["record.source"], lang, record_lang)}</a></dd>',
        f'<dt>{esc(strings["record.scope"])}</dt><dd>{foreign(record.get("scope") or strings["record.not_verified"], lang, record_lang)}</dd>',
        f'<dt>{esc(strings["record.issues"])}</dt><dd>{esc(issues_text)}</dd>',
        '</dl>',
        f'<h2>{esc(strings["record.summary"])}</h2>'
        f'<p>{foreign(record.get("notes") or strings["record.no_summary"], lang, record_lang)}</p>',
        f'<p><strong>{esc(strings["record.rule_status"])}:</strong> {esc(rule_status)}</p>',
    ]
    parts.extend(research_sections(strings, lang, research))
    if record_id in SELECTED_RECORDS:
        parts.append(
            f'<section><h2>{esc(strings["visualizations.record_heading"])}</h2>'
            f'<p><a href="../visualizations/{esc(record_id)}.html">'
            f'{esc(strings["visualizations.record_link"])}</a></p></section>')

    artifacts = []
    for filename, key in ARTIFACT_KEYS.items():
        if (base / 'policies' / record_id / filename).is_file():
            artifacts.append(
                f'<li><a href="artifacts/{esc(record_id)}/{esc(filename)}">'
                f'{esc(strings[key])}</a></li>'
            )
    if artifacts:
        parts.append(f'<section><h2>{esc(strings["record.artifacts_heading"])}</h2>'
                     f'<p>{esc(strings["record.artifacts_notice"])}</p>'
                     f'<ul class="artifacts">{"".join(artifacts)}</ul></section>')
    parts.append(f'<p><a href="../index.html">{esc(strings["record.back"])}</a></p>')
    return '\n'.join(parts)


def countries_index_body(catalogues, lang, view):
    strings = catalogues[lang]
    rows = []
    for country in view['countries']:
        rows.append(
            f'<tr><th scope="row"><a href="{esc(country["code"])}.html">'
            f'{country_name(country, lang)}</a></th>'
            f'<td>{esc(status_text(strings, country["status"]))}</td>'
            f'<td>{len(country["records"])}</td>'
            f'<td>{len(country["candidates"])}</td>'
            f'<td>{len(country["tasks"])}</td></tr>'
        )
    parts = [
        f'<h1>{esc(strings["countries.h1"])}</h1>',
        f'<p class="lede">{esc(strings["countries.lede"])}</p>',
        f'<p class="notice">{esc(strings["countries.note"])}</p>',
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["countries.h1"])}" tabindex="0">'
        f'<table><caption>{esc(strings["countries.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["countries.table.jurisdiction"])}</th>'
        f'<th scope="col">{esc(strings["countries.table.status"])}</th>'
        f'<th scope="col">{esc(strings["countries.table.records"])}</th>'
        f'<th scope="col">{esc(strings["countries.table.sources"])}</th>'
        f'<th scope="col">{esc(strings["countries.table.tasks"])}</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
    ]
    if lang != 'en':
        parts.append(f'<p class="notice">{esc(strings["countries.translation_note"])}</p>')
    parts.append(f'<p><a href="../index.html">{esc(strings["countries.back"])}</a></p>')
    return '\n'.join(parts)


def country_body(catalogues, lang, view, country):
    strings = catalogues[lang]
    domain_map = {domain['id']: domain for domain in view['domains']}
    parts = [
        f'<h1>{country_name(country, lang)}</h1>',
        f'<p class="lede">{country_note(country, "scope_note", lang)}</p>',
    ]
    if country.get('jurisdiction_note'):
        parts.append(f'<p class="notice">{country_note(country, "jurisdiction_note", lang)}</p>')
    if lang != 'en':
        parts.append(f'<p class="notice">{esc(strings["countries.translation_note"])}</p>')

    latest_review = country.get('latest_review') or strings['country.not_recorded']
    latest_discovery = country.get('latest_discovery') or strings['country.not_recorded']
    summary = [
        (strings['country.code'], code(country.get('code', ''))),
        (strings['country.group'], country_group(country, lang)),
        (strings['country.status'], esc(status_text(strings, country['status']))),
        (strings['country.records'], str(len(country['records']))),
        (strings['country.sources'], str(len(country['candidates']))),
        (strings['country.tasks'], str(len(country['tasks']))),
        (strings['country.latest_review'],
         code(latest_review) if country.get('latest_review') else esc(latest_review)),
        (strings['country.latest_discovery'],
         code(latest_discovery) if country.get('latest_discovery') else esc(latest_discovery)),
    ]
    parts.append('<dl>' + ''.join(f'<dt>{esc(key)}</dt><dd>{value}</dd>'
                                  for key, value in summary) + '</dl>')

    if country['domains']:
        rows = []
        for item in country['domains']:
            domain = domain_map.get(item['id'], {'label_en': item['id']})
            records = sum(1 for record in country['records'] if record.get('topic') == item['id'])
            sources = sum(1 for candidate in country['candidates']
                          if item['id'] in (candidate.get('domains') or []))
            tasks = sum(1 for task in country['tasks'] if task.get('domain') == item['id'])
            rows.append(
                f'<tr><th scope="row"><a href="../domains/{esc(item["id"])}.html">'
                f'{domain_name(domain, lang)}</a></th>'
                f'<td>{esc(status_text(strings, item["status"]))}</td>'
                f'<td>{records}</td><td>{sources}</td><td>{tasks}</td></tr>'
            )
        parts.append(
            f'<section><h2>{esc(strings["country.domains_heading"])}</h2>'
            f'<div class="table-scroll" role="region" aria-label="{esc(strings["country.domains_heading"])}" tabindex="0">'
            f'<table><caption>{esc(strings["country.domains_caption"])}</caption><thead><tr>'
            f'<th scope="col">{esc(strings["country.table.domain"])}</th>'
            f'<th scope="col">{esc(strings["country.table.status"])}</th>'
            f'<th scope="col">{esc(strings["country.table.records"])}</th>'
            f'<th scope="col">{esc(strings["country.table.sources"])}</th>'
            f'<th scope="col">{esc(strings["country.table.tasks"])}</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
        )
    else:
        parts.append(
            f'<section><h2>{esc(strings["country.domains_heading"])}</h2>'
            f'<p>{esc(strings["country.no_domains"])}</p></section>'
        )

    if country['records']:
        items = ''.join(
            f'<li><a href="../records/{esc(record["id"])}.html">'
            f'{foreign(record.get("title", record["id"]), lang, record.get("language", "en"))}</a>'
            f' {code(record["id"])}</li>'
            for record in country['records']
        )
        parts.append(f'<section><h2>{esc(strings["country.records_heading"])}</h2>'
                     f'<ul>{items}</ul></section>')
    else:
        parts.append(f'<section><h2>{esc(strings["country.records_heading"])}</h2>'
                     f'<p>{esc(strings["country.no_records"])}</p></section>')

    if country['candidates']:
        items = ''.join(
            f'<li><a href="{esc(candidate["source_url"])}" rel="noreferrer">'
            f'{foreign(candidate.get("instrument_title", candidate["id"]), lang)}</a> '
            f'{code(candidate["id"])} — '
            f'{esc(strings["source.discovery_label"])} '
            f'({esc(capture_text(strings, candidate.get("capture_status")))}) — '
            f'{esc(strings["source.legal_review"])}: '
            f'{esc(legal_review_text(strings, candidate.get("legal_effect")))}</li>'
            for candidate in country['candidates']
        )
        parts.append(
            f'<section><h2>{esc(strings["country.sources_heading"])}</h2>'
            f'<p class="notice">{esc(strings["source.discovery_notice"])}</p>'
            f'<ul>{items}</ul></section>'
        )
    else:
        parts.append(f'<section><h2>{esc(strings["country.sources_heading"])}</h2>'
                     f'<p>{esc(strings["country.no_sources"])}</p></section>')

    if country['tasks']:
        items = ''.join(
            f'<li>{code(task["task_id"])} — '
            f'{esc(task_stage_text(strings, task.get("stage")))} — '
            f'{esc(task_status_text(strings, task.get("status")))}'
            f'<p>{foreign(task.get("question", ""), lang)}</p></li>'
            for task in country['tasks']
        )
        parts.append(f'<section><h2>{esc(strings["country.tasks_heading"])}</h2>'
                     f'<ul>{items}</ul></section>')
    else:
        parts.append(f'<section><h2>{esc(strings["country.tasks_heading"])}</h2>'
                     f'<p>{esc(strings["country.no_tasks"])}</p></section>')

    if country['open_questions']:
        items = ''.join(
            f'<li>{foreign(question.get("text", ""), lang)}'
            f' <span class="meta">({code(question.get("id", ""))})</span></li>'
            for question in country['open_questions']
        )
        parts.append(
            f'<section><h2>{esc(strings["country.questions_heading"])}</h2>'
            f'<p class="notice">{esc(strings["country.questions_notice"])}</p>'
            f'<ul>{items}</ul></section>'
        )
    else:
        parts.append(f'<section><h2>{esc(strings["country.questions_heading"])}</h2>'
                     f'<p>{esc(strings["country.no_questions"])}</p></section>')

    parts.append(f'<p><a href="index.html">{esc(strings["countries.back"])}</a></p>')
    return '\n'.join(parts)


def domains_index_body(catalogues, lang, view):
    strings = catalogues[lang]
    domain_map = {domain['id']: domain for domain in view['domains']}
    parts = [
        f'<h1>{esc(strings["domains.h1"])}</h1>',
        f'<p class="lede">{esc(strings["domains.lede"])}</p>',
        f'<p class="notice">{esc(strings["domains.note"])}</p>',
    ]
    for group in view['groups']:
        domains = [domain_map[domain['id']] for domain in view['domains']
                   if domain['group'] == group['id']]
        if not domains:
            continue
        rows = ''.join(
            f'<tr><th scope="row"><a href="{esc(domain["id"])}.html">'
            f'{domain_name(domain, lang)}</a></th>'
            f'<td>{esc(status_text(strings, domain["status"]))}</td>'
            f'<td>{len(domain["records"])}</td>'
            f'<td>{len(domain["candidates"])}</td>'
            f'<td>{len(domain["tasks"])}</td></tr>'
            for domain in domains
        )
        group_label = localized_label(group, lang)
        parts.append(
            f'<section><h2>{group_label}</h2>'
            f'<div class="table-scroll" role="region" aria-label="{group_label}" tabindex="0">'
            f'<table><caption>{esc(strings["domains.caption"])}</caption><thead><tr>'
            f'<th scope="col">{esc(strings["domains.table.domain"])}</th>'
            f'<th scope="col">{esc(strings["domains.table.status"])}</th>'
            f'<th scope="col">{esc(strings["domains.table.records"])}</th>'
            f'<th scope="col">{esc(strings["domains.table.sources"])}</th>'
            f'<th scope="col">{esc(strings["domains.table.tasks"])}</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div></section>'
        )
    if lang != 'en':
        parts.append(f'<p class="notice">{esc(strings["domains.translation_note"])}</p>')
    parts.append(f'<p><a href="../index.html">{esc(strings["domains.back"])}</a></p>')
    return '\n'.join(parts)


def domain_body(catalogues, lang, view, domain):
    strings = catalogues[lang]
    country_map = {country['code']: country for country in view['countries']}
    parts = [
        f'<h1>{domain_name(domain, lang)}</h1>',
        f'<p class="lede">{esc(strings["domain.lede"])}</p>',
    ]
    group = next((item for item in view['groups'] if item['id'] == domain.get('group')), None)
    if group:
        group_label = localized_label(group, lang)
        parts.append(f'<p>{esc(strings["domain.group"])}: {group_label}</p>')
    if lang != 'en':
        parts.append(f'<p class="notice">{esc(strings["domains.translation_note"])}</p>')

    parts.append(
        f'<dl><dt>{esc(strings["domain.status"])}</dt>'
        f'<dd>{esc(status_text(strings, domain["status"]))}</dd>'
        f'<dt>{esc(strings["domain.records"])}</dt><dd>{len(domain["records"])}</dd>'
        f'<dt>{esc(strings["domain.sources"])}</dt><dd>{len(domain["candidates"])}</dd>'
        f'<dt>{esc(strings["domain.tasks"])}</dt><dd>{len(domain["tasks"])}</dd></dl>'
    )

    if domain.get('subtopics'):
        items = ''.join(
            f'<li>{localized_label(subtopic, lang)}</li>'
            for subtopic in domain['subtopics']
        )
        parts.append(f'<section><h2>{esc(strings["domain.subtopics_heading"])}</h2>'
                     f'<p>{esc(strings["domain.subtopics_note"])}</p>'
                     f'<ul>{items}</ul></section>')

    referenced = {}
    for record in domain['records']:
        referenced.setdefault(record.get('country'), {'records': 0, 'sources': 0, 'tasks': 0})
        referenced[record.get('country')]['records'] += 1
    for candidate in domain['candidates']:
        referenced.setdefault(candidate.get('jurisdiction'), {'records': 0, 'sources': 0, 'tasks': 0})
        referenced[candidate.get('jurisdiction')]['sources'] += 1
    for task in domain['tasks']:
        referenced.setdefault(task.get('jurisdiction'), {'records': 0, 'sources': 0, 'tasks': 0})
        referenced[task.get('jurisdiction')]['tasks'] += 1

    if referenced:
        rows = []
        for country_code in sorted(referenced):
            country = country_map.get(country_code, {'code': country_code, 'name': country_code})
            counts = referenced[country_code]
            status = next((item['status'] for item in country['domains']
                           if item['id'] == domain['id']), 'not_started')
            rows.append(
                f'<tr><th scope="row"><a href="../countries/{esc(country_code)}.html">'
                f'{country_name(country, lang)}</a></th>'
                f'<td>{esc(status_text(strings, status))}</td>'
                f'<td>{counts["records"]}</td>'
                f'<td>{counts["sources"]}</td>'
                f'<td>{counts["tasks"]}</td></tr>'
            )
        parts.append(
            f'<section><h2>{esc(strings["domain.countries_heading"])}</h2>'
            f'<div class="table-scroll" role="region" aria-label="{esc(strings["domain.countries_heading"])}" tabindex="0">'
            f'<table><caption>{esc(strings["domain.countries_caption"])}</caption><thead><tr>'
            f'<th scope="col">{esc(strings["domain.table.country"])}</th>'
            f'<th scope="col">{esc(strings["domain.table.status"])}</th>'
            f'<th scope="col">{esc(strings["domain.table.records"])}</th>'
            f'<th scope="col">{esc(strings["domain.table.sources"])}</th>'
            f'<th scope="col">{esc(strings["domain.table.tasks"])}</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
        )
    else:
        parts.append(f'<section><h2>{esc(strings["domain.countries_heading"])}</h2>'
                     f'<p>{esc(strings["domain.no_countries"])}</p></section>')

    if domain['records']:
        items = ''.join(
            f'<li><a href="../records/{esc(record["id"])}.html">'
            f'{foreign(record.get("title", record["id"]), lang, record.get("language", "en"))}</a> '
            f'{code(record["id"])}</li>'
            for record in domain['records']
        )
        parts.append(f'<section><h2>{esc(strings["country.records_heading"])}</h2>'
                     f'<ul>{items}</ul></section>')
    if domain['candidates']:
        items = ''.join(
            f'<li><a href="{esc(candidate["source_url"])}" rel="noreferrer">'
            f'{foreign(candidate.get("instrument_title", candidate["id"]), lang)}</a> '
            f'{code(candidate["id"])} — {esc(strings["source.discovery_label"])} — '
            f'{esc(strings["source.legal_review"])}: '
            f'{esc(legal_review_text(strings, candidate.get("legal_effect")))}</li>'
            for candidate in domain['candidates']
        )
        parts.append(
            f'<section><h2>{esc(strings["country.sources_heading"])}</h2>'
            f'<p class="notice">{esc(strings["source.discovery_notice"])}</p>'
            f'<ul>{items}</ul></section>'
        )
    if domain['open_questions']:
        items = ''.join(
            f'<li>{foreign(question.get("text", ""), lang)} '
            f'<span class="meta">({code(question.get("id", ""))})</span></li>'
            for question in domain['open_questions']
        )
        parts.append(
            f'<section><h2>{esc(strings["country.questions_heading"])}</h2>'
            f'<p class="notice">{esc(strings["country.questions_notice"])}</p>'
            f'<ul>{items}</ul></section>'
        )
    parts.append(f'<p><a href="index.html">{esc(strings["domains.back"])}</a></p>')
    return '\n'.join(parts)


def coverage_body(catalogues, lang, view):
    strings = catalogues[lang]
    matrix_by_code = {row['country']['code']: row['cells'] for row in view['matrix']}
    headers = ''.join(
        f'<th scope="col">{domain_name(domain, lang)}</th>'
        for domain in view['domains']
    )
    rows = []
    for country in view['countries']:
        cells = ''.join(
            f'<td>{esc(status_text(strings, cell["status"]))}</td>'
            for cell in matrix_by_code.get(country['code'], [])
        )
        rows.append(
            f'<tr><th scope="row"><a href="../countries/{esc(country["code"])}.html">'
            f'{country_name(country, lang)}</a></th>{cells}</tr>'
        )
    legend = ''.join(
        f'<li><strong>{esc(status_text(strings, status))}</strong>: '
        f'{esc(strings[f"coverage.legend.{status}"])}</li>'
        for status in (
            'not_started', 'source_discovery', 'candidate_sources_identified',
            'evidence_captured', 'provision_extraction', 'legal_review_pending',
            'reviewed_findings', 'blocked',
        )
    )
    parts = [
        f'<h1>{esc(strings["coverage.h1"])}</h1>',
        f'<p class="lede">{esc(strings["coverage.lede"])}</p>',
        f'<p class="notice">{esc(strings["coverage.note"])}</p>',
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["coverage.h1"])}" tabindex="0">'
        f'<table><caption>{esc(strings["coverage.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["coverage.table.jurisdiction"])}</th>{headers}'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        f'<section><h2>{esc(strings["coverage.legend_heading"])}</h2>'
        f'<ul>{legend}</ul></section>',
    ]
    parts.append(f'<p><a href="../index.html">{esc(strings["coverage.back"])}</a></p>')
    return '\n'.join(parts)


def tasks_body(catalogues, lang, view):
    strings = catalogues[lang]
    country_map = {country['code']: country for country in view['countries']}
    domain_map = {domain['id']: domain for domain in view['domains']}
    tasks = sorted(view['tasks'], key=lambda task: (
        task.get('jurisdiction', ''), task.get('domain', ''), task.get('task_id', '')))
    rows = []
    for task in tasks:
        country = country_map.get(task.get('jurisdiction'), {'name': task.get('jurisdiction', '')})
        domain = domain_map.get(task.get('domain'), {'label_en': task.get('domain', '')})
        rows.append(
            f'<tr><th scope="row">{code(task["task_id"])} — '
            f'{foreign(task.get("question", ""), lang)}</th>'
            f'<td>{country_name(country, lang)}</td>'
            f'<td>{domain_name(domain, lang)}</td>'
            f'<td>{esc(task_stage_text(strings, task.get("stage")))}</td>'
            f'<td>{esc(priority_text(strings, task.get("priority")))}</td>'
            f'<td>{esc(task_status_text(strings, task.get("status")))}</td></tr>'
        )
    return '\n'.join([
        f'<h1>{esc(strings["tasks.h1"])}</h1>',
        f'<p class="lede">{esc(strings["tasks.lede"])}</p>',
        f'<p class="notice">{esc(strings["tasks.note"])}</p>',
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["tasks.h1"])}" tabindex="0">'
        f'<table><caption>{esc(strings["tasks.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["tasks.table.task"])}</th>'
        f'<th scope="col">{esc(strings["tasks.table.jurisdiction"])}</th>'
        f'<th scope="col">{esc(strings["tasks.table.domain"])}</th>'
        f'<th scope="col">{esc(strings["tasks.table.stage"])}</th>'
        f'<th scope="col">{esc(strings["tasks.table.priority"])}</th>'
        f'<th scope="col">{esc(strings["tasks.table.status"])}</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        f'<p><a href="../index.html">{esc(strings["tasks.back"])}</a></p>',
    ])


def sources_body(catalogues, lang, view):
    strings = catalogues[lang]
    country_map = {country['code']: country for country in view['countries']}
    domain_map = {domain['id']: domain for domain in view['domains']}
    countries = {candidate.get('jurisdiction') for candidate in view['candidates']}
    sections = []
    for candidate in view['candidates']:
        country = country_map.get(candidate.get('jurisdiction'),
                                  {'name': candidate.get('jurisdiction', '')})
        domains = '; '.join(
            domain_name(domain_map.get(domain_id, {'label_en': domain_id}), lang)
            for domain_id in candidate.get('domains', [])
        )
        recorded = candidate.get('published_date_reported')
        recorded_html = (code(recorded) if recorded and recorded != 'unknown'
                         else esc(strings['source.not_recorded']))
        details = [
            (strings['source.jurisdiction'], country_name(country, lang)),
            (strings['source.domains'], esc(domains) if domains
             else esc(strings['source.not_recorded'])),
        ]
        instrument = candidate.get('instrument')
        if instrument:
            instrument_value = [esc(instrument_type_text(
                strings, instrument.get('instrument_type_reported')))]
            if instrument.get('instrument_number_reported'):
                instrument_value.append(code(instrument['instrument_number_reported']))
            if instrument.get('instrument_year_reported'):
                instrument_value.append(code(instrument['instrument_year_reported']))
            instrument_html = ' · '.join(instrument_value)
        else:
            instrument_html = esc(strings['source.not_recorded'])
        details.append((strings['source.instrument'], instrument_html))
        details += [
            (strings['source.authority'],
             esc(candidate['issuing_authority']) if candidate.get('issuing_authority')
             else esc(strings['source.not_recorded'])),
            (strings['source.source_type'],
             esc(source_type_text(strings, candidate.get('source_type')))),
        ]
        publisher = candidate.get('publisher')
        if publisher:
            publisher_value = code(publisher.get('host', ''))
            if publisher.get('publisher_name'):
                publisher_value += f' — {foreign(publisher["publisher_name"], lang)}'
            details.append((strings['source.publisher'], publisher_value))
            details.append((strings['source.registry'],
                            esc(publisher_status_text(strings, publisher.get('verification_status')))))
        else:
            details.append((strings['source.publisher'], esc(strings['source.not_recorded'])))
            details.append((strings['source.registry'], esc(strings['source.not_recorded'])))
        check = candidate.get('source_check') or {}
        attempted = (code(check['attempted_at']) if check.get('attempted_at')
                     else esc(strings['source.not_recorded']))
        retrieval = (f'{esc(retrieval_text(strings, candidate.get("retrieval_status")))} — '
                     f'{esc(strings["source.retrieval.last_attempted"])}: {attempted}')
        if check.get('error_category'):
            retrieval += (f' — {esc(strings["source.retrieval.error"])}: '
                          f'{esc(retrieval_error_text(strings, check["error_category"]))}')
        details.append((strings['source.retrieval'], retrieval))
        successful = (code(check['last_successful_retrieval'])
                      if check.get('last_successful_retrieval')
                      else esc(strings['source.not_recorded']))
        freshness = (f'{esc(freshness_text(strings, candidate.get("freshness")))} — '
                     f'{esc(strings["source.freshness.last_successful"])}: {successful}')
        details.append((strings['source.freshness'], freshness))
        verification = candidate.get('legal_verification') or {}
        details.append((strings['source.legal_verification'],
                        esc(legal_verification_text(strings, verification.get('status')))))
        captures = candidate.get('source_captures') or []
        if captures:
            latest_capture = candidate.get('latest_capture') or {}
            capture_count = t(strings, 'source.captures.count', count=len(captures))
            capture_html = (f'<p>{esc(capture_count)} — '
                            f'{esc(strings["source.captures.latest"])}: '
                            f'{code(latest_capture.get("capture_id", ""))}</p>'
                            f'<p class="meta">{esc(strings["source.captures.captured_at"])}: '
                            f'{code(latest_capture.get("captured_at", ""))} — '
                            f'{esc(strings["source.captures.checksum"])}: '
                            f'{code(str(latest_capture.get("sha256", ""))[:12])} — '
                            f'{esc(strings["source.captures.language"])}: '
                            f'{code(latest_capture.get("language", ""))} — '
                            f'{esc(strings["source.captures.metadata_only"])}</p>')
        else:
            capture_html = esc(strings['source.captures.none'])
        details.append((strings['source.captures'], capture_html))
        changes = candidate.get('change_events') or []
        if changes:
            latest = candidate.get('latest_change') or {}
            count_line = t(strings, 'source.changes.count', count=len(changes))
            summary = (f'{esc(strings["change.detected"])}: '
                       f'{code(latest.get("detected_at", ""))} — '
                       f'{esc(label(strings, CHANGE_TECHNICAL_KEYS, latest.get("technical_change"), "change.technical.indeterminate"))} — '
                       f'{esc(label(strings, CHANGE_POTENTIAL_KEYS, latest.get("potential_legal_change"), "change.potential.relationship_unresolved"))} — '
                       f'{esc(label(strings, CHANGE_REVIEW_KEYS, candidate.get("change_review_status"), "change.review.indeterminate"))}')
            decision = candidate.get('latest_change_decision') or {}
            if decision.get('legal_change'):
                summary += (f' — {esc(strings["change.reviewed_change"])}: '
                            f'{esc(label(strings, CHANGE_LEGAL_KEYS, decision.get("legal_change"), "change.legal.indeterminate"))}')
            task_ids = candidate.get('change_task_ids') or []
            if task_ids:
                summary += (f' — {esc(strings["change.task"])}: '
                            f'{" ".join(code(task_id) for task_id in task_ids)}')
            details.append((strings['source.changes'],
                            f'<p>{esc(count_line)}</p><p>{summary}</p>'))
        else:
            details.append((strings['source.changes'], esc(strings['source.changes.none'])))
        if instrument:
            dates = instrument.get('dates') if isinstance(instrument.get('dates'), dict) else {}

            def date_value(value):
                return code(value) if value else esc(strings['source.not_recorded'])

            version = (f'{esc(strings["source.version.publication"])}: '
                       f'{date_value(instrument.get("publication_date_reported"))} · '
                       f'{esc(strings["source.version.commencement"])}: '
                       f'{date_value(dates.get("commencement"))} · '
                       f'{esc(strings["source.version.repeal"])}: '
                       f'{date_value(dates.get("repeal"))}')
            captured = esc(strings['source.captured_version.none'])
        else:
            version = esc(strings['source.not_recorded'])
            captured = esc(strings['source.not_recorded'])
        details += [
            (strings['source.version_dates'], version),
            (strings['source.captured_version'], captured),
            (strings['source.research_status'],
             esc(status_text(strings, 'candidate_sources_identified'))),
            (strings['source.legal_review'],
             esc(legal_review_text(strings, candidate.get('legal_effect')))),
        ]
        languages = candidate.get('source_languages') or []
        details.append((strings['source.languages'],
                        ', '.join(code(language) for language in languages)
                        if languages else esc(strings['source.not_recorded'])))
        task_ids = candidate.get('task_ids') or []
        details.append((strings['source.related_task'],
                        ' '.join(code(task_id) for task_id in task_ids)
                        if task_ids else esc(strings['source.related_task.none'])))
        verification = candidate.get('verification_required') or []
        if verification:
            items = ''.join(
                f'<li>{esc(strings[VERIFICATION_KEYS[requirement]])}</li>'
                for requirement in verification
            )
            details.append((strings['source.verification'], f'<ul>{items}</ul>'))
        else:
            details.append((strings['source.verification'],
                            esc(strings['source.verification.none'])))
        relations = candidate.get('relations') or []
        if relations:
            items = ''.join(
                f'<li>{esc(relation_text(strings, relation.get("relation")))} — '
                f'{code(relation.get("target_candidate_id", ""))} — '
                f'{foreign(relation.get("recorded_label", ""), lang)} '
                f'({esc(strings["source.relationship.unreviewed"])})</li>'
                for relation in relations
            )
            details.append((strings['source.relationship'], f'<ul>{items}</ul>'))
        provenance = candidate.get('provenance')
        if provenance:
            prov = [
                f'<li>{esc(strings["source.provenance.package"])}: '
                f'{code(provenance.get("package", ""))}</li>',
                f'<li>{esc(strings["source.provenance.incoming"])}: '
                f'{code(provenance.get("incoming_id", ""))}</li>',
                f'<li>{esc(strings["source.provenance.recorded"])}: '
                f'{code(provenance.get("recorded_on", ""))}</li>',
            ]
            if provenance.get('evidence_ref'):
                prov.append(
                    f'<li>{esc(strings["source.provenance.evidence_ref"])}: '
                    f'{code(provenance["evidence_ref"])} — '
                    f'{esc(strings["source.provenance.evidence_note"])}</li>')
            details.append((strings['source.provenance'], f'<ul>{"".join(prov)}</ul>'))
        details.append((strings['source.link'],
                        f'<a href="{esc(candidate["source_url"])}" rel="noreferrer">'
                        f'{code(candidate["source_url"])}</a>'))
        definition = ''.join(f'<dt>{esc(label)}</dt><dd>{value}</dd>'
                             for label, value in details)
        sections.append(
            f'<section><h2>{foreign(candidate.get("instrument_title", candidate["id"]), lang)} '
            f'{code(candidate["id"])}</h2>'
            f'<p class="meta">{esc(strings["source.discovery_label"])} — '
            f'{esc(capture_text(strings, candidate.get("capture_status")))}</p>'
            f'<dl>{definition}</dl></section>')
    count_line = t(strings, 'sources.count', count=len(view['candidates']),
                   jurisdictions=len(countries))
    return '\n'.join([
        f'<h1>{esc(strings["sources.h1"])}</h1>',
        f'<p class="lede">{esc(strings["sources.lede"])}</p>',
        f'<p class="notice">{esc(strings["source.discovery_notice"])}</p>',
        f'<p class="notice">{esc(strings["source.candidate_notice"])}</p>',
        f'<p class="notice">{esc(strings["sources.pending_review"])}</p>',
        f'<p class="notice">{esc(strings["sources.currency_notice"])}</p>',
        f'<p class="notice">{esc(strings["sources.instrument_notice"])}</p>',
        f'<p class="notice">{esc(strings["source.changes.notice"])}</p>',
        f'<p>{esc(count_line)}</p>',
        '\n'.join(sections),
        f'<p><a href="../index.html">{esc(strings["sources.back"])}</a></p>',
    ])


def comparison_body(catalogues, lang, view):
    strings = catalogues[lang]
    country_map = {country['code']: country for country in view['countries']}
    rows = []
    for record in view['records']:
        policy = record['policy']
        country = country_map.get(policy.get('country'), {'name': policy.get('country', '')})
        for provision in record['provisions']:
            locator = (provision.get('locator') or {}).get('value', '')
            rows.append(
                f'<tr><th scope="row"><a href="../records/{esc(policy["id"])}.html">'
                f'{foreign(policy.get("title", policy["id"]), lang, policy.get("language", "en"))}</a> '
                f'{code(provision.get("id", ""))} '
                f'{foreign(provision.get("heading", ""), lang)}</th>'
                f'<td>{country_name(country, lang)}</td>'
                f'<td>{foreign(locator, lang)}</td>'
                f'<td>{esc(label(strings, EFFECT_KEYS, provision.get("effect_assessment")))}</td>'
                f'<td>{esc(label(strings, ENCODING_KEYS, provision.get("encoding_status")))}</td></tr>'
            )
    return '\n'.join([
        f'<h1>{esc(strings["comparison.h1"])}</h1>',
        f'<p class="lede">{esc(strings["comparison.lede"])}</p>',
        f'<p class="notice">{esc(strings["comparison.note"])}</p>',
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["comparison.h1"])}" tabindex="0">'
        f'<table><caption>{esc(strings["comparison.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["comparison.table.provision"])}</th>'
        f'<th scope="col">{esc(strings["comparison.table.jurisdiction"])}</th>'
        f'<th scope="col">{esc(strings["comparison.table.locator"])}</th>'
        f'<th scope="col">{esc(strings["comparison.table.effect"])}</th>'
        f'<th scope="col">{esc(strings["comparison.table.encoding"])}</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>',
        f'<p><a href="../index.html">{esc(strings["comparison.back"])}</a></p>',
    ])


def build(region):
    base = ROOT / 'regions' / region
    out = ROOT / 'dist' / region
    if out.exists():
        shutil.rmtree(out)
    (out / 'assets').mkdir(parents=True)
    (out / 'assets' / 'site.css').write_text((ROOT / 'framework' / 'site.css').read_text())

    cfg = load(base / 'region.json')
    policies = load(base / 'data' / 'policies.json')
    view = build_view(load_coverage(base, ROOT / 'research-toolkit'))
    catalogues = load_i18n(base, tuple(cfg['languages']))

    for lang in cfg['languages']:
        lang_dir = out / lang
        lang_dir.mkdir()
        title = cfg['title'][lang]
        strings = catalogues[lang]
        others = other_languages(lang)
        alt_hrefs = {code: f'../{code}/' for code in others}
        stats = home_stats(policies, view)
        body = home_body(catalogues, lang, cfg, policies, view, stats=stats)
        description = t(strings, 'home.description', **{
            key: stats[key] for key in ('records', 'covered', 'total', 'domains')
        })
        (lang_dir / 'index.html').write_text(
            page(catalogues, lang, strings['home.title'], body, 1, alt_hrefs,
                 description),
            encoding='utf-8',
        )

        home_crumb = ('../index.html', esc(strings['nav.home']), False)
        body_label = {
            'countries': strings['countries.h1'],
            'domains': strings['domains.h1'],
            'coverage': strings['coverage.h1'],
            'tasks': strings['tasks.h1'],
            'sources': strings['sources.h1'],
            'comparison': strings['comparison.h1'],
            'visualizations': strings['visualizations.h1'],
        }

        def write_section(name, suffix, body_html, description):
            section_dir = lang_dir / name
            section_dir.mkdir(exist_ok=True)
            section_alt = {code: f'../../{code}/{name}/{suffix}' for code in others}
            crumb = breadcrumb_trail([
                home_crumb,
                (None, esc(body_label[name]), True),
            ])
            (section_dir / suffix).write_text(
                page(catalogues, lang, f'{body_label[name]} — {title}', body_html,
                     2, section_alt, description, crumb),
                encoding='utf-8',
            )

        write_section('countries', 'index.html',
                      countries_index_body(catalogues, lang, view),
                      strings['countries.description'])
        write_section('domains', 'index.html',
                      domains_index_body(catalogues, lang, view),
                      strings['domains.description'])
        write_section('coverage', 'index.html',
                      coverage_body(catalogues, lang, view),
                      strings['coverage.description'])
        write_section('tasks', 'index.html',
                      tasks_body(catalogues, lang, view),
                      strings['tasks.description'])
        write_section('sources', 'index.html',
                      sources_body(catalogues, lang, view),
                      strings['sources.description'])
        write_section('comparison', 'index.html',
                      comparison_body(catalogues, lang, view),
                      strings['comparison.description'])

        selected = selected_records(base)
        write_section('visualizations', 'index.html',
                      visualizations_index_body(strings, lang, selected),
                      strings['visualizations.description'])
        for record, research in selected:
            record_id = record['id']
            crumb = breadcrumb_trail([
                home_crumb,
                ('index.html', esc(strings['visualizations.h1']), False),
                (None, esc(record.get('title', record_id)), True),
            ])
            (lang_dir / 'visualizations' / f'{record_id}.html').write_text(
                page(catalogues, lang,
                     f'{record.get("title", record_id)} — {strings["visualizations.h1"]} — {title}',
                     visualization_body(strings, lang, record, research), 2,
                     {code: f'../../{code}/visualizations/{record_id}.html' for code in others},
                     strings['visualizations.description'], crumb),
                encoding='utf-8',
            )
        fixture = json.loads((ROOT / SYNTHETIC_FIXTURE).read_text(encoding='utf-8'))
        crumb = breadcrumb_trail([
            home_crumb,
            ('index.html', esc(strings['visualizations.h1']), False),
            (None, esc(strings['visualizations.synthetic_page_title']), True),
        ])
        (lang_dir / 'visualizations' / 'synthetic.html').write_text(
            page(catalogues, lang,
                 f'{strings["visualizations.synthetic_page_title"]} — {title}',
                 synthetic_page_body(strings, lang, fixture, catalogues), 2,
                 {code: f'../../{code}/visualizations/synthetic.html' for code in others},
                 strings['visualizations.synthetic_demo_notice'], crumb),
            encoding='utf-8',
        )

        for country in view['countries']:
            country_code = country['code']
            crumb = breadcrumb_trail([
                home_crumb,
                ('index.html', esc(strings['countries.h1']), False),
                (None, country_name(country, lang), True),
            ])
            (lang_dir / 'countries' / f'{country_code}.html').write_text(
                page(catalogues, lang,
                     f'{country_text(country, lang)} — {title}',
                     country_body(catalogues, lang, view, country), 2,
                     {code: f'../../{code}/countries/{country_code}.html' for code in others},
                     strings['country.description'], crumb),
                encoding='utf-8',
            )

        for domain in view['domains']:
            domain_id = domain['id']
            crumb = breadcrumb_trail([
                home_crumb,
                ('index.html', esc(strings['domains.h1']), False),
                (None, domain_name(domain, lang), True),
            ])
            (lang_dir / 'domains' / f'{domain_id}.html').write_text(
                page(catalogues, lang,
                     f'{domain_text(domain, lang)} — {title}',
                     domain_body(catalogues, lang, view, domain), 2,
                     {code: f'../../{code}/domains/{domain_id}.html' for code in others},
                     strings['domain.description'], crumb),
                encoding='utf-8',
            )

        (lang_dir / 'records').mkdir()
        for record in policies:
            record_id = record['id']
            record_lang = record.get('language', 'en')
            policy_dir = base / 'policies' / record_id
            research = (load_research(policy_dir)
                        if (policy_dir / RESEARCH_FILENAME).is_file() else None)
            crumb = breadcrumb_html(
                strings, '../index.html', record.get('title', record_id), lang != record_lang)
            description = (record.get('notes') if lang == record_lang
                           else strings['record.description'])
            (lang_dir / 'records' / f'{record_id}.html').write_text(
                page(
                    catalogues, lang,
                    f'{record.get("title", record_id)} — {title}',
                    record_body(catalogues, lang, record, base, research),
                    2,
                    {code: f'../../{code}/records/{record_id}.html' for code in others},
                    description,
                    crumb,
                ),
                encoding='utf-8',
            )

        # Publish raw artifacts under language-scoped paths, preserving URLs and provenance.
        artifact_root = lang_dir / 'records' / 'artifacts'
        artifact_root.mkdir()
        for record in policies:
            source = base / 'policies' / record['id']
            if source.exists():
                shutil.copytree(source, artifact_root / record['id'])
    print(f'Built {region}: {len(policies)} research records')


def build_root(region='mena'):
    base = ROOT / 'regions' / region
    cfg = load(base / 'region.json')
    catalogues = load_i18n(base, tuple(cfg['languages']))
    languages = tuple(cfg['languages'])
    default_lang = languages[0]
    default = catalogues[default_lang]
    default_name = LANGUAGE_NAMES[default_lang]
    default_url = f'mena/{default_lang}/'
    alternates = ''.join(
        f'<link rel="alternate" hreflang="{code}" href="mena/{code}/">\n'
        for code in languages
    )
    language_links = ''.join(
        f'<li><a href="mena/{code}/" hreflang="{code}" lang="{code}" '
        f'dir="{direction(code)}">{esc(LANGUAGE_NAMES[code])}</a></li>'
        for code in languages if code != default_lang
    )
    language_cards = ''.join(
        f'<li><a href="mena/{code}/" hreflang="{code}" lang="{code}" dir="{direction(code)}">'
        f'<strong>{esc(LANGUAGE_NAMES[code])}</strong></a></li>'
        for code in languages
    )
    start_rules_url = f'mena/{default_lang}/visualizations/synthetic.html'
    start_research_url = f'mena/{default_lang}/countries/index.html'
    start_method_url = f'mena/{default_lang}/index.html#method'
    supported = json.dumps({code: f'mena/{code}/' for code in languages}, ensure_ascii=False)
    redirect_script = """<script>
(function () {
  var supported = __SUPPORTED__;
  var defaultTarget = supported[__DEFAULT__];
  var requested = new URLSearchParams(location.search).get('lang');
  var candidates = requested ? [requested] : (navigator.languages || [navigator.language || '']);
  var target = null;
  for (var i = 0; i < candidates.length; i += 1) {
    var code = String(candidates[i] || '').toLowerCase().split('-')[0];
    if (supported[code]) { target = supported[code]; break; }
  }
  if (target && (requested || target !== defaultTarget) && !location.hash) {
    location.replace(target);
  }
})();
</script>"""
    redirect_script = (redirect_script
                       .replace('__SUPPORTED__', supported)
                       .replace('__DEFAULT__', json.dumps(default_lang, ensure_ascii=False)))
    (ROOT / 'dist').mkdir(parents=True, exist_ok=True)
    (ROOT / 'dist' / 'index.html').write_text(f"""<!doctype html>
<html lang="{default_lang}" dir="{direction(default_lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(default['root.title'])}</title>
<meta name="description" content="{esc(default['site.description'])}">
{alternates}<link rel="alternate" hreflang="x-default" href="{default_url}">
<link rel="stylesheet" href="mena/assets/site.css">
</head>
<body>
<a class="skip" href="#main">{esc(default['skip'])}</a>
<header class="site-header">
<p class="brand"><a href="{default_url}">{esc(default['site.title'])}</a></p>
<nav class="language" aria-label="{esc(default['nav.language'])}">
<ul>{language_links}</ul>
</nav>
</header>
<main id="main" tabindex="-1">
<h1>{esc(default['root.h1'])}</h1>
<p class="lede">{esc(default['root.summary'])}</p>
<section class="start-here"><h2>{esc(default['root.start_heading'])}</h2>
<p>{esc(default['root.start_body'])}</p>
<ul class="start-paths">
<li><a href="{start_rules_url}"><strong>{esc(default['root.start_rules'])}</strong></a></li>
<li><a href="{start_research_url}"><strong>{esc(default['root.start_research'])}</strong></a></li>
<li><a href="{start_method_url}"><strong>{esc(default['root.start_method'])}</strong></a></li>
</ul></section>
<section><h2>{esc(default['root.choose'])}</h2>
<ul class="language-grid">{language_cards}</ul></section>
<p class="note">{esc(default['root.note'])}</p>
<p><a href="{REPOSITORY_URL}">{esc(default['root.repo'])}</a></p>
</main>
<footer>
<p>{esc(default['footer.note'])}</p>
</footer>
{redirect_script}
</body>
</html>
""", encoding='utf-8')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--region', choices=['mena', 'all'], default='all')
    args = parser.parse_args()
    for region in (['mena'] if args.region == 'all' else [args.region]):
        build(region)
    build_root()


if __name__ == '__main__':
    main()
