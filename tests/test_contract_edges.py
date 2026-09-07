"""Independent contract-edge reproductions from the current source review."""

import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import datetime
import json
import queue
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame
from jubilee import App, Mode, Worker
from jubilee.base_classes import Animation, Sprite
from jubilee.controls import Control, HoldButton, LabeledControl, SelectButton
from jubilee.misc import Config, Log, Misc
from jubilee.mouse_interface import MouseInterface


class ContractEdges(unittest.TestCase):
    def setUp(self):
        for name in ('info', 'warning', 'error', 'debug'):
            p = patch.object(Log, name)
            p.start()
            self.addCleanup(p.stop)

    def app(self):
        app = App.__new__(App)
        app.config = {'modal': False, 'keyboard_input': False}
        app.mode = None
        app.modes = {}
        app.workers = {}
        app.pointer = None
        app.headless = True
        app.nosound = True
        app.process = Mock()
        app.handle_events = Mock()
        app.apply_music_fade = Mock()
        return app

    def test_hold_completion_does_not_undo_release(self):
        button = HoldButton('go', 0, 0, 10, 10, hold_steps=1)
        button.provided_click_handler = button.on_release
        button.on_hold()
        self.assertEqual(button.hold_step, 0)

    def test_hold_completion_exception_is_not_retriggered(self):
        callback = Mock(side_effect=RuntimeError('callback'))
        button = HoldButton('go', 0, 0, 10, 10, hold_steps=1, click=callback)
        with self.assertRaises(RuntimeError):
            button.on_hold()
        button.on_hold()
        self.assertEqual(callback.call_count, 1)

    def test_selection_survives_shorter_reordered_items(self):
        button = SelectButton(0, 0, 10, 10, ['a', 'b', 'c'], selected_index=2)
        button.set_items(['a', 'c'], reset_to_first=False)
        self.assertEqual((button.selected_index, button.selected_item), (1, 'c'))

    def test_label_layout_moves_child_vertically(self):
        child = Control(0, 0, 10, 10)
        label = LabeledControl('go', child, offset=20)
        label.y = 50
        label.set_layout()
        self.assertTrue(label.collide(25, 55))

    def test_label_respects_child_visibility(self):
        child = Control(0, 0, 10, 10)
        child.visible = False
        child.draw = Mock()
        label = LabeledControl('go', child, offset=0)
        label.bind(Mock())
        self.assertFalse(label.collide(5, 5))
        label.draw()
        child.draw.assert_not_called()

    def test_label_respects_child_disabled(self):
        callback = Mock()
        child = Control(0, 0, 10, 10, click=callback, hold=callback)
        child.enabled = False
        label = LabeledControl('go', child, offset=0)
        label.on_click()
        label.on_hold()
        callback.assert_not_called()

    def test_hold_error_after_self_removal_is_logged(self):
        mode = Mode()
        def hold():
            mode.remove_controls()
            raise RuntimeError('original failure')
        mode.selected_control = Control(0, 0, 10, 10, hold=hold, name='self-removing')
        mode.on_hold()
        self.assertIn('original failure', str(Log.error.call_args))

    def test_disabled_selected_control_stops_holding(self):
        mode = Mode()
        control = Control(0, 0, 10, 10, hold=Mock(), release=Mock())
        mode.selected_control = control
        control.enabled = False
        mode.on_hold()
        control.provided_hold_handler.assert_not_called()
        control.provided_release_handler.assert_called_once()
        self.assertIsNone(mode.selected_control)

    def test_submode_discovery_does_not_evaluate_properties(self):
        class PropertyMode(Mode):
            @property
            def display_name(self):
                raise RuntimeError('property must not run during introspection')
            def draw_menu(self):
                pass
        self.assertIn('menu', PropertyMode().submodes)

    def test_sprite_error_does_not_starve_other_sprites(self):
        mode = Mode()
        first = Mock()
        first.process.side_effect = RuntimeError('broken sprite')
        second = Mock()
        mode.sprites = [first, second]
        mode.on_process()
        second.process.assert_called_once()

    def test_offscreen_x_does_not_override_sprite_y_order(self):
        mode = Mode()
        mode.app = Mock(screen_width=320)
        first = Mock(x=1000, y=0, z=None, image=None)
        second = Mock(x=0, y=1, z=None, image=None)
        mode.sprites = [second, first]
        mode.render_sprites()
        self.assertEqual(mode.sprites, [first, second])

    def test_app_process_error_does_not_starve_events(self):
        app = self.app()
        app.process.side_effect = RuntimeError('broken hook')
        app.on_process()
        app.handle_events.assert_called_once()

    def test_modeless_processing_allows_mode_registration(self):
        app = self.app()
        first = Mock()
        first.name = 'first'
        second = Mock()
        second.name = 'second'
        first.on_process.side_effect = lambda: app.modes.update(third=Mock())
        app.modes = {'first': first, 'second': second}
        app.on_process()
        second.on_process.assert_called_once()

    def test_enter_redirect_does_not_apply_submode_to_other_mode(self):
        app = self.app()
        first = Mock()
        first.name = 'first'
        second = Mock()
        second.name = 'second'
        first.on_enter.side_effect = lambda **kw: app.set_mode(second)
        app.set_mode(first, {'submode': 'menu'})
        self.assertIs(app.mode, second)
        second.set_submode.assert_not_called()

    def test_headless_processing_advances_music_fade(self):
        app = self.app()
        app.on_process()
        app.apply_music_fade.assert_called_once()

    def test_keyboard_disable_clears_pressed_state(self):
        app = self.app()
        app.new_keys = ['a']
        app.held_keys = ['a']
        app.receive_messages = Mock()
        with patch('pygame.event.get', return_value=[]):
            App.handle_events(app)
        self.assertEqual((app.new_keys, app.held_keys), ([], []))

    def test_explicit_alpha_flag_survives_surface_conversion(self):
        pygame.display.init()
        self.addCleanup(pygame.display.quit)
        pygame.display.set_mode((16, 16))
        surface = App.create_surface(self.app(), 4, 4, color=None, flags=pygame.SRCALPHA)
        self.assertTrue(surface.get_flags() & pygame.SRCALPHA)
        self.assertEqual(surface.get_at((0, 0)).a, 0)

    def test_cleanup_survives_logging_failure(self):
        app = self.app()
        Log.info.side_effect = OSError('disk unavailable')
        with patch('pygame.quit') as quit_pygame:
            app._cleanup()
            quit_pygame.assert_called_once()

    def test_worker_broken_queue_stops_drain(self):
        worker = Worker.__new__(Worker)
        worker.app_queue = Mock()
        worker.app_queue.get_nowait.side_effect = [OSError('closed pipe'), queue.Empty()]
        worker.receive_messages()
        self.assertEqual(worker.app_queue.get_nowait.call_count, 1)

    def test_reload_stat_race_keeps_current_config(self):
        worker = Worker.__new__(Worker)
        worker.config_manager = True
        worker.config_filename = 'vanishing.toml'
        worker.config = {'keep': 7}
        with patch('os.path.isfile', return_value=True), patch('os.path.getmtime', side_effect=FileNotFoundError):
            worker.manage_config()
        self.assertEqual(worker.config, {'keep': 7})

    def test_reload_rejects_untransportable_config_before_install(self):
        worker = Worker.__new__(Worker)
        worker.config_manager = True
        worker.config_filename = 'config.toml'
        worker.config_date = 1
        worker.config_defaults = {}
        worker.config = {'keep': 7}
        worker.send_updated_config = Mock()
        with patch('os.path.isfile', return_value=True), patch('os.path.getmtime', return_value=2), patch.object(Config, 'load', return_value={'date': datetime.date(2026, 9, 7)}):
            worker.manage_config()
        self.assertEqual(worker.config, {'keep': 7})
        self.assertEqual(worker.config_date, 1)
        worker.send_updated_config.assert_not_called()

    def test_wifi_exit_restores_interface(self):
        worker = Worker.__new__(Worker)
        worker._wifi_run_command = Mock()
        worker._wifi_send_recovery = Mock()
        worker._wifi_ping = Mock(return_value=False)
        worker._wifi_interruptible_sleep = Mock(side_effect=[None, SystemExit()])
        with self.assertRaises(SystemExit):
            worker._wifi_escalating_recovery('gateway', 'wlan0', 1, 1)
        commands = [call.args[0] for call in worker._wifi_run_command.call_args_list]
        self.assertIn(['ip', 'link', 'set', 'wlan0', 'up'], commands)

    def test_wifi_exit_reloads_removed_driver(self):
        worker = Worker.__new__(Worker)
        worker._wifi_run_command = Mock()
        worker._wifi_send_recovery = Mock()
        worker._wifi_ping = Mock(return_value=False)
        worker._wifi_interruptible_sleep = Mock(side_effect=[None, None, None, None, SystemExit()])
        with self.assertRaises(SystemExit):
            worker._wifi_escalating_recovery('gateway', 'wlan0', 1, 1)
        commands = [call.args[0] for call in worker._wifi_run_command.call_args_list]
        self.assertIn(['modprobe', 'brcmfmac'], commands)

    def test_http_respects_case_insensitive_header_override(self):
        with patch.object(Misc, 'user_agent', 'default'), patch('requests.get', return_value=SimpleNamespace(status_code=200)) as get:
            Misc.http_request('https://example.invalid', headers={'user-agent': 'chosen'})
        headers = get.call_args.kwargs['headers']
        values = [v for k, v in headers.items() if k.lower() == 'user-agent']
        self.assertEqual(values, ['chosen'])

    def test_http_agent_failure_returns_error(self):
        with patch.object(Misc, 'user_agent', None), patch.object(Misc, 'choose_user_agent', side_effect=OSError('missing data')):
            status, error = Misc.http_request('https://example.invalid')
        self.assertIsNone(status)
        self.assertIn('missing data', error)

    def test_log_parses_empty_message(self):
        record = Log.parse('20260907 12:00:00\tClass\tmethod\tINFO\t\n')
        self.assertIsNotNone(record)
        self.assertEqual(record['message'], '')

    def test_constructor_failure_cleans_up_started_workers(self):
        process = Mock()
        process.is_alive.return_value = False
        worker = SimpleNamespace(name='worker', worker_process=process,
                                 app_queue=Mock(), worker_queue=Mock())
        class BrokenApp(App):
            def _initialize(self, **kwargs):
                self.workers['worker'] = worker
                raise RuntimeError('initialization failure')
        with patch('pygame.quit') as quit_pygame:
            with self.assertRaisesRegex(RuntimeError, 'initialization failure'):
                BrokenApp()
        process.join.assert_called_once()
        worker.app_queue.close.assert_called_once()
        quit_pygame.assert_called_once()

    def test_shutdown_exits_active_mode_once(self):
        app = self.app()
        mode = Mock()
        app.mode = mode
        with patch('pygame.quit'):
            app._cleanup()
            app._cleanup()
        mode.on_exit.assert_called_once()

    def test_mode_exit_request_during_shutdown_does_not_skip_workers(self):
        app = self.app()
        app.mode = Mock()
        app.mode.on_exit.side_effect = lambda: app.exit()
        process = Mock()
        process.is_alive.return_value = False
        app.workers['worker'] = SimpleNamespace(name='worker', worker_process=process,
                                               app_queue=Mock(), worker_queue=Mock())
        with patch('pygame.quit'):
            app._cleanup()
        process.join.assert_called_once()

    def test_strict_config_disappearance_is_not_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                Config.load(str(Path(folder) / 'missing.toml'), defaults={'keep': 7}, strict=True)

    def test_worker_invalid_json_config_does_not_write(self):
        worker = Worker.__new__(Worker)
        worker.config = {'keep': 7}
        worker.config_filename = 'not-written.toml'
        with patch.object(Config, 'save') as save:
            with self.assertRaises(TypeError):
                worker.update_config('date', datetime.date(2026, 9, 7))
        save.assert_not_called()
        self.assertEqual(worker.config, {'keep': 7})

    def test_app_scheduler_ignores_wall_clock_rollback(self):
        app = self.app()
        app.process_last = 100
        app.process_period = 0.05
        app.on_process = Mock(side_effect=SystemExit())
        app._cleanup = Mock()
        with patch('time.time', return_value=1), patch('time.monotonic', return_value=101), patch('time.sleep', side_effect=RuntimeError('scheduler stalled')):
            with self.assertRaises(SystemExit):
                app.run()
        app.on_process.assert_called_once()

    def test_app_process_timestamp_is_monotonic(self):
        app = self.app()
        with patch('time.time', return_value=1), patch('time.monotonic', return_value=101):
            app.on_process()
        self.assertEqual(app.process_last, 101)

    def test_worker_periodic_timestamp_is_monotonic(self):
        worker = Worker.__new__(Worker)
        worker.config_manager = worker.log_manager = worker.wifi_manager = False
        with patch('time.time', return_value=1), patch('time.monotonic', return_value=101):
            worker.on_process_periodic()
        self.assertEqual(worker.last_periodic, 101)

    def test_invalid_sequence_selection_preserves_current_sequence(self):
        sprite = Sprite(animation=Animation(frames=[pygame.Surface((2, 2))], sequences={'good': [0]}))
        sprite.app = self.app()
        self.assertTrue(sprite.set_sequence('good'))
        self.assertFalse(sprite.set_sequence('missing'))
        self.assertEqual(sprite.sequence_name, 'good')

    def test_invalid_frame_selection_preserves_current_frame(self):
        sprite = Sprite(animation=Animation(frames=[pygame.Surface((2, 2))], sequences={'good': [0]}))
        sprite.app = self.app()
        sprite.set_sequence('good')
        sprite.animate(0)
        self.assertFalse(sprite.animate(10))
        self.assertEqual(sprite.sequence_frame, 0)

    def test_sprite_binds_to_own_mode_not_current_mode(self):
        app = self.app()
        app.animations = {}
        current, owner = Mode(), Mode()
        current.animations['actor'] = Animation('wrong')
        expected = pygame.Surface((2, 2))
        owner.animations['actor'] = Animation('right', [expected])
        app.mode = current
        owner.app = app
        sprite = owner.add_sprite(Sprite(animation='actor'))
        self.assertIs(sprite.set_image(), expected)

    def test_sprite_binding_before_resources_load_keeps_local_precedence(self):
        app = self.app()
        app.animations = {'actor': Animation('global', [pygame.Surface((2, 2))])}
        owner = Mode()
        owner.app = app
        sprite = owner.add_sprite(Sprite(animation='actor'))
        expected = pygame.Surface((2, 2))
        owner.animations['actor'] = Animation('local', [expected])
        self.assertIs(sprite.set_image(), expected)

    def test_relative_log_names_do_not_share_handler_across_directories(self):
        cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                (root / 'a').mkdir()
                (root / 'b').mkdir()
                os.chdir(root / 'a')
                first = Log.get_logger('same.txt')
                os.chdir(root / 'b')
                second = Log.get_logger('same.txt')
                self.assertIsNot(first, second)
        finally:
            os.chdir(cwd)
            for filename, handler in list(Log.file_handlers.items()):
                handler.close()
                Log.loggers[filename].removeHandler(handler)
                del Log.file_handlers[filename]
                del Log.loggers[filename]

    def test_mode_transition_cancels_in_progress_pointer_gesture(self):
        app = self.app()
        app.pointer = MouseInterface()
        app.pointer_input_last = None
        app.pointer_input_debouncing = 100
        app.receive_messages = Mock()
        first, second = Mock(), Mock()
        first.name, second.name = 'first', 'second'
        app.mode = first
        first.on_click.side_effect = lambda *args: app.set_mode(second)
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(5, 5))
        with patch('pygame.event.get', side_effect=[[down], [], [up]]):
            for _ in range(3):
                App.handle_events(app)
        second.on_hold.assert_not_called()
        second.on_release.assert_not_called()

    def test_exit_callback_can_redirect_without_recursive_exit(self):
        app = self.app()
        first, second, third = Mock(), Mock(), Mock()
        first.name, second.name, third.name = 'first', 'second', 'third'
        app.mode = first
        def redirect():
            if first.on_exit.call_count > 1:
                raise RuntimeError('recursive mode exit')
            app.set_mode(third)
        first.on_exit.side_effect = redirect
        app.set_mode(second)
        self.assertIs(app.mode, third)
        first.on_exit.assert_called_once()

    def test_configuration_reload_updates_timing(self):
        app = self.app()
        app.process_period = 1
        app.process_message({'action': 'config updated', 'config': {'app_process_fps': 40}})
        self.assertEqual(app.process_period, 0.025)

    def test_worker_constructor_failure_closes_new_queues(self):
        app = self.app()
        channels = [Mock(), Mock()]
        with patch('multiprocessing.Queue', side_effect=channels):
            with self.assertRaises(RuntimeError):
                app.add_worker(Mock(side_effect=RuntimeError('init failed')))
        for channel in channels:
            channel.close.assert_called_once()

    def test_bad_state_file_is_not_overwritten_after_failed_load(self):
        app = self.app()
        app.persist_app_state = True
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'app_state.json'
            path.write_text('{broken', encoding='utf-8')
            app.app_state_filename = str(path)
            app.app_state_start_filename = str(Path(folder) / 'initial.json')
            app.load_app_state()
            self.assertFalse(app.set_app_state('new', 1))
            self.assertEqual(path.read_text(encoding='utf-8'), '{broken')
            path.write_text('{"restored": 2}', encoding='utf-8')
            app.load_app_state()
            self.assertTrue(app.set_app_state('new', 1))
            self.assertEqual(json.loads(path.read_text()), {'restored': 2, 'new': 1})

    def test_normal_pointer_gesture_still_delivers_one_release(self):
        app = self.app()
        app.pointer = MouseInterface()
        app.pointer_input_last = None
        app.pointer_input_debouncing = 100
        app.receive_messages = Mock()
        app.mode = Mock()
        down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(5, 5))
        with patch('pygame.event.get', side_effect=[[down], [], [up]]):
            for _ in range(3):
                App.handle_events(app)
        app.mode.on_click.assert_called_once_with(5, 5)
        app.mode.on_hold.assert_called_once()
        app.mode.on_release.assert_called_once()


if __name__ == '__main__':
    unittest.main()
