import copy
import html
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.rule_presentation import (
    load_catalogues,
    render_all,
    render_page,
    validate_presentation,
)

FIXTURE = REPO_ROOT / 'tests' / 'fixtures' / 'rule-presentation' / 'synthetic-procurement.json'


def fixture():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


class RulePresentationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_catalogues()

    def test_fixture_is_valid(self):
        self.assertEqual(validate_presentation(fixture()), [])

    def test_synthetic_review_gate_is_enforced(self):
        data = fixture()
        data['review']['status'] = 'reviewed'
        self.assertTrue(any('synthetic' in error for error in validate_presentation(data)))
        data = fixture()
        data['record'] = {'instrument_id': 'i', 'source_id': 's', 'provision_id': 'p',
                          'legal_version': 'v', 'reviewed_interpretation_id': 'r'}
        self.assertTrue(any('must not be attached' in error for error in validate_presentation(data)))

    def test_reviewed_presentation_requires_the_full_chain(self):
        data = fixture()
        data['synthetic'] = False
        data['review'] = {'status': 'reviewed', 'reviewer_role': 'Legal reviewer',
                          'reviewed_at': '2026-11-07', 'notes': 'Synthetic test review.'}
        data['record'] = {'instrument_id': 'i', 'source_id': 's', 'provision_id': 'p',
                          'legal_version': 'v', 'reviewed_interpretation_id': 'r'}
        data['provenance']['artifact_sha256'] = 'a' * 64
        for source in data['sources']:
            source['url'] = 'https://gov.example/act#' + source['id'].lower()
        self.assertEqual(validate_presentation(data), [])
        data['record'] = None
        self.assertTrue(any('record chain' in error for error in validate_presentation(data)))

    def test_reviewed_presentation_requires_reviewer_and_artifact(self):
        data = fixture()
        data['synthetic'] = False
        data['review'] = {'status': 'reviewed', 'reviewer_role': None,
                          'reviewed_at': None, 'notes': 'Missing review.'}
        data['record'] = {'instrument_id': 'i', 'source_id': 's', 'provision_id': 'p',
                          'legal_version': 'v', 'reviewed_interpretation_id': 'r'}
        for source in data['sources']:
            source['url'] = 'https://gov.example/act#' + source['id'].lower()
        errors = validate_presentation(data)
        self.assertTrue(any('reviewer_role' in error for error in errors))
        self.assertTrue(any('reviewed_at' in error for error in errors))
        self.assertTrue(any('artifact SHA-256' in error for error in errors))

    def test_real_presentation_cannot_use_example_sources(self):
        data = fixture()
        data['synthetic'] = False
        data['review'] = {'status': 'reviewed', 'reviewer_role': 'Legal reviewer',
                          'reviewed_at': '2026-11-07', 'notes': 'Synthetic test review.'}
        data['record'] = {'instrument_id': 'i', 'source_id': 's', 'provision_id': 'p',
                          'legal_version': 'v', 'reviewed_interpretation_id': 'r'}
        data['provenance']['artifact_sha256'] = 'a' * 64
        self.assertTrue(any('example.org is not a real' in error for error in validate_presentation(data)))

    def test_duplicate_node_and_unknown_dependency(self):
        data = fixture()
        data['nodes'].append(copy.deepcopy(data['nodes'][0]))
        self.assertTrue(any('duplicate node' in error for error in validate_presentation(data)))
        data = fixture()
        data['nodes'][0]['depends'] = ['N99']
        self.assertTrue(any('unknown dependency' in error for error in validate_presentation(data)))

    def test_dependency_cycle_is_rejected(self):
        data = fixture()
        data['nodes'][6]['depends'].append('N8')
        self.assertTrue(any('cycle' in error for error in validate_presentation(data)))

    def test_unknown_citation_and_step_numbering(self):
        data = fixture()
        data['nodes'][0]['citation'] = 'SP-99'
        self.assertTrue(any('unknown citation' in error for error in validate_presentation(data)))
        data = fixture()
        data['ladder'][1]['step'] = 4
        self.assertTrue(any('consecutively' in error for error in validate_presentation(data)))

    def test_text_equivalent_must_match_ladder(self):
        data = fixture()
        data['text']['steps']['ar'].pop()
        self.assertTrue(any('text.steps.ar' in error for error in validate_presentation(data)))

    def test_missing_locale_is_rejected_by_the_schema(self):
        data = fixture()
        del data['title']['fr']
        self.assertTrue(any('title' in error for error in validate_presentation(data)))

    def test_invalid_effective_period_is_rejected(self):
        data = fixture()
        data['effective_period'] = {'from': '2026-02-01', 'to': '2026-01-01'}
        self.assertTrue(any('cannot be before' in error for error in validate_presentation(data)))
        data = fixture()
        data['effective_period']['from'] = '2026-02-30'
        self.assertTrue(any('valid ISO date' in error for error in validate_presentation(data)))

    def test_constant_needs_a_value(self):
        data = fixture()
        data['nodes'][5]['value'] = None
        self.assertTrue(any('constants need a value' in error for error in validate_presentation(data)))

    def test_unknown_top_level_key_is_rejected(self):
        data = fixture()
        data['extra'] = True
        self.assertTrue(validate_presentation(data))


class RulePresentationRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = fixture()
        cls.catalogues = load_catalogues()

    def page(self, lang='en', data=None):
        return render_page(data or self.data, lang, self.catalogues[lang])

    def test_all_locales_render(self):
        with tempfile.TemporaryDirectory() as temporary:
            paths = render_all(self.data, Path(temporary), self.catalogues)
            self.assertEqual(len(paths), 3)
            for lang, path in zip(('en', 'fr', 'ar'), paths):
                body = path.read_text(encoding='utf-8')
                self.assertIn(f'<html lang="{lang}"', body)
                self.assertIn('dir="rtl"' if lang == 'ar' else 'dir="ltr"', body)
                self.assertEqual(body.count('<h1'), 1)
                self.assertIn('id="main"', body)
                self.assertIn('class="skip"', body)

    def test_dependency_graph_has_text_alternative(self):
        body = self.page()
        self.assertIn('role="img"', body)
        self.assertIn('id="rule-graph-title"', body)
        self.assertIn('id="rule-graph-desc"', body)
        for node in self.data['nodes']:
            self.assertIn(f'<code lang="en" dir="ltr">{node["id"]}</code>', body)
        self.assertIn(self.data['nodes'][0]['label']['en'], body)

    def test_all_dependencies_and_citations_are_rendered(self):
        body = self.page()
        for node in self.data['nodes']:
            for dependency in node['depends']:
                self.assertIn(dependency, body)
            self.assertIn(node['citation'], body)

    def test_ladder_renders_every_branch(self):
        body = self.page('fr')
        for step in self.data['ladder']:
            for value in (step['condition']['fr'], step['true']['fr'], step['false']['fr'], step['note']['fr']):
                self.assertIn(html.escape(value, quote=True), body)

    def test_linear_explanation_is_complete(self):
        body = self.page('ar')
        for explanation in self.data['text']['steps']['ar']:
            self.assertIn(html.escape(explanation, quote=True), body)
        self.assertIn(html.escape(self.data['text']['unknown']['ar'], quote=True), body)
        self.assertIn(html.escape(self.data['text']['limits']['ar'], quote=True), body)

    def test_sources_and_unsupported_semantics_are_rendered(self):
        body = self.page()
        for source in self.data['sources']:
            self.assertIn(source['url'], body)
            self.assertIn(source['label']['en'], body)
        for item in self.data['unsupported']:
            self.assertIn(item['label']['en'], body)
            self.assertIn(item['reason']['en'], body)

    def test_synthetic_badge_and_no_legal_claim(self):
        body = self.page()
        self.assertIn(self.catalogues['en']['rule.presentation.synthetic'], body)
        self.assertNotIn('Verified law', body)
        self.assertNotIn('in force', body.lower())

    def test_page_is_static_and_has_no_canvas_or_drag(self):
        body = self.page()
        self.assertNotIn('<script', body)
        self.assertNotIn('<canvas', body)
        self.assertNotIn('onclick', body)
        self.assertNotIn('draggable=', body)
        self.assertNotIn('<table', body)

    def test_rendering_is_deterministic(self):
        self.assertEqual(self.page('en'), self.page('en'))

    def test_rendering_does_not_mutate_input(self):
        data = copy.deepcopy(self.data)
        render_page(data, 'en', self.catalogues['en'])
        self.assertEqual(data, self.data)

    def test_missing_ui_string_fails_loudly(self):
        strings = dict(self.catalogues['en'])
        del strings['rule.presentation.ladder']
        with self.assertRaises(ValueError):
            render_page(self.data, 'en', strings)

    def test_invalid_artifact_cannot_render(self):
        data = fixture()
        data['nodes'][0]['depends'] = ['N99']
        with self.assertRaises(ValueError):
            render_page(data, 'en', self.catalogues['en'])

    def test_reviewed_presentation_renders_record_chain(self):
        data = fixture()
        data['synthetic'] = False
        data['review'] = {'status': 'reviewed', 'reviewer_role': 'Legal reviewer',
                          'reviewed_at': '2026-11-07', 'notes': 'Synthetic test review.'}
        data['record'] = {'instrument_id': 'instrument-1', 'source_id': 'source-1',
                          'provision_id': 'provision-1', 'legal_version': 'version-1',
                          'reviewed_interpretation_id': 'interpretation-1'}
        data['provenance']['artifact_sha256'] = 'a' * 64
        for source in data['sources']:
            source['url'] = 'https://gov.example/act#' + source['id'].lower()
        body = self.page('en', data)
        self.assertIn(self.catalogues['en']['rule.presentation.reviewed'], body)
        self.assertIn('instrument-1', body)
        self.assertIn('interpretation-1', body)
        self.assertNotIn('example.org', body)

    def test_locale_mode_and_ids(self):
        for lang in ('en', 'fr', 'ar'):
            body = self.page(lang)
            self.assertEqual(body.count('id="rule-graph-title"'), 1)
            self.assertEqual(body.count('id="rule-graph-desc"'), 1)
            self.assertIn(f'<html lang="{lang}"', body)

    def test_bilingual_content_is_present(self):
        self.assertIn('Politique de passation synthétique', self.page('fr'))
        self.assertIn('سياسة شراء اصطناعية', self.page('ar'))


if __name__ == '__main__':
    unittest.main()
