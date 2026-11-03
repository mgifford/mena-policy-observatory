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
    from .research import RESEARCH_FILENAME, load_research
except ImportError:  # run as a script
    from research import RESEARCH_FILENAME, load_research

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_URL = 'https://github.com/mgifford/mena-policy-observatory'
WORKFLOW_URL = REPOSITORY_URL + '/blob/main/docs/WORKFLOW.md'
AUDIT_URL = REPOSITORY_URL + '/blob/main/docs/BASELINE-AUDIT.md'
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
TRANSLATION_REVIEW_KEYS = {
    'not_reviewed': 'record.translation.not_reviewed',
    'native_reviewed': 'record.translation.native_reviewed',
}


def esc(value):
    return html.escape(str(value), quote=True)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_i18n(base, languages=('en', 'ar')):
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


def other_language(lang):
    return 'ar' if lang == 'en' else 'en'


def direction(lang):
    return 'rtl' if lang == 'ar' else 'ltr'


def page(catalogues, lang, title, body, depth, alt_href, description,
         breadcrumb_html=''):
    strings = catalogues[lang]
    prefix = '../' * depth
    home_href = ('../' * (depth - 1)) + 'index.html'
    root_href = prefix + '../index.html'
    lang_other = other_language(lang)
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
<link rel="alternate" hreflang="{lang_other}" href="{esc(alt_href)}">
<link rel="alternate" hreflang="x-default" href="{esc(root_href)}">
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
<li><a href="{home_href}#records">{esc(strings['nav.records'])}</a></li>
<li><a href="{REPOSITORY_URL}">{esc(strings['nav.repository'])}</a></li>
</ul>
</nav>
<nav class="language" aria-label="{esc(strings['nav.language'])}">
<a href="{esc(alt_href)}" hreflang="{lang_other}" lang="{lang_other}" dir="{direction(lang_other)}">{esc(strings['nav.language_other'])}</a>
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


