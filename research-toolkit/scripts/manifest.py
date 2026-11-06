#!/usr/bin/env python3
"""Deterministically hash local artifacts; excludes manifest output, caches and OS files."""
import argparse,hashlib,json
from pathlib import Path

EXCLUDED_PARTS={'.git','__pycache__','.pytest_cache','node_modules'}
EXCLUDED_NAMES={'.DS_Store'}

def build(root,output):
 records=[];out=output.resolve()
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.resolve()==out:continue
  if any(s in EXCLUDED_PARTS for s in p.parts) or p.name in EXCLUDED_NAMES:continue
  if p.suffix=='.pyc':continue
  b=p.read_bytes();records.append({'path':p.relative_to(root).as_posix(),'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 return {'version':'1','root':'.','files':records,'note':'Hash inventory only, not proof of authenticity or legal correctness'}

def main():
 a=argparse.ArgumentParser();a.add_argument('root');a.add_argument('--output',required=True);a.add_argument('--check',action='store_true',help='fail if the output is missing or differs from a fresh inventory');args=a.parse_args()
 root=Path(args.root).resolve();out=Path(args.output)
 data=build(root,out);text=json.dumps(data,indent=2)+'\n'
 if args.check:
  try:current=out.read_text(encoding='utf-8')
  except OSError:print(f'MISSING {out}');return 1
  if current!=text:print(f'STALE {out}');return 1
  print(f'{len(data["files"])} files hashed; manifest current');return 0
 out.write_text(text,encoding='utf-8');print(f'{len(data["files"])} files hashed');return 0

if __name__=='__main__':raise SystemExit(main())
