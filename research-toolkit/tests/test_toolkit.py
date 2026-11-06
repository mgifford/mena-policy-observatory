import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_packets import validate
from manifest import build as build_manifest
from report_queue import normalize as normalize_task_id
from report_queue import summarize as summarize_queue

class TestCandidateSchema(unittest.TestCase):
 def setUp(self):self.obj=json.loads((ROOT/'examples/valid-packet.json').read_text(encoding='utf-8'))
 def test_candidate_passes(self):self.assertEqual(validate(self.obj),[])
 def test_false_approval_rejected(self):
  self.obj['review']['legal_reviewed']=True
  self.assertTrue(any('legal_reviewed' in x for x in validate(self.obj)))
 def test_fabricated_capture_metadata_rejected(self):
  self.obj['source']['sha256']='a'*64
  self.assertTrue(any('require sha256' in x for x in validate(self.obj)))
 def test_unreviewed_rule_cannot_be_certified(self):
  self.obj['rules_as_code']['status']='legally_reviewed'
  self.assertTrue(any('cannot claim compiled' in x for x in validate(self.obj)))
 def test_bad_url(self):
  self.obj['source']['official_url']='http://bad.example'
  self.assertTrue(any('https URL' in x for x in validate(self.obj)))
 def test_empty_domain_rejected(self):
  self.obj['domain']=''
  self.assertTrue(any('domain must be' in x for x in validate(self.obj)))
 def test_unknown_source_type_rejected(self):
  self.obj['source']['source_type']='blog_post'
  self.assertTrue(any('invalid source_type' in x for x in validate(self.obj)))
 def test_non_string_excerpt_rejected(self):
  self.obj['evidence']['exact_excerpt']=['not','text']
  self.assertTrue(any('exact_excerpt' in x for x in validate(self.obj)))
 def test_non_string_proposed_interpretation_rejected(self):
  self.obj['interpretation']['proposed']={'text':'x'}
  self.assertTrue(any('proposed must be' in x for x in validate(self.obj)))

class TestQueues(unittest.TestCase):
 def load(self,name):
  return [json.loads(x) for x in (ROOT/'backlog'/name).read_text(encoding='utf-8').splitlines() if x.strip()]
 def test_primary_queue_unique(self):
  ts=self.load('tasks.jsonl')
  self.assertEqual(len(ts),24)
  self.assertEqual(len({x['task_id'] for x in ts}),24)
 def test_combined_queue_has_no_logical_duplicates(self):
  ts=self.load('tasks.jsonl')+self.load('cross-domain-tasks.jsonl')
  self.assertEqual(len(ts),40)
  normalized={normalize_task_id(x['task_id']) for x in ts}
  self.assertEqual(len(normalized),40)

class TestQueueSummary(unittest.TestCase):
 def test_normalization_ignores_separators(self):
  self.assertEqual(normalize_task_id('BH-DIGITAL_RIGHTS-DISCOVERY-001'),normalize_task_id('BH-DIGITAL-RIGHTS-DISCOVERY-001'))
 def test_duplicates_and_missing_metadata_are_reported(self):
  rows=[
   {'task_id':'AA-X-001','jurisdiction':'AA','domain':'d','question':'q','stage':'source_discovery','status':'unstarted'},
   {'task_id':'AA_X_001','jurisdiction':'AA','domain':'d','question':'q','stage':'source_discovery','status':'unstarted','priority':'high','deliverable':'x'},
  ]
  summary=summarize_queue(rows)
  self.assertEqual(summary['tasks'],2)
  self.assertEqual(summary['duplicates'],['AA-X-001'])
  self.assertEqual(summary['missing_optional'],1)
  self.assertEqual(summary['missing_required'],0)

class TestManifest(unittest.TestCase):
 def test_os_files_excluded(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'.DS_Store').write_bytes(b'junk');(root/'keep.txt').write_text('keep',encoding='utf-8')
   data=build_manifest(root,root/'MANIFEST.json')
   self.assertEqual([entry['path'] for entry in data['files']],['keep.txt'])
 def test_check_detects_stale_and_current(self):
  script=str(ROOT/'scripts'/'manifest.py')
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'a.txt').write_text('one',encoding='utf-8');out=root/'MANIFEST.json'
   write=subprocess.run([sys.executable,script,str(root),'--output',str(out)],capture_output=True,text=True)
   self.assertEqual(write.returncode,0,write.stderr)
   current=subprocess.run([sys.executable,script,str(root),'--output',str(out),'--check'],capture_output=True,text=True)
   self.assertEqual(current.returncode,0,current.stdout+current.stderr)
   (root/'a.txt').write_text('two',encoding='utf-8')
   stale=subprocess.run([sys.executable,script,str(root),'--output',str(out),'--check'],capture_output=True,text=True)
   self.assertEqual(stale.returncode,1)
   self.assertIn('STALE',stale.stdout)

if __name__=='__main__':unittest.main()
