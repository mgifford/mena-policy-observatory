import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / 'research-toolkit' / 'scripts'))

from framework.coverage import build_view, load_coverage, validate_coverage  # noqa: E402
from instruments import derive, parse_instrument, run  # noqa: E402

SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
INSTRUMENTS = REPO_ROOT / 'research-toolkit' / 'sources' / 'instruments.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class InstrumentParsingTests(unittest.TestCase):
    def test_law_with_year(self):
        self.assertEqual(parse_instrument('Law 18-07 of 2018'), ('law', '18-07', '2018'))

    def test_act_with_number(self):
        self.assertEqual(parse_instrument('Data Protection Act 005 of 2023'),
                         ('act', '005', '2023'))

    def test_decree_law(self):
        self.assertEqual(parse_instrument('Decree-Law 10 of 2018 concerning cybercrime'),
                         ('decree_law', '10', '2018'))

    def test_policy_statement_has_unknown_identity(self):
        self.assertEqual(parse_instrument('Ministry of Education Accessibility Statement'),
                         ('unknown', None, None))

    def test_announcement_without_number_has_unknown_identity(self):
        self.assertEqual(parse_instrument('2026 Data Protection Act regulations approval'),
                         ('unknown', None, None))

    def test_number_without_standalone_year(self):
        self.assertEqual(parse_instrument('Law 177/AN/25 ratifying a protocol'),
                         ('law', '177/AN/25', None))


class InstrumentDataTests(unittest.TestCase):
    def test_committed_instruments_are_current(self):
        self.assertEqual(run(check=True), 0)

    def test_every_candidate_has_one_instrument(self):
        instruments = load(INSTRUMENTS)['instruments']
        candidates = load(SOURCES)['records']
        self.assertEqual(len(instruments), len(candidates))
        self.assertEqual({item['candidate_id'] for item in instruments},
                         {candidate['id'] for candidate in candidates})
        for item in instruments:
            self.assertEqual(item['work_id'], item['candidate_id'])
            self.assertEqual(item['review_state'], 'reported')
            self.assertIsNone(item['captured_item'])

    def test_derivation_is_idempotent(self):
        sources = load(SOURCES)
        first = derive(sources)
        second = derive(sources, first)
        self.assertEqual(first, second)

    def test_human_dates_and_authority_are_preserved(self):
        sources = load(SOURCES)
        first = derive(sources)
        first['instruments'][0]['dates']['commencement'] = '2020-01-01'
        first['instruments'][0]['issuing_authority'] = 'Recorded authority'
        second = derive(sources, first)
        self.assertEqual(second['instruments'][0]['dates']['commencement'], '2020-01-01')
        self.assertEqual(second['instruments'][0]['issuing_authority'], 'Recorded authority')

    def test_write_and_recheck_in_temporary_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'instruments.json'
            self.assertEqual(run(SOURCES, path), 0)
            first = path.read_text(encoding='utf-8')
            self.assertEqual(run(SOURCES, path, check=True), 0)
            self.assertEqual(run(SOURCES, path), 0)
            self.assertEqual(path.read_text(encoding='utf-8'), first)

    def test_live_data_validates(self):
        self.assertEqual(validate_coverage(load_coverage()), [])

    def test_publication_date_matches_candidate(self):
        instruments = load(INSTRUMENTS)['instruments']
        candidates = {candidate['id']: candidate for candidate in load(SOURCES)['records']}
        for item in instruments:
            reported = candidates[item['candidate_id']]['published_date_reported']
            expected = reported if isinstance(reported, str) and len(reported) == 10 else None
            self.assertEqual(item['publication_date_reported'], expected)


class InstrumentValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = load_coverage()

    def errors(self):
        return validate_coverage(self.data)

    def test_missing_instrument_is_rejected(self):
        self.data.instruments = self.data.instruments[1:]
        self.assertTrue(any('has no instrument record' in error for error in self.errors()))

    def test_title_mismatch_is_rejected(self):
        self.data.instruments[0]['title_reported'] = 'Different title'
        self.assertTrue(any('title_reported does not match' in error for error in self.errors()))

    def test_unknown_type_with_number_is_rejected(self):
        self.data.instruments[0]['instrument_type_reported'] = 'unknown'
        self.data.instruments[0]['instrument_number_reported'] = '1'
        self.assertTrue(any('unknown type may not carry' in error for error in self.errors()))

    def test_year_without_number_is_rejected(self):
        instrument = self.data.instruments[0]
        instrument['instrument_number_reported'] = None
        instrument['instrument_year_reported'] = '2020'
        self.assertTrue(any('year needs an instrument number' in error for error in self.errors()))

    def test_publication_date_cannot_be_invented(self):
        instrument = self.data.instruments[0]
        instrument['publication_date_reported'] = '2020-01-01'
        candidate = next(item for item in self.data.candidate_inventory['records']
                         if item['id'] == instrument['candidate_id'])
        if candidate.get('published_date_reported') != '2020-01-01':
            self.assertTrue(any('publication_date_reported must match' in error
                                for error in self.errors()))

    def test_captured_item_is_rejected(self):
        self.data.instruments[0]['captured_item'] = {'url': 'https://example.gov/a.pdf'}
        self.assertTrue(any('captured item may not be recorded' in error for error in self.errors()))

    def test_review_state_may_not_be_promoted(self):
        self.data.instruments[0]['review_state'] = 'reviewed'
        self.assertTrue(any('review_state must remain reported' in error for error in self.errors()))

    def test_invalid_date_is_rejected(self):
        self.data.instruments[0]['dates']['commencement'] = 'January 2020'
        self.assertTrue(any('dates.commencement must be an ISO date' in error
                            for error in self.errors()))

    def test_instrument_appears_in_view(self):
        view = build_view(self.data)
        candidate = view['candidates'][0]
        self.assertIsNotNone(candidate['instrument'])
        self.assertEqual(view['totals']['instruments'], 23)


if __name__ == '__main__':
    unittest.main()
