"""Fresh staged-example runtime checks; no prior audit fixtures are used."""

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import importlib.util
import multiprocessing
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame
from jubilee import App, Worker
from jubilee.misc import Config, Log


class CurrentExamples(unittest.TestCase):
    def test_all_example_applications(self):
        root = Path(__file__).resolve().parents[1] / 'examples'
        entries = [('Hello', 'hello', 'HelloApp'),
                   ('Headless', 'headless', 'HeadlessApp'),
                   ('Controls', 'controls', 'ControlsApp'),
                   ('Image_Effects', 'image_effects', 'ImageEffectsApp'),
                   ('Images', 'images', 'ImagesApp'),
                   ('Modes', 'modes', 'ModesApp'),
                   ('Pointer', 'pointer', 'PointerApp'),
                   ('Screen_Rotation', 'screen_rotation', 'ScreenRotationApp'),
                   ('Script', 'script', 'ScriptApp'),
                   ('Sound', 'sound', 'SoundApp'),
                   ('Submodes', 'submodes', 'SubmodesApp')]
        original_paths = Config.project_path, Log.project_path
        try:
            for folder, module_name, class_name in entries:
                with self.subTest(example=folder), tempfile.TemporaryDirectory() as temp:
                    source = root / folder
                    project = Path(temp) / folder
                    shutil.copytree(source, project)
                    config = Config.load(str(project / 'config.toml'))
                    config.update(nosound=True, pointer_input=False, wifi_watchdog=False)
                    Config.save(config, str(project / 'config.toml'))
                    sys.path.insert(0, str(source))
                    try:
                        spec = importlib.util.spec_from_file_location('current_example_' + module_name, source / (module_name + '.py'))
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        with patch.object(App, 'check_running_process', return_value=False), patch.object(Log, 'error') as errors:
                            app = getattr(module, class_name)(project_path=project)
                            processes = [worker.worker_process for worker in app.workers.values()]
                            try:
                                for _ in range(8):
                                    app.on_process()
                                    if not app.headless:
                                        app.on_draw()
                                    time.sleep(0.025)
                                if not app.headless:
                                    pixels = pygame.surfarray.array3d(app.window)
                                    self.assertGreater(int(pixels.max()), int(pixels.min()))
                                self.assertEqual(errors.call_args_list, [])
                            finally:
                                app._cleanup()
                            self.assertTrue(all(not process.is_alive() for process in processes))
                    finally:
                        sys.path.pop(0)
                        for filename, handler in list(Log.file_handlers.items()):
                            handler.close()
                            Log.loggers[filename].removeHandler(handler)
                            del Log.file_handlers[filename]
                            del Log.loggers[filename]
        finally:
            Config.project_path, Log.project_path = original_paths

    def test_actual_worker_is_reaped_after_app_init_failure(self):
        previous = {child.pid for child in multiprocessing.active_children()}
        original_paths = Config.project_path, Log.project_path
        class FailingApp(App):
            def init(self):
                self.add_worker(Worker)
                raise RuntimeError('deliberate init failure')
        try:
            with tempfile.TemporaryDirectory() as folder:
                Config.save({'headless': True, 'nosound': True}, str(Path(folder) / 'config.toml'))
                with patch.object(App, 'check_running_process', return_value=False):
                    with self.assertRaisesRegex(RuntimeError, 'deliberate init failure'):
                        FailingApp(project_path=folder)
                self.assertEqual({child.pid for child in multiprocessing.active_children()}, previous)
        finally:
            Config.project_path, Log.project_path = original_paths


if __name__ == '__main__':
    unittest.main()
