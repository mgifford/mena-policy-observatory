#!/usr/bin/env python3
"""Summarize candidate task queue, no network or AI calls."""
import json,sys
from collections import Counter
from pathlib import Path
if len(sys.argv)!=2:raise SystemExit('usage: report_queue.py backlog/tasks.jsonl')
rows=[json.loads(l) for l in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines() if l.strip()]
ids=[r['task_id'] for r in rows]
if len(ids)!=len(set(ids)):raise SystemExit('ERROR: duplicate task IDs')
print('Tasks:',len(rows));print('Domains:',dict(Counter(r['domain'] for r in rows)))
print('Statuses:',dict(Counter(r['status'] for r in rows)))
print('Jurisdictions:',len(set(r['jurisdiction'] for r in rows)))
