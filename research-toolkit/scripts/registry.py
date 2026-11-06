#!/usr/bin/env python3
"""Derive the official-publisher registry and source-check records.

The registry is built from the hosts already cited by candidate leads and
published policy records. It records what is known: host, jurisdiction,
citation links and explicit unknowns. It does not fetch anything, does not
verify a publisher and does not create a source check that was not performed.

Source-check records start at ``not_checked``. A later retrieval process may
update them; this script only preserves recorded checks and adds a
``not_checked`` record for any new candidate.

Usage:

    python3 research-toolkit/scripts/registry.py
    python3 research-toolkit/scripts/registry.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
DEFAULT_POLICIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'policies.json'
DEFAULT_PUBLISHERS = REPO_ROOT / 'research-toolkit' / 'sources' / 'publishers.json'
DEFAULT_CHECKS = REPO_ROOT / 'research-toolkit' / 'sources' / 'source-checks.json'

AS_OF = '2026-11-06'
STALE_AFTER_DAYS = 180
PUBLISHER_NOTE = ('Derived from a cited source URL. Publisher name, authority type '
                  'and status remain unknown until a human reviewer records them.')
CHECK_NOTE = 'No retrieval has been attempted.'
RETRIEVAL_MIGRATION = {
    'not_checked': 'not_attempted',
    'reachable': 'success',
    'unchanged': 'success',
    'changed': 'success',
    'failed': 'failed',
    'blocked': 'blocked',
    'unknown': 'unknown',
}


def _check_from_previous(previous, candidate_id, publisher_id):
    if 'retrieval_status' in previous:
        return {
            'candidate_id': candidate_id,
            'publisher_id': publisher_id,
            'retrieval_status': previous.get('retrieval_status', 'not_attempted'),
            'attempted_at': previous.get('attempted_at'),
            'http_status': previous.get('http_status'),
            'final_url': previous.get('final_url'),
            'content_type': previous.get('content_type'),
            'error_category': previous.get('error_category'),
            'last_successful_retrieval': previous.get('last_successful_retrieval'),
            'legal_verification': previous.get('legal_verification') or {
                'status': 'unreviewed', 'evidence': None, 'reviewed_at': None,
            },
            'notes': (CHECK_NOTE if previous.get('notes') == 'No source check has been recorded.'
                      else previous.get('notes', CHECK_NOTE)),
        }
    legacy = previous.get('status')
    retrieval = RETRIEVAL_MIGRATION.get(legacy, 'not_attempted')
    attempted = previous.get('checked_at') if legacy not in (None, 'not_checked') else None
    return {
        'candidate_id': candidate_id,
        'publisher_id': publisher_id,
        'retrieval_status': retrieval,
        'attempted_at': attempted,
        'http_status': previous.get('http_status'),
        'final_url': previous.get('final_url'),
        'content_type': previous.get('content_type'),
        'error_category': None,
        'last_successful_retrieval': attempted if retrieval == 'success' else None,
        'legal_verification': {'status': 'unreviewed', 'evidence': None, 'reviewed_at': None},
        'notes': (CHECK_NOTE if previous.get('notes') == 'No source check has been recorded.'
                  else previous.get('notes', CHECK_NOTE)),
    }


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def host_of(url) -> str:
    if not isinstance(url, str):
        return ''
    parts = urlsplit(url.strip())
    if parts.scheme != 'https':
        return ''
    return (parts.hostname or '').lower()


def publisher_id(host: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', host.lower()).strip('-')


def publisher_url(host: str) -> str:
    return f'https://{host}/'


def _existing_by_host(document) -> dict:
    return {entry.get('host'): entry for entry in (document or {}).get('publishers', [])}


def _existing_checks(document) -> dict:
    return {entry.get('candidate_id'): entry for entry in (document or {}).get('checks', [])}


def derive(sources_doc, policies_doc, publishers_doc=None, checks_doc=None):
    """Return the desired publisher and source-check documents."""
    hosts = {}

    def add(host, jurisdiction, candidate=None, record=None):
        entry = hosts.setdefault(host, {'jurisdictions': set(), 'candidates': set(), 'records': set()})
        if jurisdiction:
            entry['jurisdictions'].add(jurisdiction)
        if candidate:
            entry['candidates'].add(candidate)
        if record:
            entry['records'].add(record)

    candidates = sources_doc.get('records', [])
    for candidate in candidates:
        host = host_of(candidate.get('source_url'))
        add(host, candidate.get('jurisdiction'), candidate=candidate.get('id'))
    for record in policies_doc:
        host = host_of(record.get('source_url'))
        add(host, record.get('country'), record=record.get('id'))
    hosts.pop('', None)

    previous_publishers = _existing_by_host(publishers_doc)
    publishers = []
    for host in sorted(hosts):
        previous = previous_publishers.get(host, {})
        entry = hosts[host]
        publishers.append({
            'id': publisher_id(host),
            'host': host,
            'url': publisher_url(host),
            'jurisdictions': sorted(entry['jurisdictions']),
            'publisher_name': previous.get('publisher_name'),
            'authority_type': previous.get('authority_type', 'unknown'),
            'verification_status': previous.get('verification_status', 'unverified'),
            'languages': sorted(previous.get('languages') or []),
            'monitoring': previous.get('monitoring', 'not_configured'),
            'retrieval_notes': previous.get('retrieval_notes', PUBLISHER_NOTE),
            'cited_by_candidates': sorted(entry['candidates']),
            'cited_by_records': sorted(entry['records']),
        })

    publisher_ids = {publisher['host']: publisher['id'] for publisher in publishers}
    previous_checks = _existing_checks(checks_doc)
    checks = []
    for candidate in sorted(candidates, key=lambda item: str(item.get('id'))):
        host = host_of(candidate.get('source_url'))
        previous = previous_checks.get(candidate.get('id'), {})
        checks.append(_check_from_previous(
            previous, candidate.get('id'), publisher_ids.get(host, '')))

    as_of = (checks_doc or {}).get('as_of') or AS_OF
    publishers_document = {
        'version': '1',
        'as_of': as_of,
        'note': ('Publisher identities are recorded from cited URLs only. '
                 'This registry does not verify authority, coverage or currency.'),
        'publishers': publishers,
    }
    checks_document = {
        'version': '2',
        'as_of': as_of,
        'stale_after_days': (checks_doc or {}).get('stale_after_days', STALE_AFTER_DAYS),
        'policy': ('Retrieval outcome, source freshness and legal verification are separate. '
                   'A successful request never verifies legal effect or currency, a failed '
                   'request does not erase an earlier successful retrieval, and no check is '
                   'evidence of absence.'),
        'checks': checks,
    }
    return publishers_document, checks_document


def run(sources_path=DEFAULT_SOURCES, policies_path=DEFAULT_POLICIES,
        publishers_path=DEFAULT_PUBLISHERS, checks_path=DEFAULT_CHECKS,
        check=False) -> int:
    sources_doc = read_json(sources_path)
    policies_doc = read_json(policies_path)
    publishers_path = Path(publishers_path)
    checks_path = Path(checks_path)
    publishers_doc = read_json(publishers_path) if publishers_path.is_file() else None
    checks_doc = read_json(checks_path) if checks_path.is_file() else None

    desired_publishers, desired_checks = derive(
        sources_doc, policies_doc, publishers_doc, checks_doc)
    publishers_text = dump_json(desired_publishers)
    checks_text = dump_json(desired_checks)

    if check:
        failures = []
        for path, text in ((publishers_path, publishers_text), (checks_path, checks_text)):
            if not path.is_file() or path.read_text(encoding='utf-8') != text:
                failures.append(str(path))
        if failures:
            print('STALE: ' + ', '.join(failures), file=sys.stderr)
            return 1
        print(f'{len(desired_publishers["publishers"])} publishers and '
              f'{len(desired_checks["checks"])} checks recorded; registry current')
        return 0

    publishers_path.write_text(publishers_text, encoding='utf-8')
    checks_path.write_text(checks_text, encoding='utf-8')
    print(f'{len(desired_publishers["publishers"])} publishers and '
          f'{len(desired_checks["checks"])} checks recorded')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=DEFAULT_SOURCES)
    parser.add_argument('--policies', type=Path, default=DEFAULT_POLICIES)
    parser.add_argument('--publishers', type=Path, default=DEFAULT_PUBLISHERS)
    parser.add_argument('--checks', type=Path, default=DEFAULT_CHECKS)
    parser.add_argument('--check', action='store_true',
                        help='fail if the registry files differ from a fresh derivation')
    args = parser.parse_args()
    return run(args.sources, args.policies, args.publishers, args.checks, args.check)


if __name__ == '__main__':
    raise SystemExit(main())
