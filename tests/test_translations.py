import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import load_i18n, source_sections
from framework.research import validate_record
from framework.schema_lite import Validator

FIXTURES = Path(__file__).resolve().parent / 'fixtures' / 'research'
VALID = FIXTURES / 'valid'
SCHEMAS = REPO_ROOT / 'regions' / 'mena' / 'schemas'
BASE = REPO_ROOT / 'regions' / 'mena'
ARTIFACTS = ('SOURCE.md', 'PROVISIONS.md', 'INTERPRETATION.md', 'RELATED.md')
RECORD_ID = 'fixture-record'
SOURCE_ID = 'src-fixture-source'


def load_valid():
    return json.loads((VALID / 'research.json').read_text(encoding='utf-8'))


def expressions():
    return [
        {
            'id': 'expr-original',
            'kind': 'original_authoritative',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'en',
            'original_language': 'en',
            'review_status': 'unreviewed',
            'uncertainties': [],
        },
        {
            'id': 'expr-official-fr',
            'kind': 'official_translation',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'fr',
            'original_language': 'en',
            'url': 'https://example.org/official-fr',
            'authority': 'Official gazette',
            'translation_method': 'human',
            'review_status': 'unreviewed',
            'uncertainties': ['Translation authority not independently verified.'],
        },
        {
            'id': 'expr-research-fr',
            'kind': 'research_translation',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'fr',
            'original_language': 'en',
            'authority': 'Research project',
            'translation_method': 'human',
            'review_status': 'reviewed',
            'reviewed_at': '2026-11-01',
            'reviewer_role': 'Translator and legal reviewer',
            'uncertainties': [],
        },
    ]


class ExpressionValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = Validator(SCHEMAS)

    def check(self, data, warnings=None):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            for name in ARTIFACTS:
                shutil.copy(VALID / name, target / name)
            (target / 'research.json').write_text(
                json.dumps(data, ensure_ascii=False), encoding='utf-8')
            return validate_record(target, RECORD_ID, self.validator, {RECORD_ID}, warnings)

    def with_expressions(self):
        data = load_valid()
        data['sources'][0]['expressions'] = expressions()
        return data

    def test_multiple_expressions_of_one_instrument_are_valid(self):
        self.assertEqual(self.check(self.with_expressions()), [])

    def test_original_content_is_not_modified_by_validation(self):
        data = self.with_expressions()
        snapshot = copy.deepcopy(data)
        self.check(data)
        self.assertEqual(data, snapshot)

    def test_invalid_language_tag_is_rejected(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'][0]['language'] = 'English'
        self.assertTrue(any('language' in error and ('does not match' in error or
                                                     'BCP47' in error)
                            for error in self.check(data)))

    def test_expression_source_reference_must_match(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'][0]['source_id'] = 'other-source'
        self.assertTrue(any('source_id must match' in error for error in self.check(data)))

    def test_expression_instrument_reference_must_match(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'][0]['instrument_id'] = 'other-record'
        self.assertTrue(any('instrument_id must match' in error for error in self.check(data)))

    def test_reviewed_translation_needs_reviewer_and_date(self):
        data = self.with_expressions()
        expression = data['sources'][0]['expressions'][2]
        expression.pop('reviewed_at')
        expression.pop('reviewer_role')
        self.assertTrue(any('needs an ISO reviewed_at' in error for error in self.check(data)))
        self.assertTrue(any('needs a reviewer_role' in error for error in self.check(data)))

    def test_machine_draft_cannot_be_promoted(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'].append({
            'id': 'expr-machine-ar',
            'kind': 'machine_assisted_draft',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'ar',
            'original_language': 'en',
            'translation_method': 'machine_assisted',
            'review_status': 'reviewed',
            'reviewed_at': '2026-11-01',
            'reviewer_role': 'Reviewer',
            'uncertainties': [],
        })
        self.assertTrue(any('machine-assisted draft may not claim review' in error
                            for error in self.check(data)))

    def test_pending_translation_may_not_carry_a_url(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'].append({
            'id': 'expr-pending-ar',
            'kind': 'translation_pending',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'ar',
            'original_language': 'en',
            'url': 'https://example.org/not-yet',
            'review_status': 'unreviewed',
            'uncertainties': [],
        })
        self.assertTrue(any('may not record a URL or authority' in error
                            for error in self.check(data)))

    def test_duplicate_language_and_kind_is_rejected(self):
        data = self.with_expressions()
        duplicate = copy.deepcopy(data['sources'][0]['expressions'][0])
        duplicate['id'] = 'expr-original-duplicate'
        data['sources'][0]['expressions'].append(duplicate)
        self.assertTrue(any('duplicate language and kind' in error for error in self.check(data)))

    def test_original_language_must_match_source_language(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'][0]['language'] = 'fr'
        self.assertTrue(any('original language does not match' in error
                            for error in self.check(data)))

    def test_unresolved_authority_cannot_claim_review(self):
        data = self.with_expressions()
        data['sources'][0]['expressions'].append({
            'id': 'expr-unresolved',
            'kind': 'authority_unresolved',
            'source_id': SOURCE_ID,
            'instrument_id': RECORD_ID,
            'language': 'ar',
            'original_language': 'en',
            'review_status': 'reviewed',
            'reviewed_at': '2026-11-01',
            'reviewer_role': 'Reviewer',
            'uncertainties': [],
        })
        self.assertTrue(any('unresolved authority may not claim review' in error
                            for error in self.check(data)))


class ExpressionRenderingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))
        cls.research = load_valid()
        cls.research['sources'][0]['expressions'] = expressions()

    def test_expression_status_is_rendered(self):
        body = source_sections(self.catalogues['en'], 'en', self.research)[0]
        self.assertIn('Language expressions', body)
        self.assertIn('Original authoritative text', body)
        self.assertIn('Official translation', body)
        self.assertIn('/officia'.replace('/officia', 'Official gazette'), body)
        self.assertIn('Reviewed', body)
        self.assertIn('https://example.org/official-fr', body)
        self.assertIn('Language versions do not carry equal legal authority', body)

    def test_expression_rendering_french(self):
        body = source_sections(self.catalogues['fr'], 'fr', self.research)[0]
        self.assertIn('Expressions linguistiques', body)
        self.assertIn('Traduction officielle', body)
        self.assertIn('Non revue', body)

    def test_expression_rendering_arabic(self):
        body = source_sections(self.catalogues['ar'], 'ar', self.research)[0]
        self.assertIn('التعبيرات اللغوية', body)
        self.assertIn('ترجمة رسمية', body)
        self.assertIn('غير مراجعة', body)
        self.assertIn('<code lang="en" dir="ltr">fr</code>', body)

    def test_missing_expression_record_is_explicit(self):
        research = load_valid()
        body = source_sections(self.catalogues['en'], 'en', research)[0]
        self.assertIn('No language-expression record is recorded for this source', body)

    def test_source_preview_is_unchanged(self):
        research = load_valid()
        body = source_sections(self.catalogues['en'], 'en', research)[0]
        self.assertIn('The fixture sentence appears here verbatim.', body)


if __name__ == '__main__':
    unittest.main()
