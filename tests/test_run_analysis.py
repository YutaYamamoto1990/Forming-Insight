"""Exercise the runner over real loopback HTTP without Rhino or a solver."""
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import time
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / 'distribution/press-analysis-agent/scripts/run_analysis.py'
spec = importlib.util.spec_from_file_location('run_analysis', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'agent'
        self.root.mkdir()
        self.process_dir = self.root / 'processes' / 'test'
        self.process_dir.mkdir(parents=True)
        (self.root / 'AGENTS.md').write_text('unchanged', encoding='utf-8')
        self.gh = self.process_dir / 'test.gh'
        self.gh.write_bytes(b'fake definition for HTTP contract tests')
        self.source = Path(self.temp.name) / 'input.k'
        self.source.write_text('*KEYWORD\n*END\n', encoding='utf-8')
        self.behavior = 'success'
        self.requests = []
        case = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                value = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                case.requests.append(self.path)
                if self.path == '/io':
                    if case.behavior == 'definition_change':
                        (case.root / 'AGENTS.md').write_text('changed', encoding='utf-8')
                    body = {'InputNames': ['Get File Path'], 'Errors': []}
                    if case.behavior == 'two_inputs':
                        body['InputNames'] = ['Output Directory', 'Get File Path']
                else:
                    if case.behavior == 'timeout':
                        time.sleep(0.35)
                    if case.behavior == 'http_error':
                        self.send_response(500)
                        self.end_headers()
                        self.wfile.write(b'{"errors":["server failed"]}')
                        return
                    item = value['values'][0]['InnerTree']['{0}'][0]
                    copied_input = Path(json.loads(item['data']))
                    output = copied_input.parent
                    if case.behavior == 'two_inputs':
                        item = value['values'][1]['InnerTree']['{0}'][0]
                        output = Path(json.loads(item['data']))
                        case.output_received = output
                    (output / 'result.bin').write_bytes(b'raw result')
                    self.assert_no_cache = value['cachesolve'] is False
                    body = {'values': [], 'errors': ['opaque GH warning treated per user policy'], 'warnings': []}
                self.send_response(200)
                self.end_headers()
                try:
                    self.wfile.write(json.dumps(body).encode())
                except ConnectionError:
                    pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.config = self.root / 'config.json'
        runner.write_json(self.config, {
            'compute_url': f'http://127.0.0.1:{self.server.server_port}',
            'timeout_seconds': 2,
            'processes': {},
        })
        runner.write_json(self.process_dir / 'process.json', {
            'gh_definition': str(self.gh), 'input_parameter': 'Get File Path',
        })

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def run_case(self, prepare=False):
        return runner.execute(self.root, 'test', self.source, self.config, prepare)

    def test_response_is_success_without_claiming_solver_verification(self):
        before = runner.digest(self.source)
        run, manifest = self.run_case()
        self.assertEqual(manifest['status'], 'succeeded')
        self.assertEqual(manifest['success_basis'], 'gh_response_received')
        self.assertFalse(manifest['solver_success_verified'])
        self.assertTrue(manifest['gh_errors'])
        self.assertEqual((run / 'raw/solver/result.bin').read_bytes(), b'raw result')
        self.assertEqual(before, runner.digest(self.source))
        self.assertEqual(self.requests, ['/io', '/grasshopper'])
        self.assertFalse((self.root / 'workspace/.analysis.lock').exists())
        second_run, _ = self.run_case()
        self.assertNotEqual(run, second_run)

    def test_prepare_does_not_call_compute(self):
        run, manifest = self.run_case(True)
        self.assertEqual(manifest['status'], 'prepared')
        self.assertEqual(self.requests, [])
        self.assertEqual((run / 'input/input.k').read_bytes(), self.source.read_bytes())

    def test_two_inputs_route_results_and_preserve_include(self):
        self.behavior = 'two_inputs'
        asset = self.root / 'cal_setup.k'
        asset.write_text('*KEYWORD\n*END\n')
        process = runner.read_json(self.process_dir / 'process.json')
        process.update(output_directory_parameter='Output Directory',
                       layout={'input_file':'input_shape/input.k','result_directory':'input_run'},
                       assets=[{'id':'cal_setup','source':str(asset),'destination':'cal_setup.k'}])
        runner.write_json(self.process_dir / 'process.json', process)
        run, manifest = self.run_case()
        self.assertEqual('succeeded', manifest['status'])
        self.assertEqual(run/'work/solver/input_run', self.output_received)
        self.assertEqual(b'raw result', (run/'raw/solver/result.bin').read_bytes())
        self.assertEqual(asset.read_bytes(), (run/'raw/cal_setup.k').read_bytes())

    def test_process_layout_assets_timeout_and_execution_gate(self):
        asset = self.root / 'cal_setup.k'
        asset.write_text('*KEYWORD\n*END\n')
        process = runner.read_json(self.process_dir / 'process.json')
        process.update(timeout_seconds=1200, requires_run_relative_output=True,
                       layout={'input_file':'input_shape/input.k','result_directory':'input_run'},
                       assets=[{'id':'cal_setup','source':str(asset),'destination':'cal_setup.k'}])
        runner.write_json(self.process_dir / 'process.json', process)
        run, manifest = self.run_case(True)
        self.assertEqual(1200, manifest['timeout_seconds'])
        self.assertEqual(1260, manifest['server_timeout_recommended_seconds'])
        self.assertEqual(asset.read_bytes(), (run/'work/solver/cal_setup.k').read_bytes())
        self.assertEqual(asset.read_bytes(), (run/'input/assets/cal_setup.k').read_bytes())
        self.assertTrue((run/'work/solver/input_run').is_dir())
        self.assertEqual(self.source.read_bytes(), (run/'work/solver/input_shape/input.k').read_bytes())
        _, blocked = self.run_case()
        self.assertEqual('failed_before_solve', blocked['status'])
        self.assertEqual([], self.requests)
        config = runner.read_json(self.config)
        config['processes'] = {'test':{'timeout_seconds':1500}}
        runner.write_json(self.config, config)
        _, override = self.run_case(True)
        self.assertEqual(1500, override['timeout_seconds'])

    def test_http_failure_is_unknown_and_blocks_accidental_retry(self):
        self.behavior = 'http_error'
        run, manifest = self.run_case()
        self.assertEqual(manifest['status'], 'unknown')
        self.assertTrue((run / 'raw/gh-response.json').exists())
        self.assertTrue((self.root / 'workspace/.analysis.lock').exists())
        _, second = self.run_case()
        self.assertEqual(second['status'], 'failed_before_solve')
        self.assertEqual(self.requests, ['/io', '/grasshopper'])

    def test_timeout_preserves_unknown_and_does_not_write_late_response(self):
        self.behavior = 'timeout'
        config = runner.read_json(self.config)
        config['timeout_seconds'] = 0.1
        runner.write_json(self.config, config)
        run, manifest = self.run_case()
        self.assertEqual(manifest['status'], 'unknown')
        time.sleep(0.45)
        self.assertFalse((run / 'raw/gh-response.json').exists())
        self.assertEqual(self.requests, ['/io', '/grasshopper'])

    def test_include_input_rejected_before_run(self):
        self.source.write_text('*KEYWORD\n*INCLUDE\npart.k\n*END\n')
        with self.assertRaisesRegex(ValueError, 'INCLUDE'):
            self.run_case()
        self.assertEqual(self.requests, [])

    def test_definition_change_blocks_completion(self):
        self.behavior = 'definition_change'
        _, manifest = self.run_case()
        self.assertEqual(manifest['status'], 'integrity_error')
        self.assertEqual(manifest['post_status'], 'blocked')
        self.assertEqual(self.requests, ['/io'])

    def test_remote_url_rejected_before_sending_files(self):
        config = runner.read_json(self.config)
        config['compute_url'] = 'http://example.com:6500'
        runner.write_json(self.config, config)
        with self.assertRaisesRegex(ValueError, 'local'):
            self.run_case()
        self.assertEqual(self.requests, [])


if __name__ == '__main__':
    unittest.main()
