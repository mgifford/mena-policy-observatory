import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_packets import validate

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
 def test_queue_unique(self):
  ts=[json.loads(x) for x in (ROOT/'backlog/tasks.jsonl').read_text(encoding='utf-8').splitlines()]
  self.assertEqual(len(ts),24)
  self.assertEqual(len({x['task_id'] for x in ts}),24)
if __name__=='__main__':unittest.main()
