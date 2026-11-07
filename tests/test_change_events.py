import copy
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import build_view, load_coverage, load_i18n, sources_body
from framework.change_events import (
    derive_tasks,
    event_identity,
    review_status,
    run,
    validate_change_records,
)

BASE = REPO_ROOT / 'regions' / 'mena'
TOOLKIT = REPO_ROOT / 'research-toolkit'
AS_OF = date(2026, 11, 6)
CANDIDATES = [{
    'id': 'cand-1',
    'jurisdiction': 'DZ',
    'domains': ['digital_rights'],
    'source_url': 'https://example.gov/act',
}]
PUBLISHERS = [{'id': 'example-gov', 'host': 'example.gov', 'url': 'https://example.gov/'}]
INSTRUMENTS = [{'work_id': 'cand-1', 'candidate_id': 'cand-1'}]


def event(**overrides):
    value = {
        'event_id': 'evt-1',
        'candidate_id': 'cand-1',
        'instrument_id': 'cand-1',
        'publisher_id': 'example-gov',
        'jurisdiction': 'DZ',
        'detected_at': '2026-11-06T10:00:00Z',
        'detection_method': 'fixture',
        'retrieval_outcome': 'success',
        'technical_change': 'text_changed',
        'potential_legal_change': 'possible_amendment',
        'classification_status': 'potentially_substantive',
        'previous_ref': 'cap-1',
        'new_ref': 'cap-2',
        'evidence_refs': ['cap-1', 'cap-2'],
        'review_task_id': None,
        'notes': 'Synthetic fixture only.',
        'uncertainties': [],
    }
    value.update(overrides)
    return value


def decision(**overrides):
    value = {
        'decision_id': 'dec-1',
        'event_id': 'evt-1',
        'reviewed_at': '2026-11-06',
        'reviewer_role': 'Legal reviewer',
        'decision': 'confirmed_substantive_change',
        'legal_change': 'confirmed_amendment',
        'evidence_refs': ['cap-1', 'cap-2'],
        'explanation': 'Synthetic fixture decision only.',
        'uncertainties': [],
    }
    value.update(overrides)
    return value


def validate(events, decisions=None, tasks=None):
    decisions = decisions or []
    if tasks is None:
        tasks = derive_tasks(events, CANDIDATES, decisions)
    return validate_change_records(events, decisions, tasks, CANDIDATES,
                                   PUBLISHERS, INSTRUMENTS, AS_OF)


