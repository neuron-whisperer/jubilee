""" Misc classes and functions. """

import datetime, json, os, shutil, socket, time
from enum import Enum
from hashlib import sha256
import __main__, random_user_agent.params, random_user_agent.user_agent, requests

class Config:
	""" Config class. """

	@classmethod
	def load(cls, filename: str=None, defaults: dict=None) -> dict:
		""" Loads config file.

				Args:
					filename:			Filename, or default filename (config.txt).
					defaults:			Dict of default values to be used for any not indicated in file.

				Returns:
					arg:					Config dict, or copy of default dict (or empty dict) on failure.
		"""

		return_dict = (defaults or {}).copy()
		try:
			filename = filename or cls.get_filename()
			if os.path.isfile(filename) is False:
				Log.info('Config', 'load', f'{filename} does not exist - using defaults')
			else:
				with open(filename, 'rt', encoding='UTF-8') as f:
					config = json.loads(f.read().strip())
					return_dict.update(config)
		except Exception as e:
			Log.error('Config', 'load', str(e))
		return return_dict

	@classmethod
	def save(cls, config: dict=None, filename: str=None):
		""" Saves config dict.

				Args:
					filename:			Filename, or default filename (config.txt).
					defaults:			Dict of default values to be used for any not indicated in file.
		"""

		filename = filename or cls.get_filename()
		with open(filename, 'wt', encoding='UTF-8') as f:
			f.write(json.dumps(config or {}))

	@staticmethod
	def get_filename() -> str:
		""" Gets default filename. """

		if hasattr(__main__, '__file__'):
			folder = os.path.dirname(os.path.realpath(__main__.__file__))
		else:		# the above instruction fails for spawned processes with no file.
			folder = os.getcwd()
		return os.path.join(folder, 'config.txt')

class Log:
	""" Log class. """

	levels = ['Error', 'Warning', 'Info', 'Debug']
	file_levels = {}					# all log files default to Info if not indicated here
	console_level = 'Warning'

	@classmethod
	def reset(cls, filename: str=None):
		""" Resets log at specified filename or default filename (log.txt). """

		filename = filename or cls.get_filename()
		if os.path.isfile(filename):
			os.unlink(filename)
		Log.info('Log', 'reset', 'Starting new log')

	@classmethod
	def backup(cls, filename: str=None, backup_folder: str=None) -> bool:
		""" Saves current log in backup folder.

				Args:
					filename:				Filename, or default filename (config.txt).
					backup_folder:	Folder for backups, or "logs" folder in same folder as log.

				Returns:
					arg:						Success indicator.
		"""

		try:
			filename = filename or cls.get_filename()
			if os.path.isfile(filename) is False:		# no log to backup
				return True
			backup_folder = backup_folder or os.path.join(os.path.dirname(filename), 'logs')
			if os.path.isdir(backup_folder) is False:
				os.mkdir(backup_folder)
				if os.path.isdir(backup_folder) is False:
					Log.warning('Log', 'backup', f'{backup_folder} does not exist and could not be created')
					return False
			current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S.%f')
			backup_filename = os.path.join(backup_folder, f'log_{current_time}.txt')
			shutil.move(filename, backup_filename)
			Log.info('Log', 'backup', f'Backed up previous log ({backup_filename}) and starting new log')
			return True

		except Exception as e:
			Log.error('Log', 'backup', str(e))
			return False

	@classmethod
	def _write(cls, class_name: str, function_name: str, level: str, message: str, filename: str=None):
		""" Writes (appends) to log at specified filename. Called by following methods.

				Args:
					class_name:			Class name.
					function_name:	Function name.
					level:					Error, Warning, Info, or Debug.
					message:				Log message.
					filename:				Log filename or default filename (log.txt).
		"""

		d = datetime.datetime.now()
		log_message = f'{d:%Y%m%d %H:%M:%S} {class_name:<15} {function_name:<20} {level:<7} {message}'
		filename = filename or cls.get_filename()
		file_level = cls.levels.index(cls.file_levels.get(filename, 'Info'))
		if cls.levels.index(level) <= file_level:
			with open(filename, 'at', encoding='UTF-8') as f:
				f.write(f'{log_message}\n')
		console_level = cls.levels.index(cls.console_level)
		if cls.levels.index(level) <= console_level:
			print(log_message)

	@classmethod
	def error(cls, class_name: str, function_name: str, message: str, filename: str=None):
		""" Writes error message to log. """

		Log._write(class_name, function_name, 'Error', message, filename)

	@classmethod
	def warning(cls, class_name: str, function_name: str, message: str, filename: str=None):
		""" Writes warning message to log. """

		Log._write(class_name, function_name, 'Warning', message, filename)

	@classmethod
	def info(cls, class_name: str, function_name: str, message: str, filename: str=None):
		""" Writes info message to log. """

		Log._write(class_name, function_name, 'Info', message, filename)

	@classmethod
	def debug(cls, class_name: str, function_name: str, message: str, filename: str=None):
		""" Writes debug message to log. """

		Log._write(class_name, function_name, 'Debug', message, filename)

	@classmethod
	def read(cls, filename: str=None):
		""" Read log at specified filename. """

		filename = filename or cls.get_filename()
		if os.path.isfile(filename) is False:
			return []
		with open(filename, 'rt', encoding='UTF-8') as f:
			log_lines = list(line.strip() for line in f.readlines())
		return log_lines

	@classmethod
	def get_modification_date(cls, filename: str=None):
		""" Get file modification date of specified filename. """

		filename = filename or cls.get_filename()
		return None if os.path.isfile(filename) is False else os.path.getmtime(filename)

	@staticmethod
	def get_filename() -> str:
		""" Returns default filename. """

		if hasattr(__main__, '__file__'):
			folder = os.path.dirname(os.path.realpath(__main__.__file__))
		else:		# the above instruction fails for spawned processes with no file.
			folder = os.getcwd()
		return os.path.join(folder, 'log.txt')

