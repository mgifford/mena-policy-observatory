import copy
import sys
import unittest
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.coverage import (
    audit_coverage,
    build_view,
    cell_status,
    country_status,
    load_coverage,
    normalized_task_id,
    record_is_reviewed,
    safe_url,
    validate_coverage,
)


class CoverageRegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = load_coverage()

    def test_live_registries_validate(self):
        self.assertEqual(validate_coverage(self.data), [])

    def test_jurisdiction_registry_is_reconciled(self):
        codes = {country['code'] for country in self.data.countries}
        proposed = {entry['code'] for entry in self.data.proposed_scope['entries']}
        self.assertEqual(codes, proposed)
        self.assertEqual(len(codes), 24)

    def test_registry_keeps_policy_record_ids(self):
        record_ids = {policy['id'] for policy in self.data.policies}
        self.assertIn('ae-national-digital-accessibility', record_ids)
        self.assertEqual(len(record_ids), 7)

    def test_unknown_country_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.countries.append(dict(data.countries[0], code='ZZ'))
        self.assertTrue(any('undocumented additions' in error
                            for error in validate_coverage(data)))

    def test_unreconciled_name_is_rejected(self):
        data = copy.deepcopy(self.data)
        for country in data.countries:
            if country['code'] == 'SY':
                country.pop('reconciled_from_name', None)
        self.assertTrue(any('SY' in error and 'reconciled_from_name' in error
                            for error in validate_coverage(data)))

    def test_record_count_mismatch_is_rejected(self):
        data = copy.deepcopy(self.data)
        for country in data.countries:
            if country['code'] == 'AE':
                country['reviewed_policy_records'] = 99
        self.assertTrue(any('reviewed_policy_records' in error
                            for error in validate_coverage(data)))

    def test_unknown_domain_group_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.domains[0]['group'] = 'missing_group'
        self.assertTrue(any('unknown group' in error
                            for error in validate_coverage(data)))

    def test_region_domain_label_drift_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.region_config['domain_labels']['digital_accessibility']['en'] = 'Changed'
        self.assertTrue(any('English label differs' in error
                            for error in validate_coverage(data)))

    def test_candidate_with_unsafe_url_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.candidate_inventory['records'][0]['source_url'] = 'http://example.test/x'
        self.assertTrue(any('safe https URL' in error
                            for error in validate_coverage(data)))

    def test_candidate_cannot_promote_legal_effect(self):
        data = copy.deepcopy(self.data)
        data.candidate_inventory['records'][0]['legal_effect'] = 'binding_confirmed'
        self.assertTrue(any('may not be promoted' in error
                            for error in validate_coverage(data)))

    def test_candidate_needs_display_review(self):
        data = copy.deepcopy(self.data)
        data.candidate_inventory['records'][0].pop('display_review', None)
        self.assertTrue(any('display_review is required' in error
                            for error in validate_coverage(data)))

    def test_candidate_unknown_domain_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.candidate_inventory['records'][0]['domains'] = ['not_a_domain']
        self.assertTrue(any('unknown domain' in error
                            for error in validate_coverage(data)))

    def test_task_with_unknown_stage_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.tasks[0]['stage'] = 'estimate'
        self.assertTrue(any('unknown stage' in error
                            for error in validate_coverage(data)))

    def test_task_with_unknown_source_lead_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.tasks[0]['source_lead_ids'] = ['missing-lead']
        self.assertTrue(any('unknown source lead' in error
                            for error in validate_coverage(data)))

    def test_countries_carry_provisional_arabic_and_french_labels(self):
        for country in self.data.countries:
            for language in ('ar', 'fr'):
                self.assertTrue(country[f'name_{language}'], country['code'])
                self.assertEqual(country[f'name_{language}_status'], 'provisional', country['code'])
                self.assertTrue(country[f'group_{language}'], country['code'])
                self.assertEqual(country[f'group_{language}_status'], 'provisional', country['code'])
                self.assertTrue(country[f'scope_note_{language}'], country['code'])
                self.assertEqual(country[f'scope_note_{language}_status'], 'provisional', country['code'])
                if country.get('jurisdiction_note'):
                    self.assertTrue(country.get(f'jurisdiction_note_{language}'), country['code'])
                    self.assertEqual(country.get(f'jurisdiction_note_{language}_status'), 'provisional')

    def test_missing_arabic_group_label_is_rejected(self):
        data = copy.deepcopy(self.data)
        for country in data.countries:
            if country['code'] == 'EH':
                country.pop('group_ar')
        self.assertTrue(any('group_ar' in error for error in validate_coverage(data)))

    def test_missing_french_group_label_is_rejected(self):
        data = copy.deepcopy(self.data)
        for country in data.countries:
            if country['code'] == 'EH':
                country.pop('group_fr')
        self.assertTrue(any('group_fr' in error for error in validate_coverage(data)))

    def test_jurisdiction_note_without_arabic_is_rejected(self):
        data = copy.deepcopy(self.data)
        for country in data.countries:
            if country['code'] == 'DZ':
                country['jurisdiction_note'] = 'An editorial note that needs a translation.'
        self.assertTrue(any('DZ' in error and 'jurisdiction_note_ar' in error
                            for error in validate_coverage(data)))

    def test_confirmed_effect_needs_recorded_review(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                policy['legal_effect'] = 'binding_confirmed'
        self.assertTrue(any('complete recorded review' in error
                            for error in validate_coverage(data)))

    def test_incomplete_review_record_is_rejected(self):
        data = copy.deepcopy(self.data)
        data.research[data.policies[0]['id']]['review'] = {
            'status': 'reviewed',
            'reviewer': 'Fixture reviewer',
        }
        self.assertTrue(any('reviewed record needs' in error
                            for error in validate_coverage(data)))

    def test_pending_review_record_is_allowed(self):
        data = copy.deepcopy(self.data)
        data.research[data.policies[0]['id']]['review'] = {'status': 'pending'}
        self.assertFalse(any('review' in error for error in validate_coverage(data)))

    def test_logical_task_duplicate_is_rejected(self):
        data = copy.deepcopy(self.data)
        duplicate = dict(data.tasks[0], task_id=data.tasks[0]['task_id'].replace('-', '_'))
        data.tasks.append(duplicate)
        self.assertTrue(any('duplicate logical task ID' in error
                            for error in validate_coverage(data)))


class CoverageStatusTests(unittest.TestCase):
    def setUp(self):
        self.data = load_coverage()

    def test_safe_url_rules(self):
        self.assertTrue(safe_url('https://example.org/document'))
        self.assertFalse(safe_url('http://example.org/document'))
        self.assertFalse(safe_url('https://user:pass@example.org/document'))
        self.assertFalse(safe_url('https://127.0.0.1/document'))
        self.assertFalse(safe_url('https://[::1]/document'))
        self.assertFalse(safe_url('file:///etc/passwd'))
        self.assertFalse(safe_url(None))

    def test_task_id_normalization(self):
        self.assertEqual(
            normalized_task_id('BH-DIGITAL_RIGHTS-DISCOVERY-001'),
            normalized_task_id('BH-DIGITAL-RIGHTS-DISCOVERY-001'),
        )

    def test_documented_cell_statuses(self):
        view = build_view(self.data)
        cells = {(row['country']['code'], cell['domain_id']): cell['status']
                 for row in view['matrix'] for cell in row['cells']}
        self.assertEqual(cells[('AE', 'digital_accessibility')], 'legal_review_pending')
        self.assertEqual(cells[('JO', 'digital_accessibility')], 'candidate_sources_identified')
        self.assertEqual(cells[('DZ', 'digital_accessibility')], 'not_started')
        self.assertEqual(cells[('DZ', 'digital_rights')], 'candidate_sources_identified')
        self.assertEqual(cells[('IL', 'digital_accessibility')], 'not_started')

    def test_country_status_aggregates_evidence(self):
        statuses = {country['code']: country['status']
                    for country in build_view(self.data)['countries']}
        self.assertEqual(statuses['AE'], 'legal_review_pending')
        self.assertEqual(statuses['JO'], 'candidate_sources_identified')
        self.assertEqual(statuses['DZ'], 'candidate_sources_identified')
        self.assertEqual(statuses['IL'], 'not_started')

    def test_blocked_task_outranks_other_statuses(self):
        data = copy.deepcopy(self.data)
        for task in data.tasks:
            if task['jurisdiction'] == 'DZ':
                task['status'] = 'blocked'
        self.assertEqual(cell_status(data, 'DZ', 'digital_accessibility'), 'blocked')
        self.assertEqual(country_status(data, 'DZ', ['digital_accessibility']), 'blocked')

    def test_reviewed_findings_require_confirmed_effect_and_recorded_review(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                policy['legal_effect'] = 'binding_confirmed'
                data.research[policy['id']]['interpretations'] = []
                data.research[policy['id']]['review'] = {
                    'status': 'reviewed',
                    'reviewer': 'Fixture reviewer',
                    'reviewed_at': '2026-11-06',
                    'scope': 'Fixture review of the legal-effect finding',
                }
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'reviewed_findings')

    def test_confirmed_effect_without_review_is_not_reviewed(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                policy['legal_effect'] = 'binding_confirmed'
                data.research[policy['id']]['interpretations'] = []
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'provision_extraction')

    def test_incomplete_review_is_not_reviewed(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                policy['legal_effect'] = 'binding_confirmed'
                data.research[policy['id']]['interpretations'] = []
                data.research[policy['id']]['review'] = {
                    'status': 'reviewed',
                    'reviewer': 'Fixture reviewer',
                }
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'provision_extraction')

    def test_pending_review_is_not_reviewed(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                policy['legal_effect'] = 'binding_confirmed'
                data.research[policy['id']]['interpretations'] = []
                data.research[policy['id']]['review'] = {'status': 'pending'}
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'provision_extraction')

    def test_provision_extraction_and_capture_states(self):
        data = copy.deepcopy(self.data)
        for policy in data.policies:
            if policy['country'] == 'AE':
                data.research[policy['id']]['interpretations'] = []
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'provision_extraction')
        for policy in data.policies:
            if policy['country'] == 'AE':
                data.research[policy['id']]['provisions'] = []
        self.assertEqual(cell_status(data, 'AE', 'digital_accessibility'), 'evidence_captured')

    def test_record_review_requires_no_open_question(self):
        policy = {'id': 'x', 'legal_effect': 'binding_confirmed'}
        review = {
            'status': 'reviewed',
            'reviewer': 'Fixture reviewer',
            'reviewed_at': '2026-11-06',
            'scope': 'Fixture review of the legal-effect finding',
        }
        self.assertTrue(record_is_reviewed(policy, {'interpretations': [], 'review': review}))
        self.assertFalse(record_is_reviewed(
            policy, {'interpretations': [{'status': 'unresolved'}], 'review': review}))
        self.assertFalse(record_is_reviewed(
            {'id': 'x', 'legal_effect': 'not_legally_assessed'},
            {'interpretations': [], 'review': review}))

    def test_record_review_requires_recorded_review_evidence(self):
        policy = {'id': 'x', 'legal_effect': 'binding_confirmed'}
        self.assertFalse(record_is_reviewed(policy, {'interpretations': []}))
        self.assertFalse(record_is_reviewed(policy, {
            'interpretations': [], 'review': {'status': 'pending'}}))
        self.assertFalse(record_is_reviewed(policy, {
            'interpretations': [],
            'review': {'status': 'reviewed', 'reviewer': 'Fixture reviewer',
                       'reviewed_at': '2026-11-06'}}))

    def test_public_view_hides_non_displayable_candidates(self):
        data = copy.deepcopy(self.data)
        data.candidate_inventory['records'][0]['source_url'] = 'http://unsafe.test/x'
        view = build_view(data)
        self.assertEqual(view['totals']['candidates'], 22)
        self.assertNotIn(data.candidate_inventory['records'][0]['id'],
                         {candidate['id'] for candidate in view['candidates']})

    def test_view_totals(self):
        view = build_view(self.data)
        self.assertEqual(view['totals']['countries'], 24)
        self.assertEqual(view['totals']['domains'], 8)
        self.assertEqual(view['totals']['records'], 7)
        self.assertEqual(view['totals']['candidates'], 23)
        self.assertEqual(view['totals']['tasks'], 54)


class CoverageAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = load_coverage()

    def test_live_queue_has_no_logical_duplicates(self):
        audit = audit_coverage(self.data, reference_date=date(2026, 11, 6))
        self.assertEqual(audit['duplicates'], [])
        self.assertEqual(audit['task_count'], 54)
        self.assertEqual(audit['candidate_count'], 23)

    def test_audit_reports_logical_duplicates(self):
        data = copy.deepcopy(self.data)
        data.tasks.append(dict(data.tasks[0], task_id=data.tasks[0]['task_id'].replace('-', '_')))
        audit = audit_coverage(data, reference_date=date(2026, 11, 6))
        self.assertTrue(audit['duplicates'])

    def test_audit_reports_pending_human_review(self):
        audit = audit_coverage(self.data, reference_date=date(2026, 11, 6))
        pending = [item for item in audit['unresolved_review']
                   if item['kind'] == 'candidate_display']
        self.assertEqual(len(pending), 23)
        self.assertTrue(all(item['status'] == 'human_review_pending' for item in pending))


if __name__ == '__main__':
    unittest.main()
