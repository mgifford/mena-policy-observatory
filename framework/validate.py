#!/usr/bin/env python3
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1]
errors=[]
for region in ('mena',):
 base=root/'regions'/region
 config=json.loads((base/'region.json').read_text())
 records=json.loads((base/'data/policies.json').read_text())
 ids=set()
 for r in records:
  id=r.get('id');p=base/'policies'/str(id)
  if not id or id in ids:errors.append(f'{region}: missing or duplicate id: {id}')
  ids.add(id)
  if not r.get('source_url','').startswith('https://'):errors.append(f'{id}: missing secure official source URL')
  for file in ('SOURCE.md','INTERPRETATION.md','RELATED.md','rule.rulespec.yaml'):
   if not (p/file).is_file():errors.append(f'{id}: missing {file}')
  if r.get('execution_status') not in ('not_implemented','scaffold','not_encoded',None):errors.append(f'{id}: unexpected execution status; verify separately')
 print(region,len(records),'records; language variants',','.join(config['languages']))
if errors:print('\n'.join(errors),file=sys.stderr);sys.exit(1)
print('Structure validation passed; no legal or RuleSpec verification implied.')
