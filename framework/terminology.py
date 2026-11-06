#!/usr/bin/env python3
"""Validate the multilingual terminology registry.

The registry records candidate terminology, not legal definitions. A concept
may be promoted to ``reviewed`` only with recorded review history; the
validator never invents a review or a translation.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

DEFAULT_BASE = Path(__file__).resolve().parents[1] / 'regions' / 'mena'
TERMINOLOGY_FILENAME = 'terminology.json'
ID_PATTERN = re.compile(r'^[a-z0-9_-]+$')
LANGUAGE_PATTERN = re.compile(r'^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$')
ISO_DATE = re.compile(r'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')
REVIEW_STATES = ('draft', 'in_review', 'reviewed')
HISTORY_OUTCOMES = ('approved', 'changes_requested', 'rejected')


def _iso_date(value):
    if not isinstance(value, str) or not ISO_DATE.match(value):
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        return None
    return value


def load_terminology(base=DEFAULT_BASE):
    path = Path(base) / 'data' / TERMINOLOGY_FILENAME
    return json.loads(path.read_text(encoding='utf-8'))


def validate_terminology(base=DEFAULT_BASE) -> list[str]:
    base = Path(base)
    errors: list[str] = []
    path = base / 'data' / TERMINOLOGY_FILENAME
    if not path.is_file():
        return [f'terminology: missing {TERMINOLOGY_FILENAME}']
    try:
        document = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        return [f'terminology: {TERMINOLOGY_FILENAME} is not valid JSON: {exc}']
    countries = {country.get('code') for country in
                 json.loads((base / 'data' / 'countries.json').read_text(encoding='utf-8'))}
    for key in ('version', 'scope', 'translation_status'):
        if not isinstance(document.get(key), str) or not document[key].strip():
            errors.append(f'terminology: {key} must be a nonempty string')
    concepts = document.get('concepts')
    if not isinstance(concepts, list) or not concepts:
        errors.append('terminology: concepts must be a nonempty array')
        return errors

    seen = set()
    for concept in concepts:
        if not isinstance(concept, dict):
            errors.append('terminology: each concept must be an object')
            continue
        concept_id = concept.get('id')
        label = concept_id or 'unknown'
        if not isinstance(concept_id, str) or not ID_PATTERN.match(concept_id):
            errors.append(f'terminology {label}: id must be a stable lowercase slug')
        elif concept_id in seen:
            errors.append(f'terminology {label}: duplicate concept id')
        else:
            seen.add(concept_id)
        labels = concept.get('labels')
        if not isinstance(labels, dict):
            errors.append(f'terminology {label}: labels must be an object')
        else:
            for language in ('en', 'fr', 'ar'):
                value = labels.get(language)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f'terminology {label}: labels.{language} must be nonempty')
                elif '<' in value:
                    errors.append(f'terminology {label}: labels.{language} contains HTML')
        for field in ('definition', 'context'):
            value = concept.get(field)
            if not isinstance(value, dict):
                errors.append(f'terminology {label}: {field} must be an object')
                continue
            if not isinstance(value.get('language'), str) or \
                    not LANGUAGE_PATTERN.match(value['language']):
                errors.append(f'terminology {label}: {field}.language must be a BCP47 tag')
            if not isinstance(value.get('text'), str) or not value['text'].strip():
                errors.append(f'terminology {label}: {field}.text must be nonempty')
        jurisdictions = concept.get('jurisdictions')
        if not isinstance(jurisdictions, list):
            errors.append(f'terminology {label}: jurisdictions must be an array')
        else:
            for code in jurisdictions:
                if code not in countries:
                    errors.append(f'terminology {label}: unknown jurisdiction {code!r}')
        if not isinstance(concept.get('provenance'), str) or not concept['provenance'].strip():
            errors.append(f'terminology {label}: provenance must be nonempty')
        review_state = concept.get('review_state')
        if review_state not in REVIEW_STATES:
            errors.append(f'terminology {label}: unknown review_state {review_state!r}')
        notes = concept.get('notes')
        if not isinstance(notes, list):
            errors.append(f'terminology {label}: notes must be an array')
        else:
            for note in notes:
                if not isinstance(note, str) or not note.strip():
                    errors.append(f'terminology {label}: notes must be nonempty strings')
        history = concept.get('review_history')
        if not isinstance(history, list):
            errors.append(f'terminology {label}: review_history must be an array')
            continue
        approved = False
        for entry in history:
            if not isinstance(entry, dict):
                errors.append(f'terminology {label}: review entries must be objects')
                continue
            if _iso_date(entry.get('reviewed_at')) is None:
                errors.append(f'terminology {label}: review needs a valid ISO reviewed_at')
            if not isinstance(entry.get('reviewer_role'), str) or \
                    not entry['reviewer_role'].strip():
                errors.append(f'terminology {label}: review needs a reviewer_role')
            outcome = entry.get('outcome')
            if outcome not in HISTORY_OUTCOMES:
                errors.append(f'terminology {label}: unknown review outcome {outcome!r}')
            if outcome == 'approved':
                approved = True
        if review_state == 'reviewed' and not approved:
            errors.append(f'terminology {label}: reviewed status needs an approved review entry')
    return errors
