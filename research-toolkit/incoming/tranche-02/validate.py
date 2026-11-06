#!/usr/bin/env python3
"""Validate tranche-02 candidate inventory; does not establish legal accuracy."""
import json, pathlib, sys
root=pathlib.Path(__file__).resolve().parent
obj=json.loads((root/'candidate-sources.json').read_text())
records=obj['records']
ids=[r['candidate_id'] for r in records]
assert len(ids)==len(set(ids)), 'Duplicate IDs'
assert obj['metadata']['total']==len(records)
assert all(r['source_url'].startswith('https://') for r in records)
assert all(r['source_status'].endswith('_identified') for r in records)
assert all(r['legal_effect']=='not_assessed' and r['review_status']=='unreviewed' and r['publication_status']=='candidate_only' and not r['original_text_verified'] for r in records)
assert all(not r['source_capture']['bytes_stored'] and r['source_capture']['sha256'] is None for r in records)
tasks=[json.loads(x) for x in (root/'tasks.jsonl').read_text().splitlines() if x.strip()]
assert len(tasks)==len(records) and {x['candidate_source_id'] for x in tasks}==set(ids)
print(f"PASS: {len(records)} candidate leads, {len(set(r['jurisdiction'] for r in records))} jurisdictions, {len(tasks)} tasks; all unreviewed")
