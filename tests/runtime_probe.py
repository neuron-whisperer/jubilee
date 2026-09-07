"""Disposable source/example runtime probe, invoked by test_runtime.py."""

import importlib.util
import multiprocessing
import os
from pathlib import Path
import sys
import time

import pygame
from jubilee import App, Config, Log, Worker


class EchoWorker(Worker):
    def init(self):
        self.name = 'Echo'

    def process_message(self, message, sender=None):
        if message.get('action') == 'ping':
            Log.info('worker pong')
            self.send_message({'action': 'pong'})
        else:
            super().process_message(message, sender)


class ProbeApp(App):
    def init(self):
        self.pong = False
        self.add_worker(EchoWorker)
        self.send_message('ping')

    def process_message(self, message, sender=None):
        if message.get('action') == 'pong':
            self.pong = True
        else:
            super().process_message(message, sender)


def main():
    root = Path(sys.argv[1])
    App.check_running_process = staticmethod(lambda *_: False)
    if len(sys.argv) == 2:
        Config.save({'headless': True, 'nosound': True, 'keyboard_input': False}, str(root / 'config.toml'))
        app = ProbeApp(project_path=root)
        process = app.workers['Echo'].worker_process
        try:
            deadline = time.monotonic() + 5
            while not app.pong and time.monotonic() < deadline:
                app.on_process()
                time.sleep(0.01)
            assert app.pong, 'Mode-free App did not receive spawned Worker response'
            Log.backup()
            app.pong = False
            app.send_message('ping')
            deadline = time.monotonic() + 5
            while not app.pong and time.monotonic() < deadline:
                app.on_process()
                time.sleep(0.01)
            assert app.pong
            assert 'worker pong' in (root / 'log.txt').read_text()
            try:
                app.add_worker(EchoWorker)
            except ValueError:
                pass
            else:
                raise AssertionError('Duplicate Worker silently replaced original')
            assert app.workers['Echo'].worker_process is process
        finally:
            try:
                app.exit()
            except SystemExit:
                pass
        assert not process.is_alive(), 'Worker survived App.exit'
    else:
        entry = Path(sys.argv[2])
        sys.path.insert(0, str(entry.parent))
        spec = importlib.util.spec_from_file_location('example', entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app_type = next(value for value in vars(module).values()
                        if isinstance(value, type) and issubclass(value, App) and value is not App)
        app = app_type(project_path=root)
        processes = [worker.worker_process for worker in app.workers.values()]
        try:
            for _ in range(45):
                app.on_process()
                if not app.headless:
                    app.on_draw()
            if not app.headless:
                assert pygame.surfarray.array3d(app.window).any(), 'Blank example display'
            if entry.parent.name == 'Sound':
                app.mode.play_music()
                app.mode.play_sound()
                app.mode.stop_music()
            if entry.parent.name == 'Script':
                for scene in range(len(app.script)):
                    app.select_scene(scene)
                    app.on_draw()
        finally:
            try:
                app.exit()
            except SystemExit:
                pass
        assert all(not process.is_alive() for process in processes)
    assert not multiprocessing.active_children(), 'Leaked children'
    for logfile in root.glob('**/log*.txt'):
        assert '\tERROR\t' not in logfile.read_text(), logfile.read_text()


if __name__ == '__main__':
    main()
