import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.research import relation_cycles, validate_record, validate_region
from framework.schema_lite import Validator

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'research'
VALID = FIXTURES / 'valid'
SCHEMAS = REPO_ROOT / 'regions' / 'mena' / 'schemas'
ARTIFACTS = ('SOURCE.md', 'PROVISIONS.md', 'INTERPRETATION.md', 'RELATED.md')
RECORD_ID = 'fixture-record'


def load_valid():
    return json.loads((VALID / 'research.json').read_text(encoding='utf-8'))


class ResearchValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = Validator(SCHEMAS)

    def check(self, data):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for name in ARTIFACTS:
                shutil.copy(VALID / name, target / name)
            (target / 'research.json').write_text(
                json.dumps(data, ensure_ascii=False), encoding='utf-8')
            return validate_record(target, RECORD_ID, self.validator, {RECORD_ID})

    def assert_error(self, data, fragment):
        errors = self.check(data)
        self.assertTrue(
            any(fragment in error for error in errors),
            f'expected an error containing {fragment!r}, got {errors}',
        )

    def test_valid_fixture_passes(self):
        self.assertEqual(self.check(load_valid()), [])

    def test_missing_required_field_is_rejected(self):
        data = load_valid()
        del data['schema_version']
        self.assert_error(data, 'missing required property')

    def test_unexpected_field_is_rejected(self):
        data = load_valid()
        data['legal_conclusion'] = 'compliant'
        self.assert_error(data, "unexpected property 'legal_conclusion'")

    def test_reviewed_review_records_reviewer_date_and_scope(self):
        data = load_valid()
        data['review'] = {
            'status': 'reviewed',
            'reviewer': 'Fixture reviewer',
            'reviewed_at': '2026-11-06',
            'scope': 'Fixture review of legal effect and scope',
        }
        self.assertEqual(self.check(data), [])

    def test_pending_review_is_allowed(self):
        data = load_valid()
        data['review'] = {'status': 'pending'}
        self.assertEqual(self.check(data), [])

    def test_reviewed_review_without_scope_is_rejected(self):
        data = load_valid()
        data['review'] = {
            'status': 'reviewed',
            'reviewer': 'Fixture reviewer',
            'reviewed_at': '2026-11-06',
        }
        self.assert_error(data, 'must match exactly one allowed shape')

    def test_reviewed_review_with_invalid_date_is_rejected(self):
        data = load_valid()
        data['review'] = {
            'status': 'reviewed',
            'reviewer': 'Fixture reviewer',
            'reviewed_at': '6 November 2026',
            'scope': 'Fixture review of legal effect and scope',
        }
        self.assert_error(data, 'must match exactly one allowed shape')

    def test_review_may_not_carry_extra_fields(self):
        data = load_valid()
        data['review'] = {'status': 'pending', 'legal_effect': 'binding_confirmed'}
        self.assert_error(data, 'must match exactly one allowed shape')

    def test_duplicate_source_ids_are_rejected(self):
        data = load_valid()
        data['sources'].append(copy.deepcopy(data['sources'][0]))
        self.assert_error(data, 'duplicate source id')

    def test_unknown_source_reference_is_rejected(self):
        data = load_valid()
        data['provisions'][0]['source_ids'] = ['src-missing']
        self.assert_error(data, 'references unknown source')

    def test_unknown_question_reference_is_rejected(self):
        data = load_valid()
        data['provisions'][0]['interpreting_questions'] = ['FX-99']
        self.assert_error(data, 'references unknown question')

    def test_effective_date_before_publication_is_rejected(self):
        data = load_valid()
        source = data['sources'][0]
        source['publication_date'] = '2025-01-02'
        source['effective_date'] = '2025-01-01'
        self.assert_error(data, 'effective date precedes publication date')

    def test_unknown_date_marker_is_allowed(self):
        data = load_valid()
        data['sources'][0]['publication_date'] = 'unknown'
        data['sources'][0]['effective_date'] = 'unknown'
        self.assertEqual(self.check(data), [])

    def test_free_text_date_is_rejected(self):
        data = load_valid()
        data['sources'][0]['publication_date'] = 'sometime in 2011'
        self.assert_error(data, 'must be an ISO date or "unknown"')

    def test_excerpt_must_appear_verbatim_in_the_artifact(self):
        data = load_valid()
        data['sources'][0]['excerpt']['text'] = 'A sentence that was never captured.'
        self.assert_error(data, 'excerpt text is not found verbatim')

    def test_excerpt_status_must_match_excerpt_presence(self):
        data = load_valid()
        data['sources'][0]['excerpt_status'] = 'not_recorded'
        self.assert_error(data, 'excerpt present but excerpt_status')

    def test_checksum_without_stored_bytes_is_rejected(self):
        data = load_valid()
        data['sources'][0]['capture']['sha256'] = 'a' * 64
        self.assert_error(data, 'checksum is recorded for bytes that are not stored')

    def test_stored_bytes_need_checksum_and_timestamp(self):
        data = load_valid()
        data['sources'][0]['capture']['bytes_stored'] = True
        self.assert_error(data, 'stored bytes need a SHA-256 checksum')

    def test_native_review_needs_recorded_provenance(self):
        data = load_valid()
        data['sources'][0]['translation']['review_state'] = 'native_reviewed'
        self.assert_error(data, 'native review needs recorded provenance')

    def test_asserted_relation_requires_review(self):
        data = load_valid()
        data['relations'][0]['relation'] = 'cites'
        self.assert_error(data, 'without review')

    def test_unspecified_relation_needs_recorded_label(self):
        data = load_valid()
        data['relations'][0]['recorded_label'] = None
        self.assert_error(data, 'needs a recorded label')

    def test_internal_record_relation_must_resolve(self):
        data = load_valid()
        data['relations'][0]['target'] = {
            'kind': 'internal_record',
            'title': 'Missing record',
            'url': None,
            'record_id': 'not-a-record',
        }
        self.assert_error(data, 'points at unknown record')

    def test_relation_must_not_point_at_its_own_record(self):
        data = load_valid()
        data['relations'][0]['target'] = {
            'kind': 'internal_record',
            'title': 'This record',
            'url': None,
            'record_id': RECORD_ID,
        }
        self.assert_error(data, 'points at its own record')

    def test_reviewed_provision_cannot_have_open_questions(self):
        data = load_valid()
        data['provisions'][0]['effect_assessment'] = 'in_force_confirmed'
        data['provisions'][0]['encoding_status'] = 'reviewed'
        self.assert_error(data, 'cannot be reviewed with unresolved questions')

    def test_reviewed_provision_needs_confirmed_effect(self):
        data = load_valid()
        data['provisions'][0]['interpreting_questions'] = []
        data['provisions'][0]['encoding_status'] = 'reviewed'
        self.assert_error(data, 'without a confirmed effect assessment')

    def test_resolved_question_needs_reviewer_and_date(self):
        data = load_valid()
        question = data['interpretations'][0]
        question['status'] = 'resolved'
        question['resolution'] = 'Accepted the first reading.'
        question['reviewed_at'] = '2026-11-01'
        question['reviewer'] = None
        self.assert_error(data, 'is resolved but lacks')

    def test_artifact_documented_provision_needs_structured_entry(self):
        data = load_valid()
        data['provisions'] = []
        data['interpretations'][0]['provision_id'] = None
        self.assert_error(data, 'documents provision P-01 with no structured entry')

    def test_structured_provision_must_be_documented(self):
        data = load_valid()
        data['provisions'][0]['id'] = 'P-02'
        data['interpretations'][0]['provision_id'] = 'P-02'
        self.assert_error(data, 'is not documented in PROVISIONS.md')

    def test_summary_must_appear_verbatim_in_the_artifact(self):
        data = load_valid()
        data['provisions'][0]['summary'] = 'A rewritten summary that is not in the artifact.'
        self.assert_error(data, 'summary is not found verbatim')

    def test_question_statement_must_appear_verbatim_in_the_artifact(self):
        data = load_valid()
        data['interpretations'][0]['statement'] = 'A question that is not in the artifact.'
        self.assert_error(data, 'statement is not found verbatim')

    def test_missing_artifact_file_is_rejected(self):
        data = load_valid()
        data['artifacts']['provisions'] = 'MISSING.md'
        self.assert_error(data, 'does not exist')

    def test_record_id_must_match_the_directory(self):
        data = load_valid()
        data['record_id'] = 'another-record'
        self.assert_error(data, 'does not match directory')


