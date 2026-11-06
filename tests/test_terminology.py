import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.terminology import load_terminology, validate_terminology

BASE = REPO_ROOT / 'regions' / 'mena'


class TerminologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_terminology(BASE)

    def check(self, document):
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / 'data'
            data.mkdir()
            shutil.copy(BASE / 'data' / 'countries.json', data / 'countries.json')
            (data / 'terminology.json').write_text(
                json.dumps(document, ensure_ascii=False), encoding='utf-8')
            return validate_terminology(Path(temporary))

    def concept(self, document, concept_id):
        return next(item for item in document['concepts'] if item['id'] == concept_id)

    def test_live_registry_validates(self):
        self.assertEqual(validate_terminology(BASE), [])

    def test_initial_concepts_cover_the_project_vocabulary(self):
        ids = {concept['id'] for concept in self.document['concepts']}
        self.assertGreaterEqual(len(ids), 15)
        for concept_id in ('legislation', 'regulation', 'binding', 'guidance',
                           'amendment', 'repeal', 'commencement', 'accessibility',
                           'disability_inclusion', 'privacy', 'data_protection',
                           'public_procurement', 'open_source_software',
                           'digital_sovereignty', 'environmental_sustainability'):
            self.assertIn(concept_id, ids)
        for concept in self.document['concepts']:
            for language in ('en', 'fr', 'ar'):
                self.assertTrue(concept['labels'][language].strip())
            self.assertEqual(concept['review_state'], 'draft')
            self.assertEqual(concept['review_history'], [])

    def test_duplicate_id_is_rejected(self):
        document = copy.deepcopy(self.document)
        document['concepts'].append(copy.deepcopy(document['concepts'][0]))
        self.assertTrue(any('duplicate concept id' in error
                            for error in self.check(document)))

    def test_missing_french_label_is_rejected(self):
        document = copy.deepcopy(self.document)
        self.concept(document, 'legislation')['labels']['fr'] = ''
        self.assertTrue(any('labels.fr' in error for error in self.check(document)))

    def test_unknown_jurisdiction_is_rejected(self):
        document = copy.deepcopy(self.document)
        self.concept(document, 'privacy')['jurisdictions'] = ['ZZ']
        self.assertTrue(any('unknown jurisdiction' in error
                            for error in self.check(document)))

    def test_reviewed_concept_needs_approved_history(self):
        document = copy.deepcopy(self.document)
        self.concept(document, 'privacy')['review_state'] = 'reviewed'
        self.assertTrue(any('reviewed status needs an approved review entry' in error
                            for error in self.check(document)))

    def test_reviewed_concept_with_history_is_valid(self):
        document = copy.deepcopy(self.document)
        concept = self.concept(document, 'privacy')
        concept['review_state'] = 'reviewed'
        concept['review_history'] = [{
            'reviewed_at': '2026-11-06',
            'reviewer_role': 'Native reviewer',
            'outcome': 'approved',
            'note': 'Fixture review only.',
        }]
        self.assertEqual(self.check(document), [])

    def test_invalid_review_date_is_rejected(self):
        document = copy.deepcopy(self.document)
        concept = self.concept(document, 'privacy')
        concept['review_history'] = [{
            'reviewed_at': '2026-02-31',
            'reviewer_role': 'Native reviewer',
            'outcome': 'changes_requested',
        }]
        self.assertTrue(any('valid ISO reviewed_at' in error
                            for error in self.check(document)))

    def test_unknown_review_outcome_is_rejected(self):
        document = copy.deepcopy(self.document)
        concept = self.concept(document, 'privacy')
        concept['review_history'] = [{
            'reviewed_at': '2026-11-06',
            'reviewer_role': 'Native reviewer',
            'outcome': 'approved_by_model',
        }]
        self.assertTrue(any('unknown review outcome' in error
                            for error in self.check(document)))

    def test_definition_language_must_be_a_tag(self):
        document = copy.deepcopy(self.document)
        self.concept(document, 'privacy')['definition']['language'] = 'English'
        self.assertTrue(any('definition.language' in error
                            for error in self.check(document)))


if __name__ == '__main__':
    unittest.main()
