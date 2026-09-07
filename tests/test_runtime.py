"""Headless SDL and real spawn tests. No hardware or network commands are run."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RuntimeTests(unittest.TestCase):
    def probe(self, entry=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            if entry:
                shutil.copytree(entry.parent, root, dirs_exist_ok=True,
                                ignore=shutil.ignore_patterns('log*', '__pycache__', 'app_state.json'))
            env = dict(os.environ, PYTHONPATH=str(ROOT), SDL_VIDEODRIVER='dummy',
                       SDL_AUDIODRIVER='dummy', PYTHONDONTWRITEBYTECODE='1')
            args = [sys.executable, str(ROOT / 'tests/runtime_probe.py'), str(root)]
            if entry:
                args.append(str(entry))
            result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('Exception ignored', result.stderr)

    def test_real_spawn_without_modes(self):
        self.probe()

    def test_all_examples(self):
        for entry in sorted((ROOT / 'examples').glob('*/*.py')):
            if entry.stem.endswith('_worker'):
                continue
            with self.subTest(example=entry.parent.name):
                self.probe(entry)
