import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.validate import REQUIRED_FILES, validate_region


def valid_record(**overrides):
    record = {
        'id': 'test-record',
        'source_url': 'https://example.test/source',
        'execution_status': 'not_implemented',
    }
    record.update(overrides)
    return record


def write_region(root: Path, records: list[dict], files=REQUIRED_FILES) -> Path:
    base = root / 'regions' / 'mena'
    (base / 'data').mkdir(parents=True)
    (base / 'region.json').write_text(json.dumps({'languages': ['en', 'ar']}), encoding='utf-8')
    (base / 'data' / 'policies.json').write_text(json.dumps(records), encoding='utf-8')
    for record in records:
        policy_dir = base / 'policies' / str(record.get('id'))
        policy_dir.mkdir(parents=True, exist_ok=True)
        for filename in files:
            (policy_dir / filename).write_text('placeholder', encoding='utf-8')
    return base


def run_validation(root: Path) -> tuple[list[str], str]:
    output = io.StringIO()
    with redirect_stdout(output):
        errors = validate_region(root, 'mena')
    return errors, output.getvalue()


class ValidateRegionTests(unittest.TestCase):
    def test_valid_region_has_no_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [valid_record()])
            errors, output = run_validation(Path(tmp))
        self.assertEqual(errors, [])
        self.assertIn('1 records; language variants en,ar', output)

    def test_duplicate_id_is_rejected(self):
        record = valid_record()
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [record, record.copy()])
            errors, _ = run_validation(Path(tmp))
        self.assertTrue(any('missing or duplicate id' in error for error in errors))

    def test_missing_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [valid_record(id=None)])
            errors, _ = run_validation(Path(tmp))
        self.assertTrue(any('missing or duplicate id' in error for error in errors))

    def test_insecure_source_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [valid_record(source_url='http://example.test/source')])
            errors, _ = run_validation(Path(tmp))
        self.assertTrue(any('missing secure official source URL' in error for error in errors))

    def test_missing_required_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [valid_record()], files=('SOURCE.md',))
            errors, _ = run_validation(Path(tmp))
        self.assertTrue(any('missing INTERPRETATION.md' in error for error in errors))
        self.assertTrue(any('missing RELATED.md' in error for error in errors))
        self.assertTrue(any('missing rule.rulespec.yaml' in error for error in errors))

    def test_unexpected_execution_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(Path(tmp), [valid_record(execution_status='approved')])
            errors, _ = run_validation(Path(tmp))
        self.assertTrue(any('unexpected execution status' in error for error in errors))

    def test_multiple_errors_are_reported_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_region(
                Path(tmp),
                [valid_record(source_url='http://example.test/source', execution_status='approved')],
                files=(),
            )
            errors, _ = run_validation(Path(tmp))
        self.assertGreaterEqual(len(errors), 6)

    def test_current_repository_passes(self):
        errors, output = run_validation(REPO_ROOT)
        self.assertEqual(errors, [])
        self.assertIn('records; language variants en,ar', output)


if __name__ == '__main__':
    unittest.main()
