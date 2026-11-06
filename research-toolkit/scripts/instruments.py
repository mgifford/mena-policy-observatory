#!/usr/bin/env python3
"""Derive legal-instrument identity and version metadata from reported titles.

Instrument identity is reported, not verified: the type, number and year are
parsed from the candidate's reported title. Dates other than the already
reported publication date stay null unless a human records them. No captured
item is created.

Usage:

    python3 research-toolkit/scripts/instruments.py
    python3 research-toolkit/scripts/instruments.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = REPO_ROOT / 'research-toolkit' / 'sources' / 'candidate-sources.json'
DEFAULT_INSTRUMENTS = REPO_ROOT / 'research-toolkit' / 'sources' / 'instruments.json'

DATE_KEYS = ('adoption', 'commencement', 'expiry', 'repeal', 'consolidation')
TYPE_MAP = {
    'law': 'law',
    'act': 'act',
    'decree-law': 'decree_law',
    'decree law': 'decree_law',
    'decision': 'decision',
    'regulation': 'regulation',
    'ordinance': 'ordinance',
}
INSTRUMENT_PATTERN = re.compile(
    r'\b(Decree-?Law|Law|Act|Decision|Regulation|Ordinance)\s+'
    r'(?:No\.?\s*)?([0-9][0-9A-Za-z./-]*)',
    re.IGNORECASE,
)
YEAR_PATTERN = re.compile(r'\b((?:19|20)[0-9]{2})\b')


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def parse_instrument(title) -> tuple[str, str | None, str | None]:
    """Return (type, number, year) parsed from a reported title, or unknowns."""
    if not isinstance(title, str):
        return 'unknown', None, None
    match = INSTRUMENT_PATTERN.search(title)
    if not match:
        return 'unknown', None, None
    raw_type = re.sub(r'\s+', ' ', match.group(1).lower())
    instrument_type = TYPE_MAP.get(raw_type, 'unknown')
    number = match.group(2).strip(' .,;:')
    if not number:
        return instrument_type, None, None
    year_match = YEAR_PATTERN.search(title)
    year = year_match.group(1) if year_match else None
    return instrument_type, number, year


def _uncertainties(instrument_type, number, year) -> list[str]:
    notes = []
    if number:
        notes.append('Instrument type and number are parsed from the reported '
                     'title; they are not verified against the instrument.')
    else:
        notes.append('No instrument number could be parsed from the reported '
                     'title; the instrument identity remains unknown.')
    if year:
        notes.append('The reported year is parsed from the title and is not an '
                     'effective, commencement or repeal date.')
    notes.append('No captured version is recorded. Version dates are recorded '
                 'only where documented.')
    return notes


def derive(sources_doc, previous_doc=None):
    previous = {item.get('candidate_id'): item
                for item in (previous_doc or {}).get('instruments', [])}
    instruments = []
    for candidate in sorted(sources_doc.get('records', []),
                            key=lambda item: str(item.get('id'))):
        candidate_id = candidate.get('id')
        stored = previous.get(candidate_id, {})
        instrument_type, number, year = parse_instrument(candidate.get('instrument_title'))
        published = candidate.get('published_date_reported')
        publication = published if isinstance(published, str) and re.fullmatch(
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}', published) else None
        stored_dates = stored.get('dates') if isinstance(stored.get('dates'), dict) else {}
        stored_expression = (stored.get('expression')
                             if isinstance(stored.get('expression'), dict) else {})
        instruments.append({
            'work_id': candidate_id,
            'candidate_id': candidate_id,
            'jurisdiction': candidate.get('jurisdiction'),
            'title_reported': candidate.get('instrument_title'),
            'instrument_type_reported': instrument_type,
            'instrument_number_reported': number,
            'instrument_year_reported': year,
            'issuing_authority': stored.get('issuing_authority'),
            'publication_date_reported': publication,
            'dates': {key: stored_dates.get(key) for key in DATE_KEYS},
            'expression': {
                'language': stored_expression.get('language'),
                'label': stored_expression.get('label', 'Reported title only'),
            },
            'captured_item': None,
            'review_state': stored.get('review_state', 'reported'),
            'uncertainties': _uncertainties(instrument_type, number, year),
        })
    return {
        'version': '1',
        'note': ('Instrument identity is parsed from reported titles. It is not '
                 'verified against the instrument, and a null date means the date '
                 'is unknown, not that no date exists.'),
        'instruments': instruments,
    }


def run(sources_path=DEFAULT_SOURCES, instruments_path=DEFAULT_INSTRUMENTS,
        check=False) -> int:
    sources_doc = read_json(sources_path)
    instruments_path = Path(instruments_path)
    previous = read_json(instruments_path) if instruments_path.is_file() else None
    desired = derive(sources_doc, previous)
    text = dump_json(desired)
    if check:
        if not instruments_path.is_file() or \
                instruments_path.read_text(encoding='utf-8') != text:
            print(f'STALE: {instruments_path}', file=sys.stderr)
            return 1
        print(f'{len(desired["instruments"])} instruments recorded; identity current')
        return 0
    instruments_path.write_text(text, encoding='utf-8')
    print(f'{len(desired["instruments"])} instruments recorded')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=DEFAULT_SOURCES)
    parser.add_argument('--instruments', type=Path, default=DEFAULT_INSTRUMENTS)
    parser.add_argument('--check', action='store_true',
                        help='fail if the file differs from a fresh derivation')
    args = parser.parse_args()
    return run(args.sources, args.instruments, args.check)


if __name__ == '__main__':
    raise SystemExit(main())
