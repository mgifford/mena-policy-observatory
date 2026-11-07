import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import build_view, load_coverage, load_i18n, sources_body
from framework.change_events import validate_source_captures

BASE = REPO_ROOT / 'regions' / 'mena'
TOOLKIT = REPO_ROOT / 'research-toolkit'


class CaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_coverage(BASE, TOOLKIT)
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))

    def errors(self, data):
        return validate_source_captures(
            data.source_captures, data.candidate_inventory['records'],
            data.publishers, data.source_checks, __import__('datetime').date(2026, 11, 7))

    def test_three_real_captures_are_recorded(self):
        self.assertEqual(len(self.data.source_captures), 3)
        ids = {capture['candidate_id'] for capture in self.data.source_captures}
        self.assertEqual(ids, {'mena-t02-002', 'bh-personal-data-30-2018',
                               'om-national-digital-accessibility'})
        self.assertEqual(self.errors(self.data), [])

    def test_capture_metadata_is_complete(self):
        for capture in self.data.source_captures:
            self.assertEqual(capture['http_status'], 200)
            self.assertRegex(capture['sha256'], r'^[0-9a-f]{64}$')
            self.assertGreater(capture['content_length'], 0)
            self.assertEqual(capture['retrieval_method'], 'http_get')
            self.assertEqual(capture['storage'], 'not_stored')
            self.assertIn(capture['language'], ('en', 'fr'))
            self.assertEqual(capture['captured_at'][:10], '2026-11-07')

    def test_capture_matches_latest_source_check(self):
        for capture in self.data.source_captures:
            check = next(item for item in self.data.source_checks
                         if item['candidate_id'] == capture['candidate_id'])
            self.assertEqual(check['retrieval_status'], 'success')
            self.assertEqual(check['last_successful_retrieval'], '2026-11-07')
            self.assertEqual(check['http_status'], capture['http_status'])
            self.assertEqual(check['final_url'], capture['final_url'])
            self.assertEqual(check['content_type'], capture['content_type'])

    def test_capture_does_not_promote_legal_verification(self):
        for capture in self.data.source_captures:
            check = next(item for item in self.data.source_checks
                         if item['candidate_id'] == capture['candidate_id'])
            self.assertEqual(check['legal_verification']['status'], 'unreviewed')

    def test_publishers_record_observed_identity(self):
        publishers = {publisher['host']: publisher for publisher in self.data.publishers}
        self.assertEqual(publishers['www.joradp.dz']['authority_type'], 'gazette')
        self.assertEqual(publishers['www.lloc.gov.bh']['authority_type'],
                         'legislation_portal')
        self.assertEqual(publishers['www.mtcit.gov.om']['authority_type'], 'ministry')
        for host in ('www.joradp.dz', 'www.lloc.gov.bh', 'www.mtcit.gov.om'):
            self.assertEqual(publishers[host]['verification_status'], 'unverified')
            self.assertTrue(publishers[host]['publisher_name'])

    def test_duplicate_capture_id_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.source_captures.append(copy.deepcopy(data.source_captures[0]))
        self.assertTrue(any('duplicate capture_id' in error for error in self.errors(data)))

    def test_unknown_candidate_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.source_captures[0]['candidate_id'] = 'missing-candidate'
        self.assertTrue(any('unknown candidate' in error for error in self.errors(data)))

    def test_invalid_checksum_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.source_captures[0]['sha256'] = 'not-a-checksum'
        self.assertTrue(any('sha256' in error for error in self.errors(data)))

    def test_invalid_timestamp_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.source_captures[0]['captured_at'] = '2026-11-07'
        self.assertTrue(any('captured_at must be an ISO 8601' in error
                            for error in self.errors(data)))

    def test_future_capture_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.source_captures[0]['captured_at'] = '2027-01-01T00:00:00Z'
        self.assertTrue(any('after the fixed as_of' in error for error in self.errors(data)))

    def test_source_check_mismatch_is_rejected(self):
        data = copy.deepcopy(self.data)
        check = next(item for item in data.source_checks
                     if item['candidate_id'] == data.source_captures[0]['candidate_id'])
        check['http_status'] = 404
        self.assertTrue(any('source-check http_status' in error for error in self.errors(data)))

    def test_missing_source_check_is_rejected(self):
        data = copy.deepcopy(self.data)
        candidate_id = data.source_captures[0]['candidate_id']
        data.source_checks = [check for check in data.source_checks
                              if check['candidate_id'] != candidate_id]
        self.assertTrue(any('has no source-check record' in error for error in self.errors(data)))

    def test_captured_version_is_rendered(self):
        body = sources_body(self.catalogues, 'en', build_view(self.data))
        self.assertIn('Captured versions', body)
        self.assertIn('Metadata and checksum recorded; bytes not stored', body)
        self.assertIn('cap-mena-t02-002-855ff487d526', body)
        self.assertIn('Successful', body)
        self.assertIn('Within the monitoring interval', body)
        self.assertIn('Unreviewed', body)

    def test_capture_rendering_french_and_arabic(self):
        fr = sources_body(self.catalogues, 'fr', build_view(self.data))
        self.assertIn('Versions capturées', fr)
        self.assertIn('Métadonnées et empreinte consignées', fr)
        ar = sources_body(self.catalogues, 'ar', build_view(self.data))
        self.assertIn('النسخ المسترجعة', ar)
        self.assertIn('سُجلت البيانات الوصفية والبصمة', ar)
        self.assertIn('<code lang="en" dir="ltr">cap-mena-t02-002-855ff487d526</code>', ar)

    def test_uncaptured_candidate_shows_empty_state(self):
        body = sources_body(self.catalogues, 'en', build_view(self.data))
        self.assertIn('No captured version is recorded.', body)

    def test_capture_inputs_are_not_mutated(self):
        data = copy.deepcopy(self.data)
        snapshot = copy.deepcopy(data.source_captures)
        self.errors(data)
        self.assertEqual(data.source_captures, snapshot)


if __name__ == '__main__':
    unittest.main()
