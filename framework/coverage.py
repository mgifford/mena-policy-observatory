#!/usr/bin/env python3
"""Research coverage registries and status derivation.

This module joins the repository's published research records with the
toolkit's candidate-source inventory and task queue. It never promotes a
candidate lead into a verified source and never derives a legal finding from
missing data.

The status vocabulary is deliberately about research activity, not compliance:

- not_started
- source_discovery
- candidate_sources_identified
- evidence_captured
- provision_extraction
- legal_review_pending
- reviewed_findings
- blocked

A status is always derived from recorded evidence. An empty country or domain
page means only that this repository has no recorded research yet.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import json
import re

RESEARCH_STATUSES = (
    'not_started',
    'source_discovery',
    'candidate_sources_identified',
    'evidence_captured',
    'provision_extraction',
    'legal_review_pending',
    'reviewed_findings',
    'blocked',
)
STATUS_RANK = {status: index for index, status in enumerate(RESEARCH_STATUSES)}

TASK_STATUSES = ('unstarted', 'in_progress', 'blocked', 'complete', 'cancelled')
TASK_STAGES = (
    'source_discovery', 'capture', 'transcription', 'provision_extraction',
    'interpretation', 'challenge', 'review', 'publication', 'formalization',
)
CANDIDATE_SOURCE_TYPES = (
    'official_instrument',
    'official_index',
    'official_summary',
    'official_ministry_policy_listing',
    'official_ministry_policy_index',
    'official_ministry_explainer',
    'official_legislative_publication',
    'official_regulator_legal_index',
    'official_legislation_index',
    'official_government_explainer_not_statute',
    'official_ministry_explainer_not_statute',
    'official_agency_accessibility_statement',
    'secondary',
    'unknown',
)
CAPTURE_STATUSES = ('not_captured', 'captured', 'verified')
VERIFICATION_REQUIREMENTS = (
    'official_source',
    'legal_scope',
    'language',
    'publication_permissions',
)
CANDIDATE_RELATIONS = ('amends', 'related', 'implements', 'consolidates')
TASK_FILES = ('tasks.jsonl', 'cross-domain-tasks.jsonl', 'tasks-tranche-02.jsonl')
PUBLISHER_AUTHORITY_TYPES = (
    'unknown', 'gazette', 'legislation_portal', 'parliament', 'ministry',
    'regulator', 'intergovernmental_index', 'standards_body', 'other',
)
PUBLISHER_VERIFICATION_STATUSES = ('unverified', 'reviewed', 'disputed')
PUBLISHER_MONITORING_STATES = ('not_configured', 'manual', 'scheduled')
RETRIEVAL_STATUSES = ('not_attempted', 'success', 'failed', 'blocked', 'unknown')
RETRIEVAL_ERROR_CATEGORIES = (
    'timeout', 'dns', 'tls', 'http_error', 'blocked', 'unsupported_content', 'other',
)
FRESHNESS_STATES = ('not_established', 'within_interval', 'interval_exceeded', 'unknown')
LEGAL_VERIFICATION_STATUSES = ('unreviewed', 'in_review', 'verified', 'disputed', 'superseded')
DEFAULT_STALE_AFTER_DAYS = 180
INSTRUMENT_TYPES = (
    'unknown', 'law', 'act', 'decree_law', 'decision', 'regulation', 'ordinance',
)
INSTRUMENT_DATE_KEYS = ('adoption', 'commencement', 'expiry', 'repeal', 'consolidation')
CONFIRMED_LEGAL_EFFECT = ('binding_confirmed', 'nonbinding_confirmed')
LEGACY_RECORD_STATUSES = ('not_assessed', 'source_verified', 'source_identified', 'identified')
REQUIRED_DISPLAY_CHECKS = (
    'https_scheme',
    'no_credentials',
    'hostname_not_ip',
    'no_personal_data_fields',
    'link_only_no_text_reproduced',
)
SENSITIVE_KEYS = (
    'case_history', 'personal_data', 'patient', 'health_detail',
    'immigration_record', 'surveillance_target', 'home_address', 'phone',
    'email_address', 'national_id', 'passport_number',
)
ISO_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
COUNTRY_CODE = re.compile(r'^[A-Z]{2}$')
STALE_AFTER = timedelta(days=365)

DEFAULT_BASE = Path(__file__).resolve().parents[1] / 'regions' / 'mena'
DEFAULT_TOOLKIT = Path(__file__).resolve().parents[1] / 'research-toolkit'


@dataclass
class CoverageData:
    base: Path
    toolkit: Path
    countries: list[dict]
    groups: list[dict]
    domains: list[dict]
    policies: list[dict]
    region_config: dict
    research: dict[str, dict]
    tasks: list[dict]
    candidate_inventory: dict
    proposed_scope: dict
    instruments: list[dict] = field(default_factory=list)
    publishers: list[dict] = field(default_factory=list)
    source_checks: list[dict] = field(default_factory=list)
    registry_as_of: str = ''
    stale_after_days: int = DEFAULT_STALE_AFTER_DAYS
    extra: dict = field(default_factory=dict)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def load_coverage(base=DEFAULT_BASE, toolkit=DEFAULT_TOOLKIT) -> CoverageData:
    """Load the registries, records, candidate leads and task queue."""
    base = Path(base)
    toolkit = Path(toolkit)
    domain_registry = _read_json(base / 'data' / 'domains.json')
    countries = _read_json(base / 'data' / 'countries.json')
    policies = _read_json(base / 'data' / 'policies.json')
    region_config = _read_json(base / 'region.json')
    research = {}
    for policy in policies:
        path = base / 'policies' / str(policy.get('id')) / 'research.json'
        if path.is_file():
            research[str(policy.get('id'))] = _read_json(path)
    tasks = []
    for name in TASK_FILES:
        for task in _read_jsonl(toolkit / 'backlog' / name):
            tasks.append(task)
    candidate_inventory = _read_json(toolkit / 'sources' / 'candidate-sources.json')
    instruments_doc = _read_json(toolkit / 'sources' / 'instruments.json') \
        if (toolkit / 'sources' / 'instruments.json').is_file() else {'instruments': []}
    publishers_doc = _read_json(toolkit / 'sources' / 'publishers.json') \
        if (toolkit / 'sources' / 'publishers.json').is_file() else {'publishers': []}
    checks_doc = _read_json(toolkit / 'sources' / 'source-checks.json') \
        if (toolkit / 'sources' / 'source-checks.json').is_file() else {'checks': []}
    proposed_path = toolkit / 'backlog' / 'jurisdictions-proposed.json'
    proposed_scope = _read_json(proposed_path) if proposed_path.is_file() else {'entries': []}
    return CoverageData(
        base=base,
        toolkit=toolkit,
        countries=countries,
        groups=domain_registry.get('groups', []),
        domains=domain_registry.get('domains', []),
        policies=policies,
        region_config=region_config,
        research=research,
        tasks=tasks,
        candidate_inventory=candidate_inventory,
        proposed_scope=proposed_scope,
        instruments=instruments_doc.get('instruments', []),
        publishers=publishers_doc.get('publishers', []),
        source_checks=checks_doc.get('checks', []),
        registry_as_of=str(checks_doc.get('as_of') or ''),
        stale_after_days=checks_doc.get('stale_after_days', DEFAULT_STALE_AFTER_DAYS),
        extra={'domain_registry': domain_registry},
    )


def normalized_task_id(task_id) -> str:
    """Collapse separators so duplicate logical IDs are detectable."""
    return re.sub(r'[^A-Za-z0-9]+', '-', str(task_id)).strip('-').upper()


def safe_url(value) -> bool:
    """A conservative URL check for public candidate metadata."""
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.scheme != 'https' or not parsed.netloc:
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname or ''
    if not host or re.fullmatch(r'[0-9.]+', host) or ':' in host:
        return False
    return True


def _host_of(url) -> str:
    if not isinstance(url, str):
        return ''
    return (urlparse(url).hostname or '').lower()


def publisher_slug(host: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', str(host).lower()).strip('-')


def freshness_state(check, as_of, stale_after_days) -> str:
    """Derive freshness from the last successful retrieval, never from a failure."""
    if not check:
        return 'not_established'
    success = _iso_date(check.get('last_successful_retrieval'))
    if success is None:
        return 'not_established'
    if as_of is None or success > as_of:
        return 'unknown'
    if (as_of - success).days > stale_after_days:
        return 'interval_exceeded'
    return 'within_interval'


def _iso_date(value):
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _candidate_view(candidate):
    display = candidate.get('display_review') if isinstance(candidate.get('display_review'), dict) else {}
    checks = display.get('checks') if isinstance(display.get('checks'), list) else []
    return {
        **candidate,
        'displayable': (
            safe_url(candidate.get('source_url'))
            and all(check in checks for check in REQUIRED_DISPLAY_CHECKS)
            and isinstance(display.get('human_reviewed'), bool)
        ),
        'display_review': display,
    }


def recorded_review(research: dict | None) -> dict | None:
    """Return the record-level review entry only when it is complete.

    The presence of a review object is not enough: a review is recorded only
    with a reviewer, a date and a stated scope. An absent or partial review
    leaves the record unreviewed rather than inferred from silence.
    """
    review = (research or {}).get('review')
    if not isinstance(review, dict) or review.get('status') != 'reviewed':
        return None
    for key in ('reviewer', 'scope'):
        if not isinstance(review.get(key), str) or not review[key].strip():
            return None
    if not _iso_date(review.get('reviewed_at')):
        return None
    return review


def record_is_reviewed(policy: dict, research: dict | None) -> bool:
    """A record is reviewed with a confirmed effect, a recorded review and no open questions.

    The status vocabulary calls ``reviewed_findings`` a review outcome, so the
    gate requires recorded review evidence. Absence of interpretation questions
    is not by itself review evidence.
    """
    if policy.get('legal_effect') not in CONFIRMED_LEGAL_EFFECT:
        return False
    if recorded_review(research) is None:
        return False
    questions = (research or {}).get('interpretations') or []
    return not any(question.get('status') != 'resolved' for question in questions)


def cell_status(data: CoverageData, code: str, domain_id: str) -> str:
    """Derive one country/domain cell from recorded evidence only."""
    records = [policy for policy in data.policies
               if policy.get('country') == code and policy.get('topic') == domain_id]
    if records:
        if all(record_is_reviewed(policy, data.research.get(str(policy.get('id')))) for policy in records):
            return 'reviewed_findings'
        research = [data.research.get(str(policy.get('id'))) or {} for policy in records]
        if any(item.get('provisions') for item in research):
            if any(item.get('interpretations') for item in research):
                return 'legal_review_pending'
            return 'provision_extraction'
        return 'evidence_captured'
    candidates = [candidate for candidate in data.candidate_inventory.get('records', [])
                  if candidate.get('jurisdiction') == code and domain_id in (candidate.get('domains') or [])]
    if candidates:
        return 'candidate_sources_identified'
    tasks = [task for task in data.tasks
             if task.get('jurisdiction') == code and task.get('domain') == domain_id]
    if any(task.get('status') == 'blocked' for task in tasks):
        return 'blocked'
    if any(task.get('status') == 'in_progress' for task in tasks):
        return 'source_discovery'
    return 'not_started'


def _status_from(statuses) -> str:
    values = list(statuses) or ['not_started']
    return max(values, key=lambda status: STATUS_RANK.get(status, 0))


def country_status(data: CoverageData, code: str, domain_ids) -> str:
    statuses = [cell_status(data, code, domain_id) for domain_id in domain_ids]
    tasks = [task for task in data.tasks if task.get('jurisdiction') == code]
    if any(task.get('status') == 'in_progress' for task in tasks):
        statuses.append('source_discovery')
    if any(task.get('status') == 'blocked' for task in tasks):
        statuses.append('blocked')
    return _status_from(statuses)


def domain_status(data: CoverageData, domain_id: str, codes) -> str:
    statuses = [cell_status(data, code, domain_id) for code in codes]
    tasks = [task for task in data.tasks if task.get('domain') == domain_id]
    if any(task.get('status') == 'in_progress' for task in tasks):
        statuses.append('source_discovery')
    if any(task.get('status') == 'blocked' for task in tasks):
        statuses.append('blocked')
    return _status_from(statuses)


def _latest_review(records) -> str | None:
    dates = []
    for record in records:
        match = re.match(r'^(\d{4}-[0-9]{2}-[0-9]{2})', str(record.get('reviewed_on') or ''))
        if match and _iso_date(match.group(1)):
            dates.append(match.group(1))
    return max(dates) if dates else None


def _open_questions(data: CoverageData, records, candidates) -> list[dict]:
    items = []
    for record in records:
        research = data.research.get(str(record.get('id'))) or {}
        for question in research.get('interpretations') or []:
            if question.get('status') == 'resolved':
                continue
            items.append({
                'kind': 'record',
                'record_id': record.get('id'),
                'record_title': record.get('title'),
                'id': question.get('id'),
                'text': question.get('statement'),
                'risk': question.get('risk'),
                'requires': question.get('requires'),
                'language': 'en',
            })
    for candidate in candidates:
        if candidate.get('research_question'):
            items.append({
                'kind': 'candidate',
                'candidate_id': candidate.get('id'),
                'id': candidate.get('id'),
                'text': candidate.get('research_question'),
                'language': 'en',
                'source_url': candidate.get('source_url'),
            })
    return items


def build_view(data: CoverageData) -> dict:
    """Build the deterministic view model used by the static generator."""
    domain_order = {domain['id']: index for index, domain in enumerate(data.domains)}
    candidates = [candidate for candidate in (
        _candidate_view(item) for item in data.candidate_inventory.get('records', []))
        if candidate['displayable']]
    candidates.sort(key=lambda candidate: (str(candidate.get('jurisdiction')),
                                           str(candidate.get('id'))))
    tasks = list(data.tasks)
    tasks_by_candidate = {}
    for task in tasks:
        for lead in task.get('source_lead_ids') or []:
            tasks_by_candidate.setdefault(lead, []).append(str(task.get('task_id')))
    for candidate in candidates:
        candidate['task_ids'] = sorted(tasks_by_candidate.get(candidate.get('id'), []))
    instruments_by_candidate = {instrument.get('candidate_id'): instrument
                                for instrument in data.instruments}
    publishers_by_host = {publisher.get('host'): publisher for publisher in data.publishers}
    checks_by_candidate = {check.get('candidate_id'): check for check in data.source_checks}
    as_of = _iso_date(data.registry_as_of)
    for candidate in candidates:
        host = (urlparse(str(candidate.get('source_url') or '')).hostname or '').lower()
        check = checks_by_candidate.get(candidate.get('id'))
        candidate['instrument'] = instruments_by_candidate.get(candidate.get('id'))
        candidate['publisher'] = publishers_by_host.get(host)
        candidate['source_check'] = check
        candidate['retrieval_status'] = (check or {}).get('retrieval_status', 'not_attempted')
        candidate['freshness'] = freshness_state(check, as_of, data.stale_after_days)
        candidate['legal_verification'] = ((check or {}).get('legal_verification')
                                           or {'status': 'unreviewed', 'evidence': None,
                                               'reviewed_at': None})

    records_view = []
    for policy in data.policies:
        research = data.research.get(str(policy.get('id'))) or {}
        records_view.append({
            'policy': policy,
            'provisions': research.get('provisions') or [],
        })

    country_views = []
    for country in data.countries:
        code = country.get('code')
        records = [policy for policy in data.policies if policy.get('country') == code]
        country_candidates = [candidate for candidate in candidates
                              if candidate.get('jurisdiction') == code]
        country_tasks = [task for task in tasks if task.get('jurisdiction') == code]
        referenced = set()
        referenced.update(policy.get('topic') for policy in records if policy.get('topic'))
        for candidate in country_candidates:
            referenced.update(candidate.get('domains') or [])
        referenced.update(task.get('domain') for task in country_tasks if task.get('domain'))
        referenced_domains = sorted(referenced, key=lambda item: domain_order.get(item, 999))
        country_views.append({
            **country,
            'records': records,
            'candidates': country_candidates,
            'tasks': country_tasks,
            'open_questions': _open_questions(data, records, country_candidates),
            'latest_review': _latest_review(records),
            'latest_discovery': (data.candidate_inventory.get('research_date')
                                 if country_candidates else None),
            'status': country_status(data, code, list(domain_order)),
            'domains': [
                {'id': domain_id, 'status': cell_status(data, code, domain_id)}
                for domain_id in referenced_domains
            ],
        })

    domain_views = []
    for domain in data.domains:
        domain_id = domain.get('id')
        records = [policy for policy in data.policies if policy.get('topic') == domain_id]
        domain_candidates = [candidate for candidate in candidates
                             if domain_id in (candidate.get('domains') or [])]
        domain_tasks = [task for task in tasks if task.get('domain') == domain_id]
        domain_views.append({
            **domain,
            'records': records,
            'candidates': domain_candidates,
            'tasks': domain_tasks,
            'open_questions': _open_questions(data, records, domain_candidates),
            'status': domain_status(data, domain_id, [country.get('code') for country in data.countries]),
        })

    matrix = []
    for country in country_views:
        matrix.append({
            'country': country,
            'cells': [
                {'domain_id': domain.get('id'), 'status': cell_status(data, country.get('code'), domain.get('id'))}
                for domain in data.domains
            ],
        })

    return {
        'countries': country_views,
        'domains': domain_views,
        'groups': data.groups,
        'matrix': matrix,
        'records': records_view,
        'tasks': tasks,
        'candidates': candidates,
        'registry_as_of': data.registry_as_of,
        'stale_after_days': data.stale_after_days,
        'totals': {
            'countries': len(country_views),
            'domains': len(domain_views),
            'records': len(records_view),
            'candidates': len(candidates),
            'tasks': len(tasks),
            'instruments': len(data.instruments),
            'publishers': len(data.publishers),
            'source_checks': len(data.source_checks),
            'unresolved_questions': sum(len(item['open_questions']) for item in country_views),
        },
    }


def _error(errors: list[str], message: str):
    errors.append(message)


def validate_coverage(data: CoverageData) -> list[str]:
    """Validate the coverage registries and their cross-file references."""
    errors: list[str] = []
    codes = []
    country_map = {}
    for country in data.countries:
        code = country.get('code')
        label = str(code)
        if not isinstance(code, str) or not COUNTRY_CODE.match(code):
            _error(errors, f'country {label}: code must be two uppercase letters')
        codes.append(code)
        country_map[code] = country
        for key in ('name', 'group'):
            if not isinstance(country.get(key), str) or not country.get(key).strip():
                _error(errors, f'country {label}: {key} must be a nonempty string')
        for language in ('ar', 'fr'):
            for key in (f'name_{language}', f'group_{language}', f'scope_note_{language}'):
                if not isinstance(country.get(key), str) or not country.get(key).strip():
                    _error(errors, f'country {label}: {key} must be a nonempty string')
                if country.get(f'{key}_status') not in ('provisional', 'reviewed'):
                    _error(errors, f'country {label}: {key}_status must be provisional or reviewed')
            note_key = f'jurisdiction_note_{language}'
            if country.get('jurisdiction_note'):
                if not isinstance(country.get(note_key), str) or not country[note_key].strip():
                    _error(errors, f'country {label}: {note_key} is required '
                                   f'when jurisdiction_note is set')
                if country.get(f'{note_key}_status') not in ('provisional', 'reviewed'):
                    _error(errors, f'country {label}: {note_key}_status must be '
                                   f'provisional or reviewed')
            elif country.get(note_key):
                _error(errors, f'country {label}: {note_key} is set without jurisdiction_note')
        if country.get('in_scope') is not True:
            _error(errors, f'country {label}: in_scope must be true for a listed entry')
        if country.get('status') not in LEGACY_RECORD_STATUSES:
            _error(errors, f'country {label}: unexpected legacy status {country.get("status")!r}')
        published = sum(1 for policy in data.policies if policy.get('country') == code)
        if country.get('reviewed_policy_records') != published:
            _error(errors, f'country {label}: reviewed_policy_records is '
                           f'{country.get("reviewed_policy_records")!r} but {published} records are listed')
    duplicates = sorted({code for code in codes if codes.count(code) > 1})
    for code in duplicates:
        _error(errors, f'country {code}: duplicate code')

    proposed = data.proposed_scope.get('entries') or []
    proposed_codes = {entry.get('code') for entry in proposed}
    if proposed_codes != set(codes):
        missing = sorted(proposed_codes - set(codes))
        extra = sorted(set(codes) - proposed_codes)
        _error(errors, f'jurisdiction reconciliation: missing proposed entries {missing}; '
                       f'undocumented additions {extra}')
    for entry in proposed:
        code = entry.get('code')
        country = country_map.get(code)
        if not country:
            continue
        if entry.get('name') != country.get('name'):
            if country.get('reconciled_from_name') != entry.get('name'):
                _error(errors, f'country {code}: proposed name {entry.get("name")!r} differs '
                               f'from {country.get("name")!r} without reconciled_from_name')

    group_ids = []
    for group in data.groups:
        group_id = group.get('id')
        group_ids.append(group_id)
        for language in ('en', 'ar', 'fr'):
            key = f'label_{language}'
            if not isinstance(group.get(key), str) or not group.get(key).strip():
                _error(errors, f'domain group {group_id}: {key} must be a nonempty string')
            if language != 'en' and group.get(f'{key}_status') not in ('provisional', 'reviewed'):
                _error(errors, f'domain group {group_id}: {key}_status must be provisional or reviewed')
    for group_id in sorted({item for item in group_ids if group_ids.count(item) > 1}):
        _error(errors, f'domain group {group_id}: duplicate id')

    domain_ids = []
    for domain in data.domains:
        domain_id = domain.get('id')
        domain_ids.append(domain_id)
        if not domain_id:
            _error(errors, 'domain: missing id')
        if domain.get('group') not in group_ids:
            _error(errors, f'domain {domain_id}: unknown group {domain.get("group")!r}')
        for language in ('en', 'ar', 'fr'):
            key = f'label_{language}'
            if not isinstance(domain.get(key), str) or not domain.get(key).strip():
                _error(errors, f'domain {domain_id}: {key} must be a nonempty string')
            if language != 'en' and domain.get(f'{key}_status') not in ('provisional', 'reviewed'):
                _error(errors, f'domain {domain_id}: {key}_status must be provisional or reviewed')
        subtopic_ids = []
        for subtopic in domain.get('subtopics') or []:
            subtopic_ids.append(subtopic.get('id'))
            for language in ('en', 'ar', 'fr'):
                key = f'label_{language}'
                if not isinstance(subtopic.get(key), str) or not subtopic.get(key).strip():
                    _error(errors, f'domain {domain_id} subtopic {subtopic.get("id")}: '
                                   f'{key} must be a nonempty string')
                if language != 'en' and \
                        subtopic.get(f'{key}_status') not in ('provisional', 'reviewed'):
                    _error(errors, f'domain {domain_id} subtopic {subtopic.get("id")}: '
                                   f'{key}_status must be provisional or reviewed')
        for subtopic_id in sorted({item for item in subtopic_ids if subtopic_ids.count(item) > 1}):
            _error(errors, f'domain {domain_id}: duplicate subtopic {subtopic_id}')
    for domain_id in sorted({item for item in domain_ids if domain_ids.count(item) > 1}):
        _error(errors, f'domain {domain_id}: duplicate id')

    region_labels = data.region_config.get('domain_labels') or {}
    domain_map = {domain.get('id'): domain for domain in data.domains}
    for domain_id, labels in region_labels.items():
        domain = domain_map.get(domain_id)
        if not domain:
            _error(errors, f'region domain_labels: unknown domain {domain_id!r}')
            continue
        if labels.get('en') != domain.get('label_en'):
            _error(errors, f'region domain_labels: {domain_id} English label differs from domains.json')
        for language in ('ar', 'fr'):
            if labels.get(language) != domain.get(f'label_{language}'):
                _error(errors, f'region domain_labels: {domain_id} {language} label '
                               f'differs from domains.json')

    policy_ids = []
    for policy in data.policies:
        policy_id = policy.get('id')
        policy_ids.append(policy_id)
        if policy.get('country') not in country_map:
            _error(errors, f'policy {policy_id}: unknown country {policy.get("country")!r}')
        if policy.get('topic') not in domain_map:
            _error(errors, f'policy {policy_id}: unknown domain {policy.get("topic")!r}')
        if not str(policy.get('source_url', '')).startswith('https://'):
            _error(errors, f'policy {policy_id}: source_url must be https')
        research = data.research.get(str(policy_id))
        review = (research or {}).get('review')
        if review is not None:
            if not isinstance(review, dict):
                _error(errors, f'policy {policy_id}: review must be an object')
            elif review.get('status') not in ('pending', 'reviewed'):
                _error(errors, f'policy {policy_id}: review.status must be pending or reviewed')
            elif review.get('status') == 'reviewed' and recorded_review(research) is None:
                _error(errors, f'policy {policy_id}: a reviewed record needs a reviewer, '
                               f'an ISO reviewed_at and a stated scope')
        if policy.get('legal_effect') in CONFIRMED_LEGAL_EFFECT and recorded_review(research) is None:
            _error(errors, f'policy {policy_id}: a confirmed legal effect needs a complete '
                           f'recorded review; coverage will not infer one from silence')
    for policy_id in sorted({item for item in policy_ids if policy_ids.count(item) > 1}):
        _error(errors, f'policy {policy_id}: duplicate id')

    candidate_ids = []
    candidate_map = {}
    for candidate in data.candidate_inventory.get('records', []):
        candidate_id = candidate.get('id')
        candidate_ids.append(candidate_id)
        candidate_map[candidate_id] = candidate
        if not candidate_id:
            _error(errors, 'candidate source: missing id')
        if candidate.get('jurisdiction') not in country_map:
            _error(errors, f'candidate {candidate_id}: unknown jurisdiction '
                           f'{candidate.get("jurisdiction")!r}')
        domains = candidate.get('domains')
        if not isinstance(domains, list) or not domains:
            _error(errors, f'candidate {candidate_id}: domains must be a nonempty array')
        else:
            for domain_id in domains:
                if domain_id not in domain_map:
                    _error(errors, f'candidate {candidate_id}: unknown domain {domain_id!r}')
        if not safe_url(candidate.get('source_url')):
            _error(errors, f'candidate {candidate_id}: source_url must be a safe https URL')
        if candidate.get('source_type') not in CANDIDATE_SOURCE_TYPES:
            _error(errors, f'candidate {candidate_id}: unknown source_type '
                           f'{candidate.get("source_type")!r}')
        if candidate.get('legal_effect') != 'not_assessed':
            _error(errors, f'candidate {candidate_id}: legal_effect may not be promoted in a candidate record')
        if candidate.get('capture_status') not in CAPTURE_STATUSES:
            _error(errors, f'candidate {candidate_id}: unknown capture_status '
                           f'{candidate.get("capture_status")!r}')
        if candidate.get('capture_status') != 'not_captured':
            if not _iso_date(candidate.get('captured_at')):
                _error(errors, f'candidate {candidate_id}: a captured source needs an ISO captured_at')
            if not SHA256.match(str(candidate.get('sha256', ''))):
                _error(errors, f'candidate {candidate_id}: a captured source needs a SHA-256')
        if not isinstance(candidate.get('research_question'), str) or \
                len(candidate.get('research_question').strip()) < 12:
            _error(errors, f'candidate {candidate_id}: research_question is too short')
        published = candidate.get('published_date_reported')
        if published not in (None, 'unknown') and not _iso_date(published):
            _error(errors, f'candidate {candidate_id}: published_date_reported must be an ISO date, '
                           f'unknown or absent')
        for key in SENSITIVE_KEYS:
            if key in candidate:
                _error(errors, f'candidate {candidate_id}: sensitive field {key!r} is not allowed')
        display = candidate.get('display_review')
        if not isinstance(display, dict):
            _error(errors, f'candidate {candidate_id}: display_review is required before public display')
        else:
            checks = display.get('checks')
            if not isinstance(checks, list):
                _error(errors, f'candidate {candidate_id}: display_review.checks must be an array')
            else:
                for check in REQUIRED_DISPLAY_CHECKS:
                    if check not in checks:
                        _error(errors, f'candidate {candidate_id}: display check {check} is missing')
            if not isinstance(display.get('human_reviewed'), bool):
                _error(errors, f'candidate {candidate_id}: display_review.human_reviewed must be boolean')
            if not _iso_date(display.get('checked_at')):
                _error(errors, f'candidate {candidate_id}: display_review.checked_at must be an ISO date')
        languages = candidate.get('source_languages')
        if languages is not None:
            if not isinstance(languages, list) or not languages:
                _error(errors, f'candidate {candidate_id}: source_languages must be a nonempty array')
            else:
                for language in languages:
                    if not isinstance(language, str) or len(language.strip()) != 2:
                        _error(errors, f'candidate {candidate_id}: invalid language tag {language!r}')
        authority = candidate.get('issuing_authority')
        if authority is not None and (not isinstance(authority, str) or not authority.strip()):
            _error(errors, f'candidate {candidate_id}: issuing_authority must be a nonempty string or null')
        verification = candidate.get('verification_required')
        if verification is not None:
            if not isinstance(verification, list):
                _error(errors, f'candidate {candidate_id}: verification_required must be an array')
            else:
                for token in verification:
                    if token not in VERIFICATION_REQUIREMENTS:
                        _error(errors, f'candidate {candidate_id}: unknown verification requirement {token!r}')
        provenance = candidate.get('provenance')
        if provenance is not None:
            if not isinstance(provenance, dict):
                _error(errors, f'candidate {candidate_id}: provenance must be an object')
            else:
                for key in ('package', 'incoming_id', 'note'):
                    if not isinstance(provenance.get(key), str) or not provenance[key].strip():
                        _error(errors, f'candidate {candidate_id}: provenance.{key} must be a nonempty string')
                if not _iso_date(provenance.get('recorded_on')):
                    _error(errors, f'candidate {candidate_id}: provenance.recorded_on must be an ISO date')
                evidence_ref = provenance.get('evidence_ref')
                if evidence_ref is not None and not isinstance(evidence_ref, str):
                    _error(errors, f'candidate {candidate_id}: provenance.evidence_ref must be a string or null')
        relations = candidate.get('relations')
        if relations is not None:
            if not isinstance(relations, list):
                _error(errors, f'candidate {candidate_id}: relations must be an array')
            else:
                relation_ids = []
                for relation in relations:
                    if not isinstance(relation, dict):
                        _error(errors, f'candidate {candidate_id}: each relation must be an object')
                        continue
                    relation_ids.append(relation.get('id'))
                    if not relation.get('id'):
                        _error(errors, f'candidate {candidate_id}: relation needs an id')
                    if relation.get('relation') not in CANDIDATE_RELATIONS:
                        _error(errors, f'candidate {candidate_id}: unknown relation {relation.get("relation")!r}')
                    if relation.get('review_state') != 'unreviewed':
                        _error(errors, f'candidate {candidate_id}: candidate relations must stay unreviewed')
                    if not isinstance(relation.get('recorded_label'), str) or \
                            not relation['recorded_label'].strip():
                        _error(errors, f'candidate {candidate_id}: relation needs a recorded label')
                    target = relation.get('target_candidate_id')
                    if not isinstance(target, str) or not target:
                        _error(errors, f'candidate {candidate_id}: relation needs a target candidate')
                    elif target == candidate_id:
                        _error(errors, f'candidate {candidate_id}: relation points at its own record')
                for relation_id in sorted({item for item in relation_ids if relation_ids.count(item) > 1}):
                    _error(errors, f'candidate {candidate_id}: duplicate relation {relation_id!r}')
    for candidate_id in sorted({item for item in candidate_ids if candidate_ids.count(item) > 1}):
        _error(errors, f'candidate {candidate_id}: duplicate id')
    for candidate in data.candidate_inventory.get('records', []):
        for relation in candidate.get('relations') or []:
            if not isinstance(relation, dict):
                continue
            target = relation.get('target_candidate_id')
            if isinstance(target, str) and target and target not in candidate_map:
                _error(errors, f'candidate {candidate.get("id")}: relation target {target!r} is unknown')

    task_ids = []
    for task in data.tasks:
        task_id = task.get('task_id')
        task_ids.append(normalized_task_id(task_id))
        label = str(task_id)
        for key in ('task_id', 'jurisdiction', 'domain', 'question', 'stage', 'status'):
            if key not in task:
                _error(errors, f'task {label}: missing {key}')
        if task.get('jurisdiction') not in country_map:
            _error(errors, f'task {label}: unknown jurisdiction {task.get("jurisdiction")!r}')
        if task.get('domain') not in domain_map:
            _error(errors, f'task {label}: unknown domain {task.get("domain")!r}')
        if task.get('stage') not in TASK_STAGES:
            _error(errors, f'task {label}: unknown stage {task.get("stage")!r}')
        if task.get('status') not in TASK_STATUSES:
            _error(errors, f'task {label}: unknown status {task.get("status")!r}')
        if not isinstance(task.get('human_review_required'), bool):
            _error(errors, f'task {label}: human_review_required must be boolean')
        if not isinstance(task.get('question'), str) or len(task.get('question').strip()) < 12:
            _error(errors, f'task {label}: question is too short')
        leads = task.get('source_lead_ids')
        if leads is not None:
            if not isinstance(leads, list):
                _error(errors, f'task {label}: source_lead_ids must be an array')
            else:
                for lead in leads:
                    if lead not in candidate_map:
                        _error(errors, f'task {label}: unknown source lead {lead!r}')
        for unsupported in ('legal_effect', 'finding', 'conclusion'):
            if unsupported in task:
                _error(errors, f'task {label}: may not assert {unsupported}')
        if 'deliverable' in task and not isinstance(task.get('deliverable'), str):
            _error(errors, f'task {label}: deliverable must be a string')
    for task_id in sorted({item for item in task_ids if task_ids.count(item) > 1}):
        _error(errors, f'task {task_id}: duplicate logical task ID after separator normalization')

    for country in data.countries:
        code = country.get('code')
        status = country_status(data, code, list(domain_map))
        if status not in RESEARCH_STATUSES:
            _error(errors, f'country {code}: unknown derived research status {status!r}')

    errors.extend(validate_evidence_currency(data))
    errors.extend(validate_instruments(data))
    return errors


def validate_evidence_currency(data: CoverageData) -> list[str]:
    """Validate the publisher registry and source-check records.

    Currency is unknown unless a check is recorded. The validator never infers
    a check, a date or a publisher identity.
    """
    errors: list[str] = []
    country_codes = {country.get('code') for country in data.countries}
    candidate_map = {candidate.get('id'): candidate
                     for candidate in data.candidate_inventory.get('records', [])}
    record_map = {record.get('id'): record for record in data.policies}
    as_of = _iso_date(data.registry_as_of)
    if as_of is None:
        _error(errors, f'registry: as_of must be an ISO date, got {data.registry_as_of!r}')
    if not isinstance(data.stale_after_days, int) or data.stale_after_days <= 0:
        _error(errors, 'registry: stale_after_days must be a positive integer')

    publisher_map = {}
    for publisher in data.publishers:
        publisher_id = publisher.get('id')
        host = publisher.get('host')
        label = publisher_id or host or 'unknown'
        if not publisher_id:
            _error(errors, 'publisher: missing id')
        if not isinstance(host, str) or not host:
            _error(errors, f'publisher {label}: host must be a nonempty string')
            continue
        if host in publisher_map:
            _error(errors, f'publisher {label}: duplicate host {host!r}')
        publisher_map[host] = publisher
        if publisher_id != publisher_slug(host):
            _error(errors, f'publisher {label}: id must be the host slug {publisher_slug(host)!r}')
        url = publisher.get('url')
        if not safe_url(url):
            _error(errors, f'publisher {label}: url must be a safe https URL')
        elif _host_of(url) != host:
            _error(errors, f'publisher {label}: url host does not match {host!r}')
        jurisdictions = publisher.get('jurisdictions')
        if not isinstance(jurisdictions, list) or not jurisdictions:
            _error(errors, f'publisher {label}: jurisdictions must be a nonempty array')
        else:
            for code in jurisdictions:
                if code not in country_codes:
                    _error(errors, f'publisher {label}: unknown jurisdiction {code!r}')
        if publisher.get('authority_type') not in PUBLISHER_AUTHORITY_TYPES:
            _error(errors, f'publisher {label}: unknown authority_type '
                           f'{publisher.get("authority_type")!r}')
        if publisher.get('verification_status') not in PUBLISHER_VERIFICATION_STATUSES:
            _error(errors, f'publisher {label}: unknown verification_status '
                           f'{publisher.get("verification_status")!r}')
        if publisher.get('monitoring') not in PUBLISHER_MONITORING_STATES:
            _error(errors, f'publisher {label}: unknown monitoring state '
                           f'{publisher.get("monitoring")!r}')
        name = publisher.get('publisher_name')
        if name is not None and (not isinstance(name, str) or not name.strip()):
            _error(errors, f'publisher {label}: publisher_name must be a nonempty string or null')
        languages = publisher.get('languages')
        if not isinstance(languages, list):
            _error(errors, f'publisher {label}: languages must be an array')
        else:
            for language in languages:
                if not isinstance(language, str) or len(language.strip()) != 2:
                    _error(errors, f'publisher {label}: invalid language tag {language!r}')
        cited_candidates = publisher.get('cited_by_candidates')
        if not isinstance(cited_candidates, list):
            _error(errors, f'publisher {label}: cited_by_candidates must be an array')
            cited_candidates = []
        for candidate_id in cited_candidates:
            candidate = candidate_map.get(candidate_id)
            if candidate is None:
                _error(errors, f'publisher {label}: cites unknown candidate {candidate_id!r}')
            elif _host_of(candidate.get('source_url')) != host:
                _error(errors, f'publisher {label}: candidate {candidate_id} has a different host')
        cited_records = publisher.get('cited_by_records')
        if not isinstance(cited_records, list):
            _error(errors, f'publisher {label}: cited_by_records must be an array')
            cited_records = []
        for record_id in cited_records:
            record = record_map.get(record_id)
            if record is None:
                _error(errors, f'publisher {label}: cites unknown record {record_id!r}')
            elif _host_of(record.get('source_url')) != host:
                _error(errors, f'publisher {label}: record {record_id} has a different host')
        if not cited_candidates and not cited_records:
            _error(errors, f'publisher {label}: must cite at least one candidate or record')

    host_sources = {}
    for candidate in data.candidate_inventory.get('records', []):
        host_sources.setdefault(_host_of(candidate.get('source_url')), set()).add(
            f'candidate {candidate.get("id")}')
    for record in data.policies:
        host_sources.setdefault(_host_of(record.get('source_url')), set()).add(
            f'record {record.get("id")}')
    for host, sources in sorted(host_sources.items()):
        if host not in publisher_map:
            _error(errors, f'registry: no publisher entry for host {host!r} '
                           f'({", ".join(sorted(sources))})')
    for host in sorted(set(publisher_map) - set(host_sources)):
        _error(errors, f'registry: publisher {host!r} is not cited by any candidate or record')

    check_map = {}
    for check in data.source_checks:
        candidate_id = check.get('candidate_id')
        label = f'check {candidate_id!r}'
        if not candidate_id:
            _error(errors, 'check: missing candidate_id')
            continue
        if candidate_id in check_map:
            _error(errors, f'{label}: duplicate check')
        check_map[candidate_id] = check
        candidate = candidate_map.get(candidate_id)
        if candidate is None:
            _error(errors, f'{label}: unknown candidate')
            continue
        host = _host_of(candidate.get('source_url'))
        publisher = publisher_map.get(host) or {}
        if check.get('publisher_id') != publisher.get('id'):
            _error(errors, f'{label}: publisher_id does not match the candidate host')

        retrieval = check.get('retrieval_status')
        if retrieval not in RETRIEVAL_STATUSES:
            _error(errors, f'{label}: unknown retrieval_status {retrieval!r}')
            continue
        retrieval_fields = ('attempted_at', 'http_status', 'final_url', 'content_type',
                            'error_category')
        if retrieval == 'not_attempted':
            present = [key for key in retrieval_fields if check.get(key) is not None]
            if present:
                _error(errors, f'{label}: a not_attempted record may not carry {present}')
        else:
            attempted = _iso_date(check.get('attempted_at'))
            if attempted is None:
                _error(errors, f'{label}: a {retrieval} retrieval needs an ISO attempted_at')
            elif as_of is not None and attempted > as_of:
                _error(errors, f'{label}: attempted_at is after the registry as_of date')
            error_category = check.get('error_category')
            if error_category is not None and error_category not in RETRIEVAL_ERROR_CATEGORIES:
                _error(errors, f'{label}: unknown error_category {error_category!r}')
            if retrieval == 'failed' and error_category is None:
                _error(errors, f'{label}: a failed retrieval needs an error_category')
            if retrieval == 'success':
                http_status = check.get('http_status')
                if not isinstance(http_status, int) or isinstance(http_status, bool) \
                        or not 100 <= http_status <= 599:
                    _error(errors, f'{label}: a successful retrieval needs an HTTP status')
                if not safe_url(check.get('final_url')):
                    _error(errors, f'{label}: a successful retrieval needs a safe https final_url')
            elif check.get('http_status') is not None:
                http_status = check.get('http_status')
                if not isinstance(http_status, int) or isinstance(http_status, bool) \
                        or not 100 <= http_status <= 599:
                    _error(errors, f'{label}: http_status must be an integer HTTP status or null')
            if check.get('final_url') is not None and not safe_url(check.get('final_url')):
                _error(errors, f'{label}: final_url must be a safe https URL or null')
            content_type = check.get('content_type')
            if content_type is not None and (not isinstance(content_type, str)
                                             or not content_type.strip()):
                _error(errors, f'{label}: content_type must be a nonempty string or null')

        success = check.get('last_successful_retrieval')
        if retrieval == 'success' and success is None:
            _error(errors, f'{label}: a successful retrieval needs last_successful_retrieval')
        attempted_date = _iso_date(check.get('attempted_at'))
        success_date = _iso_date(success)
        if attempted_date and success_date and success_date > attempted_date:
            _error(errors, f'{label}: last_successful_retrieval is after attempted_at')
        if success is not None:
            parsed_success = _iso_date(success)
            if parsed_success is None:
                _error(errors, f'{label}: last_successful_retrieval must be an ISO date or null')
            elif as_of is not None and parsed_success > as_of:
                _error(errors, f'{label}: last_successful_retrieval is after the registry as_of date')

        verification = check.get('legal_verification')
        if not isinstance(verification, dict):
            _error(errors, f'{label}: legal_verification must be an object')
            continue
        status = verification.get('status')
        if status not in LEGAL_VERIFICATION_STATUSES:
            _error(errors, f'{label}: unknown legal verification status {status!r}')
            continue
        evidence = verification.get('evidence')
        reviewed_at = verification.get('reviewed_at')
        if status in ('verified', 'disputed', 'superseded'):
            if not isinstance(evidence, str) or not evidence.strip():
                _error(errors, f'{label}: {status} legal verification needs recorded evidence')
            if _iso_date(reviewed_at) is None:
                _error(errors, f'{label}: {status} legal verification needs an ISO reviewed_at')
        elif reviewed_at is not None and _iso_date(reviewed_at) is None:
            _error(errors, f'{label}: reviewed_at must be an ISO date or null')
        if reviewed_at is not None and as_of is not None and _iso_date(reviewed_at) \
                and _iso_date(reviewed_at) > as_of:
            _error(errors, f'{label}: legal verification review date is after the registry as_of date')
        if status == 'unreviewed' and (evidence is not None or reviewed_at is not None):
            _error(errors, f'{label}: an unreviewed record may not carry verification evidence')
    for candidate_id in candidate_map:
        if candidate_id not in check_map:
            _error(errors, f'check: candidate {candidate_id!r} has no source-check record')
    return errors


def validate_instruments(data: CoverageData) -> list[str]:
    """Validate reported instrument identity and documented version dates."""
    errors: list[str] = []
    candidate_map = {candidate.get('id'): candidate
                     for candidate in data.candidate_inventory.get('records', [])}
    instrument_map = {}
    for instrument in data.instruments:
        candidate_id = instrument.get('candidate_id')
        label = f'instrument {candidate_id!r}'
        if not candidate_id:
            _error(errors, 'instrument: missing candidate_id')
            continue
        if candidate_id in instrument_map:
            _error(errors, f'{label}: duplicate instrument')
        instrument_map[candidate_id] = instrument
        candidate = candidate_map.get(candidate_id)
        if candidate is None:
            _error(errors, f'{label}: unknown candidate')
            continue
        if instrument.get('work_id') != candidate_id:
            _error(errors, f'{label}: work_id must match the candidate id')
        if instrument.get('jurisdiction') != candidate.get('jurisdiction'):
            _error(errors, f'{label}: jurisdiction does not match the candidate')
        if instrument.get('title_reported') != candidate.get('instrument_title'):
            _error(errors, f'{label}: title_reported does not match the candidate title')
        instrument_type = instrument.get('instrument_type_reported')
        if instrument_type not in INSTRUMENT_TYPES:
            _error(errors, f'{label}: unknown instrument type {instrument_type!r}')
        number = instrument.get('instrument_number_reported')
        if number is not None and (not isinstance(number, str) or not number.strip()):
            _error(errors, f'{label}: instrument number must be a nonempty string or null')
        if instrument_type == 'unknown' and number:
            _error(errors, f'{label}: an unknown type may not carry an instrument number')
        year = instrument.get('instrument_year_reported')
        if year is not None and (not isinstance(year, str)
                                 or not re.fullmatch(r'[0-9]{4}', year)):
            _error(errors, f'{label}: instrument year must be four digits or null')
        if year and not number:
            _error(errors, f'{label}: an instrument year needs an instrument number')
        authority = instrument.get('issuing_authority')
        if authority is not None and (not isinstance(authority, str) or not authority.strip()):
            _error(errors, f'{label}: issuing_authority must be a nonempty string or null')
        reported = candidate.get('published_date_reported')
        expected_publication = reported if _iso_date(reported) else None
        if instrument.get('publication_date_reported') != expected_publication:
            _error(errors, f'{label}: publication_date_reported must match the candidate '
                           f'publication date or stay null')
        dates = instrument.get('dates')
        if not isinstance(dates, dict):
            _error(errors, f'{label}: dates must be an object')
        else:
            for key in INSTRUMENT_DATE_KEYS:
                value = dates.get(key)
                if value is not None and _iso_date(value) is None:
                    _error(errors, f'{label}: dates.{key} must be an ISO date or null')
            for key in sorted(set(dates) - set(INSTRUMENT_DATE_KEYS)):
                _error(errors, f'{label}: unexpected date key {key!r}')
        expression = instrument.get('expression')
        if not isinstance(expression, dict):
            _error(errors, f'{label}: expression must be an object')
        else:
            language = expression.get('language')
            if language is not None and (not isinstance(language, str)
                                         or len(language.strip()) != 2):
                _error(errors, f'{label}: expression language must be a two-letter tag or null')
            if not isinstance(expression.get('label'), str) or not expression['label'].strip():
                _error(errors, f'{label}: expression label must be a nonempty string')
        if instrument.get('captured_item') is not None:
            _error(errors, f'{label}: a captured item may not be recorded without capture evidence')
        if instrument.get('review_state') != 'reported':
            _error(errors, f'{label}: review_state must remain reported')
        uncertainties = instrument.get('uncertainties')
        if not isinstance(uncertainties, list) or not uncertainties:
            _error(errors, f'{label}: uncertainties must be a nonempty array')
        else:
            for note in uncertainties:
                if not isinstance(note, str) or not note.strip():
                    _error(errors, f'{label}: uncertainty notes must be nonempty strings')
    for candidate_id in candidate_map:
        if candidate_id not in instrument_map:
            _error(errors, f'instrument: candidate {candidate_id!r} has no instrument record')
    return errors


def audit_coverage(data: CoverageData, reference_date: date | None = None) -> dict:
    """Return deterministic research-queue diagnostics for the public backlog."""
    reference_date = reference_date or date.today()
    candidates = data.candidate_inventory.get('records', [])
    tasks = data.tasks

    normalized = {}
    for task in tasks:
        normalized.setdefault(normalized_task_id(task.get('task_id')), []).append(task.get('task_id'))
    duplicates = [
        {'normalized': key, 'task_ids': sorted(values)}
        for key, values in sorted(normalized.items()) if len(values) > 1
    ]

    missing_metadata = []
    for candidate in candidates:
        missing = [key for key in ('instrument_title', 'source_url', 'source_type',
                                   'research_question', 'published_date_reported')
                   if not candidate.get(key)]
        if missing:
            missing_metadata.append({'kind': 'candidate', 'id': candidate.get('id'), 'fields': missing})
    for task in tasks:
        if 'priority' not in task:
            missing_metadata.append({'kind': 'task', 'id': task.get('task_id'), 'fields': ['priority']})
        if 'deliverable' not in task:
            missing_metadata.append({'kind': 'task', 'id': task.get('task_id'), 'fields': ['deliverable']})

    stale = []
    for candidate in candidates:
        if candidate.get('capture_status') in ('captured', 'verified'):
            captured = _iso_date(candidate.get('captured_at'))
            if captured and reference_date - captured > STALE_AFTER:
                stale.append({'kind': 'candidate_capture', 'id': candidate.get('id'),
                              'captured_at': candidate.get('captured_at')})
    for policy in data.policies:
        match = re.match(r'^(\d{4}-[0-9]{2}-[0-9]{2})', str(policy.get('reviewed_on') or ''))
        if match:
            checked = _iso_date(match.group(1))
            if checked and reference_date - checked > STALE_AFTER:
                stale.append({'kind': 'policy_metadata', 'id': policy.get('id'),
                              'reviewed_on': match.group(1)})

    unresolved = []
    for task in tasks:
        if task.get('human_review_required') is True and task.get('status') != 'complete':
            unresolved.append({'kind': 'task', 'id': task.get('task_id'),
                               'status': task.get('status')})
    for candidate in candidates:
        display = candidate.get('display_review') or {}
        if display.get('human_reviewed') is not True:
            unresolved.append({'kind': 'candidate_display', 'id': candidate.get('id'),
                               'status': 'human_review_pending'})

    relationships = []
    for candidate in candidates:
        for policy in data.policies:
            if candidate.get('source_url') == policy.get('source_url'):
                relationships.append({
                    'kind': 'same_source_url',
                    'candidate_id': candidate.get('id'),
                    'record_id': policy.get('id'),
                })
            elif candidate.get('jurisdiction') == policy.get('country') and \
                    policy.get('topic') in (candidate.get('domains') or []):
                relationships.append({
                    'kind': 'same_jurisdiction_and_domain',
                    'candidate_id': candidate.get('id'),
                    'record_id': policy.get('id'),
                })

    return {
        'task_count': len(tasks),
        'candidate_count': len(candidates),
        'duplicates': duplicates,
        'missing_metadata': missing_metadata,
        'stale_verification': stale,
        'unresolved_review': unresolved,
        'relationships': relationships,
        'by_jurisdiction': _counts(tasks, 'jurisdiction'),
        'by_domain': _counts(tasks, 'domain'),
        'by_status': _counts(tasks, 'status'),
    }


def _counts(items, key):
    counts = {}
    for item in items:
        value = item.get(key)
        if value:
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
