import copy
import html
import hashlib
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
    validate_publication,
)

FIXTURE = REPO_ROOT / 'regions' / 'mena' / 'data' / 'visualizations' / 'synthetic-procurement.json'


def fixture():
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


class RulePresentationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_catalogues()

    def page_en(self, data):
        return render_page(data, 'en', self.catalogues['en'])

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

    def test_partial_translation_is_allowed_but_all_missing_is_rejected(self):
        data = fixture()
        del data['title']['fr']
        del data['text']['steps']['fr']
        self.assertEqual(validate_presentation(data), [])
        data = fixture()
        for code in ('en', 'fr', 'ar'):
            data['title'][code] = None
        self.assertTrue(any('at least one language expression' in error
                            for error in validate_presentation(data)))

    def test_unknown_effective_period_is_allowed_without_dates(self):
        data = fixture()
        data['effective_period'] = {'from': None, 'to': None, 'status': 'unknown'}
        self.assertEqual(validate_presentation(data), [])
        body = self.page_en(data)
        self.assertIn('Unknown', body)
        self.assertNotIn('None', body)

    def test_unknown_status_cannot_invent_a_date(self):
        data = fixture()
        data['effective_period']['status'] = 'unknown'
        self.assertTrue(any('must not invent dates' in error
                            for error in validate_presentation(data)))

    def test_conditional_period_requires_a_condition(self):
        data = fixture()
        data['effective_period'] = {
            'from': '2026-01-01', 'to': None, 'status': 'conditional',
            'condition': {'en': 'When the commencement order is made', 'fr': 'Lorsque l’ordre est pris', 'ar': 'عند صدور أمر البدء'},
        }
        self.assertEqual(validate_presentation(data), [])
        body = self.page_en(data)
        self.assertIn('Conditional', body)

    def test_mapping_references_are_checked(self):
        data = fixture()
        data['mappings']['node_steps'].append({'node': 'N99', 'step': 1})
        self.assertTrue(any('unknown node' in error for error in validate_presentation(data)))
        data = fixture()
        data['mappings']['branches'].append({'step': 1, 'true': 'continue', 'false': 'continue'})
        self.assertTrue(any('same true and false' in error for error in validate_presentation(data)))
        data = fixture()
        data['mappings']['tests'].append({'id': 'unknown', 'expected': 'not_an_outcome'})
        self.assertTrue(any('unknown expected outcome' in error for error in validate_presentation(data)))

    def test_invalid_effective_period_is_rejected(self):
        data = fixture()
        data['effective_period'] = {'from': '2026-02-01', 'to': '2026-01-01'}
        self.assertTrue(any('cannot be before' in error for error in validate_presentation(data)))
        data = fixture()
        data['effective_period']['from'] = '2026-02-30'
        self.assertTrue(any('needs a valid from date' in error or 'valid ISO date' in error for error in validate_presentation(data)))

    def test_constant_needs_a_value(self):
        data = fixture()
        data['nodes'][5]['value'] = None
        self.assertTrue(any('constants need a value' in error for error in validate_presentation(data)))

    def test_unknown_top_level_key_is_rejected(self):
        data = fixture()
        data['extra'] = True
        self.assertTrue(validate_presentation(data))


