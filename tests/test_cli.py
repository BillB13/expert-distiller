import unittest
import sys
import json
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import main as cli_main


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.temp_files = []

    def tearDown(self):
        for f in self.temp_files:
            if os.path.exists(f):
                os.unlink(f)

    def _run_cli(self, args):
        """Helper to run CLI with args"""
        import io
        from contextlib import redirect_stdout, redirect_stderr

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                cli_main(args)
        except SystemExit as e:
            pass

        return stdout_capture.getvalue(), stderr_capture.getvalue()

    def test_init_command(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        self.temp_files.append(temp_path)

        stdout, stderr = self._run_cli([
            'init',
            '--domain', '消费行业投资',
            '--expert', 'VC合伙人',
            '--target', '50',
            '--keywords', '品牌,渠道',
            '--output', temp_path
        ])

        self.assertTrue(os.path.exists(temp_path))
        with open(temp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data["meta"]["domain"], "消费行业投资")
        self.assertEqual(data["meta"]["target_count"], 50)

    def test_status_command(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        self.temp_files.append(temp_path)

        self._run_cli([
            'init', '--domain', '测试领域', '--expert', '测试专家',
            '--target', '10', '--output', temp_path
        ])

        stdout, stderr = self._run_cli(['status', '--state', temp_path])
        self.assertIn("测试领域", stdout)
        self.assertIn("0/10", stdout)

    def test_update_command(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        self.temp_files.append(temp_path)

        self._run_cli([
            'init', '--domain', '测试领域', '--expert', '测试专家',
            '--target', '10', '--output', temp_path
        ])

        stdout, stderr = self._run_cli([
            'update', '--state', temp_path,
            '--q-id', '1',
            '--question', '测试问题',
            '--answer', '测试回答',
            '--analysis', '{"dimension": "core_principles", "needs_follow_up": false, "quality": "high"}'
        ])

        with open(temp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data["progress"]["completed_count"], 1)
        self.assertEqual(len(data["qa_pairs"]), 1)

    def test_export_command(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            state_path = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            export_path = f.name
        self.temp_files.extend([state_path, export_path])

        self._run_cli([
            'init', '--domain', '测试领域', '--expert', '测试专家',
            '--target', '10', '--output', state_path
        ])
        self._run_cli([
            'update', '--state', state_path,
            '--q-id', '1', '--question', 'Q1', '--answer', 'A1',
            '--analysis', '{"dimension": "core_principles", "needs_follow_up": false}'
        ])

        self._run_cli([
            'export', '--state', state_path,
            '--format', 'jsonl', '--output', export_path
        ])

        with open(export_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        obj = json.loads(lines[0])
        self.assertEqual(obj["q_id"], 1)


if __name__ == '__main__':
    unittest.main()
