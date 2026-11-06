import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / 'research-toolkit' / 'scripts'))

from framework.coverage import build_view, load_coverage, validate_coverage  # noqa: E402
from registry import derive, run  # noqa: E402

SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
POLICIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'policies.json'
PUBLISHERS = REPO_ROOT / 'research-toolkit' / 'sources' / 'publishers.json'
CHECKS = REPO_ROOT / 'research-toolkit' / 'sources' / 'source-checks.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_coverage()

    def test_committed_registry_is_current(self):
        self.assertEqual(run(check=True), 0)

    def test_registry_covers_every_cited_host(self):
        hosts = set()
        for candidate in load(SOURCES)['records']:
            hosts.add(urlsplit(candidate['source_url']).hostname)
        for record in load(POLICIES):
            hosts.add(urlsplit(record['source_url']).hostname)
        publishers = load(PUBLISHERS)['publishers']
        self.assertEqual({publisher['host'] for publisher in publishers}, hosts)
        self.assertEqual(len(publishers), len(hosts))

    def test_every_candidate_has_a_check_and_none_is_fabricated(self):
        checks = load(CHECKS)['checks']
        candidate_ids = {candidate['id'] for candidate in load(SOURCES)['records']}
        self.assertEqual({check['candidate_id'] for check in checks}, candidate_ids)
        for check in checks:
            self.assertEqual(check['retrieval_status'], 'not_attempted')
            self.assertIsNone(check['attempted_at'])
            self.assertIsNone(check['http_status'])
            self.assertIsNone(check['final_url'])
            self.assertIsNone(check['content_type'])
            self.assertIsNone(check['last_successful_retrieval'])
            self.assertEqual(check['legal_verification']['status'], 'unreviewed')

    def test_derivation_is_idempotent(self):
        sources = load(SOURCES)
        policies = load(POLICIES)
        first_publishers, first_checks = derive(sources, policies)
        second_publishers, second_checks = derive(
            sources, policies, first_publishers, first_checks)
        self.assertEqual(first_publishers, second_publishers)
        self.assertEqual(first_checks, second_checks)

    def test_write_and_recheck_in_temporary_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            publishers = root / 'publishers.json'
            checks = root / 'checks.json'
            self.assertEqual(run(SOURCES, POLICIES, publishers, checks), 0)
            first = (publishers.read_text(encoding='utf-8'),
                     checks.read_text(encoding='utf-8'))
            self.assertEqual(run(SOURCES, POLICIES, publishers, checks), 0)
            second = (publishers.read_text(encoding='utf-8'),
                      checks.read_text(encoding='utf-8'))
            self.assertEqual(first, second)
            self.assertEqual(run(SOURCES, POLICIES, publishers, checks, check=True), 0)

    def test_registry_validates_on_live_data(self):
        self.assertEqual(validate_coverage(self.data), [])


class RegistryValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = load_coverage()

    def errors(self):
        return validate_coverage(self.data)

    def test_missing_publisher_is_rejected(self):
        self.data.publishers = self.data.publishers[1:]
        self.assertTrue(any('no publisher entry' in error for error in self.errors()))

    def test_unknown_authority_type_is_rejected(self):
        self.data.publishers[0]['authority_type'] = 'newspaper'
        self.assertTrue(any('authority_type' in error for error in self.errors()))

    def test_publisher_id_must_match_host(self):
        self.data.publishers[0]['id'] = 'not-the-host'
        self.assertTrue(any('host slug' in error for error in self.errors()))

    def test_publisher_without_citations_is_rejected(self):
        publisher = copy.deepcopy(self.data.publishers[0])
        publisher['host'] = 'example.gov'
        publisher['id'] = 'example-gov'
        publisher['url'] = 'https://example.gov/'
        publisher['cited_by_candidates'] = []
        publisher['cited_by_records'] = []
        self.data.publishers.append(publisher)
        self.assertTrue(any('must cite at least one' in error for error in self.errors()))

    def test_check_for_unknown_candidate_is_rejected(self):
        check = copy.deepcopy(self.data.source_checks[0])
        check['candidate_id'] = 'missing-candidate'
        self.data.source_checks.append(check)
        self.assertTrue(any('unknown candidate' in error for error in self.errors()))

    def test_not_attempted_with_details_is_rejected(self):
        self.data.source_checks[0]['attempted_at'] = '2026-11-06'
        self.assertTrue(any('not_attempted record may not carry' in error
                            for error in self.errors()))

    def test_attempted_retrieval_needs_a_timestamp(self):
        self.data.source_checks[0]['retrieval_status'] = 'success'
        self.data.source_checks[0]['http_status'] = 200
        self.data.source_checks[0]['final_url'] = (
            self.data.candidate_inventory['records'][0]['source_url'])
        self.assertTrue(any('needs an ISO attempted_at' in error for error in self.errors()))

    def test_missing_check_is_rejected(self):
        self.data.source_checks = self.data.source_checks[1:]
        self.assertTrue(any('has no source-check record' in error for error in self.errors()))

    def test_invalid_registry_as_of_is_rejected(self):
        self.data.registry_as_of = 'unknown'
        self.assertTrue(any('as_of must be an ISO date' in error for error in self.errors()))

    def candidate_view(self, check):
        view = build_view(self.data)
        return next(item for item in view['candidates']
                    if item['id'] == check['candidate_id'])

    def source_url(self, check):
        return next(candidate['source_url']
                    for candidate in self.data.candidate_inventory['records']
                    if candidate['id'] == check['candidate_id'])

    def record_success(self, check, day):
        check.update({
            'retrieval_status': 'success',
            'attempted_at': day,
            'http_status': 200,
            'final_url': self.source_url(check),
            'content_type': 'text/html',
            'error_category': None,
            'last_successful_retrieval': day,
        })

    def test_never_checked_is_not_established(self):
        candidate = self.candidate_view(self.data.source_checks[0])
        self.assertEqual(candidate['retrieval_status'], 'not_attempted')
        self.assertEqual(candidate['freshness'], 'not_established')
        self.assertEqual(candidate['legal_verification']['status'], 'unreviewed')

    def test_successful_retrieval_is_fresh_but_not_legally_verified(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2026-11-01')
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['retrieval_status'], 'success')
        self.assertEqual(candidate['freshness'], 'within_interval')
        self.assertEqual(candidate['legal_verification']['status'], 'unreviewed')

    def test_failed_retrieval_is_not_a_success(self):
        check = self.data.source_checks[0]
        check.update({
            'retrieval_status': 'failed',
            'attempted_at': '2026-11-06',
            'error_category': 'timeout',
        })
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['retrieval_status'], 'failed')
        self.assertEqual(candidate['freshness'], 'not_established')

    def test_blocked_retrieval_is_reported(self):
        check = self.data.source_checks[0]
        check.update({
            'retrieval_status': 'blocked',
            'attempted_at': '2026-11-06',
            'error_category': 'blocked',
        })
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['retrieval_status'], 'blocked')

    def test_unknown_retrieval_is_reported(self):
        check = self.data.source_checks[0]
        check.update({'retrieval_status': 'unknown', 'attempted_at': '2026-11-06'})
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['retrieval_status'], 'unknown')

    def test_expired_freshness_interval(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2024-01-01')
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['freshness'], 'interval_exceeded')

    def test_failed_retrieval_keeps_earlier_success(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2026-10-01')
        check.update({
            'retrieval_status': 'failed',
            'attempted_at': '2026-11-06',
            'error_category': 'http_error',
            'http_status': 503,
            'final_url': None,
            'content_type': None,
        })
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['retrieval_status'], 'failed')
        self.assertEqual(check['last_successful_retrieval'], '2026-10-01')
        self.assertEqual(candidate['freshness'], 'within_interval')

    def test_successful_retrieval_needs_last_successful_date(self):
        check = self.data.source_checks[0]
        check.update({
            'retrieval_status': 'success',
            'attempted_at': '2026-11-01',
            'http_status': 200,
            'final_url': self.source_url(check),
        })
        self.assertTrue(any('needs last_successful_retrieval' in error for error in self.errors()))

    def test_last_successful_retrieval_cannot_follow_attempt(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2026-11-01')
        check['last_successful_retrieval'] = '2026-11-02'
        self.assertTrue(any('is after attempted_at' in error for error in self.errors()))

    def test_freshness_uses_the_fixed_as_of_date(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2020-12-01')
        self.data.registry_as_of = '2020-12-31'
        self.assertEqual(self.candidate_view(check)['freshness'], 'within_interval')

    def test_future_dated_retrieval_is_rejected(self):
        check = self.data.source_checks[0]
        check.update({
            'retrieval_status': 'failed',
            'attempted_at': '2027-01-01',
            'error_category': 'other',
        })
        self.assertTrue(any('attempted_at is after the registry as_of' in error
                            for error in self.errors()))

    def test_future_dated_success_is_unknown_not_fresh(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2027-01-01')
        candidate = self.candidate_view(check)
        self.assertEqual(candidate['freshness'], 'unknown')

    def test_legal_verification_cannot_be_promoted_without_evidence(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2026-11-01')
        check['legal_verification'] = {
            'status': 'verified', 'evidence': None, 'reviewed_at': None,
        }
        self.assertTrue(any('needs recorded evidence' in error for error in self.errors()))
        self.assertTrue(any('needs an ISO reviewed_at' in error for error in self.errors()))

    def test_valid_legal_verification_requires_evidence_and_date(self):
        check = self.data.source_checks[0]
        self.record_success(check, '2026-11-01')
        check['legal_verification'] = {
            'status': 'verified', 'evidence': 'Recorded reviewer evidence',
            'reviewed_at': '2026-11-05',
        }
        self.assertEqual(self.errors(), [])


if __name__ == '__main__':
    unittest.main()