def home_body(catalogues, lang, cfg, policies, countries):
    strings = catalogues[lang]
    records = len(policies)
    covered = len({record.get('country') for record in policies})
    total = len(countries)
    encoded = sum(1 for record in policies
                  if record.get('execution_status') not in
                  (None, 'not_implemented', 'scaffold', 'not_encoded'))
    reviewed = sum(1 for record in policies
                   if record.get('legal_effect') in ('binding_confirmed', 'nonbinding_confirmed'))
    country_names = {country['code']: country['name'] for country in countries}

    parts = [
        f'<h1>{esc(cfg["title"][lang])}</h1>',
        f'<p class="lede">{esc(strings["home.lede"])}</p>',
        f'<section><h2>{esc(strings["home.what.heading"])}</h2>'
        f'<p>{esc(strings["home.what.body"])}</p></section>',
        f'<section><h2>{esc(strings["home.why.heading"])}</h2>'
        f'<p>{esc(strings["home.why.body"])}</p><ul>'
        f'<li>{esc(strings["home.why.item1"])}</li>'
        f'<li>{esc(strings["home.why.item2"])}</li>'
        f'<li>{esc(strings["home.why.item3"])}</li></ul></section>',
        f'<section><h2>{esc(strings["home.pilot.heading"])}</h2>'
        f'<p>{esc(t(strings, "home.pilot.body", records=records, covered=covered, total=total))}</p></section>',
        f'<section><h2>{esc(strings["home.ric.heading"])}</h2>'
        f'<p>{esc(strings["home.ric.body1"])}</p>'
        f'<p>{esc(strings["home.ric.body2"])}</p>',
        f'<p class="notice">{esc(strings["home.ric.certification"])}</p>',
    ]
    if lang != 'en':
        parts.append(
            f'<p class="terms">{esc(strings["home.ric.english_terms"])}: '
            f'<span lang="en" dir="ltr">Rules as Code · Axiom · RuleSpec</span></p>'
        )
    parts.append('</section>')

    steps = ('source', 'clause', 'interpretation', 'candidate', 'test', 'review')
    step_items = ''.join(
        f'<li><strong>{esc(strings[f"home.step.{key}.title"])}</strong> '
        f'<span>{esc(strings[f"home.step.{key}.body"])}</span></li>'
        for key in steps
    )
    parts.append(
        f'<section id="method"><h2>{esc(strings["home.pipeline.heading"])}</h2>'
        f'<p>{esc(strings["home.pipeline.intro"])}</p>'
        f'<ol class="steps">{step_items}</ol></section>'
    )

    claims = ''.join(f'<li>{esc(strings[f"home.claims.item{index}"])}</li>' for index in range(1, 6))
    parts.append(
        f'<section><h2>{esc(strings["home.missing.heading"])}</h2>'
        f'<p>{esc(strings["home.missing.body"])}</p></section>'
        f'<section><h2>{esc(strings["home.claims.heading"])}</h2><ul>{claims}</ul></section>'
    )

    status_items = [
        t(strings, 'home.status.records', records=records),
        t(strings, 'home.status.coverage', covered=covered, total=total),
        t(strings, 'home.status.rules', encoded=encoded, records=records),
        t(strings, 'home.status.review', reviewed=reviewed, records=records),
        strings['home.status.arabic'],
    ]
    parts.append(
        f'<section><h2>{esc(strings["home.status.heading"])}</h2><ul>'
        + ''.join(f'<li>{esc(item)}</li>' for item in status_items)
        + '</ul></section>'
    )

    rows = []
    for record in policies:
        record_id = record['id']
        title = foreign(record.get('title', record_id), lang)
        country = foreign(country_names.get(record.get('country'), record.get('country', '')), lang)
        standard = foreign(record.get('standard') or '—', lang)
        legal = esc(label(strings, LEGAL_STATUS_KEYS, record.get('legal_effect')))
        rows.append(
            f'<tr><th scope="row">{title}</th><td>{country}</td><td>{standard}</td>'
            f'<td>{legal}</td><td><a href="records/{esc(record_id)}.html">'
            f'{esc(strings["home.comparison.link"])}</a></td></tr>'
        )
    parts.append(
        f'<section id="records"><h2>{esc(strings["home.comparison.heading"])}</h2>'
        f'<p>{esc(strings["home.comparison.intro"])}</p>'
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["home.comparison.heading"])}" tabindex="0">'
        f'<table><caption>{esc(strings["home.comparison.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["home.table.document"])}</th>'
        f'<th scope="col">{esc(strings["home.table.jurisdiction"])}</th>'
        f'<th scope="col">{esc(strings["home.table.standard"])}</th>'
        f'<th scope="col">{esc(strings["home.table.legal"])}</th>'
        f'<th scope="col">{esc(strings["home.table.evidence"])}</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>'
    )

    coverage_rows = []
    for country in countries:
        count = sum(1 for record in policies if record.get('country') == country['code'])
        status = strings['home.coverage.status'] if count else strings['home.coverage.none']
        coverage_rows.append(
            f'<tr><th scope="row">{foreign(country["name"], lang)}</th>'
            f'<td>{count}</td><td>{esc(status)}</td></tr>'
        )
    parts.append(
        f'<section><h2>{esc(strings["home.coverage.heading"])}</h2>'
        f'<div class="table-scroll" role="region" aria-label="{esc(strings["home.coverage.heading"])}" tabindex="0">'
        f'<table><caption>{esc(strings["home.coverage.caption"])}</caption><thead><tr>'
        f'<th scope="col">{esc(strings["home.table.jurisdiction"])}</th>'
        f'<th scope="col">{esc(strings["home.table.records"])}</th>'
        f'<th scope="col">{esc(strings["home.coverage.status_heading"])}</th>'
        f'</tr></thead><tbody>{"".join(coverage_rows)}</tbody></table></div></section>'
    )

    domains = ''.join(f'<li>{esc(value[lang])}</li>' for value in cfg['domain_labels'].values())
    parts.append(
        f'<section><h2>{esc(strings["home.domains.heading"])}</h2>'
        f'<p>{esc(strings["home.domains.note"])}</p><ul>{domains}</ul></section>'
    )

    parts.append(
        f'<section><h2>{esc(strings["home.resources.heading"])}</h2><ul>'
        f'<li><a href="{WORKFLOW_URL}">{esc(strings["home.resources.method"])}</a></li>'
        f'<li><a href="{AUDIT_URL}">{esc(strings["home.resources.audit"])}</a></li>'
        f'<li><a href="{REPOSITORY_URL}">{esc(strings["home.resources.repo"])}</a></li>'
        f'<li><a href="{ESCWA_URL}">{esc(strings["home.resources.escwa"])}</a>'
        f' {esc(strings["home.resources.escwa_note"])}</li>'
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


def build(region):
    base = ROOT / 'regions' / region
    out = ROOT / 'dist' / region
    if out.exists():
        shutil.rmtree(out)
    (out / 'assets').mkdir(parents=True)
    (out / 'assets' / 'site.css').write_text((ROOT / 'framework' / 'site.css').read_text())

    cfg = load(base / 'region.json')
    policies = load(base / 'data' / 'policies.json')
    countries = load(base / 'data' / 'countries.json')
    catalogues = load_i18n(base, tuple(cfg['languages']))

    for lang in cfg['languages']:
        lang_dir = out / lang
        lang_dir.mkdir()
        title = cfg['title'][lang]
        strings = catalogues[lang]
        alt_href = f'../{other_language(lang)}/'
        body = home_body(catalogues, lang, cfg, policies, countries)
        (lang_dir / 'index.html').write_text(
            page(catalogues, lang, strings['home.title'], body, 1, alt_href,
                 strings['home.description']),
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
                    f'../../{other_language(lang)}/records/{record_id}.html',
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
    en, ar = catalogues['en'], catalogues['ar']
    (ROOT / 'dist').mkdir(parents=True, exist_ok=True)
    (ROOT / 'dist' / 'index.html').write_text(f"""<!doctype html>
<html lang="en" dir="ltr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(en['root.title'])}</title>
<meta name="description" content="{esc(en['site.description'])}">
<link rel="alternate" hreflang="en" href="mena/en/">
<link rel="alternate" hreflang="ar" href="mena/ar/">
<link rel="stylesheet" href="mena/assets/site.css">
</head>
<body>
<a class="skip" href="#main">{esc(en['skip'])}</a>
<header class="site-header">
<p class="brand"><a href="mena/en/">{esc(en['site.title'])}</a></p>
<nav class="site-nav" aria-label="{esc(en['nav.label'])}">
<ul>
<li><a href="mena/en/">{esc(en['nav.home'])}</a></li>
<li><a href="mena/en/#method">{esc(en['nav.method'])}</a></li>
<li><a href="mena/en/#records">{esc(en['nav.records'])}</a></li>
<li><a href="{REPOSITORY_URL}">{esc(en['nav.repository'])}</a></li>
</ul>
</nav>
<nav class="language" aria-label="{esc(en['nav.language'])}">
<a href="mena/ar/" hreflang="ar" lang="ar" dir="rtl">{esc(en['nav.language_other'])}</a>
</nav>
</header>
<main id="main" tabindex="-1">
<h1>{esc(en['root.h1'])}</h1>
<p class="lede">{esc(en['root.summary'])}</p>
<h2>{esc(en['root.choose'])}</h2>
<p><a href="mena/en/">{esc(en['root.continue_english'])}</a></p>
<section lang="ar" dir="rtl">
<h2>{esc(ar['root.h1'])}</h2>
<p>{esc(ar['root.summary'])}</p>
<p><a href="mena/ar/">{esc(ar['root.continue_arabic'])}</a></p>
</section>
<p class="note">{esc(en['root.note'])}</p>
<p><a href="{REPOSITORY_URL}">{esc(en['root.repo'])}</a></p>
</main>
<footer>
<p>{esc(en['footer.note'])}</p>
</footer>
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
