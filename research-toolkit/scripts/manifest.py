#!/usr/bin/env python3
"""Deterministically hash local artifacts; excludes manifest output and caches."""
import argparse,hashlib,json
from pathlib import Path

def build(root,output):
 records=[];out=output.resolve()
 for p in sorted(root.rglob('*')):
  if not p.is_file() or p.resolve()==out or any(s in {'.git','__pycache__','.pytest_cache','node_modules'} for s in p.parts):continue
  if p.suffix=='.pyc':continue
  b=p.read_bytes();records.append({'path':p.relative_to(root).as_posix(),'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 return {'version':'1','root':'.','files':records,'note':'Hash inventory only, not proof of authenticity or legal correctness'}
def main():
 a=argparse.ArgumentParser();a.add_argument('root');a.add_argument('--output',required=True);args=a.parse_args()
 root=Path(args.root).resolve();out=Path(args.output)
 data=build(root,out)
 out.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8');print(f'{len(data["files"])} files hashed')
if __name__=='__main__':main()
