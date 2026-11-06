#!/usr/bin/env python3
"""Summarize candidate task queues offline; structural checks only, no legal review."""
import json,re,sys
from collections import Counter
from pathlib import Path

REQUIRED_KEYS=('task_id','jurisdiction','domain','question','stage','status')
OPTIONAL_KEYS=('priority','deliverable')

def normalize(task_id):
 return re.sub(r'[^A-Z0-9]+','-',str(task_id).upper()).strip('-')

def load_rows(path):
 return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]

def summarize(rows):
 counts=Counter(normalize(row.get('task_id','')) for row in rows)
 return {
  'tasks':len(rows),
  'duplicates':sorted(task_id for task_id,count in counts.items() if count>1),
  'missing_required':sum(1 for row in rows if any(row.get(key) in (None,'') for key in REQUIRED_KEYS)),
  'missing_optional':sum(1 for row in rows if any(row.get(key) in (None,'') for key in OPTIONAL_KEYS)),
  'domains':dict(sorted(Counter(row.get('domain','') for row in rows).items())),
  'statuses':dict(sorted(Counter(row.get('status','') for row in rows).items())),
  'jurisdictions':len({row.get('jurisdiction') for row in rows if row.get('jurisdiction')}),
 }

def print_summary(label,summary):
 print(f'== {label}')
 print('Tasks:',summary['tasks'])
 print('Domains:',summary['domains'])
 print('Statuses:',summary['statuses'])
 print('Jurisdictions:',summary['jurisdictions'])
 print('Missing required fields:',summary['missing_required'])
 print('Missing priority/deliverable:',summary['missing_optional'])
 if summary['duplicates']:
  print('Duplicate logical task IDs:',', '.join(summary['duplicates']))

def main(paths):
 failed=False;all_rows=[]
 for path in paths:
  rows=load_rows(path);all_rows.extend(rows)
  summary=summarize(rows);print_summary(path,summary)
  failed=failed or bool(summary['duplicates'])
 if len(paths)>1:
  combined=summarize(all_rows);print_summary('combined',combined)
  failed=failed or bool(combined['duplicates'])
 return 1 if failed else 0

if __name__=='__main__':
 if len(sys.argv)<2:raise SystemExit('usage: report_queue.py backlog/tasks.jsonl [more.jsonl ...]')
 raise SystemExit(main(sys.argv[1:]))
