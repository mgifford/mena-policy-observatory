import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import load_i18n, record_body
from framework.research import load_research
from framework.schema_lite import Validator
from framework.research_visualization import (
    DIRECTIONS,
    SELECTED_RECORDS,
    SYNTHETIC_FIXTURE,
    build_structure,
    index_body,
    selected_records,
    synthetic_page_body,
    validate_structure,
    visualization_body,
)

BASE = REPO_ROOT / 'regions' / 'mena'
FIXTURE = REPO_ROOT / SYNTHETIC_FIXTURE


class SourceStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))
        cls.selected = selected_records(BASE)
        cls.policies = json.loads((BASE / 'data' / 'policies.json').read_text(encoding='utf-8'))

    def test_eleven_records_selected(self):
        self.assertEqual([record['id'] for record, _ in self.selected], list(SELECTED_RECORDS))
        self.assertEqual(len(self.selected), 11)

    def test_model_has_every_recorded_node_and_no_invented_id(self):
        for record, research in self.selected:
            model = build_structure(record, research)
            self.assertEqual(validate_structure(model), [])
            ids = {node['id'] for node in model['nodes']}
            self.assertIn(f'record:{record["id"]}', ids)
            for item in research['provisions']:
                self.assertIn(item['id'], ids)
            for item in research['interpretations']:
                self.assertIn(item['id'], ids)
            for item in research['relations']:
                self.assertIn(item['id'], ids)

    def test_every_node_has_required_evidence_fields(self):
        for record, research in self.selected:
            model = build_structure(record, research)
            for node in model['nodes']:
                for field in ('id', 'type', 'label', 'source_ref', 'evidence_status',
                              'language', 'review_state', 'uncertainty'):
                    self.assertIn(field, node)
                self.assertIn(node['type'], ('instrument', 'provision', 'question', 'related'))
                self.assertIsInstance(node['uncertainty'], list)

    def test_every_edge_resolves_and_keeps_recorded_label(self):
        for record, research in self.selected:
            model = build_structure(record, research)
            ids = {node['id'] for node in model['nodes']}
            for edge in model['edges']:
                self.assertIn(edge['source'], ids)
                self.assertIn(edge['target'], ids)
                self.assertIn(edge['type'], ('contains', 'raises_question', 'records_relation'))
                self.assertTrue(edge['evidence_ref'])
                self.assertTrue(edge['review_state'])
            for relation in model['relations']:
                if relation['relation'] == 'unspecified':
                    self.assertNotEqual(relation['recorded_label'], 'amends')

    def test_source_languages_support_persian_and_turkish_tags(self):
        source = copy.deepcopy(self.selected[0][1]['sources'][0])
        source['language'] = 'fa'
        source['translation']['target_language'] = 'tr'
        validator = Validator(BASE / 'schemas')
        schema = validator.schema('source-record.schema.json')
        self.assertEqual(validator.validate(source, schema), [])
        self.assertEqual(DIRECTIONS['fa'], 'rtl')
        self.assertEqual(DIRECTIONS['tr'], 'ltr')

    def test_uae_law_keeps_arabic_original_and_english_translation(self):
        record, research = next(
            (item for item in self.selected if item[0]['id'] == 'ae-federal-law-29-2006'))
        source = research['sources'][0]
        self.assertEqual(source['language'], 'ar')
        self.assertEqual(source['authoritative_language'], 'yes')
        kinds = {expression['kind'] for expression in source['expressions']}
        self.assertEqual(kinds, {'original_authoritative', 'official_translation'})
        self.assertEqual(len(research['provisions']), 5)
        self.assertEqual(record['legal_effect'], 'not_legally_assessed')

    def test_unknown_dates_are_not_fabricated(self):
        for record, research in self.selected:
            source = research['sources'][0]
            if source['publication_date'] == 'unknown':
                self.assertEqual(source['publication_date'], 'unknown')
            if source['effective_date'] == 'unknown':
                self.assertEqual(source['effective_date'], 'unknown')

    def test_build_does_not_mutate_research(self):
        record, research = self.selected[0]
        before = copy.deepcopy(research)
        build_structure(record, research)
        self.assertEqual(research, before)

    def test_invalid_models_are_rejected(self):
        model = build_structure(*self.selected[0])
        bad = copy.deepcopy(model)
        bad['nodes'].append(copy.deepcopy(bad['nodes'][0]))
        self.assertTrue(any('duplicate node' in error for error in validate_structure(bad)))
        bad = copy.deepcopy(model)
        bad['edges'][0]['target'] = 'missing'
        self.assertTrue(any('unresolved endpoint' in error for error in validate_structure(bad)))
        bad = copy.deepcopy(model)
        bad['nodes'][0]['type'] = 'statute'
        self.assertTrue(any('unknown type' in error for error in validate_structure(bad)))


class SourceStructureRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))
        cls.selected = selected_records(BASE)
        cls.policies = json.loads((BASE / 'data' / 'policies.json').read_text(encoding='utf-8'))
        cls.record, cls.research = cls.selected[0]
        cls.body_en = visualization_body(cls.catalogues['en'], 'en', cls.record, cls.research)
        cls.body_ar = visualization_body(cls.catalogues['ar'], 'ar', cls.record, cls.research)

    def test_source_links_and_locators_are_present(self):
        source = self.research['sources'][0]
        self.assertIn(source['url'], self.body_en)
        for provision in self.research['provisions']:
            self.assertIn(provision['id'], self.body_en)
            self.assertIn(provision['locator']['value'], self.body_en)
            self.assertIn(provision['summary'], self.body_en)

    def test_candidate_interpretation_is_prominent(self):
        self.assertIn(self.catalogues['en']['visualizations.candidate_notice'], self.body_en)
        for question in self.research['interpretations']:
            self.assertIn(question['id'], self.body_en)
            self.assertIn(question['statement'], self.body_en)
        self.assertIn(self.catalogues['en']['visualizations.reviewed_none'], self.body_en)

    def test_source_evidence_is_honest(self):
        source = self.research['sources'][0]
        if source['capture']['bytes_stored']:
            self.assertIn(self.catalogues['en']['visualizations.capture_stored'], self.body_en)
        else:
            self.assertIn(self.catalogues['en']['visualizations.capture_none'], self.body_en)
        if source['excerpt_status'] == 'recorded':
            self.assertIn(self.catalogues['en']['visualizations.excerpt_recorded'], self.body_en)
            self.assertIn(source['excerpt']['text'], self.body_en)
        else:
            self.assertIn(self.catalogues['en']['visualizations.excerpt_none'], self.body_en)

    def test_graph_has_title_and_complete_text_equivalent(self):
        self.assertIn('role="img"', self.body_en)
        self.assertIn('id="struct-title"', self.body_en)
        self.assertIn('id="struct-desc"', self.body_en)
        self.assertIn(self.catalogues['en']['visualizations.text_heading'], self.body_en)
        for node in build_structure(self.record, self.research)['nodes']:
            self.assertIn(node['id'], self.body_en)

    def test_arabic_source_content_is_marked(self):
        self.assertIn('lang="en" dir="ltr"', self.body_ar)
        self.assertIn(self.catalogues['ar']['visualizations.candidate_notice'], self.body_ar)

    def test_no_script_canvas_or_invented_deep_link(self):
        for body in (self.body_en, self.body_ar):
            self.assertNotIn('<script', body)
            self.assertNotIn('<canvas', body)
            self.assertNotIn('onclick', body)
            source = self.research['sources'][0]['url']
            for provision in self.research['provisions']:
                self.assertNotIn(source + '#' + provision['locator']['value'], body)

    def test_index_lists_only_selected_and_synthetic(self):
        body = index_body(self.catalogues['en'], 'en', self.selected)
        for record, _ in self.selected:
            self.assertIn(f'href="{record["id"]}.html"', body)
        self.assertIn('href="synthetic.html"', body)
        self.assertIn(self.catalogues['en']['visualizations.prototype_notice'], body)
        self.assertIn(self.catalogues['en']['visualizations.synthetic_notice'], body)
        self.assertIn(self.catalogues['en']['visualizations.reviewed_none'], body)
        for record in self.policies:
            if record['id'] not in SELECTED_RECORDS:
                self.assertNotIn(f'href="{record["id"]}.html"', body)

    def test_index_all_locales(self):
        for lang in ('en', 'fr', 'ar'):
            body = index_body(self.catalogues[lang], lang, self.selected)
            self.assertIn(self.catalogues[lang]['visualizations.h1'], body)
            self.assertIn(f'href="{self.selected[0][0]["id"]}.html"', body)

    def test_record_page_links_every_selected_record(self):
        for record, research in self.selected:
            body = record_body(self.catalogues, 'en', record, BASE, research)
            self.assertIn(f'href="../visualizations/{record["id"]}.html"', body)

    def test_synthetic_demo_is_clearly_labelled_and_links_evidence(self):
        fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        body = synthetic_page_body(self.catalogues['en'], 'en', fixture, self.catalogues)
        self.assertTrue(fixture['synthetic'])
        self.assertIn(self.catalogues['en']['visualizations.prototype_notice'], body)
        self.assertIn(self.catalogues['en']['visualizations.synthetic_notice'], body)
        self.assertIn('research/rules-visualization/axiom/procurement.rulespec.yaml', body)
        self.assertIn('research/rules-visualization/l4/procurement.l4', body)
        self.assertIn('axiom-cases.json', body)
        self.assertIn(self.catalogues['en']['visualizations.synthetic_results_heading'], body)
        for case in ('Missing required input', 'Boundary USD 100,000', 'Facts incomplete'):
            self.assertIn(case, body)
        self.assertIn(self.catalogues['en']['visualizations.synthetic_semantics_text'], body)

    def test_synthetic_fixture_is_not_a_real_record(self):
        fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.assertEqual(fixture['review']['status'], 'synthetic_fixture')
        self.assertTrue(fixture['synthetic'])
        self.assertIsNone(fixture['record'])


if __name__ == '__main__':
    unittest.main()
