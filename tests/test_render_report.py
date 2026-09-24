import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'distribution/press-analysis-agent'
spec = importlib.util.spec_from_file_location('render_report', ROOT / 'scripts/render_report.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.previous = report.ROOT
        self.addCleanup(setattr, report, 'ROOT', self.previous)
        report.ROOT = Path(self.temp.name)
        assets = report.ROOT / 'assets/report'
        assets.mkdir(parents=True)
        (assets / 'template.html').write_bytes((ROOT / 'assets/report/template.html').read_bytes())
        self.run = report.ROOT / 'workspace/runs/process/run'
        (self.run / 'exchange').mkdir(parents=True)
        (self.run / 'exchange/run.json').write_text(json.dumps({'run_id':'run', 'status':'unknown', 'solver_success_verified':False}))
        self.data = json.loads((ROOT / 'assets/report/report-data.example.json').read_text(encoding='utf-8'))
        self.data['run_id'] = 'run'

    def test_escape_and_preserve_existing_report(self):
        self.data['title'] = '<script>alert(1)</script>'
        result = report.render(self.run, self.data, 'one')
        rendered = result.read_text(encoding='utf-8')
        self.assertIn('&lt;script&gt;', rendered)
        self.assertNotIn('<script>', rendered)
        self.assertIn('状態未確定', rendered)
        before = result.read_bytes()
        with self.assertRaises(FileExistsError):
            report.render(self.run, self.data, 'one')
        self.assertEqual(before, result.read_bytes())

    def test_reject_wrong_run_and_missing_evidence(self):
        bad = copy.deepcopy(self.data)
        bad['run_id'] = 'another-run'
        with self.assertRaises(ValueError): report.render(self.run, bad, 'wrong')
        bad = copy.deepcopy(self.data)
        bad['conclusion'][0]['evidence'] = ['E999']
        with self.assertRaises(ValueError): report.render(self.run, bad, 'missing')
        self.assertFalse((self.run / 'report').exists())

    def test_reject_read_and_write_outside_run(self):
        self.data['evidence'][0]['path'] = '../../../outside.txt'
        with self.assertRaises(ValueError): report.render(self.run, self.data, 'outside')
        with self.assertRaises(ValueError): report.render(self.run, self.data, '../overwrite')

    def test_missing_image_creates_no_report(self):
        self.data['figures'] = [{'path':'post/missing.png'}]
        with self.assertRaises(FileNotFoundError): report.render(self.run, self.data, 'missing-image')
        self.assertFalse((self.run / 'report').exists())


if __name__ == '__main__':
    unittest.main()
