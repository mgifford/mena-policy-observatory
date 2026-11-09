import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import (
    FEATURED_VISUALIZATION_ID,
    build_view,
    esc,
    home_body,
    home_stats,
    load_coverage,
    load_i18n,
    page,
    t,
)

BASE = REPO_ROOT / 'regions' / 'mena'
DIST = REPO_ROOT / 'dist' / 'mena'


class HomepageResearchDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(BASE, ('en', 'fr', 'ar'))
        cls.cfg = json.loads((BASE / 'region.json').read_text(encoding='utf-8'))
        cls.view = build_view(load_coverage(BASE, REPO_ROOT / 'research-toolkit'))
        cls.policies = json.loads((BASE / 'data' / 'policies.json').read_text(encoding='utf-8'))
        cls.stats = home_stats(cls.policies, cls.view)

    def body(self, lang='en', policies=None, view=None, stats=None):
        return home_body(
            self.catalogues, lang, self.cfg,
            policies if policies is not None else self.policies,
            view if view is not None else self.view,
            stats=stats,
        )

    def test_counts_come_from_canonical_coverage_data(self):
        stats = home_stats(self.policies, self.view)
        self.assertEqual(stats['records'], len(self.policies))
        self.assertEqual(stats['total'], len(self.view['countries']))
        self.assertEqual(stats['covered'], len([c for c in self.view['countries'] if c['records']]))
        self.assertEqual(stats['domains'], len([d for d in self.view['domains'] if d['records']]))
        self.assertEqual(stats['candidates'], self.view['totals']['candidates'])
        self.assertEqual(
            stats['reviewed'],
            sum(1 for policy in self.policies
                if policy.get('legal_effect') in ('binding_confirmed', 'nonbinding_confirmed')),
        )
        body = self.body(stats=stats)
        for key in ('records', 'covered', 'total', 'domains', 'candidates', 'retrievals', 'reviewed'):
            self.assertIn(f'<dd>{stats[key]}</dd>', body)

    def test_jurisdictions_with_records_are_data_driven(self):
        body = self.body()
        with_records = [country for country in self.view['countries'] if country['records']]
        for country in with_records:
            self.assertIn(f'href="countries/{country["code"]}.html"', body)
        without_records = [country for country in self.view['countries'] if not country['records']]
        for country in without_records[:3]:
            self.assertNotIn(f'href="countries/{country["code"]}.html"', body)

    def test_policy_areas_with_records_are_data_driven(self):
        body = self.body()
        with_records = [domain for domain in self.view['domains'] if domain['records']]
        for domain in with_records:
            self.assertIn(f'href="domains/{domain["id"]}.html"', body)
        without_records = [domain for domain in self.view['domains'] if not domain['records']]
        for domain in without_records[:2]:
            self.assertNotIn(f'href="domains/{domain["id"]}.html"', body)

    def test_new_record_in_unrepresented_jurisdiction_and_domain_updates_homepage(self):
        view = copy.deepcopy(self.view)
        policies = copy.deepcopy(self.policies)
        country = next(country for country in view['countries'] if not country['records'])
        domain = next(domain for domain in view['domains'] if not domain['records'])
        record = copy.deepcopy(policies[0])
        record['id'] = 'test-homepage-new-record'
        record['title'] = 'Test homepage record'
        record['country'] = country['code']
        record['topic'] = domain['id']
        policies.append(record)
        country['records'].append(record)
        domain['records'].append(record)
        view['totals']['records'] += 1
        before = home_stats(self.policies, self.view)
        after = home_stats(policies, view)
        self.assertEqual(after['records'], before['records'] + 1)
        self.assertEqual(after['covered'], before['covered'] + 1)
        self.assertEqual(after['domains'], before['domains'] + 1)
        body = self.body(policies=policies, view=view, stats=after)
        self.assertIn(f'href="countries/{country["code"]}.html"', body)
        self.assertIn(f'href="domains/{domain["id"]}.html"', body)
        for key in ('records', 'covered', 'domains'):
            self.assertIn(f'<dd>{after[key]}</dd>', body)

    def test_no_bilingual_claim_remains(self):
        for lang in ('en', 'fr', 'ar'):
            strings = self.catalogues[lang]
            self.assertNotIn('biling', strings['home.title'].lower())
            self.assertNotIn('biling', strings['home.description'].lower())
            body = self.body(lang)
            self.assertNotIn('bilingual', body.lower())
            self.assertNotIn('bilingue', body.lower())

    def test_old_three_country_and_single_domain_claims_gone(self):
        body = self.body()
        self.assertNotIn('the United Arab Emirates, Saudi Arabia, and Qatar', body)
        self.assertNotIn('Digital accessibility is the only researched policy area', body)
        self.assertNotIn('Every other listed country is marked as not yet researched', body)

    def test_primary_paths_are_semantic_and_equivalent_across_locales(self):
        paths = (
            'countries/index.html',
            'comparison/index.html',
            'visualizations/index.html',
            'sources/index.html',
        )
        for lang in ('en', 'fr', 'ar'):
            body = self.body(lang)
            for path in paths:
                self.assertIn(f'href="{path}"', body)
            self.assertIn('<nav aria-label=', body)

    def test_featured_visualization_is_linked_and_labeled(self):
        body = self.body()
        self.assertIn(f'visualizations/{FEATURED_VISUALIZATION_ID}.html', body)
        self.assertIn(self.catalogues['en']['home.featured.status'], body)
        self.assertIn(self.catalogues['en']['home.featured.link'], body)
        self.assertTrue((DIST / 'en' / 'visualizations' / f'{FEATURED_VISUALIZATION_ID}.html').is_file())

    def test_synthetic_example_is_separate_and_clearly_labeled(self):
        body = self.body()
        self.assertIn('href="visualizations/synthetic.html#legalese-visualization"', body)
        self.assertIn(self.catalogues['en']['home.rules.synthetic'], body)
        self.assertIn(self.catalogues['en']['home.rules.engine_note'], body)
        self.assertIn('docs/RULES-ENGINE-COMPARISON.md', body)

    def test_rules_as_code_section_shows_machine_readable_examples_and_ladder(self):
        body = self.body()
        self.assertIn(self.catalogues['en']['home.rules.heading'], body)
        self.assertIn('procurement_obligation', body)
        self.assertIn('procurement outcome', body)
        self.assertIn(self.catalogues['en']['home.rules.axiom_label'], body)
        self.assertIn(self.catalogues['en']['home.rules.l4_label'], body)
        self.assertIn(self.catalogues['en']['home.rules.ladder_heading'], body)
        self.assertIn('SP-3', body)
        self.assertIn('visualizations/synthetic.html#legalese-visualization', body)
        self.assertIn('docs/RULES-ENGINE-COMPARISON.md', body)
        self.assertIn(self.catalogues['en']['home.rules.synthetic'], body)
        self.assertIn('No real legal instrument is encoded', body)

    def test_rules_navigation_link_is_present(self):
        strings = self.catalogues['en']
        html = page(
            self.catalogues, 'en', strings['home.title'], self.body(),
            1, {'fr': '../fr/', 'ar': '../ar/'},
            t(strings, 'home.description', **{
                key: self.stats[key] for key in ('records', 'covered', 'total', 'domains')
            }),
        )
        self.assertIn('#rules-as-code', html)
        self.assertIn(strings['nav.rules'], html)

    def test_comparison_and_source_links_resolve(self):
        body = self.body()
        for relative in ('comparison/index.html', 'sources/index.html',
                         'coverage/index.html', 'countries/index.html',
                         'domains/index.html', 'tasks/index.html'):
            self.assertIn(f'href="{relative}"', body)
            self.assertTrue((DIST / 'en' / relative).is_file(), relative)

    def test_homepage_does_not_promote_unreviewed_legal_effect(self):
        body = self.body()
        confirmed = [policy for policy in self.policies
                     if policy.get('legal_effect') in ('binding_confirmed', 'nonbinding_confirmed')]
        if not confirmed:
            for lang in ('en', 'fr', 'ar'):
                self.assertNotIn(self.catalogues[lang]['record.legal.binding'], body)
        self.assertIn('not legally reviewed', body.lower())

    def test_homepage_has_no_full_country_table(self):
        body = self.body()
        self.assertNotIn('<table', body)
        self.assertIn('<dl class="stat-grid">', body)

    def test_homepage_has_a_short_start_here_orientation(self):
        body = self.body()
        self.assertIn(self.catalogues['en']['home.start.heading'], body)
        self.assertIn(self.catalogues['en']['home.start.rules'], body)
        self.assertIn('href="visualizations/synthetic.html"', body)
        self.assertIn('href="countries/index.html"', body)
        self.assertIn('href="index.html#method"', body)

    def test_root_is_a_short_start_here_and_language_chooser(self):
        root = (REPO_ROOT / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('<html lang="en"', root)
        self.assertIn(self.catalogues['en']['root.start_heading'], root)
        self.assertIn(self.catalogues['en']['root.start_rules'], root)
        self.assertIn('mena/en/visualizations/synthetic.html', root)
        self.assertIn('mena/fr/', root)
        self.assertIn('mena/ar/', root)
        self.assertNotIn('class="site-nav"', root)
        self.assertIn('location.replace', root)

    def test_favicon_is_copied_and_linked_at_every_depth(self):
        svg = REPO_ROOT / 'dist' / 'favicon.svg'
        self.assertTrue(svg.is_file())
        markup = svg.read_text(encoding='utf-8')
        self.assertIn('<title id="title">MENA Policy Observatory</title>', markup)
        self.assertIn('role="img"', markup)
        root = (REPO_ROOT / 'dist' / 'index.html').read_text(encoding='utf-8')
        home = (DIST / 'en' / 'index.html').read_text(encoding='utf-8')
        record = (DIST / 'en' / 'records' / 'ae-national-digital-accessibility.html').read_text(encoding='utf-8')
        self.assertIn('href="favicon.svg"', root)
        self.assertIn('href="../../favicon.svg"', home)
        self.assertIn('href="../../../favicon.svg"', record)
        self.assertIn('name="theme-color" content="#0B2A4A"', home)

    def test_metadata_is_trilingual_and_uses_derived_counts(self):
        for lang in ('en', 'fr', 'ar'):
            strings = self.catalogues[lang]
            stats = self.stats
            description = t(strings, 'home.description', **{
                key: stats[key] for key in ('records', 'covered', 'total', 'domains')
            })
            html = page(
                self.catalogues, lang, strings['home.title'], self.body(lang),
                1, {'en': '../en/', 'fr': '../fr/', 'ar': '../ar/'}, description,
            )
            self.assertIn(f'<meta name="description" content="{esc(description)}">', html)
            self.assertIn(f'<html lang="{lang}"', html)
            self.assertNotIn('bilingual', html.lower())
            self.assertNotIn('bilingue', html.lower())

    def test_rendered_homepage_has_no_dynamic_content(self):
        body = self.body()
        self.assertNotIn('<script', body)
        self.assertNotIn('onclick=', body)


if __name__ == '__main__':
    unittest.main()