class ChangeEventValidationTests(unittest.TestCase):
    def test_new_observation_is_valid_and_creates_a_review_task(self):
        events = [event()]
        tasks = derive_tasks(events, CANDIDATES, [])
        self.assertEqual(validate(events, tasks=tasks), [])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['task_id'], 'CHG-EVT-1-REVIEW')
        self.assertEqual(tasks[0]['stage'], 'review')
        self.assertEqual(tasks[0]['status'], 'unstarted')
        self.assertTrue(tasks[0]['human_review_required'])
        self.assertEqual(tasks[0]['change_event_id'], 'evt-1')

    def test_repeated_observation_is_rejected(self):
        second = event(event_id='evt-2')
        errors = validate([event(), second], tasks=[])
        self.assertTrue(any('duplicate observation' in error for error in errors))

    def test_duplicate_event_id_is_rejected(self):
        errors = validate([event(), event(previous_ref='cap-3', new_ref='cap-4',
                                          evidence_refs=['cap-3', 'cap-4'])], tasks=[])
        self.assertTrue(any('duplicate event_id' in error for error in errors))

    def test_different_captures_of_one_source_are_allowed(self):
        second = event(event_id='evt-2', previous_ref='cap-3', new_ref='cap-4',
                       evidence_refs=['cap-3', 'cap-4'])
        events = [event(), second]
        tasks = derive_tasks(events, CANDIDATES, [])
        self.assertEqual(validate(events, tasks=tasks), [])
        self.assertEqual(len(tasks), 2)

    def test_missing_previous_capture_is_allowed(self):
        value = event(previous_ref=None, evidence_refs=['cap-2'])
        self.assertEqual(validate([value]), [])

    def test_missing_new_capture_is_allowed(self):
        value = event(new_ref=None, evidence_refs=['cap-1'],
                      technical_change='indeterminate', potential_legal_change='none',
                      classification_status='indeterminate')
        self.assertEqual(validate([value]), [])

    def test_failed_retrieval_cannot_assert_a_document_change(self):
        value = event(retrieval_outcome='failed')
        errors = validate([value], tasks=[])
        self.assertTrue(any('non-successful retrieval may not assert' in error
                            for error in errors))

    def test_byte_change_without_textual_change_is_valid_and_needs_no_task(self):
        value = event(technical_change='bytes_changed', potential_legal_change='none',
                      classification_status='technical_only')
        tasks = derive_tasks([value], CANDIDATES, [])
        self.assertEqual(validate([value], tasks=tasks), [])
        self.assertEqual(tasks, [])

    def test_textual_change_without_review_awaits_review(self):
        value = event()
        tasks = derive_tasks([value], CANDIDATES, [])
        self.assertEqual(review_status(value, {}), 'awaiting_review')
        self.assertEqual(tasks[0]['status'], 'unstarted')

    def test_invalid_event_identifier_is_rejected(self):
        errors = validate([event(event_id='Bad ID')], tasks=[])
        self.assertTrue(any('event_id must be a stable lowercase slug' in error
                            for error in errors))

    def test_unknown_instrument_is_rejected(self):
        errors = validate([event(instrument_id='missing-instrument')], tasks=[])
        self.assertTrue(any('unknown instrument' in error for error in errors))

    def test_evidence_refs_must_include_the_observed_versions(self):
        errors = validate([event(evidence_refs=['cap-1'])], tasks=[])
        self.assertTrue(any('must include new_ref' in error for error in errors))
        errors = validate([event(evidence_refs=[])], tasks=[])
        self.assertTrue(any('evidence_refs must be a nonempty' in error for error in errors))

    def test_invalid_and_future_timestamps_are_rejected(self):
        self.assertTrue(any('ISO 8601 timestamp' in error
                            for error in validate([event(detected_at='2026-11-06')],
                                                  tasks=[])))
        self.assertTrue(any('after the fixed as_of' in error
                            for error in validate([event(detected_at='2027-01-01T00:00:00Z')],
                                                  tasks=[])))

    def test_review_task_id_must_match_the_derived_task(self):
        errors = validate([event(review_task_id='CHG-OTHER-REVIEW')], tasks=[])
        self.assertTrue(any('review_task_id does not match' in error for error in errors))

    def test_unsupported_legal_promotion_is_rejected(self):
        errors = validate([event()], [decision(decision='no_substantive_change',
                                                legal_change='confirmed_amendment')])
        self.assertTrue(any('confirmed legal change needs' in error for error in errors))

    def test_review_decision_without_evidence_is_rejected(self):
        errors = validate([event()], [decision(evidence_refs=[])])
        self.assertTrue(any('evidence_refs must be a nonempty' in error for error in errors))

    def test_indeterminate_decision_keeps_task_open(self):
        events = [event()]
        decisions = [decision(decision='unable_to_determine', legal_change=None)]
        tasks = derive_tasks(events, CANDIDATES, decisions)
        self.assertEqual(validate(events, decisions, tasks), [])
        self.assertEqual(tasks[0]['status'], 'in_progress')
        self.assertEqual(review_status(events[0], {'evt-1': decisions[0]}), 'indeterminate')

    def test_valid_technical_only_review_closes_task(self):
        events = [event()]
        decisions = [decision(decision='technical_only', legal_change=None)]
        tasks = derive_tasks(events, CANDIDATES, decisions)
        self.assertEqual(validate(events, decisions, tasks), [])
        self.assertEqual(tasks[0]['status'], 'complete')
        self.assertEqual(review_status(events[0], {'evt-1': decisions[0]}),
                         'reviewed_technical')

    def test_confirmed_change_requires_a_decision(self):
        events = [event()]
        decisions = [decision()]
        tasks = derive_tasks(events, CANDIDATES, decisions)
        self.assertEqual(validate(events, decisions, tasks), [])
        self.assertEqual(tasks[0]['status'], 'complete')
        self.assertEqual(review_status(events[0], {'evt-1': decisions[0]}),
                         'reviewed_substantive')

    def test_stale_or_extra_task_is_rejected(self):
        events = [event()]
        tasks = derive_tasks(events, CANDIDATES, [])
        stale = copy.deepcopy(tasks)
        stale[0]['status'] = 'complete'
        self.assertTrue(any('is stale' in error for error in validate(events, tasks=stale)))
        extra = tasks + [{'task_id': 'CHG-EXTRA-REVIEW'}]
        self.assertTrue(any('unexpected review task' in error
                            for error in validate(events, tasks=extra)))

    def test_no_events_is_valid(self):
        self.assertEqual(validate([]), [])
        self.assertEqual(derive_tasks([], CANDIDATES, []), [])

    def test_validation_and_derivation_do_not_mutate_inputs(self):
        events = [event()]
        view = copy.deepcopy(events[0])
        validate(events)
        derive_tasks(events, CANDIDATES, [])
        self.assertEqual(events[0], view)

    def test_task_generation_is_idempotent(self):
        events = [event()]
        self.assertEqual(derive_tasks(events, CANDIDATES, []),
                         derive_tasks(events, CANDIDATES, []))


