import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.build import load_i18n, t

PLACEHOLDER = re.compile(r'\{([a-z_]+)\}')
LATIN = re.compile(r'[A-Za-z]')


class I18nCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogues = load_i18n(REPO_ROOT / 'regions' / 'mena', ('en', 'fr', 'ar'))
        cls.en = cls.catalogues['en']
        cls.fr = cls.catalogues['fr']
        cls.ar = cls.catalogues['ar']

    def test_locales_declare_the_same_keys(self):
        self.assertEqual(set(self.en), set(self.fr))
        self.assertEqual(set(self.en), set(self.ar))

    def test_placeholders_match_between_locales(self):
        for key in self.en:
            with self.subTest(key=key):
                expected = set(PLACEHOLDER.findall(self.en[key]))
                self.assertEqual(expected, set(PLACEHOLDER.findall(self.fr[key])))
                self.assertEqual(expected, set(PLACEHOLDER.findall(self.ar[key])))

    def test_no_empty_values(self):
        for lang, catalogue in self.catalogues.items():
            for key, value in catalogue.items():
                with self.subTest(lang=lang, key=key):
                    self.assertTrue(value.strip())

    def test_values_contain_no_html_markup(self):
        for lang, catalogue in self.catalogues.items():
            for key, value in catalogue.items():
                with self.subTest(lang=lang, key=key):
                    self.assertNotIn('<', value)

    def test_arabic_values_have_no_unmarked_latin_text(self):
        for key, value in self.ar.items():
            without_placeholders = PLACEHOLDER.sub('', value)
            with self.subTest(key=key):
                self.assertIsNone(
                    LATIN.search(without_placeholders),
                    f'{key} contains Latin text that must be marked in the markup',
                )

    def test_missing_key_fails_loudly(self):
        with self.assertRaises(KeyError):
            t(self.en, 'home.missing.key')

    def test_placeholders_are_filled(self):
        self.assertEqual(
            t(self.en, 'home.snapshot.discovery', remaining=18, discovery=18),
            'Of the remaining 18 jurisdictions, 18 have candidate sources or queued discovery tasks.',
        )


if __name__ == '__main__':
    unittest.main()
