#!/usr/bin/env python3
"""Validate source-change observations, human review decisions and review tasks.

The model keeps three things separate:

* a retrieval outcome;
* an observed document change;
* a reviewed legal classification.

A change event records what was observed. A review decision records what a
human reviewer concluded. Neither can promote a source into a verified legal
finding, and neither changes a policy record's legal effect.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, date
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TOOLKIT = REPO_ROOT / 'research-toolkit'
EVENT_FILE = 'monitoring/change-events.jsonl'
DECISION_FILE = 'monitoring/review-decisions.jsonl'
TASK_FILE = 'backlog/tasks-change-review.jsonl'
CAPTURE_FILE = 'monitoring/source-captures.jsonl'

RETRIEVAL_OUTCOMES = ('success', 'failed', 'blocked', 'not_attempted', 'unknown')
TECHNICAL_CHANGES = (
    'new_content', 'bytes_changed', 'text_changed', 'metadata_changed',
    'url_changed', 'format_changed', 'no_observed_change', 'indeterminate',
)
POTENTIAL_LEGAL_CHANGES = (
    'possible_new_instrument', 'possible_amendment', 'possible_repeal',
    'possible_correction', 'possible_consolidation',
    'possible_translation_update', 'possible_effective_date_change',
    'relationship_unresolved', 'none',
)
CLASSIFICATION_STATUSES = (
    'observation', 'technical_only', 'potentially_substantive', 'indeterminate',
)
DETECTION_METHODS = ('manual_review', 'source_check', 'fixture', 'other')
REVIEW_DECISIONS = (
    'no_substantive_change', 'confirmed_substantive_change', 'technical_only',
    'further_evidence_required', 'interpretation_pending',
    'translation_review_required', 'unable_to_determine',
)
LEGAL_CHANGES = (
    'confirmed_amendment', 'confirmed_repeal', 'confirmed_correction',
    'confirmed_consolidation', 'confirmed_translation_update',
    'no_substantive_change', 'indeterminate',
)
CONFIRMED_LEGAL_CHANGES = (
    'confirmed_amendment', 'confirmed_repeal', 'confirmed_correction',
    'confirmed_consolidation', 'confirmed_translation_update',
)
CAPTURE_METHODS = ('http_get', 'manual', 'other')
CAPTURE_STORAGE = ('not_stored', 'stored_elsewhere')
SLUG = re.compile(r'^[a-z0-9-]+$')
SHA256 = re.compile(r'^[0-9a-f]{64}$')
BCP47 = re.compile(r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$')
TIMESTAMP = re.compile(
    r'^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+-][0-9]{2}:[0-9]{2})$')
ISO_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.is_file():
        return []
    rows = []
    for index, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f'{path}:{index}: invalid JSON: {exc}') from exc
        if not isinstance(value, dict):
            raise ValueError(f'{path}:{index}: expected an object')
        rows.append(value)
    return rows


def dump_jsonl(rows) -> str:
    return ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)


def load_change_events(toolkit=DEFAULT_TOOLKIT) -> list[dict]:
    return read_jsonl(Path(toolkit) / EVENT_FILE)


def load_review_decisions(toolkit=DEFAULT_TOOLKIT) -> list[dict]:
    return read_jsonl(Path(toolkit) / DECISION_FILE)


def load_change_tasks(toolkit=DEFAULT_TOOLKIT) -> list[dict]:
    return read_jsonl(Path(toolkit) / TASK_FILE)


def load_source_captures(toolkit=DEFAULT_TOOLKIT) -> list[dict]:
    return read_jsonl(Path(toolkit) / CAPTURE_FILE)


def timestamp_date(value) -> date | None:
    if not isinstance(value, str) or not TIMESTAMP.match(value):
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
    except ValueError:
        return None


def event_identity(event) -> tuple:
    """Identity of one observed difference, independent of event_id."""
    return (
        event.get('candidate_id'),
        event.get('previous_ref'),
        event.get('new_ref'),
        event.get('technical_change'),
    )


def review_task_id(event_id: str) -> str:
    return f'CHG-{str(event_id).upper()}-REVIEW'


def latest_decisions(decisions) -> dict:
    """Return the last recorded decision per event, preserving order."""
    latest = {}
    for decision in decisions:
        latest[decision.get('event_id')] = decision
    return latest


def review_status(event, latest) -> str:
    decision = latest.get(event.get('event_id'))
    if decision:
        mapping = {
            'no_substantive_change': 'reviewed_no_change',
            'confirmed_substantive_change': 'reviewed_substantive',
            'technical_only': 'reviewed_technical',
            'further_evidence_required': 'further_evidence',
            'interpretation_pending': 'interpretation_pending',
            'translation_review_required': 'translation_review',
            'unable_to_determine': 'indeterminate',
        }
        return mapping.get(decision.get('decision'), 'indeterminate')
    if (event.get('potential_legal_change') not in (None, 'none')
            or event.get('classification_status') == 'potentially_substantive'):
        return 'awaiting_review'
    return 'not_required'


def derive_tasks(events, candidates, decisions) -> list[dict]:
    candidate_map = {candidate.get('id'): candidate for candidate in candidates}
    latest = latest_decisions(decisions)
    tasks = []
    for event in events:
        needs_review = (event.get('potential_legal_change') not in (None, 'none')
                        or event.get('classification_status') == 'potentially_substantive')
        if not needs_review:
            continue
        candidate = candidate_map.get(event.get('candidate_id'))
        if not candidate:
            continue
        domains = list(candidate.get('domains') or [])
        if not domains:
            continue
        decision = latest.get(event.get('event_id'))
        if decision is None:
            status = 'unstarted'
        elif decision.get('decision') in ('further_evidence_required',
                                          'interpretation_pending',
                                          'translation_review_required',
                                          'unable_to_determine'):
            status = 'in_progress'
        else:
            status = 'complete'
        tasks.append({
            'task_id': review_task_id(event.get('event_id')),
            'jurisdiction': event.get('jurisdiction'),
            'domain': domains[0],
            'question': ('A source document appears to have changed. Determine whether this '
                         'reflects an amendment, correction, consolidation, translation '
                         'update, technical replacement, or another event, and record the '
                         'evidence and remaining uncertainty.'),
            'stage': 'review',
            'status': status,
            'human_review_required': True,
            'source_lead_ids': [event.get('candidate_id')],
            'deliverable': 'Recorded review decision with evidence and remaining uncertainty',
            'change_event_id': event.get('event_id'),
        })
    return sorted(tasks, key=lambda task: task['task_id'])


def _validate_event(event, label, candidate_map, publisher_map, instrument_map,
                    as_of, errors, seen_ids, seen_identities):
    event_id = event.get('event_id')
    if not isinstance(event_id, str) or not SLUG.match(event_id):
        errors.append(f'{label}: event_id must be a stable lowercase slug')
    elif event_id in seen_ids:
        errors.append(f'{label}: duplicate event_id')
    else:
        seen_ids.add(event_id)
    identity = event_identity(event)
    if identity in seen_identities:
        errors.append(f'{label}: duplicate observation for the same candidate, references '
                      'and technical change')
    else:
        seen_identities.add(identity)
    candidate_id = event.get('candidate_id')
    candidate = candidate_map.get(candidate_id)
    if candidate is None:
        errors.append(f'{label}: unknown candidate {candidate_id!r}')
    else:
        if event.get('jurisdiction') != candidate.get('jurisdiction'):
            errors.append(f'{label}: jurisdiction does not match the candidate')
        host = ''
        if isinstance(candidate.get('source_url'), str):
            host = (urlsplit(candidate['source_url']).hostname or '').lower()
        publisher = publisher_map.get(event.get('publisher_id'))
        if publisher is None:
            errors.append(f'{label}: unknown publisher {event.get("publisher_id")!r}')
        elif publisher.get('host') != host:
            errors.append(f'{label}: publisher does not match the candidate host')
    instrument_id = event.get('instrument_id')
    if instrument_id is not None:
        instrument = instrument_map.get(instrument_id)
        if instrument is None:
            errors.append(f'{label}: unknown instrument {instrument_id!r}')
        elif instrument.get('candidate_id') != candidate_id:
            errors.append(f'{label}: instrument does not belong to the candidate')
    if event.get('detection_method') not in DETECTION_METHODS:
        errors.append(f'{label}: unknown detection_method')
    if event.get('retrieval_outcome') not in RETRIEVAL_OUTCOMES:
        errors.append(f'{label}: unknown retrieval_outcome')
    if event.get('technical_change') not in TECHNICAL_CHANGES:
        errors.append(f'{label}: unknown technical_change')
    if event.get('potential_legal_change') not in POTENTIAL_LEGAL_CHANGES:
        errors.append(f'{label}: unknown potential_legal_change')
    if event.get('classification_status') not in CLASSIFICATION_STATUSES:
        errors.append(f'{label}: unknown classification_status')
    if event.get('technical_change') == 'no_observed_change' and \
            event.get('potential_legal_change') != 'none':
        errors.append(f'{label}: no observed change cannot be a potential legal change')
    if event.get('classification_status') == 'technical_only' and \
            event.get('potential_legal_change') != 'none':
        errors.append(f'{label}: technical_only cannot carry a potential legal change')
    if event.get('classification_status') == 'potentially_substantive' and \
            event.get('potential_legal_change') == 'none':
        errors.append(f'{label}: potentially_substantive needs a potential legal change')
    if event.get('retrieval_outcome') != 'success':
        if event.get('technical_change') != 'indeterminate' or \
                event.get('potential_legal_change') != 'none':
            errors.append(f'{label}: a non-successful retrieval may not assert a document change')
    detected = timestamp_date(event.get('detected_at'))
    if detected is None:
        errors.append(f'{label}: detected_at must be an ISO 8601 timestamp with a zone')
    elif as_of is not None and detected > as_of:
        errors.append(f'{label}: detected_at is after the fixed as_of date')
    previous_ref = event.get('previous_ref')
    new_ref = event.get('new_ref')
    for field, value in (('previous_ref', previous_ref), ('new_ref', new_ref)):
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f'{label}: {field} must be a nonempty string or null')
    if previous_ref is None and new_ref is None:
        errors.append(f'{label}: at least one evidence reference is required')
    evidence = event.get('evidence_refs')
    if not isinstance(evidence, list) or not evidence or \
            not all(isinstance(item, str) and item.strip() for item in evidence):
        errors.append(f'{label}: evidence_refs must be a nonempty array of strings')
    elif isinstance(evidence, list):
        for field, value in (('previous_ref', previous_ref), ('new_ref', new_ref)):
            if value is not None and value not in evidence:
                errors.append(f'{label}: evidence_refs must include {field}')
    uncertainties = event.get('uncertainties')
    if not isinstance(uncertainties, list) or \
            not all(isinstance(item, str) and item.strip() for item in uncertainties):
        errors.append(f'{label}: uncertainties must be an array of nonempty strings')
    if event.get('review_task_id') is not None and \
            event.get('review_task_id') != review_task_id(event_id or ''):
        errors.append(f'{label}: review_task_id does not match the derived task id')
    if event.get('notes') is not None and not isinstance(event.get('notes'), str):
        errors.append(f'{label}: notes must be a string or null')


def _validate_decision(decision, label, event_ids, as_of, errors, seen_ids):
    decision_id = decision.get('decision_id')
    if not isinstance(decision_id, str) or not SLUG.match(decision_id):
        errors.append(f'{label}: decision_id must be a stable lowercase slug')
    elif decision_id in seen_ids:
        errors.append(f'{label}: duplicate decision_id')
    else:
        seen_ids.add(decision_id)
    if decision.get('event_id') not in event_ids:
        errors.append(f'{label}: unknown event_id')
    reviewed = decision.get('reviewed_at')
    reviewed_date = None
    if isinstance(reviewed, str) and ISO_DATE.match(reviewed):
        try:
            reviewed_date = date.fromisoformat(reviewed)
        except ValueError:
            reviewed_date = None
    if reviewed_date is None:
        errors.append(f'{label}: reviewed_at must be a valid ISO date')
    elif as_of is not None and reviewed_date > as_of:
        errors.append(f'{label}: reviewed_at is after the fixed as_of date')
    if not isinstance(decision.get('reviewer_role'), str) or \
            not decision['reviewer_role'].strip():
        errors.append(f'{label}: reviewer_role must be nonempty')
    outcome = decision.get('decision')
    if outcome not in REVIEW_DECISIONS:
        errors.append(f'{label}: unknown decision {outcome!r}')
    legal = decision.get('legal_change')
    if legal is not None and legal not in LEGAL_CHANGES:
        errors.append(f'{label}: unknown legal_change {legal!r}')
    if legal in CONFIRMED_LEGAL_CHANGES and outcome != 'confirmed_substantive_change':
        errors.append(f'{label}: a confirmed legal change needs a confirmed_substantive_change '
                      'decision')
    if outcome == 'confirmed_substantive_change' and legal not in CONFIRMED_LEGAL_CHANGES:
        errors.append(f'{label}: confirmed_substantive_change needs a confirmed legal change')
    if outcome == 'no_substantive_change' and legal not in (None, 'no_substantive_change'):
        errors.append(f'{label}: no_substantive_change contradicts {legal!r}')
    if outcome == 'technical_only' and legal not in (None, 'no_substantive_change'):
        errors.append(f'{label}: technical_only contradicts {legal!r}')
    if outcome in ('further_evidence_required', 'interpretation_pending',
                   'translation_review_required', 'unable_to_determine') and \
            legal not in (None, 'indeterminate'):
        errors.append(f'{label}: {outcome} cannot carry a confirmed legal change')
    evidence = decision.get('evidence_refs')
    if not isinstance(evidence, list) or not evidence or \
            not all(isinstance(item, str) and item.strip() for item in evidence):
        errors.append(f'{label}: evidence_refs must be a nonempty array of strings')
    if not isinstance(decision.get('explanation'), str) or not decision['explanation'].strip():
        errors.append(f'{label}: explanation must be nonempty')
    uncertainties = decision.get('uncertainties')
    if not isinstance(uncertainties, list) or \
            not all(isinstance(item, str) and item.strip() for item in uncertainties):
        errors.append(f'{label}: uncertainties must be an array of nonempty strings')


def validate_source_captures(captures, candidates, publishers, checks, as_of=None) -> list[str]:
    """Validate captured source items and their link to the latest source check."""
    errors: list[str] = []
    candidate_map = {candidate.get('id'): candidate for candidate in candidates}
    publisher_map = {publisher.get('id'): publisher for publisher in publishers}
    check_map = {check.get('candidate_id'): check for check in checks}
    seen = set()
    by_candidate = {}
    for index, capture in enumerate(captures, start=1):
        capture_id = capture.get('capture_id')
        label = f'capture {capture_id or index}'
        if not isinstance(capture_id, str) or not SLUG.match(capture_id):
            errors.append(f'{label}: capture_id must be a stable lowercase slug')
        elif capture_id in seen:
            errors.append(f'{label}: duplicate capture_id')
        else:
            seen.add(capture_id)
        candidate_id = capture.get('candidate_id')
        candidate = candidate_map.get(candidate_id)
        if candidate is None:
            errors.append(f'{label}: unknown candidate {candidate_id!r}')
        publisher = publisher_map.get(capture.get('publisher_id'))
        if publisher is None:
            errors.append(f'{label}: unknown publisher {capture.get("publisher_id")!r}')
        elif candidate is not None:
            host = (urlsplit(str(candidate.get('source_url') or '')).hostname or '').lower()
            if publisher.get('host') != host:
                errors.append(f'{label}: publisher does not match the candidate host')
        for field in ('url', 'final_url'):
            value = capture.get(field)
            if not isinstance(value, str) or not value.startswith('https://'):
                errors.append(f'{label}: {field} must be an https URL')
        captured = timestamp_date(capture.get('captured_at'))
        if captured is None:
            errors.append(f'{label}: captured_at must be an ISO 8601 timestamp with a zone')
        elif as_of is not None and captured > as_of:
            errors.append(f'{label}: captured_at is after the fixed as_of date')
        http_status = capture.get('http_status')
        if not isinstance(http_status, int) or isinstance(http_status, bool) or \
                not 100 <= http_status <= 599:
            errors.append(f'{label}: http_status must be an integer HTTP status')
        content_type = capture.get('content_type')
        if not isinstance(content_type, str) or not content_type.strip():
            errors.append(f'{label}: content_type must be nonempty')
        length = capture.get('content_length')
        if not isinstance(length, int) or isinstance(length, bool) or length < 0:
            errors.append(f'{label}: content_length must be a nonnegative integer')
        if not isinstance(capture.get('sha256'), str) or not SHA256.match(capture['sha256']):
            errors.append(f'{label}: sha256 must be 64 lowercase hex characters')
        if capture.get('retrieval_method') not in CAPTURE_METHODS:
            errors.append(f'{label}: unknown retrieval_method')
        if capture.get('storage') not in CAPTURE_STORAGE:
            errors.append(f'{label}: unknown storage state')
        if not isinstance(capture.get('language'), str) or not BCP47.match(capture['language']):
            errors.append(f'{label}: language must be a BCP47 tag')
        if not isinstance(capture.get('notes'), str) or not capture['notes'].strip():
            errors.append(f'{label}: notes must be nonempty')
        by_candidate.setdefault(candidate_id, []).append(capture)

    for candidate_id, items in by_candidate.items():
        latest = max(items, key=lambda capture: str(capture.get('captured_at')))
        check = check_map.get(candidate_id)
        if check is None:
            errors.append(f'capture: candidate {candidate_id!r} has no source-check record')
            continue
        latest_date = timestamp_date(latest.get('captured_at'))
        if check.get('retrieval_status') != 'success':
            errors.append(f'capture {latest.get("capture_id")}: source check is not successful')
        if latest_date and check.get('last_successful_retrieval') != latest_date.isoformat():
            errors.append(f'capture {latest.get("capture_id")}: '
                          'last_successful_retrieval does not match the latest capture')
        attempted = check.get('attempted_at')
        if latest_date and isinstance(attempted, str) and ISO_DATE.match(attempted):
            try:
                attempted_date = date.fromisoformat(attempted)
            except ValueError:
                attempted_date = None
            if attempted_date and attempted_date < latest_date:
                errors.append(f'capture {latest.get("capture_id")}: '
                              'source-check attempted_at is before the latest capture')
        for field in ('http_status', 'final_url', 'content_type'):
            if check.get(field) != latest.get(field):
                errors.append(f'capture {latest.get("capture_id")}: source-check {field} '
                              'does not match the latest capture')
    return errors


def validate_change_records(events, decisions, tasks, candidates, publishers,
                            instruments, as_of=None) -> list[str]:
    """Validate events, decisions and the derived review-task queue."""
    errors: list[str] = []
    candidate_map = {candidate.get('id'): candidate for candidate in candidates}
    publisher_map = {publisher.get('id'): publisher for publisher in publishers}
    instrument_map = {instrument.get('work_id'): instrument for instrument in instruments}
    seen_ids, seen_identities = set(), set()
    for index, event in enumerate(events, start=1):
        _validate_event(event, f'event {index}', candidate_map, publisher_map,
                        instrument_map, as_of, errors, seen_ids, seen_identities)
    event_ids = {event.get('event_id') for event in events}
    decision_ids = set()
    for index, decision in enumerate(decisions, start=1):
        _validate_decision(decision, f'decision {index}', event_ids, as_of,
                           errors, decision_ids)
    expected = derive_tasks(events, candidates, decisions)
    actual = {task.get('task_id'): task for task in tasks}
    for task in expected:
        if task['task_id'] not in actual:
            errors.append(f'tasks: missing derived review task {task["task_id"]}')
        elif actual[task['task_id']] != task:
            errors.append(f'tasks: review task {task["task_id"]} is stale')
    for task_id in sorted(set(actual) - {task['task_id'] for task in expected}):
        errors.append(f'tasks: unexpected review task {task_id}')
    return errors


def run(toolkit=DEFAULT_TOOLKIT, check=False) -> int:
    toolkit = Path(toolkit)
    candidates = json.loads((toolkit / 'sources' / 'candidate-sources.json')
                            .read_text(encoding='utf-8'))['records']
    publishers = json.loads((toolkit / 'sources' / 'publishers.json')
                            .read_text(encoding='utf-8'))['publishers']
    instruments = json.loads((toolkit / 'sources' / 'instruments.json')
                             .read_text(encoding='utf-8'))['instruments']
    checks = json.loads((toolkit / 'sources' / 'source-checks.json')
                        .read_text(encoding='utf-8'))
    as_of = None
    if isinstance(checks.get('as_of'), str) and ISO_DATE.match(checks['as_of']):
        try:
            as_of = date.fromisoformat(checks['as_of'])
        except ValueError:
            as_of = None
    events = read_jsonl(toolkit / EVENT_FILE)
    decisions = read_jsonl(toolkit / DECISION_FILE)
    tasks = read_jsonl(toolkit / TASK_FILE)
    captures = read_jsonl(toolkit / CAPTURE_FILE)
    checks = json.loads((toolkit / 'sources' / 'source-checks.json')
                        .read_text(encoding='utf-8')).get('checks', [])
    expected = dump_jsonl(derive_tasks(events, candidates, decisions))
    expected_tasks = derive_tasks(events, candidates, decisions)
    path = toolkit / TASK_FILE
    validation_tasks = tasks if check else expected_tasks
    errors = validate_change_records(events, decisions, validation_tasks, candidates,
                                     publishers, instruments, as_of)
    errors.extend(validate_source_captures(captures, candidates, publishers, checks, as_of))
    if not check and not errors:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expected, encoding='utf-8')
    if errors:
        for error in errors:
            print(error)
        return 1
    if check:
        current = path.read_text(encoding='utf-8') if path.is_file() else ''
        if current != expected:
            print(f'STALE: {path}')
            return 1
    print(f'{len(events)} change events, {len(decisions)} review decisions, '
          f'{len(derive_tasks(events, candidates, decisions))} review tasks, '
          f'{len(captures)} captures')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolkit', type=Path, default=DEFAULT_TOOLKIT)
    parser.add_argument('--check', action='store_true',
                        help='validate and fail if the derived task queue is stale')
    args = parser.parse_args()
    return run(args.toolkit, args.check)


if __name__ == '__main__':
    raise SystemExit(main())