class ChangeEventRunTests(unittest.TestCase):
    def test_write_and_recheck_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            toolkit = Path(temporary)
            (toolkit / 'sources').mkdir()
            (toolkit / 'monitoring').mkdir()
            (toolkit / 'backlog').mkdir()
            (toolkit / 'sources' / 'candidate-sources.json').write_text(
                json.dumps({'records': CANDIDATES}), encoding='utf-8')
            (toolkit / 'sources' / 'publishers.json').write_text(
                json.dumps({'publishers': PUBLISHERS}), encoding='utf-8')
            (toolkit / 'sources' / 'instruments.json').write_text(
                json.dumps({'instruments': INSTRUMENTS}), encoding='utf-8')
            (toolkit / 'sources' / 'source-checks.json').write_text(
                json.dumps({'as_of': '2026-11-06'}), encoding='utf-8')
            (toolkit / 'monitoring' / 'change-events.jsonl').write_text(
                json.dumps(event()) + '\n', encoding='utf-8')
            (toolkit / 'monitoring' / 'review-decisions.jsonl').write_text('', encoding='utf-8')
            self.assertEqual(run(toolkit), 0)
            first = (toolkit / 'backlog' / 'tasks-change-review.jsonl').read_text(encoding='utf-8')
            self.assertEqual(run(toolkit), 0)
            second = (toolkit / 'backlog' / 'tasks-change-review.jsonl').read_text(encoding='utf-8')
            self.assertEqual(first, second)
            self.assertEqual(run(toolkit, check=True), 0)


class ChangeEventRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))
        cls.data = load_coverage(BASE, TOOLKIT)
        candidate = cls.data.candidate_inventory['records'][0]
        host = candidate['source_url'].split('/')[2]
        publisher = next(item for item in cls.data.publishers if item['host'] == host)
        instrument = next(item for item in cls.data.instruments
                          if item['candidate_id'] == candidate['id'])
        cls.change = event(
            event_id='evt-render-1',
            candidate_id=candidate['id'],
            instrument_id=instrument['work_id'],
            publisher_id=publisher['id'],
            jurisdiction=candidate['jurisdiction'],
            previous_ref='cap-render-1',
            new_ref='cap-render-2',
            evidence_refs=['cap-render-1', 'cap-render-2'],
        )
        cls.data.change_events = [cls.change]
        cls.data.change_tasks = derive_tasks(
            [cls.change], cls.data.candidate_inventory['records'], [])

    def test_english_change_status(self):
        body = sources_body(self.catalogues, 'en', build_view(self.data))
        self.assertIn('Source-change observations', body)
        self.assertIn('Possible amendment', body)
        self.assertIn('Awaiting human review', body)
        self.assertIn('CHG-EVT-RENDER-1-REVIEW', body)
        self.assertIn('A detected change to a source document does not necessarily indicate',
                      body)

    def test_confirmed_decision_is_rendered_separately(self):
        data = copy.deepcopy(self.data)
        decision = {
            'decision_id': 'dec-render-1',
            'event_id': self.change['event_id'],
            'reviewed_at': '2026-11-06',
            'reviewer_role': 'Legal reviewer',
            'decision': 'confirmed_substantive_change',
            'legal_change': 'confirmed_amendment',
            'evidence_refs': self.change['evidence_refs'],
            'explanation': 'Synthetic fixture decision only.',
            'uncertainties': [],
        }
        data.review_decisions = [decision]
        data.change_tasks = derive_tasks(
            [self.change], data.candidate_inventory['records'], [decision])
        body = sources_body(self.catalogues, 'en', build_view(data))
        self.assertIn('Reviewed: substantive change confirmed', body)
        self.assertIn('Confirmed amendment', body)

    def test_french_change_status(self):
        body = sources_body(self.catalogues, 'fr', build_view(self.data))
        self.assertIn('Observations de modification des sources', body)
        self.assertIn('Amendement possible', body)
        self.assertIn('En attente de revue humaine', body)

    def test_arabic_change_status_and_direction(self):
        body = sources_body(self.catalogues, 'ar', build_view(self.data))
        self.assertIn('ملاحظات تغيّر المصادر', body)
        self.assertIn('تعديل محتمل', body)
        self.assertIn('بانتظار المراجعة البشرية', body)
        self.assertIn('<code lang="en" dir="ltr">CHG-EVT-RENDER-1-REVIEW</code>', body)

    def test_no_events_shows_truthful_empty_state(self):
        data = load_coverage(BASE, TOOLKIT)
        body = sources_body(self.catalogues, 'en', build_view(data))
        self.assertIn('No source-change observations have been recorded.', body)


if __name__ == '__main__':
    unittest.main()
