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
            self.assertEqual(check['status'], 'not_checked')
            self.assertIsNone(check['checked_at'])
            self.assertIsNone(check['http_status'])
            self.assertIsNone(check['final_url'])
            self.assertIsNone(check['content_type'])

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

    def test_not_checked_with_a_date_is_rejected(self):
        self.data.source_checks[0]['checked_at'] = '2026-11-06'
        self.assertTrue(any('not_checked record may not carry' in error for error in self.errors()))

    def test_checked_status_needs_a_date(self):
        self.data.source_checks[0]['status'] = 'reachable'
        self.assertTrue(any('needs an ISO checked_at' in error for error in self.errors()))

    def test_missing_check_is_rejected(self):
        self.data.source_checks = self.data.source_checks[1:]
        self.assertTrue(any('has no source-check record' in error for error in self.errors()))

    def test_invalid_registry_as_of_is_rejected(self):
        self.data.registry_as_of = 'unknown'
        self.assertTrue(any('as_of must be an ISO date' in error for error in self.errors()))

    def test_recorded_check_marks_a_stale_source(self):
        check = self.data.source_checks[0]
        check.update({
            'status': 'reachable',
            'checked_at': '2024-01-01',
            'http_status': 200,
            'final_url': self.data.candidate_inventory['records'][0]['source_url'],
            'content_type': 'text/html',
        })
        view = build_view(self.data)
        candidate = next(item for item in view['candidates']
                         if item['id'] == check['candidate_id'])
        self.assertEqual(candidate['check_state'], 'stale')

    def test_recent_check_is_not_stale(self):
        check = self.data.source_checks[0]
        check.update({
            'status': 'unchanged',
            'checked_at': '2026-11-01',
            'http_status': 200,
            'final_url': self.data.candidate_inventory['records'][0]['source_url'],
            'content_type': 'text/html',
        })
        view = build_view(self.data)
        candidate = next(item for item in view['candidates']
                         if item['id'] == check['candidate_id'])
        self.assertEqual(candidate['check_state'], 'checked')


if __name__ == '__main__':
    unittest.main()