class RelationCycleTests(unittest.TestCase):
    @staticmethod
    def relation(label, record_id, kind='internal_record'):
        return {
            'relation': label,
            'target': {'kind': kind, 'record_id': record_id},
        }

    def test_amendment_cycle_is_reported(self):
        cycles = relation_cycles({
            'a': [self.relation('amends', 'b')],
            'b': [self.relation('amends', 'a')],
        })
        self.assertEqual(len(cycles), 1)
        self.assertEqual(cycles[0][0], cycles[0][-1])

    def test_supersession_cycle_is_reported(self):
        cycles = relation_cycles({
            'a': [self.relation('supersedes', 'b')],
            'b': [self.relation('supersedes', 'c')],
            'c': [self.relation('supersedes', 'a')],
        })
        self.assertEqual(len(cycles), 1)

    def test_citation_cycle_is_allowed(self):
        self.assertEqual(relation_cycles({
            'a': [self.relation('cites', 'b')],
            'b': [self.relation('cites', 'a')],
        }), [])

    def test_unreviewed_unspecified_relations_are_ignored(self):
        self.assertEqual(relation_cycles({
            'a': [{'relation': 'unspecified', 'target': {'kind': 'internal_record', 'record_id': 'b'}}],
            'b': [{'relation': 'unspecified', 'target': {'kind': 'internal_record', 'record_id': 'a'}}],
        }), [])


class RealDataTests(unittest.TestCase):
    def test_all_regional_research_files_validate(self):
        self.assertEqual(validate_region(REPO_ROOT / 'regions' / 'mena', 'mena'), [])


class SchemaLiteTests(unittest.TestCase):
    def setUp(self):
        self.validator = Validator(SCHEMAS)

    def test_unsupported_keyword_fails_loudly(self):
        with self.assertRaises(ValueError):
            self.validator.validate({}, {'type': 'object', 'minProperties': 1})

    def test_one_of_requires_exactly_one_match(self):
        schema = {'oneOf': [{'type': 'null'}, {'type': 'object'}]}
        self.assertEqual(self.validator.validate(None, schema), [])
        self.assertTrue(self.validator.validate('text', schema))


if __name__ == '__main__':
    unittest.main()
