""" Jubilee Worker class. """

import datetime, json, multiprocessing, os, platform, queue, subprocess, sys, time
import __main__
from .misc import Config, Log

class Worker:
	""" Worker class. """

	config_defaults = {'headless': False,
		'nosound': False,
		'screen_resolution': [320, 240],
		'screen_scale': [[0, 319, -1], [0, 239, 1]],
		'screen_rotation': 0,
		'app_process_fps': 20,
		'app_draw_fps': 20, 'modal': True,
		'worker_process_fps': 20,
		'worker_process_periodic_fps': 1,
		'persist_app_state': True,
		'app_state_filename': 'app_state.txt',
		'app_state_start_filename': 'app_state_start.txt',
		'keyboard_input': True,
		'log_rotation': 'daily',
		'font_size': 14,
		'font_size_desktop': 15,
		'wifi_watchdog': False,
		'wifi_ping_target': None,
		'wifi_ping_interval': 300,
		'wifi_interface': 'wlan0',
		'wifi_ping_count': 3,
		'wifi_ping_timeout': 5,
		'wifi_reboot_enabled': True,
		'wifi_reboot_daily_max': 3,
		'wifi_reboot_after_failures': 3
	}

	def __init__(self, app_queue, worker_queue, config_manager=False, log_manager=False, wifi_manager=False):
		self.name = 'Worker'
		self.app_queue = app_queue
		self.worker_queue = worker_queue
		self.config_manager = config_manager
		self.log_manager = log_manager
		self.wifi_manager = wifi_manager
		self.worker_process = None
		self.base_path = os.path.dirname(os.path.realpath(__main__.__file__))
		self.config_filename = os.path.join(self.base_path, 'config.txt')
		self.config = Config.load(self.config_filename, defaults=self.config_defaults)
		self.config_date = None
		self.log_date = None
		if os.path.isfile(self.config_filename) is True:
			self.config_date = os.path.getmtime(self.config_filename)
		self.last_periodic = None
		self.wifi_last_check = None
		self.wifi_consecutive_failures = 0
		self.wifi_reboot_count_today = 0
		self.wifi_reboot_date = None
		self.wifi_recovering = False
		self.wifi_connected = None
		self.wifi_boot_grace = True
		self.init()

		# start process
		self.worker_process = multiprocessing.Process(target=self.run)
		self.worker_process.daemon = True
		self.worker_process.start()

	def init(self):
		""" Worker-specific initializer that runs before the worker starts.
					State changes made here are visible to the App.
		"""

	def start_worker(self):
		""" Worker-specific initializer that runs at the start of run loop.
					State changes made here are *not* visible to the App.
		"""

	def run(self):
		""" Worker run loop. """

		try:
			Log.info('Starting')
			self.start_worker()

			while True:
				loop_start = time.time()
				self.receive_messages()

				# call main process function
				self.on_process()

				# call periodic process function occasionally
				process_periodic_fps = self.config.get('worker_process_periodic_fps', 1)
				if process_periodic_fps is not None:
					elapsed = time.time() - (self.last_periodic or 0)
					if elapsed >= 1 / process_periodic_fps:
						self.on_process_periodic()

				# delay to next loop
				loop_time = time.time() - loop_start
				delay = 1 / max(1, int(self.config.get('worker_process_fps', 20))) - loop_time
				if delay > 0:
					time.sleep(delay)

		except Exception as e:
			Log.error(e)

	def manage_config(self):
		""" Config manager. """

		if self.config_manager is False:
			return
		if os.path.isfile(self.config_filename) is False:
			self.config_date = None
			return
		config_date = os.path.getmtime(self.config_filename)
		if config_date != self.config_date:
			Log.info(f'Loading config ({self.config_date} != {config_date})')
			self.config_date = config_date
			self.config = Config.load(self.config_filename, defaults=self.config_defaults)
			self.send_updated_config()

	def manage_log(self):
		""" Log manager. """

		if self.log_manager is False:
			return
		if os.path.isfile(Log.get_filename()) is False:
			self.log_date = None
			return
		self.log_date = self.log_date or datetime.datetime.now()
		rotation = self.config.get('log_rotation', 'daily')
		rotate = False
		log_format = None
		if rotation == 'daily':
			rotate = (datetime.datetime.now().strftime('%Y%m%d') != self.log_date.strftime('%Y%m%d'))
			log_format = '%Y%m%d'
		elif rotation == 'monthly':
			rotate = (datetime.datetime.now().strftime('%Y%m') != self.log_date.strftime('%Y%m'))
			log_format = '%Y%m'
		elif rotation == 'hourly':
			rotate = (datetime.datetime.now().strftime('%Y%m%d%H') != self.log_date.strftime('%Y%m%d%H'))
			log_format = '%Y%m%d%H'
		else:
			Log.warning(f'Unrecognized log_rotation value: {rotation}')
			return
		if rotate is True:
			filename = f'log_{datetime.datetime.now().strftime(log_format)}.txt'
			Log.backup(backup_filename=filename)
			self.log_date = datetime.datetime.now()

	def manage_wifi(self):
		""" WiFi watchdog manager. Periodically checks connectivity and performs
				escalating recovery when WiFi is lost. Also serves as keepalive traffic
				to prevent the WiFi firmware from entering problematic idle states.
				Only operates on Linux. """

		if self.wifi_manager is False:
			return
		if platform.system() != 'Linux':
			return
		if self.config.get('wifi_watchdog', False) is not True:
			return

		# timer-based throttling: only run at configured interval
		now = time.time()
		interval = self.config.get('wifi_ping_interval', 300)
		if self.wifi_last_check is not None and (now - self.wifi_last_check) < interval:
			return
		self.wifi_last_check = now

		# boot grace: skip first check to allow network to come up
		if self.wifi_boot_grace is True:
			self.wifi_boot_grace = False
			Log.info('WiFi watchdog: boot grace period, skipping first check')
			return

		# guard against re-entry during recovery
		if self.wifi_recovering is True:
			return

		# resolve ping target
		target = self.config.get('wifi_ping_target')
		if target is None:
			target = self._wifi_detect_gateway()
		if target is None:
			Log.warning('WiFi watchdog: no ping target configured and could not detect gateway')
			return

		interface = self.config.get('wifi_interface', 'wlan0')
		ping_count = self.config.get('wifi_ping_count', 3)
		ping_timeout = self.config.get('wifi_ping_timeout', 5)

		# connectivity check (also serves as keepalive traffic)
		connected = self._wifi_ping(target, interface, ping_count, ping_timeout)

		if connected:
			if self.wifi_consecutive_failures > 0:
				Log.info(f'WiFi watchdog: connectivity restored after {self.wifi_consecutive_failures} failure(s)')
			self.wifi_consecutive_failures = 0
			if self.wifi_connected is not True:
				self.wifi_connected = True
				self._wifi_send_status(True, target)
			return

		# connectivity failed
		self.wifi_consecutive_failures += 1
		self.wifi_connected = False
		Log.warning(f'WiFi watchdog: connectivity check failed (consecutive: {self.wifi_consecutive_failures})')
		self._wifi_send_status(False, target)

		# begin escalating recovery
		self.wifi_recovering = True
		try:
			self._wifi_escalating_recovery(target, interface, ping_count, ping_timeout)
		finally:
			self.wifi_recovering = False

	def _wifi_detect_gateway(self):
		""" Detects default gateway IP address via ip route. """

		try:
			result = subprocess.run(
				['ip', 'route', 'show', 'default'],
				capture_output=True, text=True, timeout=5
			)
			if result.returncode == 0 and result.stdout.strip():
				parts = result.stdout.strip().split()
				if len(parts) >= 3 and parts[0] == 'default' and parts[1] == 'via':
					return parts[2]
		except Exception as e:
			Log.debug(f'WiFi watchdog: gateway detection failed: {e}')
		return None

	def _wifi_ping(self, target, interface, count, timeout):
		""" Pings target through interface. Returns True if reachable. """

		try:
			result = subprocess.run(
				['ping', '-c', str(count), '-W', str(timeout), '-I', interface, target],
				capture_output=True, timeout=count * timeout + 10
			)
			return result.returncode == 0
		except subprocess.TimeoutExpired:
			Log.warning('WiFi watchdog: ping subprocess timed out')
			return False
		except Exception as e:
			Log.error(f'WiFi watchdog: ping failed: {e}')
			return False

	def _wifi_send_status(self, connected, target):
		""" Sends WiFi status message to App. """

		self.send_message({
			'action': 'wifi status',
			'connected': connected,
			'target': target,
			'consecutive_failures': self.wifi_consecutive_failures
		})

	def _wifi_send_recovery(self, step):
		""" Sends WiFi recovery action message to App. """

		self.send_message({
			'action': 'wifi recovery',
			'step': step,
			'consecutive_failures': self.wifi_consecutive_failures
		})

	def _wifi_run_command(self, args, timeout=30, description='command'):
		""" Runs a subprocess command with timeout. Returns True on success. """

		try:
			result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
			if result.returncode != 0:
				Log.debug(f'WiFi watchdog: {description} returned {result.returncode}: {result.stderr.strip()}')
			return result.returncode == 0
		except subprocess.TimeoutExpired:
			Log.warning(f'WiFi watchdog: {description} timed out after {timeout}s')
			return False
		except Exception as e:
			Log.error(f'WiFi watchdog: {description} failed: {e}')
			return False

	def _wifi_interruptible_sleep(self, seconds):
		""" Sleeps for the specified duration while remaining responsive to exit messages. """

		end = time.time() + seconds
		while time.time() < end:
			try:
				message = self.app_queue.get_nowait()
				parsed = json.loads(message)
				if parsed.get('action') == 'exit':
					self.exit()
			except queue.Empty:
				pass
			remaining = end - time.time()
			if remaining > 0:
				time.sleep(min(remaining, 0.5))

	def _wifi_escalating_recovery(self, target, interface, ping_count, ping_timeout):
		""" Performs escalating WiFi recovery steps, remaining responsive to exit messages. """

		# step 1: nmcli device connect
		Log.info('WiFi watchdog: Step 1 - nmcli reconnect')
		self._wifi_run_command(
			['nmcli', 'device', 'connect', interface],
			timeout=30, description='nmcli reconnect'
		)
		self._wifi_send_recovery('nmcli reconnect')
		self._wifi_interruptible_sleep(15)
		if self._wifi_ping(target, interface, ping_count, ping_timeout):
			Log.info('WiFi watchdog: recovered via nmcli reconnect')
			self.wifi_consecutive_failures = 0
			self.wifi_connected = True
			self._wifi_send_status(True, target)
			return

		# step 2: interface restart (ip link down/up)
		Log.info('WiFi watchdog: Step 2 - interface restart')
		self._wifi_run_command(
			['ip', 'link', 'set', interface, 'down'],
			timeout=10, description='interface down'
		)
		self._wifi_interruptible_sleep(2)
		self._wifi_run_command(
			['ip', 'link', 'set', interface, 'up'],
			timeout=10, description='interface up'
		)
		self._wifi_send_recovery('interface restart')
		self._wifi_interruptible_sleep(15)
		if self._wifi_ping(target, interface, ping_count, ping_timeout):
			Log.info('WiFi watchdog: recovered via interface restart')
			self.wifi_consecutive_failures = 0
			self.wifi_connected = True
			self._wifi_send_status(True, target)
			return

		# step 3: restart NetworkManager
		Log.info('WiFi watchdog: Step 3 - NetworkManager restart')
		self._wifi_run_command(
			['systemctl', 'restart', 'NetworkManager'],
			timeout=30, description='NetworkManager restart'
		)
		self._wifi_send_recovery('NetworkManager restart')
		self._wifi_interruptible_sleep(20)
		if self._wifi_ping(target, interface, ping_count, ping_timeout):
			Log.info('WiFi watchdog: recovered via NetworkManager restart')
			self.wifi_consecutive_failures = 0
			self.wifi_connected = True
			self._wifi_send_status(True, target)
			return

		# step 4: reload WiFi driver (modprobe -r / modprobe brcmfmac)
		Log.info('WiFi watchdog: Step 4 - driver reload')
		self._wifi_run_command(
			['modprobe', '-r', 'brcmfmac'],
			timeout=10, description='modprobe remove'
		)
		self._wifi_interruptible_sleep(3)
		self._wifi_run_command(
			['modprobe', 'brcmfmac'],
			timeout=10, description='modprobe load'
		)
		self._wifi_interruptible_sleep(10)
		self._wifi_run_command(
			['systemctl', 'restart', 'NetworkManager'],
			timeout=30, description='NetworkManager restart after driver reload'
		)
		self._wifi_send_recovery('driver reload')
		self._wifi_interruptible_sleep(20)
		if self._wifi_ping(target, interface, ping_count, ping_timeout):
			Log.info('WiFi watchdog: recovered via driver reload')
			self.wifi_consecutive_failures = 0
			self.wifi_connected = True
			self._wifi_send_status(True, target)
			return

		# step 5: reboot (conditional)
		Log.error('WiFi watchdog: all recovery steps failed')
		reboot_enabled = self.config.get('wifi_reboot_enabled', True)
		reboot_daily_max = self.config.get('wifi_reboot_daily_max', 3)
		reboot_after_failures = self.config.get('wifi_reboot_after_failures', 3)

		if reboot_enabled is not True:
			Log.warning('WiFi watchdog: reboot disabled in config')
			return

		if self.wifi_consecutive_failures < reboot_after_failures:
			Log.info(f'WiFi watchdog: deferring reboot ({self.wifi_consecutive_failures}/{reboot_after_failures} consecutive failures)')
			return

		# check daily reboot cap
		today = time.strftime('%Y%m%d')
		if self.wifi_reboot_date != today:
			self.wifi_reboot_date = today
			self.wifi_reboot_count_today = 0

		if self.wifi_reboot_count_today >= reboot_daily_max:
			Log.error(f'WiFi watchdog: daily reboot limit ({reboot_daily_max}) reached, manual intervention required')
			return

		self.wifi_reboot_count_today += 1
		Log.warning(f'WiFi watchdog: initiating reboot ({self.wifi_reboot_count_today}/{reboot_daily_max} today)')
		self._wifi_send_recovery('reboot')
		self._wifi_interruptible_sleep(1)
		self._wifi_run_command(
			['sudo', 'shutdown', '-r', 'now'],
			timeout=5, description='reboot'
		)

	def on_process(self):
		""" Regular (high-frequency) worker processing event receiver.
				This merely wraps process() but is a placeholder for future
				functionality and for consistency with other event receivers. """

		self.process()

	def process(self):
		""" Regular (high-frequency) worker processing stub function. """

	def on_process_periodic(self):
		""" Periodic (low-frequency) worker processing event receiver. """

		self.last_periodic = time.time()
		if self.config_manager is True:
			self.manage_config()
		if self.log_manager is True:
			self.manage_log()
		if self.wifi_manager is True:
			self.manage_wifi()
		self.process_periodic()

	def process_periodic(self):
		""" Periodic (low-frequency) worker processing stub function. """

	def exit(self, code=0):
		sys.exit(code)

	# messaging with app

	def send_message(self, message: str|dict):
		""" Send a message to the app. """

		if isinstance(message, str):
			message = {'action': message}
		try:
			self.worker_queue.put(json.dumps(message, ensure_ascii=True))
		except Exception as e:
			Log.error(f'Failed to send message: {e}')

	def receive_messages(self):
		""" Receive messages from app. """

		while True:
			try:
				message = self.app_queue.get_nowait()
				self.process_message(json.loads(message), sender='App')
			except queue.Empty:
				return
			except Exception as e:
				Log.error(e)
				continue

	def process_message(self, message: dict, sender: str=None):
		""" Process a message from app. This method can be extended in subclass. """

		action = message.get('action')
		if action == 'update config':
			key = message.get('key')
			value = message.get('value')
			self.update_config(key, value)
		elif action == 'config updated':
			self.config = message.get('config', {})
		elif action == 'exit':
			self.exit()
		else:
			Log.warning(f'Received unknown message: {message}')

	def update_config(self, key, value):
		self.config[key] = value
		self.write_config()

	def write_config(self):
		Config.save(self.config, self.config_filename)
		self.config_date = os.path.getmtime(self.config_filename) if os.path.isfile(self.config_filename) else None
		self.send_updated_config()

	def send_updated_config(self):
		message = {'action': 'config updated', 'config': self.config}
		self.send_message(message)
