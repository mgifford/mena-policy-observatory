import json
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import (
    breadcrumb_trail,
    build_view,
    comparison_body,
    countries_index_body,
    country_body,
    coverage_body,
    domain_body,
    domains_index_body,
    home_body,
    load_coverage,
    load_i18n,
    sources_body,
    tasks_body,
)

BASE = REPO_ROOT / 'regions' / 'mena'


class CoveragePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'ar'))
        cls.cfg = json.loads((BASE / 'region.json').read_text(encoding='utf-8'))
        cls.view = build_view(load_coverage(BASE, REPO_ROOT / 'research-toolkit'))
        cls.policies = json.loads((BASE / 'data' / 'policies.json').read_text(encoding='utf-8'))

    def country(self, code):
        return next(item for item in self.view['countries'] if item['code'] == code)

    def domain(self, domain_id):
        return next(item for item in self.view['domains'] if item['id'] == domain_id)

    def test_countries_index_lists_every_jurisdiction(self):
        body = countries_index_body(self.catalogues, 'en', self.view)
        for code in ('AE', 'SA', 'QA', 'PS', 'EH'):
            self.assertIn(f'href="{code}.html"', body)
        self.assertIn('Not started', body)
        self.assertIn('Candidate sources identified', body)

    def test_country_page_links_records_and_candidates(self):
        body = country_body(self.catalogues, 'en', self.view, self.country('AE'))
        self.assertIn('href="../records/ae-national-digital-accessibility.html"', body)
        self.assertIn('Legal review pending', body)
        self.assertIn('href="../domains/digital_accessibility.html"', body)

    def test_country_without_evidence_states_that_absence_is_not_proof(self):
        body = country_body(self.catalogues, 'en', self.view, self.country('LY'))
        self.assertIn('No policy record is published for this jurisdiction', body)
        self.assertIn('does not establish that no relevant instrument exists', body)

    def test_country_page_marks_english_notes_on_arabic_page(self):
        body = country_body(self.catalogues, 'ar', self.view, self.country('EH'))
        self.assertIn('<span lang="en" dir="ltr">', body)
        self.assertIn('غير مسجل', body)

    def test_arabic_country_page_translates_group_and_notes(self):
        body = country_body(self.catalogues, 'ar', self.view, self.country('EH'))
        self.assertIn('إضافات إقليمية', body)
        self.assertIn('إقليم لم تُحسم سيادته', body)
        self.assertNotIn('<span lang="en" dir="ltr">Regional additions</span>', body)
        self.assertNotIn('Territory with unresolved sovereignty', body)

    def test_domains_index_and_page(self):
        index = domains_index_body(self.catalogues, 'en', self.view)
        for domain_id in ('digital_accessibility', 'ai_governance', 'srhr'):
            self.assertIn(f'href="{domain_id}.html"', index)
        body = domain_body(self.catalogues, 'en', self.view,
                           self.domain('digital_accessibility'))
        self.assertIn('Legal review pending', body)
        self.assertIn('href="../countries/AE.html"', body)

    def test_coverage_matrix_fills_every_cell(self):
        body = coverage_body(self.catalogues, 'en', self.view)
        self.assertEqual(body.count('<th scope="col">'), 9)
        self.assertEqual(body.count('<th scope="row">'), 24)
        self.assertEqual(body.count('<td>'), 24 * 8)
        self.assertIn('How to read the statuses', body)

    def test_tasks_page_renders_every_task(self):
        body = tasks_body(self.catalogues, 'en', self.view)
        self.assertEqual(body.count('<tr><th scope="row">'), 54)
        self.assertIn('DZ-DIGITAL-ACCESSIBILITY-DISCOVERY-001', body)
        self.assertIn('MENA-T02-001-VERIFY', body)
        self.assertIn('Source discovery', body)

    def test_sources_page_marks_leads_as_unreviewed(self):
        body = sources_body(self.catalogues, 'en', self.view)
        self.assertEqual(body.count('<dl>'), 23)
        self.assertIn('Unreviewed discovery lead', body)
        self.assertIn('Human review of these candidate leads is still pending', body)
        self.assertIn('https://www.mtcit.gov.om/', body)

    def test_sources_page_shows_candidate_verification_metadata(self):
        body = sources_body(self.catalogues, 'en', self.view)
        self.assertIn('Candidate official source. Its current legal effect, applicability, and provision-level interpretation have not yet been independently verified.', body)
        self.assertIn('mena-t02-001', body)
        self.assertIn('MENA-T02-001-VERIFY', body)
        self.assertIn('Outstanding verification', body)
        self.assertIn('Confirm the official source and its issuing authority', body)
        self.assertIn('Reported amendment', body)
        self.assertIn('Import package', body)
        self.assertIn('Not independently checkable', body)

    def test_sources_page_shows_instrument_identity_and_versions(self):
        body = sources_body(self.catalogues, 'en', self.view)
        self.assertIn('Reported instrument', body)
        self.assertIn('Version dates', body)
        self.assertIn('Captured version', body)
        self.assertIn('Instrument types and numbers are parsed from reported titles', body)
        self.assertIn('Decree-law', body)
        self.assertIn('<code lang="en" dir="ltr">18-07</code>', body)
        self.assertIn('Not captured', body)

    def test_arabic_sources_page_translates_instrument_labels(self):
        body = sources_body(self.catalogues, 'ar', self.view)
        self.assertIn('الوثيقة المُبلغ عنها', body)
        self.assertIn('تواريخ النسخة', body)
        self.assertIn('النسخة المحفوظة', body)
        self.assertIn('غير محفوظة', body)

    def test_sources_page_shows_publisher_and_source_health(self):
        body = sources_body(self.catalogues, 'en', self.view)
        self.assertIn('Publisher host', body)
        self.assertIn('Publisher registry', body)
        self.assertIn('Source health', body)
        self.assertIn('Not yet checked', body)
        self.assertIn('No source check is recorded for these leads', body)
        self.assertIn('droit.mjustice.gov.dz', body)
        self.assertIn('Unverified', body)

    def test_arabic_sources_page_translates_source_health(self):
        body = sources_body(self.catalogues, 'ar', self.view)
        self.assertIn('حالة المصدر', body)
        self.assertIn('لم يُفحص بعد', body)
        self.assertIn('سجل الناشرين', body)

    def test_arabic_sources_page_translates_candidate_metadata(self):
        body = sources_body(self.catalogues, 'ar', self.view)
        self.assertIn('حالة المراجعة القانونية', body)
        self.assertIn('التحقق المطلوب', body)
        self.assertIn('حزمة الاستيراد', body)
        self.assertIn('<span lang="en" dir="ltr">Law 18-07 of 2018</span>', body)

    def test_comparison_page_renders_all_provisions(self):
        body = comparison_body(self.catalogues, 'en', self.view)
        self.assertEqual(body.count('<tr><th scope="row">'), 14)
        self.assertIn('P-01', body)

    def test_home_links_new_coverage_views(self):
        body = home_body(self.catalogues, 'en', self.cfg, self.policies, self.view)
        for path in ('coverage/index.html', 'countries/index.html', 'domains/index.html',
                     'tasks/index.html', 'sources/index.html', 'comparison/index.html'):
            self.assertIn(f'href="{path}"', body)
        self.assertIn('href="countries/AE.html"', body)

    def test_page_bodies_are_deterministic(self):
        for builder, args in (
                (sources_body, ()),
                (countries_index_body, ()),
                (domains_index_body, ()),
                (coverage_body, ()),
                (tasks_body, ()),
                (comparison_body, ())):
            for lang in ('en', 'ar'):
                first = builder(self.catalogues, lang, self.view, *args)
                second = builder(self.catalogues, lang, self.view, *args)
                self.assertEqual(first, second, f'{builder.__name__} is not deterministic')

    def test_breadcrumb_lists_contain_only_list_items(self):
        class ListChildCheck(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []
                self.invalid = []

            def handle_starttag(self, tag, attrs):
                if self.stack and self.stack[-1] in ('ol', 'ul') and tag not in (
                        'li', 'script', 'template', 'style'):
                    self.invalid.append(tag)
                if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img',
                               'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if tag in self.stack:
                    while self.stack:
                        if self.stack.pop() == tag:
                            break

        markup = breadcrumb_trail([
            ('../index.html', 'Home', False),
            ('index.html', 'Coverage', False),
            (None, 'Current', True),
        ])
        check = ListChildCheck()
        check.feed(markup)
        self.assertEqual(check.invalid, [])


if __name__ == '__main__':
    unittest.main()
