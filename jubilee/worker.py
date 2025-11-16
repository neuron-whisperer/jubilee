""" Jubilee Worker class. """

import datetime, json, multiprocessing, os, queue, sys, time
import __main__
from .misc import Config, Log

class Worker:
	""" Worker class. """

	config_defaults = {'headless': False,
		'screen_resolution': [320, 240], 'screen_scale': [[0, 319, -1], [0, 239, 1]],
		'app_process_fps': 20, 'app_draw_fps': 20, 'modal': True,
		'worker_process_fps': 20, 'worker_process_periodic_fps': 1,
		'persist_app_state': True, 'app_state_filename': 'app_state.txt',
		'app_state_start_filename': 'app_state_start.txt',
		'keyboard_input': True, 'log_rotation': 'daily', 'font_size': 14}

	def __init__(self, app_queue, worker_queue, config_manager=False, log_manager=False):
		self.name = 'Worker'
		self.app_queue = app_queue
		self.worker_queue = worker_queue
		self.config_manager = config_manager
		self.log_manager = log_manager
		self.worker_process = None
		self.base_path = os.path.dirname(os.path.realpath(__main__.__file__))
		self.config_filename = os.path.join(self.base_path, 'config.txt')
		self.config = Config.load(self.config_filename, defaults=self.config_defaults)
		self.config_date = None
		self.log_date = None
		if os.path.isfile(self.config_filename) is True:
			self.config_date = os.path.getmtime(self.config_filename)
		self.last_periodic = None
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
				loop_start = time.monotonic()
				self.receive_messages()

				# call main process function
				self.process()

				# call periodic process function occasionally
				process_periodic_fps = self.config.get('worker_process_periodic_fps', 1)
				if process_periodic_fps is not None:
					elapsed = time.monotonic() - (self.last_periodic or 0)
					if elapsed >= 1 / process_periodic_fps:
						self.last_periodic = (self.last_periodic or time.monotonic()) + 1.0 / process_periodic_fps
						if self.config_manager is True:
							self.manage_config()
						if self.log_manager is True:
							self.manage_log()
						self.process_periodic()

				# delay to next loop
				loop_time = time.monotonic() - loop_start
				delay = 1 / max(1, int(self.config.get('worker_process_fps', 10))) - loop_time
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
		if rotation == 'monthly':
			rotate = (datetime.datetime.now().strftime('%Y%m') != self.log_date.strftime('%Y%m'))
			log_format = '%Y%m'
		if rotation == 'hourly':
			rotate = (datetime.datetime.now().strftime('%Y%m') != self.log_date.strftime('%Y%m'))
			log_format = '%Y%m%d%H'
		if rotate is True:
			filename = f'log_{datetime.datetime.now().strftime(log_format)}.txt'
			Log.backup(backup_filename=filename)
			self.log_date = datetime.datetime.now()

	def process(self):
		""" Regular (high-frequency) worker processing. """

	def process_periodic(self):
		""" Periodic (low-frequency) worker processing. """

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
