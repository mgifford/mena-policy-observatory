#!/usr/bin/env python3
"""Offline validator for *candidate-only* packet interchange; no legal endorsement.

Requires stdlib only. Does not replace repository's full schema/semantic validator.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED = {"schema_version", "task_id", "jurisdiction", "domain", "question", "stage", "source", "evidence", "interpretation", "review", "rules_as_code"}
SOURCE = {"official_url", "document_id", "provision_locator", "source_language", "captured_at", "sha256", "capture_path", "source_type"}
def validate(o):
    errors=[]
    if not isinstance(o,dict): return ['root must be an object']
    for x in sorted(REQUIRED-set(o)):errors.append(f'missing {x}')
    for x in sorted(set(o)-REQUIRED):errors.append(f'unknown field {x}')
    if o.get('schema_version')!='1.0':errors.append('schema_version must be 1.0')
    if not isinstance(o.get('task_id'),str) or len(o['task_id'])<4:errors.append('task_id must be nonempty')
    if not re.fullmatch(r'[A-Z]{2}',str(o.get('jurisdiction',''))):errors.append('jurisdiction must be two uppercase letters')
    domain=o.get('domain')
    if not isinstance(domain,str) or len(domain)<3:errors.append('domain must be a string of at least 3 characters')
    if not isinstance(o.get('question'),str) or len(o['question'])<12:errors.append('question too short')
    if o.get('stage') not in ('candidate','captured','transcribed','interpreted','challenged'):errors.append('invalid stage')
    s=o.get('source')
    if not isinstance(s,dict): errors.append('source must be object');s={}
    for x in sorted(SOURCE-set(s)):errors.append('source missing '+x)
    for x in sorted(set(s)-SOURCE):errors.append('source unknown '+x)
    url=s.get('official_url')
    if url is not None and (not isinstance(url,str) or urlparse(url).scheme!='https' or not urlparse(url).netloc):errors.append('official_url must be https URL or null')
    if s.get('source_type') not in ('unknown','official_instrument','official_index','official_summary','secondary'):errors.append('invalid source_type')
    sha=s.get('sha256'); cap=s.get('capture_path'); timestamp=s.get('captured_at')
    if sha is not None and not re.fullmatch(r'[0-9a-f]{64}',str(sha)):errors.append('sha256 is not 64 lowercase hex digits')
    if bool(sha)!=bool(cap) or bool(sha)!=bool(timestamp):errors.append('captured bytes require sha256, path and timestamp together')
    if cap and (Path(cap).is_absolute() or '..' in Path(cap).parts):errors.append('capture_path must be relative and traversal-free')
    e=o.get('evidence')
    if not isinstance(e,dict): errors.append('evidence must be object');e={}
    if e.get('verified_against_source') is not False:errors.append('candidate packet may not assert verified_against_source')
    if not isinstance(e.get('license_checked'),bool):errors.append('license_checked boolean required')
    if e.get('exact_excerpt') is not None and not isinstance(e.get('exact_excerpt'),str):errors.append('exact_excerpt must be string or null')
    i=o.get('interpretation')
    if not isinstance(i,dict):errors.append('interpretation must be object');i={}
    if i.get('legal_effect')!='not_assessed':errors.append('legal_effect cannot be promoted in candidate packet')
    if i.get('proposed') is not None and not isinstance(i.get('proposed'),str):errors.append('proposed must be string or null')
    for k in ('alternatives','open_questions'):
        if not isinstance(i.get(k),list):errors.append(k+' must be an array')
    r=o.get('review')
    if not isinstance(r,dict):errors.append('review must be object');r={}
    for k in ('source_verified','legal_reviewed','translation_reviewed'):
        if r.get(k) is not False: errors.append(f'{k} cannot be promoted by the candidate agent')
    a=o.get('rules_as_code')
    if not isinstance(a,dict):errors.append('rules_as_code must be object');a={}
    if a.get('engine')!='axiom':errors.append('engine must be axiom')
    if a.get('status') not in ('blocked','not_assessed','candidate_scaffold'):errors.append('candidate cannot claim compiled/reviewed rule')
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('paths',nargs='+');args=p.parse_args();failed=False
    for arg in args.paths:
        path=Path(arg)
        try: obj=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError) as e:print(f'FAIL {path}: {e}');failed=True;continue
        errors=validate(obj)
        if errors:
            failed=True
            for error in errors: print(f'FAIL {path}: {error}')
        else: print(f'PASS {path} candidate structure only; no source or legal review performed')
    return 1 if failed else 0
if __name__=='__main__':sys.exit(main())
