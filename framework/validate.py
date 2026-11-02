#!/usr/bin/env python3
"""Validate the structure of regional policy records.

This checks presence and basic consistency only. It does not verify legal
status, source accuracy, translations, or RuleSpec behaviour.
"""
from pathlib import Path
import json
import sys

REGIONS = ('mena',)
REQUIRED_FILES = ('SOURCE.md', 'INTERPRETATION.md', 'RELATED.md', 'rule.rulespec.yaml')
ALLOWED_EXECUTION_STATUS = ('not_implemented', 'scaffold', 'not_encoded', None)


def validate_region(root: Path, region: str) -> list[str]:
    """Return a list of structural errors for one region."""
    base = root / 'regions' / region
    config = json.loads((base / 'region.json').read_text(encoding='utf-8'))
    records = json.loads((base / 'data' / 'policies.json').read_text(encoding='utf-8'))

    errors: list[str] = []
    ids: set[str | None] = set()
    for record in records:
        record_id = record.get('id')
        policy_dir = base / 'policies' / str(record_id)

        if not record_id or record_id in ids:
            errors.append(f'{region}: missing or duplicate id: {record_id}')
        ids.add(record_id)

        if not str(record.get('source_url', '')).startswith('https://'):
            errors.append(f'{record_id}: missing secure official source URL')

        for filename in REQUIRED_FILES:
            if not (policy_dir / filename).is_file():
                errors.append(f'{record_id}: missing {filename}')

        if record.get('execution_status') not in ALLOWED_EXECUTION_STATUS:
            errors.append(f'{record_id}: unexpected execution status; verify separately')

    print(region, len(records), 'records; language variants', ','.join(config['languages']))
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    for region in REGIONS:
        errors.extend(validate_region(root, region))

    if errors:
        print('\n'.join(errors), file=sys.stderr)
        return 1

    print('Structure validation passed; no legal or RuleSpec verification implied.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
