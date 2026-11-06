#!/usr/bin/env python3
"""Import an unreviewed discovery tranche into the canonical candidate inventory.

The import is deterministic and idempotent. It never promotes a candidate to a
verified source, never assigns a legal effect, and never rewrites an existing
policy record. Every decision is written to a machine-readable reconciliation
report so a reviewer can see what was imported, what matched, what may be a
duplicate and what conflicts.

Usage:

    python3 research-toolkit/scripts/import_tranche.py
    python3 research-toolkit/scripts/import_tranche.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = REPO_ROOT / 'research-toolkit' / 'incoming' / 'tranche-02'
DEFAULT_SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
DEFAULT_TASKS = REPO_ROOT / 'research-toolkit' / 'backlog' / 'tasks-tranche-02.jsonl'
OTHER_TASK_FILES = (
    REPO_ROOT / 'research-toolkit' / 'backlog' / 'tasks.jsonl',
    REPO_ROOT / 'research-toolkit' / 'backlog' / 'cross-domain-tasks.jsonl',
)
DEFAULT_REPORT = REPO_ROOT / 'research-toolkit' / 'reconciliation' / 'tranche-02-report.json'
DEFAULT_POLICIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'policies.json'
DEFAULT_COUNTRIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'countries.json'
DEFAULT_DOMAINS = REPO_ROOT / 'regions' / 'mena' / 'data' / 'domains.json'

# The tranche uses working identifiers. Map them explicitly instead of silently
# accepting a second vocabulary.
DOMAIN_MAP = {
    'digital_rights': 'digital_rights',
    'disability_rights': 'disability_inclusion',
}
SOURCE_TYPE_MAP = {
    'official_gazette': 'official_legislative_publication',
    'justice_ministry_legal_portal': 'official_legislation_index',
    'justice_ministry': 'official_legislation_index',
    'official_legislative_database': 'official_legislation_index',
    'house_of_representatives_portal': 'official_legislation_index',
    'government_authority': 'official_index',
    'central_bank_official_law_collection': 'official_regulator_legal_index',
    'government_regulator': 'official_regulator_legal_index',
    'government_regulator_announcement': 'official_government_explainer_not_statute',
    'intergovernmental_index': 'secondary',
}
TASK_STATUS_MAP = {
    'ready_for_source_verification': 'unstarted',
}
TASK_STAGE = 'capture'
VERIFICATION_TOKENS = (
    'official_source',
    'legal_scope',
    'language',
    'publication_permissions',
)
DISPLAY_CHECKS = (
    'https_scheme',
    'no_credentials',
    'hostname_not_ip',
    'no_personal_data_fields',
    'link_only_no_text_reproduced',
)
# Relationships stated by the tranche document titles. They are recorded as
# unreviewed candidate relations; they are not legal-effect findings.
REPORTED_RELATIONS = {
    'MENA-T02-002': {
        'relation': 'amends',
        'target_incoming_id': 'MENA-T02-001',
        'recorded_label': 'Law 25-11 of 2025 amending Law 18-07',
    },
    'MENA-T02-004': {
        'relation': 'amends',
        'target_incoming_id': 'MENA-T02-003',
        'recorded_label': 'Law 11 of 2024, first amendment to Law 38 of 2013',
    },
    'MENA-T02-009': {
        'relation': 'related',
        'target_incoming_id': 'MENA-T02-008',
        'recorded_label': 'Reported approval of regulations for the 2023 Data Protection Act',
    },
}
INTEGRATION_DATE = '2026-11-06'
PACKAGE_LABEL = 'research-toolkit/incoming/tranche-02'
PROVENANCE_NOTE = ('Imported from an unreviewed discovery tranche. No source was '
                   'captured, transcribed, translated or legally reviewed.')
EVIDENCE_REF_NOTE = ('AI session turn reference kept as recorded provenance. It is '
                     'not a retrievable source and is not verification.')

INSTRUMENT_PATTERN = re.compile(
    r'\b(?:Law|Act|Decree-?Law|Decision|Ordinance|Regulation)\s+'
    r'(?:No\.?\s*)?([0-9][0-9A-Za-z./-]*)',
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r'(?:^|\s)((?:19|20)[0-9]{2})(?:\s|$|[,.;])')
SLUG_PATTERN = re.compile(r'[^a-z0-9]+')


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def dump_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def dump_jsonl(rows) -> str:
    return ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)


def normalize_url(value) -> str:
    """A conservative comparison key; the stored URL is never rewritten."""
    if not isinstance(value, str):
        return ''
    parsed = urlsplit(value.strip())
    host = (parsed.hostname or '').lower()
    path = parsed.path.rstrip('/')
    query = f'?{parsed.query}' if parsed.query else ''
    return f'{parsed.scheme.lower()}://{host}{path}{query}'


def instrument_key(title) -> str:
    """Extract the primary instrument number and year from a reported title.

    Only the first instrument reference is used, so an amendment title such as
    "Law 25-11 amending Law 18-07" keys on 25-11, not on the amended law.
    """
    if not isinstance(title, str):
        return ''
    match = INSTRUMENT_PATTERN.search(title)
    if not match:
        return ''
    number = match.group(1).strip(' .,;:').lower()
    year_match = YEAR_PATTERN.search(title)
    year = year_match.group(1) if year_match else ''
    return f'{number}|{year}'


def title_key(title) -> str:
    return SLUG_PATTERN.sub('-', str(title).lower()).strip('-')


def safe_url(value) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.netloc:
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname or ''
    return bool(host) and not re.fullmatch(r'[0-9.]+', host) and ':' not in host


def candidate_id(incoming_id: str) -> str:
    """Preserve the incoming identifier in the canonical lowercase form."""
    return str(incoming_id).strip().lower()


def relation_id(source_id: str, relation: str, target_id: str) -> str:
    return f'{source_id}-{relation}-{target_id}'


def _display_review(record) -> dict:
    checks = list(DISPLAY_CHECKS)
    if not safe_url(record.get('source_url')):
        checks = []
    return {
        'checks': checks,
        'human_reviewed': False,
        'checked_at': INTEGRATION_DATE,
    }


def _provenance(record) -> dict:
    return {
        'package': PACKAGE_LABEL,
        'incoming_id': record.get('candidate_id'),
        'recorded_on': record.get('researched_on'),
        'source_status': record.get('source_status'),
        'source_kind': record.get('source_kind'),
        'discovery_note': record.get('discovery_note'),
        'evidence_ref': record.get('web_evidence_ref'),
        'evidence_ref_note': EVIDENCE_REF_NOTE,
        'note': PROVENANCE_NOTE,
    }


def validate_incoming(record, country_codes, domain_ids) -> list[str]:
    """Structural and legal-status checks for one incoming candidate."""
    prefix = f'{record.get("candidate_id")!r}: '
    errors = []
    for key in ('candidate_id', 'jurisdiction', 'instrument_title_en_working',
                'source_url', 'source_kind', 'domain', 'next_research_task',
                'researched_on', 'source_status', 'legal_effect', 'review_status',
                'publication_status', 'web_evidence_ref', 'languages_to_verify'):
        if not record.get(key):
            errors.append(prefix + f'missing {key}')
    if record.get('jurisdiction') not in country_codes:
        errors.append(prefix + f'unknown jurisdiction {record.get("jurisdiction")!r}')
    if record.get('domain') not in DOMAIN_MAP:
        errors.append(prefix + f'unknown domain {record.get("domain")!r}')
    elif DOMAIN_MAP[record['domain']] not in domain_ids:
        errors.append(prefix + f'domain maps outside the registry: {record["domain"]!r}')
    if record.get('source_kind') not in SOURCE_TYPE_MAP:
        errors.append(prefix + f'unknown source_kind {record.get("source_kind")!r}')
    if not safe_url(record.get('source_url')):
        errors.append(prefix + 'source_url must be a safe https URL')
    if record.get('legal_effect') != 'not_assessed':
        errors.append(prefix + 'legal_effect may not be promoted in a discovery tranche')
    if record.get('review_status') != 'unreviewed':
        errors.append(prefix + 'review_status may not claim human review')
    if record.get('publication_status') != 'candidate_only':
        errors.append(prefix + 'publication_status must be candidate_only')
    if record.get('original_text_verified') is not False:
        errors.append(prefix + 'original_text_verified must be false')
    capture = record.get('source_capture') if isinstance(record.get('source_capture'), dict) else {}
    if capture.get('bytes_stored') or capture.get('sha256'):
        errors.append(prefix + 'a discovery tranche may not store captured bytes or a checksum')
    if len(str(record.get('next_research_task') or '').strip()) < 12:
        errors.append(prefix + 'next_research_task is too short')
    if record.get('source_status') not in ('official_portal_identified',
                                           'secondary_index_identified'):
        errors.append(prefix + f'unknown source_status {record.get("source_status")!r}')
    languages = record.get('languages_to_verify')
    if not isinstance(languages, list) or not languages:
        errors.append(prefix + 'languages_to_verify must be a nonempty array')
    else:
        for language in languages:
            if not isinstance(language, str) or len(language.strip()) != 2:
                errors.append(prefix + f'invalid language tag {language!r}')
    return errors


def validate_task(task, incoming_ids, task_ids) -> list[str]:
    prefix = f'task {task.get("task_id")!r}: '
    errors = []
    for key in ('task_id', 'jurisdiction', 'domain', 'question', 'status',
                'candidate_source_id', 'output'):
        if not task.get(key):
            errors.append(prefix + f'missing {key}')
    if task.get('task_id') in task_ids:
        errors.append(prefix + 'duplicate task id in the package')
    if task.get('candidate_source_id') not in incoming_ids:
        errors.append(prefix + f'missing candidate {task.get("candidate_source_id")!r}')
    if task.get('domain') not in DOMAIN_MAP:
        errors.append(prefix + f'unknown domain {task.get("domain")!r}')
    if task.get('status') not in TASK_STATUS_MAP:
        errors.append(prefix + f'unknown status {task.get("status")!r}')
    review = task.get('review_required')
    if not isinstance(review, list) or not review:
        errors.append(prefix + 'review_required must be a nonempty array')
    else:
        for token in review:
            if token not in VERIFICATION_TOKENS:
                errors.append(prefix + f'unknown verification requirement {token!r}')
    return errors


def _existing_indexes(sources_doc, policies, existing_tasks):
    """Index canonical evidence by URL, instrument key and title key."""
    url_index = {}
    instrument_index = {}
    title_index = {}
    task_index = {}
    for candidate in sources_doc.get('records', []):
        ref = {'kind': 'candidate', 'id': candidate.get('id')}
        url_index.setdefault(normalize_url(candidate.get('source_url')), []).append(ref)
        instrument = instrument_key(candidate.get('instrument_title'))
        if instrument:
            key = f'{candidate.get("jurisdiction")}:{instrument}'
            instrument_index.setdefault(key, []).append(ref)
        title_index.setdefault(
            f'{candidate.get("jurisdiction")}:{title_key(candidate.get("instrument_title"))}', []
        ).append(ref)
    for policy in policies:
        ref = {'kind': 'policy_record', 'id': policy.get('id')}
        url_index.setdefault(normalize_url(policy.get('source_url')), []).append(ref)
        instrument = instrument_key(policy.get('title'))
        if instrument:
            key = f'{policy.get("country")}:{instrument}'
            instrument_index.setdefault(key, []).append(ref)
        title_index.setdefault(
            f'{policy.get("country")}:{title_key(policy.get("title"))}', []
        ).append(ref)
    for task in existing_tasks:
        task_index.setdefault(task.get('task_id'), []).append(
            {'kind': 'task', 'id': task.get('task_id')})
    return url_index, instrument_index, title_index, task_index


def plan_import(package, sources_doc, policies, countries, domains, existing_tasks):
    """Return the canonical record set, the new tasks and a reconciliation report.

    The function is pure: it reads its arguments and returns data. Nothing is
    written until the caller checks for errors.
    """
    package = Path(package)
    incoming_doc = read_json(package / 'candidate-sources.json')
    incoming = incoming_doc.get('records', [])
    incoming_tasks = read_jsonl(package / 'tasks.jsonl')
    country_codes = {country.get('code') for country in countries}
    domain_ids = {domain.get('id') for domain in domains}

    errors = []
    verification_by_candidate = {
        task.get('candidate_source_id'): list(task.get('review_required') or [])
        for task in incoming_tasks
    }
    incoming_ids = {record.get('candidate_id') for record in incoming}
    duplicate_incoming = sorted(
        candidate_id for candidate_id in incoming_ids
        if sum(1 for record in incoming if record.get('candidate_id') == candidate_id) > 1)
    for candidate_id_value in duplicate_incoming:
        errors.append(f'incoming candidate {candidate_id_value!r}: duplicate id')
    package_task_ids = set()
    for task in incoming_tasks:
        errors.extend(validate_task(task, incoming_ids, package_task_ids))
        package_task_ids.add(task.get('task_id'))
    for record in incoming:
        errors.extend(validate_incoming(record, country_codes, domain_ids))

    url_index, instrument_index, title_index, task_index = _existing_indexes(
        sources_doc, policies, existing_tasks)
    existing_ids = {record.get('id') for record in sources_doc.get('records', [])}
    existing_by_id = {record.get('id'): record for record in sources_doc.get('records', [])}

    imported_candidates = []
    matched_candidates = []
    possible_duplicates = []
    conflicts = []
    new_records = []

    for record in incoming:
        incoming_id = record.get('candidate_id')
        canonical_id = candidate_id(incoming_id)
        canonical = _canonical_candidate(
            record, canonical_id, verification_by_candidate.get(incoming_id, []))
        if canonical_id in existing_ids:
            stored = existing_by_id.get(canonical_id) or {}
            differing = [key for key in ('source_url', 'instrument_title', 'jurisdiction')
                         if stored.get(key) != canonical.get(key)]
            if differing:
                conflicts.append({
                    'incoming_id': incoming_id,
                    'candidate_id': canonical_id,
                    'fields': differing,
                    'reason': 'existing candidate with the same id has different metadata',
                })
            else:
                imported_candidates.append({
                    'incoming_id': incoming_id,
                    'candidate_id': canonical_id,
                    'jurisdiction': canonical['jurisdiction'],
                    'domains': canonical['domains'],
                })
            continue

        url = normalize_url(record.get('source_url'))
        key = f'{record.get("jurisdiction")}:{instrument_key(record.get("instrument_title_en_working"))}'
        title = f'{record.get("jurisdiction")}:{title_key(record.get("instrument_title_en_working"))}'
        if url and url in url_index:
            matched_candidates.append({
                'incoming_id': incoming_id,
                'candidate_id': canonical_id,
                'reason': 'same_source_url',
                'matches': url_index[url],
            })
            continue
        if key and key in instrument_index and instrument_key(record.get('instrument_title_en_working')):
            possible_duplicates.append({
                'incoming_id': incoming_id,
                'candidate_id': canonical_id,
                'reason': 'same_jurisdiction_and_instrument_number',
                'matches': instrument_index[key],
            })
            continue
        if title and title in title_index:
            possible_duplicates.append({
                'incoming_id': incoming_id,
                'candidate_id': canonical_id,
                'reason': 'same_jurisdiction_and_title',
                'matches': title_index[title],
            })
            continue

        imported_candidates.append({
            'incoming_id': incoming_id,
            'candidate_id': canonical_id,
            'jurisdiction': canonical['jurisdiction'],
            'domains': canonical['domains'],
        })
        new_records.append(canonical)
        existing_ids.add(canonical_id)
        url_index.setdefault(url, []).append({'kind': 'candidate', 'id': canonical_id})
        instrument_index.setdefault(key, []).append({'kind': 'candidate', 'id': canonical_id})
        title_index.setdefault(title, []).append({'kind': 'candidate', 'id': canonical_id})

    imported_tasks = []
    new_tasks = []
    existing_tasks_by_id = {task.get('task_id'): task for task in existing_tasks}
    for task in incoming_tasks:
        if task.get('task_id') in task_index:
            stored = existing_tasks_by_id.get(task.get('task_id'), {})
            imported_tasks.append({
                'incoming_task_id': task.get('task_id'),
                'task_id': task.get('task_id'),
                'candidate_id': (stored.get('source_lead_ids') or [candidate_id(
                    task.get('candidate_source_id'))])[0],
            })
            continue
        canonical_task = _canonical_task(task)
        imported_tasks.append({
            'incoming_task_id': task.get('task_id'),
            'task_id': canonical_task['task_id'],
            'candidate_id': canonical_task['source_lead_ids'][0],
        })
        new_tasks.append(canonical_task)

    # Relationships are only added when both endpoints survive the import.
    known_ids = existing_ids | {candidate['id'] for candidate in new_records}
    relation_count = 0
    for canonical in new_records:
        spec = REPORTED_RELATIONS.get(canonical['provenance']['incoming_id'])
        if not spec:
            continue
        target = candidate_id(spec['target_incoming_id'])
        if target not in known_ids:
            continue
        canonical['relations'] = [{
            'id': relation_id(canonical['id'], spec['relation'], target),
            'relation': spec['relation'],
            'target_candidate_id': target,
            'recorded_label': spec['recorded_label'],
            'review_state': 'unreviewed',
        }]
        relation_count += 1

    sources_after = dict(sources_doc)
    sources_after['records'] = list(sources_doc.get('records', [])) + new_records
    relation_count = sum(
        1 for candidate in sources_after['records']
        if (candidate.get('provenance') or {}).get('package') == PACKAGE_LABEL
        and candidate.get('relations'))
    package_research_dates = sorted({
        str(record.get('researched_on')) for record in incoming if record.get('researched_on')})
    package_research_date = package_research_dates[0] if package_research_dates else INTEGRATION_DATE
    packages = list(sources_after.get('imported_packages') or [])
    package_entry = {
        'package': PACKAGE_LABEL,
        'research_date': package_research_date,
        'candidates_imported': len(imported_candidates),
        'tasks_imported': len(imported_tasks),
        'report': 'research-toolkit/reconciliation/tranche-02-report.json',
    }
    packages = [entry for entry in packages if entry.get('package') != PACKAGE_LABEL]
    if imported_candidates:
        packages.append(package_entry)
    if packages:
        sources_after['imported_packages'] = packages
    else:
        sources_after.pop('imported_packages', None)

    report = {
        'version': '1',
        'package': PACKAGE_LABEL,
        'package_research_date': package_research_date,
        'integration_date': INTEGRATION_DATE,
        'incoming': {
            'candidates': len(incoming),
            'tasks': len(incoming_tasks),
            'jurisdictions': len({record.get('jurisdiction') for record in incoming}),
        },
        'imported_candidates': imported_candidates,
        'matched_candidates': matched_candidates,
        'possible_duplicates': possible_duplicates,
        'conflicts': conflicts,
        'imported_tasks': imported_tasks,
        'outstanding_questions': [
            {
                'candidate_id': candidate_id(record.get('candidate_id')),
                'question': record.get('next_research_task'),
                'verification_required': list(
                    verification_by_candidate.get(record.get('candidate_id'), [])),
            }
            for record in incoming
        ],
        'relationships': relation_count,
        'duplicate_detection': {
            'signals': [
                'canonical source URL (scheme, host and path, fragment ignored)',
                'jurisdiction plus primary instrument number and year',
                'jurisdiction plus normalized title',
            ],
            'limitations': ('The package records one URL per lead and no alternative or '
                            'archived URLs, so URL comparison cannot detect a mirror of the '
                            'same instrument. Amendment and consolidation relationships are '
                            'stored as unreviewed candidate relations; they are not used to '
                            'merge records.'),
        },
        'mappings': {
            'domains': dict(DOMAIN_MAP),
            'source_types': dict(SOURCE_TYPE_MAP),
            'task_statuses': dict(TASK_STATUS_MAP),
            'task_stage': TASK_STAGE,
        },
        'existing_policy_records': {
            'count': len(policies),
            'ids': sorted(str(policy.get('id')) for policy in policies),
        },
        'canonical_candidate_records': len(sources_after['records']),
        'canonical_task_records': len(existing_tasks) + len(new_tasks),
        'errors': errors,
        'result': 'blocked' if errors else 'ok',
    }
    return sources_after, new_tasks, report


def _canonical_candidate(record, canonical_id, verification):
    domain = DOMAIN_MAP.get(record.get('domain'))
    source_type = SOURCE_TYPE_MAP.get(record.get('source_kind'))
    candidate = {
        'id': canonical_id,
        'jurisdiction': record.get('jurisdiction'),
        'domains': [domain] if domain else [],
        'instrument_title': record.get('instrument_title_en_working'),
        'source_url': record.get('source_url'),
        'source_type': source_type,
        'published_date_reported': 'unknown',
        'legal_effect': 'not_assessed',
        'capture_status': 'not_captured',
        'research_question': record.get('next_research_task'),
        'source_languages': list(record.get('languages_to_verify') or []),
        'verification_required': list(verification),
        'display_review': _display_review(record),
        'provenance': _provenance(record),
    }
    return candidate


def _canonical_task(task):
    review = list(task.get('review_required') or [])
    return {
        'task_id': task.get('task_id'),
        'jurisdiction': task.get('jurisdiction'),
        'domain': DOMAIN_MAP.get(task.get('domain'), task.get('domain')),
        'question': task.get('question'),
        'stage': TASK_STAGE,
        'status': TASK_STATUS_MAP.get(task.get('status'), 'unstarted'),
        'human_review_required': bool(review),
        'source_lead_ids': [candidate_id(task.get('candidate_source_id'))],
        'deliverable': task.get('output'),
    }


def run(package=DEFAULT_PACKAGE, sources_path=DEFAULT_SOURCES, tasks_path=DEFAULT_TASKS,
        report_path=DEFAULT_REPORT, policies_path=DEFAULT_POLICIES,
        countries_path=DEFAULT_COUNTRIES, domains_path=DEFAULT_DOMAINS,
        check=False) -> int:
    sources_doc = read_json(sources_path)
    policies = read_json(policies_path)
    countries = read_json(countries_path)
    domains = read_json(domains_path)['domains']
    existing_tasks = read_jsonl(tasks_path)
    for other in OTHER_TASK_FILES:
        if Path(other).resolve() != Path(tasks_path).resolve():
            existing_tasks.extend(read_jsonl(other))
    sources_after, new_tasks, report = plan_import(
        package, sources_doc, policies, countries, domains, existing_tasks)

    if report['errors']:
        print('BLOCKED: import errors found', file=sys.stderr)
        for error in report['errors']:
            print(f'  {error}', file=sys.stderr)
        return 1

    tasks_before = read_jsonl(tasks_path)
    sources_text = dump_json(sources_after)
    tasks_text = dump_jsonl(list(tasks_before) + new_tasks)
    report_text = dump_json(report)

    if check:
        failures = []
        for path, text in ((sources_path, sources_text), (tasks_path, tasks_text),
                           (report_path, report_text)):
            path = Path(path)
            if not path.is_file() or path.read_text(encoding='utf-8') != text:
                failures.append(str(path))
        if failures:
            print('STALE: ' + ', '.join(failures), file=sys.stderr)
            return 1
        print(f'{len(report["imported_candidates"])} candidates and '
              f'{len(report["imported_tasks"])} tasks recorded; integration current')
        return 0

    Path(tasks_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(sources_path).write_text(sources_text, encoding='utf-8')
    Path(tasks_path).write_text(tasks_text, encoding='utf-8')
    Path(report_path).write_text(report_text, encoding='utf-8')
    print(f'{len(report["imported_candidates"])} candidates and '
          f'{len(report["imported_tasks"])} tasks recorded; report at {report_path}')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument('--sources', type=Path, default=DEFAULT_SOURCES)
    parser.add_argument('--tasks', type=Path, default=DEFAULT_TASKS)
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--policies', type=Path, default=DEFAULT_POLICIES)
    parser.add_argument('--countries', type=Path, default=DEFAULT_COUNTRIES)
    parser.add_argument('--domains', type=Path, default=DEFAULT_DOMAINS)
    parser.add_argument('--check', action='store_true',
                        help='fail if the canonical files differ from a fresh import')
    args = parser.parse_args()
    return run(args.package, args.sources, args.tasks, args.report, args.policies,
               args.countries, args.domains, args.check)


if __name__ == '__main__':
    raise SystemExit(main())
