"""Source regressions; run with python -m unittest discover -s tests -v."""

import json
import importlib
import os
from pathlib import Path
import queue
import tempfile
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame
from jubilee import App, Animation, Color, Config, Control, Log, LogMode, Misc, Mode, SelectButton, Sprite, Worker
from jubilee.mouse_interface import MouseInterface


class Regressions(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.old_log_path = Log.project_path
        Log.project_path = self.folder.name
        Log.set_console_level(100)
        self.addCleanup(setattr, Log, 'project_path', self.old_log_path)

    def app(self):
        app = App.__new__(App)
        app.mode = None
        app.modes = {}
        app.workers = {}
        app.config = {'modal': True, 'keyboard_input': False}
        app.headless = True
        app.pointer = None
        app.process_last = 0
        app.process = Mock()
        app.project_path = str(self.root)
        app.app_state = {}
        app.persist_app_state = False
        app.app_state_filename = str(self.root / 'state.json')
        app.app_state_start_filename = str(self.root / 'initial.json')
        return app

    def graphics(self):
        pygame.init()
        pygame.display.set_mode((32, 32))
        self.addCleanup(pygame.quit)
        app = self.app()
        app.window = pygame.Surface((32, 32))
        app.images = {}
        app.animations = {}
        return app

    def worker(self):
        worker = Worker.__new__(Worker)
        worker.project_path = str(self.root)
        worker.app_queue = queue.Queue()
        worker.worker_queue = queue.Queue()
        worker.config = dict(Worker.config_defaults)
        worker.config_filename = str(self.root / 'config.toml')
        worker.config_manager = True
        worker.config_date = None
        worker.wifi_reboot_date = None
        worker.wifi_reboot_count_today = 0
        worker.wifi_consecutive_failures = 3
        return worker

    def test_modeless_app_processes_events_and_updates_clock(self):
        app = self.app()
        app.handle_events = Mock()
        app.on_process()
        app.handle_events.assert_called_once()
        self.assertGreater(app.process_last, 0)

    def test_invalid_mode_does_not_exit_current_mode(self):
        app = self.app()
        app.mode = Mock(name='current')
        app.set_mode('missing')
        app.mode.on_exit.assert_not_called()

    def test_mode_parameters_are_copied_and_reach_submode(self):
        app = self.app()
        mode = Mock()
        app.modes['next'] = mode
        parameters = {'submode': 'menu', 'answer': 42}
        app.set_mode('next', parameters)
        self.assertNotIn('previous_mode', parameters)
        self.assertEqual(mode.set_submode.call_args.kwargs['mode_parameters']['answer'], 42)

    def test_select_button_refreshes_same_index(self):
        control = SelectButton(0, 0, 10, 10, ['old'], values=[1])
        control.set_items(['new'], values=[2])
        self.assertEqual((control.selected_index, control.selected_item, control.value), (0, 'new', 2))

    def test_select_button_preserves_item_at_new_index(self):
        control = SelectButton(0, 0, 10, 10, ['a', 'b'], selected_index=1)
        control.set_items(['b', 'a'], reset_to_first=False)
        self.assertEqual((control.selected_index, control.selected_item), (0, 'b'))

    def test_select_button_bad_values_do_not_leave_crashing_control(self):
        control = SelectButton(0, 0, 10, 10, ['a', 'b'], values=[])
        control.on_click()
        self.assertEqual(control.selected_item, 'a')

    def test_remove_by_caption_handles_unlabeled_controls(self):
        mode = Mode()
        mode.controls = [Control(0, 0, 10, 10)]
        mode.remove_control('missing')
        self.assertEqual(len(mode.controls), 1)

    def test_removed_control_no_longer_receives_hold(self):
        mode = Mode()
        control = Control(0, 0, 10, 10, hold=Mock(), release=Mock())
        mode.controls = [control]
        mode.selected_control = control
        mode.remove_controls()
        mode.on_hold()
        control.provided_hold_handler.assert_not_called()
        control.provided_release_handler.assert_called_once()

    def test_invalid_submode_preserves_active_submode(self):
        mode = Mode()
        mode.submode = 'existing'
        mode.submode_timer = 5
        mode.set_submode('typo')
        self.assertEqual(mode.submode, 'existing')
        self.assertEqual(mode.submode_timer, 5)

    def test_mode_exit_clears_submode_timer(self):
        mode = Mode()
        mode.submode_timer = 5
        mode.on_exit()
        self.assertIsNone(mode.submode_timer)

    def test_sprite_zero_rate_and_invalid_frames(self):
        app = self.app()
        animation = Animation(frames=[object()], sequences={'bad': [-1]})
        sprite = Sprite(animation=animation, auto_animate_rate=0)
        sprite.bind(app)
        self.assertEqual(sprite.auto_animate_rate, 0)
        self.assertFalse(sprite.animate(-1))
        self.assertFalse(sprite.animate(1))
        sprite.set_sequence('bad', auto_animate_rate=0)
        self.assertEqual(sprite.auto_animate_rate, 0)
        self.assertFalse(sprite.animate(0))

    def test_sprite_failure_clears_dimensions(self):
        app = self.graphics()
        sprite = Sprite(static_image=pygame.Surface((2, 3)))
        sprite.bind(app)
        sprite.set_image()
        sprite.static_image = None
        sprite.set_image()
        self.assertEqual((sprite.image, sprite.width, sprite.height), (None, None, None))

    def test_sprite_resolves_animation_loaded_after_bind(self):
        app = self.graphics()
        sprite = Sprite(animation='robot')
        sprite.bind(app)
        frame = pygame.Surface((1, 1))
        app.animations['robot'] = Animation(frames=[frame])
        self.assertIs(sprite.set_image(), frame)

    def test_enum_colors_and_zero_scale(self):
        self.assertEqual(Misc.get_color(Color.RED), (255, 0, 0))
        self.assertEqual(Misc.get_color('white', 0), (0, 0, 0))

    def test_zero_y_scale(self):
        app = self.graphics()
        self.assertEqual(app.scale_image(pygame.Surface((10, 10)), 1, 0).get_size(), (10, 0))

    def test_blit_respects_explicit_blend_flags(self):
        app = self.graphics()
        app.window.fill((100, 100, 100))
        image = pygame.Surface((2, 2), pygame.SRCALPHA)
        image.fill((100, 0, 0, 255))
        app.blit(image, 0, 0, flags=pygame.BLEND_RGB_ADD)
        self.assertEqual(app.window.get_at((0, 0))[:3], (200, 100, 100))

    def test_float_stroke_widths(self):
        app = self.graphics()
        app.draw_line(0, 0, 5, 5, width=1.0)
        app.draw_rect(0, 0, 5, 5, line_width=1.0)
        app.draw_polygon([(0, 0), (5, 0), (5, 5)], width=1.0)
        app.draw_circle(5, 5, 2, width=1.0)
        app.draw_arc(0, 0, 5, 5, 0, 90, line_width=1.0)

    def test_hue_shift_preserves_surface_alpha_and_colorkey(self):
        app = self.graphics()
        surface = pygame.Surface((2, 2))
        surface.fill('red')
        surface.set_alpha(100)
        surface.set_colorkey('red')
        shifted = app.shift_image_hue(surface, 120)
        self.assertIsNotNone(shifted)
        self.assertEqual(shifted.get_alpha(), 100)
        self.assertEqual(shifted.get_colorkey()[:3], shifted.get_at((0, 0))[:3])

    def test_animation_static_underscore_does_not_overwrite_sequence(self):
        app = self.graphics()
        folder = self.root / 'robot'
        folder.mkdir()
        for name in ('walk.png', 'walk_left.png'):
            pygame.image.save(pygame.Surface((1, 1)), str(folder / name))
        _, animations = app.load_images(str(self.root))
        self.assertEqual(len(animations['robot'].sequences['walk']), 1)

    def test_state_tempfile_failure_does_not_mask_original_error(self):
        app = self.app()
        with patch('jubilee.app.tempfile.mkstemp', side_effect=OSError('disk full')):
            self.assertFalse(app.save_app_state())

    def test_state_failure_restores_previous_value(self):
        app = self.app()
        app.persist_app_state = True
        app.app_state = {'a': 1}
        with patch.object(app, 'save_app_state', return_value=False):
            self.assertFalse(app.set_app_state('a', 2))
        self.assertEqual(app.app_state, {'a': 1})

    def test_state_requires_dictionary(self):
        app = self.app()
        Path(app.app_state_filename).write_text('[]')
        app.load_app_state()
        self.assertEqual(app.app_state, {})

    def test_scene_rejects_negative_and_unknown_mode_without_state_change(self):
        app = self.app()
        app.script = [{'mode': 'missing'}]
        app.app_state = {'scene': 10}
        app.select_scene(-1)
        self.assertEqual(app.app_state['scene'], 10)
        app.select_scene(0)
        self.assertEqual(app.app_state['scene'], 10)
        app.script = []
        app.run_script()

    def test_config_defaults_do_not_share_nested_values(self):
        defaults = {'nested': [1]}
        config = Config.load(str(self.root / 'absent.toml'), defaults)
        config['nested'].append(2)
        self.assertEqual(defaults, {'nested': [1]})

    def test_invalid_config_reload_preserves_last_good_config(self):
        worker = self.worker()
        worker.config['custom'] = 'keep'
        Path(worker.config_filename).write_text('bad = [')
        worker.manage_config()
        self.assertEqual(worker.config['custom'], 'keep')
        self.assertTrue(worker.worker_queue.empty())

    def test_failed_config_save_rolls_back_memory(self):
        worker = self.worker()
        worker.config['custom'] = 1
        with patch.object(Config, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                worker.update_config('custom', 2)
        self.assertEqual(worker.config['custom'], 1)

    def test_wifi_wait_dispatches_custom_messages(self):
        worker = self.worker()
        worker.app_queue.put(json.dumps({'action': 'custom'}))
        worker.process_message = Mock()
        worker._wifi_interruptible_sleep(0.01)
        worker.process_message.assert_called_once_with({'action': 'custom'}, sender='App')

    def test_wifi_reboot_limit_survives_worker_recreation(self):
        for attempt in range(4):
            worker = self.worker()
            worker._wifi_ping = Mock(return_value=False)
            worker._wifi_run_command = Mock(return_value=False)
            worker._wifi_interruptible_sleep = Mock()
            worker._wifi_escalating_recovery('192.0.2.1', 'wlan0', 1, 1)
            reboots = [c for c in worker._wifi_run_command.call_args_list if c.args[0][:2] == ['sudo', 'shutdown']]
            self.assertEqual(len(reboots), int(attempt < 3))

    def test_wifi_invalid_existing_budget_refuses_reboot(self):
        path = self.root / 'wifi_reboot_state.toml'
        for contents in ('bad = [', 'count = 0', 'date = "20260907"',
                         'date = "invalid"\ncount = 0',
                         'date = "20260907"\ncount = -1',
                         'date = "20260907"\ncount = true'):
            with self.subTest(contents=contents):
                path.write_text(contents)
                worker = self.worker()
                worker._wifi_ping = Mock(return_value=False)
                worker._wifi_run_command = Mock(return_value=False)
                worker._wifi_interruptible_sleep = Mock()
                worker._wifi_escalating_recovery('192.0.2.1', 'wlan0', 1, 1)
                reboots = [c for c in worker._wifi_run_command.call_args_list
                           if c.args[0][:2] == ['sudo', 'shutdown']]
                self.assertEqual(reboots, [])
                self.assertEqual(path.read_text(), contents)

    def test_wifi_broken_budget_symlink_refuses_reboot(self):
        path = self.root / 'wifi_reboot_state.toml'
        path.symlink_to(self.root / 'missing-budget.toml')
        worker = self.worker()
        worker._wifi_ping = Mock(return_value=False)
        worker._wifi_run_command = Mock(return_value=False)
        worker._wifi_interruptible_sleep = Mock()
        worker._wifi_escalating_recovery('192.0.2.1', 'wlan0', 1, 1)
        self.assertFalse(any(c.args[0][:2] == ['sudo', 'shutdown']
                             for c in worker._wifi_run_command.call_args_list))
        self.assertTrue(path.is_symlink())

    def test_wifi_previous_day_budget_resets_and_reserves_before_reboot(self):
        path = self.root / 'wifi_reboot_state.toml'
        Config.save({'date': '20000101', 'count': 3}, str(path))
        worker = self.worker()
        worker._wifi_ping = Mock(return_value=False)
        worker._wifi_interruptible_sleep = Mock()
        def command(args, **kwargs):
            if args[:2] == ['sudo', 'shutdown']:
                state = Config.load(str(path), strict=True)
                self.assertEqual(state['count'], 1)
                self.assertNotEqual(state['date'], '20000101')
            return False
        worker._wifi_run_command = Mock(side_effect=command)
        worker._wifi_escalating_recovery('192.0.2.1', 'wlan0', 1, 1)
        self.assertEqual(sum(c.args[0][:2] == ['sudo', 'shutdown']
                             for c in worker._wifi_run_command.call_args_list), 1)

    def test_log_writer_reopens_after_external_rotation(self):
        filename = str(self.root / 'shared.log')
        Log.info('before', filename=filename)
        os.rename(filename, filename + '.old')
        Log.info('after', filename=filename)
        self.assertTrue(Path(filename).exists())
        self.assertIn('after', Path(filename).read_text())
        self.assertNotIn('\tINFO\tafter', Path(filename + '.old').read_text())

    def test_log_backup_reopens_requested_file(self):
        filename = str(self.root / 'custom.log')
        Log.info('before', filename=filename)
        self.assertTrue(Log.backup(filename=filename))
        self.assertTrue(Path(filename).exists())

    def test_log_parse_preserves_tabs_without_logging_bad_records(self):
        record = '20260907 12:00:00\tClass\tmethod\tINFO\ta\tb'
        self.assertEqual(Log.parse(record)['message'], 'a\tb')
        with patch.object(Log, 'error') as error:
            self.assertIsNone(Log.parse('bad\tdate\tmethod\tINFO\tmessage'))
            error.assert_not_called()

    def test_mouse_uses_event_coordinates(self):
        pointer = MouseInterface()
        with patch('pygame.mouse.get_pos', return_value=(99, 99)):
            pointer.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(2, 3), button=1))
        self.assertEqual((pointer.x, pointer.y), (2, 3))

    def test_quick_mouse_click_is_released(self):
        app = self.graphics()
        app.pointer = MouseInterface()
        app.mode = Mock()
        app.pointer_input_last = None
        app.pointer_input_debouncing = 100
        events = [pygame.event.Event(kind, pos=(2, 3), button=1) for kind in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)]
        with patch('pygame.event.get', return_value=events):
            app.handle_events()
        app.mode.on_click.assert_called_once_with(2, 3)
        app.mode.on_release.assert_called_once()

    def test_http_explicit_get_is_not_changed_to_post(self):
        with patch.object(Misc, 'user_agent', 'fixture'), patch('jubilee.misc.requests.get') as get:
            get.return_value.status_code = 200
            with patch('jubilee.misc.requests.post') as post:
                headers = {'X-Test': 'yes'}
                Misc.http_request('https://example.test', method='GET', data={'x': 1}, headers=headers)
                get.assert_called_once()
                post.assert_not_called()
                self.assertEqual(headers, {'X-Test': 'yes'})

    def test_sign_request_creates_query_before_fragment(self):
        ok, url = Misc.sign_request('https://example.test/path#section', 'secret', timestamp=1)
        self.assertTrue(ok)
        self.assertTrue(url.startswith('https://example.test/path?ts=1&hash='))
        self.assertTrue(url.endswith('#section'))

    def test_music_load_applies_volume_after_load_and_cancels_old_fade(self):
        app = self.app()
        app.nosound = False
        app.music_volume = 100
        app.music_fade_steps = 20
        app.music_fade_step = 10
        app.get_music = Mock(return_value='music.mp3')
        with patch('jubilee.app.pygame.mixer.music') as music:
            app.play_music('music.mp3', volume=25)
            self.assertLess(music.mock_calls.index(unittest.mock.call.load('music.mp3')),
                            music.mock_calls.index(unittest.mock.call.set_volume(0.25)))
        self.assertIsNone(app.music_fade_steps)

    def test_music_fade_starts_at_actual_volume(self):
        app = self.app()
        app.nosound = False
        app.music_volume = 100
        with patch('jubilee.app.pygame.mixer.music') as music:
            music.get_volume.return_value = 0.25
            music.get_busy.return_value = True
            app.start_music_fade(10)
            app.apply_music_fade()
            self.assertAlmostEqual(music.set_volume.call_args.args[0], 0.225)

    def test_repeated_sound_retainer_enable_does_not_leak_sound(self):
        app = self.app()
        app.nosound = False
        app.sound_retainer = Mock()
        with patch('jubilee.app.pygame.mixer.Sound') as sound, patch('jubilee.app.os.path.isfile', return_value=True):
            app.set_sound_retainer(True)
            sound.assert_not_called()

    def test_touch_packet_order_edges_swap_and_close(self):
        ecodes = SimpleNamespace(EV_ABS=3, EV_KEY=1, EV_SYN=0, SYN_REPORT=0,
                                 ABS_MT_POSITION_X=53, ABS_MT_POSITION_Y=54, BTN_TOUCH=330)
        def event(kind, code, value=0):
            return SimpleNamespace(type=kind, code=code, value=value)
        packets = [event(1, 330, 1), event(3, 53, 100), event(3, 54, 0), event(0, 0),
                   event(1, 330, 0), event(0, 0)]
        rejected = Mock(info=SimpleNamespace(bustype=1))
        device = Mock(info=SimpleNamespace(bustype=24))
        device.read.return_value = iter(packets)
        fake = SimpleNamespace(ecodes=ecodes, InputDevice=Mock(side_effect=[rejected, device]))
        with patch.dict(sys.modules, {'evdev': fake}):
            sys.modules.pop('jubilee.touch_interface', None)
            module = importlib.import_module('jubilee.touch_interface')
            with patch.object(module.glob, 'glob', return_value=['/dev/input/event1', '/dev/input/event10']):
                pointer = module.TouchInterface([320, 240], [[0, 100, 1], [0, 100, 1]], swap_axes=True)
            self.assertTrue(pointer.detect_events())
            self.assertEqual((pointer.x, pointer.y), (0, 239))
            self.assertFalse(pointer.detect_events())
            self.assertFalse(pointer.down)
            pointer.release()
            rejected.close.assert_called_once()
            device.close.assert_called_once()
        sys.modules.pop('jubilee.touch_interface', None)

    def test_log_graph_history_is_bounded_on_narrow_display(self):
        mode = LogMode()
        mode.app = SimpleNamespace(screen_width=180)
        with patch('jubilee.log_mode.psutil', SimpleNamespace(cpu_percent=lambda: 1)), patch('jubilee.log_mode.platform.system', return_value='Darwin'):
            for _ in range(10):
                mode.record_cpu_temperatures()
        self.assertLessEqual(len(mode.cpu_load), 1)

    def test_cleanup_terminates_unresponsive_worker_and_quits_after_pointer_failure(self):
        app = self.app()
        process = Mock()
        process.is_alive.side_effect = [True, False]
        worker = SimpleNamespace(name='worker', worker_process=process, app_queue=Mock(), worker_queue=Mock())
        app.workers = {'worker': worker}
        app.pointer = Mock()
        app.pointer.release.side_effect = RuntimeError('release failed')
        with patch('jubilee.app.pygame.quit') as quit:
            with self.assertRaises(RuntimeError):
                app._cleanup()
            quit.assert_called_once()
        process.terminate.assert_called_once()

    def test_zero_periodic_rate_does_not_crash_worker(self):
        worker = self.worker()
        worker.config['worker_process_periodic_fps'] = 0
        worker.last_periodic = None
        worker.on_process_periodic = Mock()
        with patch.object(worker, 'receive_messages', side_effect=[None, SystemExit(0)]), patch('jubilee.worker.signal.signal'):
            with self.assertRaises(SystemExit):
                worker.run()
        worker.on_process_periodic.assert_not_called()

    def test_wifi_budget_save_failure_refuses_reboot(self):
        worker = self.worker()
        worker._wifi_ping = Mock(return_value=False)
        worker._wifi_run_command = Mock(return_value=False)
        worker._wifi_interruptible_sleep = Mock()
        with patch.object(Config, 'save', side_effect=OSError('read-only')):
            worker._wifi_escalating_recovery('192.0.2.1', 'wlan0', 1, 1)
        self.assertFalse(any(c.args[0][:2] == ['sudo', 'shutdown'] for c in worker._wifi_run_command.call_args_list))

    def test_wifi_missing_gateway_still_attempts_recovery(self):
        worker = self.worker()
        worker.wifi_manager = True
        worker.config['wifi_watchdog'] = True
        worker.wifi_last_check = None
        worker.wifi_boot_grace = False
        worker.wifi_recovering = False
        worker._wifi_detect_gateway = Mock(return_value=None)
        worker._wifi_escalating_recovery = Mock()
        with patch('jubilee.worker.platform.system', return_value='Linux'):
            worker.manage_wifi()
        worker._wifi_escalating_recovery.assert_called_once()

    def test_wifi_wait_dispatches_exit_and_survives_bad_message(self):
        worker = self.worker()
        worker.app_queue.put('malformed')
        worker.app_queue.put(json.dumps({'action': 'exit'}))
        with self.assertRaises(SystemExit):
            worker._wifi_interruptible_sleep(0.01)

    def test_headless_device_commands_do_not_draw(self):
        app = self.app()
        app.fill_screen = Mock()
        with patch('jubilee.app.subprocess.run') as run:
            app.reboot()
            app.shut_down()
            self.assertEqual(run.call_count, 2)
        app.fill_screen.assert_not_called()

    def test_sprite_static_setter_invalidates_cached_transform(self):
        app = self.graphics()
        image = pygame.Surface((2, 2))
        image.fill('red')
        sprite = Sprite(static_image=image)
        sprite.bind(app)
        sprite.scale = 2
        sprite.set_image()
        image.fill('blue')
        sprite.set_static_image(image)
        self.assertEqual(sprite.set_image().get_at((0, 0))[:3], (0, 0, 255))

    def test_parse_script_ignores_indented_comments(self):
        app = self.app()
        (self.root / 'script.txt').write_text('  # mode=bad\nmode=good\n')
        app.init_script()
        self.assertEqual(app.script, [{'mode': 'good'}])

    def test_log_backup_does_not_overwrite_existing_archive(self):
        filename = str(self.root / 'custom.log')
        Log.info('first', filename=filename)
        Log.backup(filename=filename, backup_filename='same.txt')
        Log.info('second', filename=filename)
        Log.backup(filename=filename, backup_filename='same.txt')
        archives = list((self.root / 'logs').glob('same*.txt'))
        self.assertEqual(len(archives), 2)
        self.assertIn('first', (self.root / 'logs' / 'same.txt').read_text())
        self.assertNotIn('second', (self.root / 'logs' / 'same.txt').read_text())

    def test_shift_space_keeps_keyboard_buffer_consistent(self):
        app = self.graphics()
        app.config['keyboard_input'] = True
        app.held_keys = []
        app.start_keyboard_buffering()
        keys = {pygame.key.key_code('left shift'), pygame.key.key_code('space')}
        class Pressed:
            def __getitem__(self, key):
                return key in keys
        with patch('pygame.event.get', return_value=[]), patch('pygame.key.get_pressed', return_value=Pressed()):
            app.handle_events()
        self.assertEqual(app.keyboard_buffer, ' ')
        self.assertEqual(app.keyboard_buffer_chars, ['space'])

    def test_log_identifies_direct_caller(self):
        def fixture_caller():
            Log.info('caller fixture')
        fixture_caller()
        record = Log.parse((self.root / 'log.txt').read_text().strip())
        self.assertEqual(record['method'], 'fixture_caller')

    def test_worker_fatal_error_is_not_a_successful_exit(self):
        worker = self.worker()
        with patch.object(worker, 'start_worker', side_effect=RuntimeError('fatal fixture')), patch('jubilee.worker.signal.signal'):
            with self.assertRaisesRegex(RuntimeError, 'fatal fixture'):
                worker.run()

    def test_app_fatal_loop_error_runs_cleanup_and_propagates(self):
        app = self.app()
        app.process_period = 0.01
        app.on_process = Mock(side_effect=RuntimeError('fatal fixture'))
        app._cleanup = Mock()
        with self.assertRaisesRegex(RuntimeError, 'fatal fixture'):
            app.run()
        app._cleanup.assert_called_once()

    def test_exit_registration_uses_cleanup_not_system_exit(self):
        app = self.app()
        with patch('jubilee.app.atexit.register') as register, patch('jubilee.app.signal.signal'):
            app.register_exit_handlers()
        register.assert_called_once_with(app._cleanup)


if __name__ == '__main__':
    unittest.main()