class PublicationGateTests(unittest.TestCase):
    def real_case(self):
        data = fixture()
        data['synthetic'] = False
        data['review'] = {'status': 'reviewed', 'reviewer_role': 'Legal reviewer',
                          'reviewed_at': '2026-11-07', 'notes': 'Synthetic test review.'}
        data['record'] = {'instrument_id': 'instrument-1', 'source_id': 'source-1',
                          'provision_id': 'provision-1', 'legal_version': '1.0',
                          'reviewed_interpretation_id': 'interpretation-1'}
        for source in data['sources']:
            source['url'] = 'https://gov.example/act#' + source['id'].lower()
        return data

    def root(self, temporary):
        root = Path(temporary)
        (root / 'regions/mena/data').mkdir(parents=True, exist_ok=True)
        (root / 'regions/mena/policies/instrument-1').mkdir(parents=True, exist_ok=True)
        (root / 'artifacts').mkdir(exist_ok=True)
        (root / 'tests').mkdir(exist_ok=True)
        (root / 'regions/mena/data/policies.json').write_text(
            json.dumps([{'id': 'instrument-1'}]), encoding='utf-8')
        (root / 'regions/mena/policies/instrument-1/research.json').write_text(json.dumps({
            'record_id': 'instrument-1',
            'sources': [{'id': 'source-1', 'document_version': '1.0',
                         'effective_date': 'unknown', 'publication_date': 'unknown'}],
            'provisions': [{'id': 'provision-1', 'source_ids': ['source-1']}],
            'interpretations': [{'id': 'interpretation-1', 'status': 'resolved',
                                 'resolution': 'Reviewed synthetic interpretation.',
                                 'reviewer': 'Reviewer', 'reviewed_at': '2026-11-07'}],
            'review': {'status': 'reviewed', 'reviewer': 'Reviewer',
                       'reviewed_at': '2026-11-07', 'scope': 'Synthetic review'},
            'relations': [],
        }), encoding='utf-8')
        artifact = (root / 'artifacts/encoding.json')
        artifact.write_text('{"engine_version": "0.2.2"}\n', encoding='utf-8')
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        (root / 'tests/evidence.json').write_text(
            '{"results": [{"id": "case-1", "status": "passed"}]}\n', encoding='utf-8')
        data = self.real_case()
        data['provenance']['artifact_path'] = 'artifacts/encoding.json'
        data['provenance']['tests_path'] = 'tests/evidence.json'
        data['provenance']['artifact_sha256'] = digest
        return data, root

    def test_real_case_passes_with_resolved_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, root = self.root(temporary)
            self.assertEqual(validate_publication(data, root), [])

    def test_real_case_rejects_wrong_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, root = self.root(temporary)
            data['record']['source_id'] = 'missing'
            self.assertTrue(any('unknown source_id' in error
                                for error in validate_publication(data, root)))

    def test_real_case_rejects_unresolved_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, root = self.root(temporary)
            research_path = root / 'regions/mena/policies/instrument-1/research.json'
            research = json.loads(research_path.read_text())
            research['review']['status'] = 'pending'
            research_path.write_text(json.dumps(research), encoding='utf-8')
            self.assertTrue(any('research record itself is not reviewed' in error
                                for error in validate_publication(data, root)))

    def test_real_case_rejects_bad_artifact_and_test_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, root = self.root(temporary)
            data['provenance']['artifact_sha256'] = 'b' * 64
            self.assertTrue(any('artifact checksum' in error
                                for error in validate_publication(data, root)))
            data, root = self.root(temporary)
            (root / 'tests/evidence.json').write_text(
                '{"results": [{"id": "case-1", "status": "failed"}]}\n', encoding='utf-8')
            self.assertTrue(any('non-passing' in error
                                for error in validate_publication(data, root)))


class RulePresentationRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = fixture()
        cls.catalogues = load_catalogues()

    def page(self, lang='en', data=None):
        return render_page(data or self.data, lang, self.catalogues[lang])

    def page_en(self, data):
        return self.page('en', data)

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

    def test_partial_translation_renders_a_marked_fallback(self):
        data = copy.deepcopy(self.data)
        for key in ('title', 'summary', 'disclaimer'):
            data[key]['fr'] = None
        data['nodes'][0]['label']['fr'] = None
        data['ladder'][0]['condition']['fr'] = None
        data['sources'][0]['label']['fr'] = None
        data['text']['steps']['fr'] = None
        body = self.page('fr', data)
        self.assertIn(html.escape(self.catalogues['fr']['rule.presentation.translation_fallback'], quote=True), body)
        self.assertIn('Synthetic procurement policy', body)
        self.assertIn('lang="en"', body)

    def test_publication_gate_exempts_synthetic(self):
        self.assertEqual(validate_publication(self.data, REPO_ROOT), [])

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
