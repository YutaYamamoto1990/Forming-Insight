import json
from pathlib import Path
import struct
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distribution/press-analysis-agent/scripts'))
import run_pipeline as pipeline


class PipelineTests(unittest.TestCase):
    def test_missing_output_and_timeout_preserve_separate_post_status(self):
        for timeout in (False, True):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                run = root / 'workspace/runs/test/run'
                for name in ('exchange', 'raw/solver', 'post'):
                    (run / name).mkdir(parents=True)
                source = root / 'test.cfile'
                source.write_text('openc d3plot "old"\nprint png "a.png" opaque enlisted "OGL1x1"')
                (run / 'raw/solver/d3plot').write_bytes(b'raw')
                (run / 'exchange/run.json').write_text(json.dumps({'status':'succeeded','process_id':'test'}))
                (run / 'exchange/raw-hashes.json').write_text(json.dumps(pipeline.raw_hashes(run)))
                with patch.object(pipeline, 'settings', return_value=({'expected_images':['a.png']}, root/'test.exe', source, 1)), patch.object(pipeline.subprocess, 'Popen') as launch:
                    launch.return_value.pid = 123
                    launch.return_value.wait.return_value = 0
                    if timeout:
                        launch.return_value.wait.side_effect = subprocess.TimeoutExpired('test', 1)
                    with self.assertRaises((TimeoutError, FileNotFoundError)):
                        pipeline.postprocess(root, run, {})
                    launch.return_value.kill.assert_not_called()
                state = json.loads((run / 'exchange/run.json').read_text())
                self.assertEqual('succeeded', state['status'])
                self.assertEqual('unknown' if timeout else 'error', state['post_status'])
                self.assertEqual(timeout, (root / 'workspace/.post.lock').exists())

    def test_rewrite_keeps_display_commands_and_redirects_paths(self):
        source = 'openc d3plot "E:/old/d3plot"\nisometric z\nac\nprint png "E:/old/a.png" opaque enlisted "OGL1x1"'
        result = pipeline.rewrite_cfile(source, Path('new/d3plot'), Path('new/post'), ['a.png'])
        self.assertNotIn('E:/old', result)
        self.assertIn('isometric z\nac', result)
        self.assertTrue(result.endswith('exit\n'))
        for bad in [source.replace('a.png', 'b.png'), source + '\nopenc d3plot "other"']:
            with self.assertRaises(ValueError):
                pipeline.rewrite_cfile(bad, Path('new/d3plot'), Path('new/post'), ['a.png'])

    def test_registered_commands_and_plot_window_are_preserved(self):
        root = Path(__file__).resolve().parents[1] / 'distribution/press-analysis-agent'
        process = json.loads((root / 'processes/press-z/process.json').read_text())
        post = process['postprocess']
        source = (root / post['cfile']).read_text()
        result = pipeline.rewrite_cfile(source, Path('new/d3plot'), Path('new/post'), post['expected_images'])
        self.assertNotIn('E:\\Develop', result)
        for line in source.splitlines():
            if not line.strip().lower().startswith(('openc d3plot', 'print png')):
                self.assertIn(line, result)
        self.assertIn('"PlotWindow-1"', result)
        for name in post['expected_images']:
            self.assertIn(str(Path('new/post') / name), result)
        for bad in (source.replace('openc d3plot "', 'openc d3plot '), source.replace('print png "', 'print png ')):
            with self.assertRaisesRegex(ValueError, 'Cannot redirect'):
                pipeline.rewrite_cfile(bad, Path('new/d3plot'), Path('new/post'), post['expected_images'])

    def test_truncated_image_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'a.png'
            def chunk(kind, data):
                return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
            content = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0\0\0\0')) + chunk(b'IEND', b'')
            path.write_bytes(content)
            self.assertEqual((1, 1), pipeline.validate_png(path))
            path.write_bytes(content[:-3])
            with self.assertRaises(ValueError): pipeline.validate_png(path)

    def test_changed_raw_prevents_external_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = root / 'workspace/runs/test/run'
            (run / 'exchange').mkdir(parents=True)
            (run / 'raw/solver').mkdir(parents=True)
            (run / 'raw/solver/d3plot').write_bytes(b'changed')
            (run / 'exchange/run.json').write_text(json.dumps({'status':'succeeded', 'process_id':'test'}))
            (run / 'exchange/raw-hashes.json').write_text(json.dumps({'solver/d3plot':'original'}))
            with patch.object(pipeline, 'settings', return_value=({'expected_images':['a.png']}, root/'test.exe', root/'test.cfile', 600)), patch.object(pipeline.subprocess, 'Popen') as launch:
                with self.assertRaisesRegex(ValueError, 'Raw hash mismatch'):
                    pipeline.postprocess(root, run, {})
                launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
