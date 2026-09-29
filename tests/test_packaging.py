"""Build only in a disposable checkout; never publish or replace release artifacts."""

from email.parser import Parser
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_wheel_and_sdist(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source'
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(
                '.git', '.DS_Store', '__pycache__', '*.egg-info', 'dist', 'build', 'logs', 'log.txt', 'app_state.json'))
            output = root / 'artifacts'
            output.mkdir()
            code = ('from setuptools.build_meta import build_wheel, build_sdist; '
                    f'build_wheel({str(output)!r}); build_sdist({str(output)!r})')
            result = subprocess.run([sys.executable, '-c', code], cwd=source,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(next(output.glob('*.whl'))) as wheel:
                names = wheel.namelist()
                self.assertTrue(all(name.startswith('jubilee/') or '.dist-info/' in name for name in names), names)
                metadata = Parser().parsestr(wheel.read(next(name for name in names if name.endswith('/METADATA'))).decode())
                self.assertEqual(metadata['Requires-Python'], '>=3.10')
                self.assertEqual(metadata['License-Expression'], 'GPL-3.0-or-later')
                # Configuration lives in each project's config.toml; the package ships none.
                self.assertFalse(any(name.endswith('.toml') for name in names if name.startswith('jubilee/')))
                package = root / 'installed'
                wheel.extractall(package)
                env = dict(os.environ, PYTHONPATH=str(package), SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
                probe = subprocess.run([sys.executable, '-c', 'from jubilee import App, Worker, Color, Misc; assert Misc.get_color(Color.RED) == (255, 0, 0)'],
                                       cwd=root, env=env, capture_output=True, text=True, timeout=10)
                self.assertEqual(probe.returncode, 0, probe.stdout + probe.stderr)
            with tarfile.open(next(output.glob('*.tar.gz'))) as archive:
                names = [name.split('/', 1)[-1] for name in archive.getnames()]
                for required in ('Jubilee Reference.md', 'tests/test_regressions.py', 'tests/runtime_probe.py',
                                 'examples/Hello/hello.py', 'examples/Sound/music/Funshine.mp3',
                                 'examples/CREDITS.md'):
                    self.assertIn(required, names)
                self.assertFalse(any('.git/' in name or name.endswith('log.txt') for name in names))
