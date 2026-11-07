import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'research-toolkit' / 'scripts'))

from import_tranche import (  # noqa: E402
    PACKAGE_LABEL,
    candidate_id,
    instrument_key,
    normalize_url,
    plan_import,
    run,
)

PACKAGE = REPO_ROOT / 'research-toolkit' / 'incoming' / 'tranche-02'
SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
POLICIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'policies.json'
COUNTRIES = REPO_ROOT / 'regions' / 'mena' / 'data' / 'countries.json'
DOMAINS = REPO_ROOT / 'regions' / 'mena' / 'data' / 'domains.json'
REPORT = REPO_ROOT / 'research-toolkit' / 'reconciliation' / 'tranche-02-report.json'


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def load_package_records():
    return load_json(PACKAGE / 'candidate-sources.json')['records']


def load_package_tasks():
    return [json.loads(line) for line
            in (PACKAGE / 'tasks.jsonl').read_text(encoding='utf-8').splitlines()
            if line.strip()]


class TrancheImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policies = load_json(POLICIES)
        cls.countries = load_json(COUNTRIES)
        cls.domains = load_json(DOMAINS)['domains']
        cls.records = load_package_records()
        cls.tasks = load_package_tasks()

    def package(self, records=None, tasks=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        document = load_json(PACKAGE / 'candidate-sources.json')
        document['records'] = records if records is not None else [copy.deepcopy(self.records[0])]
        (root / 'candidate-sources.json').write_text(
            json.dumps(document, ensure_ascii=False), encoding='utf-8')
        task_rows = tasks if tasks is not None else [copy.deepcopy(self.tasks[0])]
        (root / 'tasks.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in task_rows),
            encoding='utf-8')
        return root

    def plan(self, package, sources, existing_tasks=None):
        return plan_import(package, sources, self.policies, self.countries, self.domains,
                           existing_tasks or [])

    def import_into_temp(self, package, root):
        sources_path = root / 'sources.json'
        if not sources_path.exists():
            sources_path.write_text(json.dumps({'version': '1', 'records': []}),
                                    encoding='utf-8')
        tasks_path = root / 'tasks.jsonl'
        report_path = root / 'report.json'
        code = run(package, sources_path, tasks_path, report_path, POLICIES, COUNTRIES, DOMAINS)
        return code, sources_path, tasks_path, report_path

    def empty_inventory(self):
        return {'version': '1', 'records': []}

    def test_normalize_url_ignores_trailing_slash_and_host_case(self):
        self.assertEqual(normalize_url('https://Example.GOV/a/'),
                         normalize_url('https://example.gov/a'))

    def test_instrument_key_uses_the_primary_instrument(self):
        self.assertEqual(instrument_key('Law 38 of 2013 on care of persons'), '38|2013')
        self.assertEqual(instrument_key('Law 11 of 2024, first amendment to Law 38 of 2013'),
                         '11|2024')
        self.assertEqual(instrument_key('Law 25-11 of 2025 amending Law 18-07'), '25-11|2025')

    def test_valid_package_imports_once(self):
        sources_after, tasks, report = self.plan(self.package(), self.empty_inventory())
        self.assertEqual(report['result'], 'ok')
        self.assertEqual(len(report['imported_candidates']), 1)
        self.assertEqual(len(report['imported_tasks']), 1)
        self.assertEqual(len(sources_after['records']), 1)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['source_lead_ids'], [candidate_id(self.records[0]['candidate_id'])])
        self.assertEqual(sources_after['records'][0]['legal_effect'], 'not_assessed')
        self.assertEqual(sources_after['records'][0]['capture_status'], 'not_captured')
        self.assertEqual(sources_after['imported_packages'][0]['package'], PACKAGE_LABEL)

    def test_repeated_import_is_idempotent(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        code, sources_path, tasks_path, report_path = self.import_into_temp(self.package(), root)
        self.assertEqual(code, 0)
        first = {path.name: path.read_text(encoding='utf-8')
                 for path in (sources_path, tasks_path, report_path)}
        code, _, _, _ = self.import_into_temp(self.package(), root)
        self.assertEqual(code, 0)
        second = {path.name: path.read_text(encoding='utf-8')
                  for path in (sources_path, tasks_path, report_path)}
        self.assertEqual(first, second)
        self.assertEqual(len(json.loads(first['sources.json'])['records']), 1)
        self.assertEqual(len([line for line in first['tasks.jsonl'].splitlines() if line]), 1)

    def test_existing_source_url_is_matched_not_reimported(self):
        sources = {'records': [{
            'id': 'existing-lead',
            'jurisdiction': self.records[0]['jurisdiction'],
            'instrument_title': 'Existing recorded title',
            'source_url': self.records[0]['source_url'].rstrip('/') + '/',
            'domains': ['digital_rights'],
        }]}
        sources_after, _, report = self.plan(self.package(), sources)
        self.assertEqual(report['imported_candidates'], [])
        self.assertEqual(report['matched_candidates'][0]['reason'], 'same_source_url')
        self.assertEqual(len(sources_after['records']), 1)

    def test_possible_duplicate_instrument_is_held_for_review(self):
        sources = {'records': [{
            'id': 'existing-lead',
            'jurisdiction': self.records[0]['jurisdiction'],
            'instrument_title': 'Law 18-07 of 2018 (consolidated text)',
            'source_url': 'https://example.gov/consolidated',
            'domains': ['digital_rights'],
        }]}
        sources_after, _, report = self.plan(self.package(), sources)
        self.assertEqual(report['imported_candidates'], [])
        self.assertEqual(report['possible_duplicates'][0]['reason'],
                         'same_jurisdiction_and_instrument_number')
        self.assertEqual(len(sources_after['records']), 1)

    def test_conflicting_metadata_is_reported(self):
        existing = copy.deepcopy(self.records[0])
        existing['id'] = candidate_id(existing['candidate_id'])
        existing['source_url'] = 'https://example.gov/different'
        existing['instrument_title'] = 'Different title'
        sources, _, report = self.plan(self.package(), {'records': [existing]})
        self.assertEqual(report['conflicts'][0]['fields'][:2], ['source_url', 'instrument_title'])
        self.assertEqual(report['imported_candidates'], [])

    def test_unknown_jurisdiction_blocks_import(self):
        record = copy.deepcopy(self.records[0])
        record['jurisdiction'] = 'ZZ'
        _, _, report = self.plan(self.package([record]), self.empty_inventory())
        self.assertEqual(report['result'], 'blocked')
        self.assertTrue(any('unknown jurisdiction' in error for error in report['errors']))

    def test_unknown_domain_blocks_import(self):
        record = copy.deepcopy(self.records[0])
        record['domain'] = 'health_policy'
        _, _, report = self.plan(self.package([record]), self.empty_inventory())
        self.assertTrue(any('unknown domain' in error for error in report['errors']))

    def test_invalid_source_url_blocks_import(self):
        record = copy.deepcopy(self.records[0])
        record['source_url'] = 'http://insecure.example.gov/act'
        _, _, report = self.plan(self.package([record]), self.empty_inventory())
        self.assertTrue(any('safe https URL' in error for error in report['errors']))

    def test_missing_task_candidate_blocks_import(self):
        task = copy.deepcopy(self.tasks[0])
        task['candidate_source_id'] = 'MENA-T02-999'
        task_package = self.package(tasks=[task])
        _, _, report = self.plan(task_package, self.empty_inventory())
        self.assertTrue(any('missing candidate' in error for error in report['errors']))

    def test_unreviewed_promotion_blocks_import(self):
        record = copy.deepcopy(self.records[0])
        record['legal_effect'] = 'binding_confirmed'
        _, _, report = self.plan(self.package([record]), self.empty_inventory())
        self.assertTrue(any('legal_effect may not be promoted' in error
                            for error in report['errors']))

    def test_captured_bytes_block_import(self):
        record = copy.deepcopy(self.records[0])
        record['source_capture'] = {'bytes_stored': True, 'sha256': 'a' * 64}
        _, _, report = self.plan(self.package([record]), self.empty_inventory())
        self.assertTrue(any('may not store captured bytes' in error
                            for error in report['errors']))

    def test_policy_records_are_preserved(self):
        before = copy.deepcopy(self.policies)
        sources_before = copy.deepcopy(load_json(SOURCES))
        self.plan(self.package(), sources_before)
        self.assertEqual(self.policies, before)
        self.assertEqual(len(self.policies), 11)

    def test_plan_does_not_mutate_its_inputs(self):
        sources = load_json(SOURCES)
        snapshot = copy.deepcopy(sources)
        self.plan(self.package(), sources)
        self.assertEqual(sources, snapshot)

    def test_committed_integration_is_current(self):
        self.assertEqual(run(check=True), 0)

    def test_committed_report_matches_the_package(self):
        report = load_json(REPORT)
        self.assertEqual(report['package'], PACKAGE_LABEL)
        self.assertEqual(report['result'], 'ok')
        self.assertEqual(len(report['imported_candidates']), 14)
        self.assertEqual(len(report['imported_tasks']), 14)
        self.assertEqual(report['relationships'], 3)
        self.assertEqual(report['existing_policy_records']['count'], 11)
        self.assertEqual(report['canonical_candidate_records'], 23)
        sources = load_json(SOURCES)
        imported = {candidate['id'] for candidate in sources['records']
                    if (candidate.get('provenance') or {}).get('package') == PACKAGE_LABEL}
        self.assertEqual(imported, {candidate['candidate_id'].lower()
                                    for candidate in self.records})
        for candidate in sources['records']:
            if candidate['id'] in imported:
                self.assertEqual(candidate['legal_effect'], 'not_assessed')
                self.assertEqual(candidate['capture_status'], 'not_captured')
                self.assertFalse(candidate['display_review']['human_reviewed'])
                self.assertEqual(candidate['provenance']['recorded_on'], '2026-11-05')


if __name__ == '__main__':
    unittest.main()