class Color(Enum):
	""" Color constants. """

	BLACK = (0, 0, 0)
	WHITE = (255, 255, 255)
	GRAY = (127, 127, 127)
	DARK_GRAY = (64, 64, 64)
	LIGHT_GRAY = (196, 196, 196)
	RED = (255, 0, 0)
	DARK_RED = (127, 0, 0)
	LIGHT_RED = (255, 64, 64)
	GREEN = (0, 255, 0)
	DARK_GREEN = (0, 127, 0)
	LIGHT_GREEN = (64, 255, 64)
	BLUE = (0, 0, 255)
	DARK_BLUE = (0, 0, 127)
	LIGHT_BLUE = (64, 64, 255)
	ORANGE = (255, 165, 0)
	PINK = (255, 192, 203)
	PURPLE = (128, 0, 128)
	CYAN = (0, 255, 255)
	MAGENTA = (255, 0, 255)
	YELLOW = (238, 210, 2)
	BROWN = (101, 67, 33)

class Misc:
	""" Misc class for misc functions. """

	key_names = ('backspace', 'tab', 'return', 'escape', 'space', '!', '"', '#', '$', '%', '&', '\'', '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'delete', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'insert' ,'home', 'end', 'right', 'left', 'up', 'down', 'left ctrl', 'left shift', 'right ctrl', 'right shift')
	key_symbols = {k: k for k in 'abcdefghijklmnopqrstuvwxyz`1234567890-=~!@#$%^&*()_+[]\\{}|;\':",./<>?'}
	key_symbols['space'] = ' '
	key_shift_symbols = {'a': 'A', 'b': 'B', 'c': 'C', 'd': 'D', 'e': 'E', 'f': 'F', 'g': 'G', 'h': 'H', 'i': 'I', 'j': 'J', 'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N', 'o': 'O', 'p': 'P', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T', 'u': 'U', 'v': 'V', 'w': 'W', 'x': 'X', 'y': 'Y', 'z': 'Z', '1': '!', '2': '@', '3': '#', '4': '$', '5': '%', '6': '^', '7': '&', '8': '*', '9': '(', '0': ')', '`': '~', '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|', ';': ':', '\'': '"', ',': '<', '.': '>', '/': '?'}

	null_date = datetime.datetime.utcfromtimestamp(0)
	user_agent = None

	@staticmethod
	def choose_user_agent():
		""" Chooses a pouplar user agent. """

		p=[random_user_agent.params.Popularity.POPULAR.value]
		return random_user_agent.user_agent.UserAgent(popularity=p).get_random_user_agent()

	@staticmethod
	def calculate_hashcode(data: dict) -> str:
		""" Calculates a sha256 hashcode for a JSON object. """

		json_string = json.dumps(data, separators=(',', ':')).encode('utf-8')
		hashcode = sha256(json_string).hexdigest()
		return hashcode

	@classmethod
	def http_request(cls, url: str, method: str=None, headers: dict=None,
		data: dict=None, password: str=None, timeout: int=30,
		randomize_user_agent: bool=False, timestamp: str=None) -> (int|None, str):
		""" Sends an HTTP GET or POST request via requests.

				Args:
					url:					URL.
					method:				GET or POST. Defaults to POST if data is included, or GET if not.
					headers:			Extra headers to specify in request.
					data:					Dictionary of data to transmit as JSON payload in POST request.
					password:			password for signing URL.
					timeout:			timeout in seconds.
					randomize_user_agent:	Randomize user agent. False = use existing popular agent.
					timestamp:		Optional timestamp to append to URL before hashing.

				Returns:
					arg1:					HTTP status code, or None on failure.
					arg2:					Signed URL, or error message on failure.
		"""

		if password is not None:
			result, message = cls.sign_request(url, password, timestamp)
			if result is False:
				return (False, f'Error signing request: {message}')
			url = message
		headers = headers or {}
		if cls.user_agent is None:
			cls.user_agent = cls.choose_user_agent()
		user_agent = cls.choose_user_agent() if randomize_user_agent else cls.user_agent
		status_code = None
		method = 'POST' if data is not None else (method or 'GET')
		try:
			if method.upper() == 'GET':
				headers = {'User-Agent': user_agent}
				response = requests.get(url, headers=headers, timeout=timeout)
				status_code = response.status_code
			else:
				headers = {'User-Agent': user_agent, 'Content-type': 'application/json'}
				response = requests.post(url, headers=headers, json=data, timeout=timeout)
				status_code = response.status_code
		except Exception as e:
			return (None, f'Exception on HTTP request: {e}')
		return (status_code, response)

	@staticmethod
	def sign_request(url: str, password: str, timestamp: int=None) -> (bool, str):
		""" Generates hashcode-signed URLs.

				Args:
					url:					url.
					password:			password for signing URL.
					timestamp:		Optional timestamp to append to URL before hashing.

				Returns:
					arg1:					Success indicator.
					arg2:					Signed URL, or error message on failure.
		"""

		if url is None:
			return (False, 'URL not specified')
		if password is None:
			return (False, 'Password not specified')
		timestamp = int(time.time()) if timestamp is None else int(timestamp)
		url = f'{url}&ts={timestamp}'
		request = password + url
		signature = sha256(request.encode('utf-8')).hexdigest()
		return (True, url + '&hash=' + signature)

	@classmethod
	def get_local_ip_address(cls) -> (bool, str):
		""" Determines local IP address.

				Returns:
					arg1:					Success indicator.
					arg2:					IP address, or error message on failure.
		"""

		with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
			s.settimeout(0)
			try:
				s.connect(('10.254.254.254', 1))			# loopback address
				return (True, s.getsockname()[0])
			except Exception as e:
				return (False, f'Exception: {e}')

	@classmethod
	def test_internet(cls) -> (bool, float|str):
		""" Tests Internet access by querying google.com.

				Returns:
					arg1:					Success indicator.
					arg2:					request duration (in seconds), or error message on failure.
		"""

		start = time.time()
		status_code, response = cls.http_request('https://google.com')
		success = (status_code == 200)
		response = time.time() if status_code == 200 else response
		return (success, response)

	@staticmethod
	def get_color(color: str|int|tuple, color_scale: float=None) -> tuple|None:
		""" Returns a color.

				Args:
					color:				String (case-insensitive), enum (e.g.: Color.WHITE),
													or custom tuple (e.g.: (255, 255, 0)).
					color_scale:	Optional value to scale color toward black (0.0-1.0).

				Returns:
					arg:					RGB tuple, or None on error.
		"""

		if isinstance(color, tuple):
			color_tuple = color
		elif isinstance(color, str):
			matches = list(c for c in Color if str(c).replace('Color.', '').lower() == color.lower())
			if len(matches) != 1:
				return None
			color_tuple = matches[0].value if len(matches) == 1 else Color.WHITE.value
		else:
			if color not in dir(Color):
				return None
			color_tuple = Color[color].value
		return tuple(int(c * color_scale) for c in color_tuple) if color_scale else color_tuple
