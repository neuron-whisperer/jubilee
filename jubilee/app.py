""" Jubilee App class. """

import atexit, json, math, multiprocessing, os, platform, queue, signal, subprocess, sys, time
import __main__, numpy, pygame
from pygame import Rect
from pygame.font import Font
from pygame.surface import Surface
from pygame.mixer import Sound, Channel
from .worker import Worker
from .mode import Mode
from .base_classes import Animation, AnimationFrame
from .misc import Config, Log, Color, Misc

class App:

	""" App class for app framework. """

	def __init__(self, workers=None):

		# single-instance check
		if self.check_running_process():
			print('Another instance of this script is already running.')
			sys.exit(0)

		# start log
		Log.backup()
		Log.info('Starting')

		# enable debug output if set
		if 'debug' in sys.argv:
			Log.set_file_level(Log.DEBUG)
		if 'console_debug' in sys.argv:
			Log.set_console_level(Log.DEBUG)

		# load config
		self.base_path = os.path.dirname(os.path.realpath(__main__.__file__))
		self.config_filename = os.path.join(self.base_path, 'config.txt')
		self.config = Config.load(self.config_filename, defaults=Worker.config_defaults)

		# init pygame
		self.headless = self.config.get('headless', False)
		if self.headless is True:
			Log.info('Running in headless mode')
			os.environ['SDL_VIDEODRIVER'] = 'dummy'
		try:
			pygame.init()
		except Exception as e:
			Log.error(f'Exception during pygame.init(): {e}')
			sys.exit(1)

		self.process_last = 0										# time of last process method
		self.process_period = 1.0 / max(1, int(self.config.get('app_process_fps', 10)))

		if self.headless is False:

			# initialize window
			self.screen_width, self.screen_height = self.config.get('screen_resolution', pygame.display.list_modes()[0])
			self.screen_center = int(self.screen_width / 2)
			self.screen_middle = int(self.screen_height / 2)
			if platform.uname().system == 'Darwin':
				pygame.mouse.set_visible(True)
				flags = pygame.DOUBLEBUF
			else:
				pygame.mouse.set_visible(False)
				flags = pygame.DOUBLEBUF | pygame.FULLSCREEN | pygame.NOFRAME
			size = (self.screen_width, self.screen_height)
			try:
				self.window = pygame.display.set_mode(size=size, flags=flags, display=0, vsync=1)
			except:
				self.window = pygame.display.set_mode(size=size, flags=flags, display=0)

			# fade overlay
			self.display_fade_overlay = Surface(size=size).convert_alpha()
			self.display_fade_steps = None
			self.display_fade_step = None
			self.display_fade_end_mode = None
			self.display_fade_end_parameters = None

			# drawing constants
			self.margin = 5													# margin between content and screen edge (px)
			self.button_margin = 3									# margin between buttons (px)
			self.button_border = 1									# width of button border (px)
			self.underscore_position = 7						# pixels under text for underscores
			self.popover_message = None							# current popover message
			self.popover_steps = 50									# steps
			self.popover_step = 0										# current popover step
			self.draw_last = 0											# time of last draw method
			self.fps_count = 0											# FPS count for last second
			self.fps_counting = 0										# FPS count for current second
			self.fps_time = int(time.monotonic())		# time of current FPS count
			self.draw_period = 1.0 / max(1, int(self.config.get('app_draw_fps', 10)))

			# fonts
			self.standard_font_size = int(self.config.get('font_size', 11))
			# use a different default font size on MacOS
			if platform.uname().system == 'Darwin':
				self.standard_font_size = 15
			self.font_list = pygame.font.get_fonts()
			self.standard_font_name = None
			self.standard_font = None
			self.set_standard_font()
			self.display_fps = self.config.get('display_fps', False)

		# fetch initial events
		# this is necessary because if MacOS receives a mouse-click on the window before
		# calling events the first time, subsequent click events are often dropped.
		pygame.event.get()

		# add workers
		self.workers = {}
		if workers is not None:
			self.add_workers(workers)

		# modes
		self.modes = {}
		self.mode = None

		# app state
		self.app_state = {}
		self.app_state_filename = self.config.get('app_state_filename', 'app_state.txt')
		self.app_state_start_filename = self.config.get('app_state_start_filename', 'app_state_start.txt')
		self.persist_app_state = self.config.get('persist_app_state', True)
		if self.persist_app_state is True:
			self.load_app_state()

		# script information
		self.script = None

		# images
		self.images_path = os.path.join(self.base_path, 'images')
		self.images, self.animations = self.load_images(self.images_path)

		# sounds
		self.sounds_path = os.path.join(self.base_path, 'sounds')
		self.sounds = self.load_sounds(self.sounds_path)
		self.sound_volume = 100
		self.sound_retainer = None
		if self.config.get('sound_retainer', False) is True:
			self.set_sound_retainer(True)

		# music
		self.music_path = os.path.join(self.base_path, 'music')
		self.music_volume = 100
		self.music_fade_steps = None
		self.music_fade_step = None

		# pointer input
		self.pointer = None
		if self.headless is False:
			if platform.uname().system == 'Darwin':
				from .mouse_interface import MouseInterface
				self.pointer = MouseInterface()
			elif self.config.get('pointer_input', True) is True:
				from .touch_interface import TouchInterface
				scale = self.config.get('screen_scale', [[0, 319, -1], [0, 239, 1]])
				swap_axes = self.config.get('swap_axes', False)
				self.pointer = TouchInterface(resolution=(self.screen_width, self.screen_height), scale=scale, swap_axes=swap_axes)
			self.pointer_input_last = time.monotonic()			# time of last pointer input
			self.pointer_input_debouncing = 100							# time between pointer inputs (ms)

		# key input
		self.new_keys = []														# all keys newly pressed this frame
		self.held_keys = []														# all keys currently pressed
		self.keyboard_buffering = False								# whether key input is being buffered
		self.keyboard_buffer = ''
		self.keyboard_buffer_chars = []

		# initialize script
		self.init_script()

		# app-specific initialization
		self.init()

	def init(self):
		""" App-specific initialization. """

	def run(self):
		""" Main run loop for application. """

		try:
			while True:
				if time.monotonic() - self.process_last >= self.process_period:
					self.process()
				if self.headless is False:
					if time.monotonic() - self.draw_last >= self.draw_period:
						self.draw()
				process_delay = self.process_period - (time.monotonic() - self.process_last)
				draw_delay = 1 if self.headless is True else self.draw_period - (time.monotonic() - self.draw_last)
				delay = min(process_delay, draw_delay)
				if delay > 0:
					time.sleep(delay)
		except Exception as e:
			Log.error(e)

	def add_worker(self, worker: type):
		""" Adds instance of worker class to app. """

		app_queue = multiprocessing.Queue()					# queue to send messages from app
		worker_queue = multiprocessing.Queue()			# queue to receive messages from worker
		config_manager = (len(self.workers) == 0)		# first worker manages config
		log_manager = (len(self.workers) == 0)			# first worker also manages log rotation
		if len(self.workers) > 0:
			time.sleep(1)															# delay to allow previous worker to start
		worker_instance = worker(app_queue, worker_queue, config_manager, log_manager)
		self.workers[worker_instance.name] = worker_instance

	def add_workers(self, workers: list):
		""" Adds workers. """

		for worker in workers:
			self.add_worker(worker)

	def add_mode(self, mode: type|Mode):
		""" Adds mode to mode list.

				Args:
					mode:								Mode name or subclass.
		"""

		if isinstance(mode, type):		# if mode is provided as a class, instantiate it
			mode = mode()
		mode.app = self
		mode.init()
		mode.load_resources()
		self.modes[mode.name] = mode
		if len(self.modes) == 1:
			self.set_mode(mode.name)

	def add_modes(self, modes: list):
		""" Adds modes. """

		for mode in modes:
			self.add_mode(mode)

	def set_mode(self, mode: str|Mode, mode_parameters: dict=None):
		""" Sets mode.

				Args:
					mode:								Mode name or object.
					mode_parameters:		Parameters for enter() for new mode.
		"""

		# insert previous_mode into mode_parameters
		mode_parameters = mode_parameters or {}
		mode_parameters['previous_mode'] = None if self.mode is None else self.mode.name

		# switch from mode
		if self.mode is not None:
			self.mode.on_exit()

		# switch to mode
		new_mode = self.modes.get(mode) if isinstance(mode, str) else mode
		if new_mode is None:
			Log.error(f'No known mode named {mode}')
			return
		self.mode = new_mode
		self.mode.on_enter(mode_parameters=mode_parameters)
		submode = mode_parameters.get('submode')
		if submode is not None:
			self.mode.set_submode(submode)

	def process(self):
		""" Main app process method. Calls current mode process method. """

		if self.mode is None:
			return

		try:
			self.process_last = time.monotonic()
			self.handle_events()
			report_threshold = 0.2		# report processing if more than 0.2 seconds
	
			start = time.monotonic()
			if self.config.get('modal') is True:			# only process current mdoe
				if self.mode is None:
					return
				try:
					self.mode.on_process()
				except Exception as e:
					Log.error(f'Error processing mode {self.mode.name}: {e}')
				duration = time.monotonic() - start
				if duration > report_threshold:
					Log.info(f'Processing mode {self.mode.name} took {duration:.3f}')
			else:																			# process all modes
				mode_times = {}
				for mode in self.modes.values():
					mode_start = time.monotonic()
					try:
						mode.on_process()
					except Exception as e:
						Log.error(f'Error processing mode {mode.name}: {e}')
					mode_times[mode.name] = f'{time.monotonic() - mode_start:.3f}'
				duration = time.monotonic() - start
				if duration > report_threshold:
					Log.info(f'Processing modes took {duration:.3f} s')
					Log.info(f'  Mode times: {mode_times}')
		except Exception as e:
			Log.error(e)

	def draw(self):
		""" Main draw method. Calls current mode draw method and
				then draws controls and popover message. """

		self.draw_last = time.monotonic()

		try:

			self.fps_counting += 1
			current_time = int(time.monotonic())
			if current_time != self.fps_time:
				self.fps_time = current_time
				self.fps_count = self.fps_counting
				self.fps_counting = 0

			# draw mode
			if self.mode is not None:
				try:
					self.mode.on_draw()
				except Exception as e:
					Log.error(f'Error drawing mode {self.mode.name}: {e}')

			# draw popover
			if self.popover_message is not None and self.popover_steps is not None:
				if self.popover_step < self.popover_steps:
					self.popover_step += 1
					width = min(int(self.screen_width * 0.8), 300)
					height = 100
					left = int(self.screen_center - width / 2)
					top = self.screen_middle - 50
					self.fill_rect(left, top, width, height, color='black')
					self.draw_rect(left, top, width, height, color='white')
					self.center_text(self.popover_message, color='white')
				else:
					self.popover_message = None
					self.popover_steps = None
					self.popover_step = None

			if self.display_fps:
				self.draw_text(str(self.fps_count), 20, 20, color='white', font=self.standard_font_sizes[18])

			# finalize display
			self.apply_display_fade()
			pygame.display.flip()

			# apply music fade
			self.apply_music_fade()

		except Exception as e:
			Log.error(e)

	def handle_events(self):
		""" Handle pygame events and messages from worker. """

		events = list(pygame.event.get())
		if self.pointer:
			self.pointer.clicked = False
		for event in events:
			if event.type == pygame.QUIT:
				self.exit(0)
			elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and self.pointer is not None:
				if self.pointer.handle_event(event):
					self.on_click(self.pointer.x, self.pointer.y)

		if self.pointer is not None:

			# detect events for touch pointer (via polling)
			if self.pointer.detect_events():
				# special function for click events to handle debouncing and mode input
				self.on_click(self.pointer.x, self.pointer.y)

			# respond to hold and release events, and then update state
			if self.pointer.down is True:
				if self.pointer.held is True:		# held
					self.mode.on_hold()
			elif self.pointer.held is True:		# released
				self.mode.on_release()

			# set state for next time
			self.pointer.held = self.pointer.down

		# register keyboard input
		if self.config.get('keyboard_input', True) is True:
			pressed_keys = pygame.key.get_pressed()
			held_keys = list(k for k in Misc.key_names if pressed_keys[pygame.key.key_code(k)])
			self.new_keys = list(k for k in held_keys if k not in self.held_keys)
			self.held_keys = held_keys

			# update keyboard buffer
			if self.keyboard_buffering is True:
				for k in self.new_keys:
					if k == 'backspace':
						if len(self.keyboard_buffer_chars) > 0:
							self.keyboard_buffer_chars = self.keyboard_buffer_chars[:-1]
							self.keyboard_buffer = self.keyboard_buffer[:-1]
					elif k not in ('return', 'left shift', 'left ctrl', 'right shift', 'right ctrl', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'insert' ,'home', 'end', 'right', 'left', 'up', 'down', 'delete', 'escape'):
						self.keyboard_buffer_chars.append(k)
						if any(shift in self.held_keys for shift in ['left shift', 'right shift']):
							if k in Misc.key_shift_symbols:
								self.keyboard_buffer += Misc.key_shift_symbols[k]
						elif k in Misc.key_symbols:
							self.keyboard_buffer += Misc.key_symbols[k]

		self.receive_messages()

	# messaging with workers

	def send_message(self, message: str|dict, worker_name: str=None):
		""" Sends a message to worker, or first worker by default. """

		if len(self.workers) == 0:
			Log.error('No workers')
			return
		if worker_name is not None and worker_name not in self.workers:
			Log.error(f'No known worker {worker_name}')
			return
		if isinstance(message, str):
			message = {'action': message}
		first_worker = self.workers[list(self.workers.keys())[0]]
		worker = self.workers.get(worker_name, first_worker)
		try:
			worker.app_queue.put(json.dumps(message))
		except Exception as e:
			Log.error(e)

	def receive_messages(self):
		""" Receives messages from workers and calls process_message() on each. """

		for worker in self.workers.values():
			try:
				while True:
					message = worker.worker_queue.get_nowait()
					self.process_message(json.loads(message), sender=worker.name)
			except queue.Empty:
				continue
			except Exception as e:
				Log.error(e)
				continue

	def process_message(self, message: dict, sender: str=None):
		""" Processes a message from worker. """

		action = message.get('action')
		if action == 'exit':
			self.exit(0)
		elif action == 'config updated':
			self.config = message.get('config', {})
			for name in (name for name, worker in self.workers.items() if worker.config_manager is False):
				self.send_message(message, name)
			if self.headless is False:
				self.set_standard_font()
		else:
			Log.error(f'Received unknown message: {message}')

	# low-level graphics methods

	def flip(self):
		""" Flips display buffers. This occurs automatically at the end of draw(). """

		pygame.display.flip()

	def fill_screen(self, color: str|int|tuple='white'):
		""" Fills screen with indicated color. """

		self.fill_color(color, dest=self.window)

	def fill_color(self, color: str|int|tuple='white', dest: Surface=None):
		""" Fills surface with indicated color. """

		dest = dest or self.window
		color = Misc.get_color(color)
		size = dest.get_size()
		dest.fill(color, (0, 0, size[0], size[1]))

	def fill_static(self, dest: Surface=None):
		""" Fills surface with white-noise static. """

		dest = dest or self.window
		pygame.surfarray.blit_array(dest, numpy.random.randint(255, size=dest.get_size()) * 65793)

	def draw_text(self, text: str, x: int|float, y: int|float, color='white', font: str|Font=None, alignment: str='left', dest: Surface=None):
		""" Draws text. Font can be either a pygame.font.SysFont, a font name (default size),
				or None for default font. """

		dest = dest or self.window
		if isinstance(font, Font) is False:
			font = pygame.font.SysFont(font, self.standard_font_size) if font in self.font_list else self.standard_font
		color = Misc.get_color(color)
		surface = font.render(text, True, color)
		(width, height) = surface.get_size()
		top = int(y - height / 2)
		left = int(x)
		if alignment == 'center':
			left = int(x - width / 2)
		elif alignment == 'right':
			left = int(x - width)
		dest.blit(surface, (left, top))

	def center_text(self, text: str, y: int|float=None, color='white', font: str|Font=None, dest: Surface=None):
		""" Draws horizontally (and, optionally, vertically) centered text. """

		dest = dest or self.window
		x = dest.get_size()[0] / 2
		y = dest.get_size()[1] / 2 if y is None else y
		self.draw_text(text, x, y, color=color, font=font, alignment='center', dest=dest)

	def get_text_size(self, text: str, font: str|Font=None):
		""" Gets size of rendered text. Font can be either a pygame.font.SysFont, a font name
				(default size), or None for default font. """

		if isinstance(font, Font) is False:
			font = pygame.font.SysFont(font, self.standard_font_size) if font in self.font_list else self.standard_font
		surface = font.render(text, True, Color.WHITE.value)
		(width, height) = surface.get_size()
		return (width, height)

	def draw_pixel(self, x: int|float, y: int|float, color='white', dest: Surface=None):
		""" Draw pixel at coordinate. """

		dest = dest or self.window
		color = Misc.get_color(color)
		dest.set_at((int(x), int(y)), color)

	def draw_line(self, x1: int|float, y1: int|float, x2: int|float, y2: int|float, width: int|float=1, color='white', dest: Surface=None):
		""" Draws pixel at coordinate. """

		dest = dest or self.window
		color = Misc.get_color(color)
		pygame.draw.line(dest, color, (x1, y1), (x2, y2), width)

	def draw_rect(self, left: int|float, top: int|float, width: int|float, height: int|float, line_width: int|float=1, color='white', dest: Surface=None):
		""" Draws rect at coordinates. """

		dest = dest or self.window
		color = Misc.get_color(color)
		pygame.draw.rect(dest, color, (left, top, width, height), line_width)

	def fill_rect(self, left: int|float, top: int|float, width: int|float, height: int|float, color='white', dest: Surface=None):
		""" Fills pixel at coordinates. """

		dest = dest or self.window
		color = Misc.get_color(color)
		dest.fill(color, (left, top, width, height))

	def draw_polygon(self, coordinates: list, width: int|float=1, color='white', dest: Surface=None):
		""" Draws polygon at coordinates. """

		dest = dest or self.window
		color = Misc.get_color(color)
		pygame.draw.polygon(dest, color, coordinates, width=width)

	def draw_circle(self, x: int|float, y: int|float, radius: int|float=1, width: int|float=1, color='white', dest: Surface=None):
		""" Draws circle centered at coordinate. """

		dest = dest or self.window
		color = Misc.get_color(color)
		pygame.draw.circle(dest, color, (x, y), radius, width=width)

	def fill_circle(self, x: int|float, y: int|float, radius: int|float=1, color='white', dest: Surface=None):
		""" Fills circle centered at coordinate. """

		self.draw_circle(x, y, radius=radius, width=0, color=color, dest=dest)

	def draw_arc(self, x: int|float, y: int|float, width: int|float, height: int|float, start_angle: int|float, stop_angle: int|float, line_width: int|float=1, color='white', dest: Surface=None):
		""" Draws arc at x/y coordinate from start_angle (degrees) to stop_angle (degrees). """

		dest = dest or self.window
		color = Misc.get_color(color)
		pygame.draw.arc(dest, color, Rect(x, y, width, height), start_angle * math.pi / 180, stop_angle * math.pi / 180, width = line_width)

	# surface and image methods

	def create_surface(self, x: int|float, y: int|float, color='black', alpha_blend: bool=False, flags: int=None) -> Surface:
		""" Creates a new pygame surface with given dimensions.
				Alpha blend specifies a surface with alpha transparency. """

		x = int(x); y = int(y); flags=flags or 0
		if alpha_blend:
			flags = flags | pygame.SRCALPHA
		surface = Surface((x, y), flags=flags)
		surface = surface.convert_alpha() if alpha_blend else surface.convert()
		if color is not None:
			c = Misc.get_color(color)
			surface.fill(c, (0, 0, x, y))
		return surface

	def copy_surface(self, surface: Surface):
		""" Returns a copy of the surface. """

		return surface.copy()

	def load_images(self, path: str) -> (dict, dict):
		""" Loads images and animations from path. Called here and also in Mode. """

		images = {}; animations = {}
		image_types = ['.jpg', '.jpeg', '.png', '.bmp']
		if os.path.isdir(path) is False:
			return images, animations

		# load images
		for filename in (f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in image_types):
			full_filename = os.path.join(path, filename)
			name = os.path.splitext(filename)[0].lower()
			try:
				image = self.load_image(full_filename)
				if image is not None:
					images[name] = image
				else:
					Log.error(f'Image {full_filename} failed to load')
			except Exception as e:
				Log.error(f'Exception loading image {full_filename}: {e}')

		# load animations
		for animation_name in list(d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))):
			animation = Animation()
			files = sorted(f for f in os.listdir(os.path.join(path, animation_name)) if os.path.splitext(f)[1].lower() in image_types)
			for filename in files:
				image = self.load_image(os.path.join(path, animation_name, filename))
				if image is not None:
					name = os.path.splitext(filename)[0].lower()
					animation.frames.append(AnimationFrame(name, image))
			if len(animation.frames) == 0:
				continue
			# define sequences
			for i, frame in enumerate(animation.frames):
				if '_' in frame.name:
					name, _ = frame.name.rsplit('_', 1)
					animation.sequences.setdefault(name, [])
					animation.sequences[name].append(i)
				else:
					animation.sequences[frame.name] = [i]
			animations[animation_name.lower()] = animation

		return images, animations

	def load_image(self, filename: str, alpha_blend: bool=False) -> Surface|None:
		""" Loads image at filename. Specify Alpha Blend if the image has an alpha channel. """

		if os.path.isfile(filename) is False:
			Log.error(f'No image named {filename}')
			return None
		try:
			alpha_blend = alpha_blend or (os.path.splitext(filename)[1].lower() == '.png')
			image = pygame.image.load(filename)
			image = image.convert_alpha() if alpha_blend else image.convert()
			return image
		except Exception as e:
			Log.error(e)
			return None

	def get_image(self, image: str|Surface) -> Surface|None:
		""" Finds an image by name or path. """

		if isinstance(image, Surface):
			return image
		if isinstance(image, str) is False:
			Log.error(f'Could not identify image of type {type(image)}')
			return None
		# in order: check mode image library, then app image library, and lastly try to load
		i = self.mode.images.get(image) if self.mode is not None else None
		i = i or self.images.get(image)
		i = i or self.load_image(image)
		return i

	def blit(self, image: str|Surface, x: int|float, y: int|float, position: str=None, scale: int|float|tuple=None, area: Rect=None, flags: int=None, dest: Surface=None):
		""" Blits image to dest at coordinates.
				Optionally scale by factor or to (width, height).
				Optionally specify an area of the source image (post-scaling).
				Position can be topleft (default), center, or bottom.
				Surfaces that have an alpha channel are blitted with pygame.BLEND_ALPHA_SDL2. """

		i = self.get_image(image)
		if i is None:
			Log.error(f'Could not get image of type {image}')
			return
		flags=flags or 0
		dest = dest or self.window
		if i.get_alpha() is not None:
			flags = flags | pygame.BLEND_ALPHA_SDL2
		try:
			if scale is not None:
				if isinstance(scale, tuple):
					i = self.scale_image(i, scale[0], scale[1])
				else:
					i = self.scale_image(i, scale)
			if position == 'center':
				size = i.get_size()
				x -= size[0] / 2; y -= size[1] / 2
			elif position == 'bottom':
				size = i.get_size()
				x -= size[0] / 2; y -= size[1]
			dest.blit(i, (x, y), area=area, special_flags=flags)
		except Exception as e:
			Log.error(e)

	def scale_image(self, image: str|Surface, x_scale: int|float, y_scale: int|float=None) -> Surface|None:
		""" Scales image. Scale proportionally (omit y_scale) or disproportionately. """

		i = self.get_image(image)
		if i is None:
			Log.error(f'Could not get image of type {image}')
			return None
		y_scale = y_scale or x_scale
		return pygame.transform.scale(i, (int(x_scale), int(y_scale)))

	def flip_image(self, image: str|Surface, horizontal: bool=False, vertical: bool=False) -> Surface|None:
		""" Flips image. """

		i = self.get_image(image)
		if i is None:
			Log.error(f'Could not get image of type {image}')
			return None
		return pygame.transform.flip(i, horizontal, vertical)

	def rotate_image(self, image: str|Surface, degrees: int|float) -> Surface|None:
		""" Rotates image. """

		i = self.get_image(image)
		if i is None:
			Log.error(f'Could not get image of type {image}')
			return None
		return pygame.transform.rotate(i, degrees)

	def shift_image_hue(self, image: str|Surface, delta: int|float) -> Surface|None:
		""" Shifts image hue by a delta value (range 0-360). """

		i = self.get_image(image)
		if i is None:
			Log.error(f'Could not get image of type {image}')
			return None
		i = i.copy()			# make a copy of the image to edit pixels in place
		pixels = pygame.PixelArray(i)
		for x in range(i.get_width()):
			for y in range(i.get_height()):
				color = i.unmap_rgb(pixels[x][y])
				h, s, l, a = color.hsla
				color.hsla = (int(h) + int(delta)) % 360, int(s), int(l), int(a)
				pixels[x][y] = color
		del pixels
		return i

	def set_popover(self, message: str, steps: int=None):
		""" Creates a popover message. """

		self.popover_message = message
		self.popover_steps = steps if steps is not None else int(self.config.get('app_draw_fps', 10) * 0.75)
		self.popover_step = 0

	def start_display_fade(self, steps: int=None, color='black', end_mode: str=None, end_parameters: dict=None):
		""" Sets fade-in or fade-out.
				Positive steps = fade in from solid and increase over specified steps.
				Negative steps = fade out to solid over specified steps.
				Optionally, call set_mode with the specified mode and parameters at end of fade.
				None or zero steps will cancel current fade.
		"""

		if steps is None or steps == 0:
			self.display_fade_steps = None
			self.display_fade_step = None
			self.display_fade_end_mode = None
			self.display_fade_end_parameters = None
			return
		c = Misc.get_color(color)
		self.display_fade_overlay.fill(c, (0, 0, self.screen_width, self.screen_height))
		self.display_fade_steps = steps
		self.display_fade_step = 0
		self.display_fade_end_mode = end_mode
		self.display_fade_end_parameters = end_parameters

	def apply_display_fade(self):
		if self.display_fade_steps is None or self.display_fade_step is None:
			return
		self.display_fade_step += 1
		total_steps = abs(self.display_fade_steps)
		fade = min(1.0, self.display_fade_step / total_steps)
		alpha = int(255 * (fade if self.display_fade_steps < 0 else (1.0 - fade)))
		self.display_fade_overlay.set_alpha(alpha)
		self.window.blit(self.display_fade_overlay, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)
		if self.display_fade_step >= total_steps:
			end_mode = self.display_fade_end_mode
			end_parameters = self.display_fade_end_parameters
			self.display_fade_steps = None
			self.display_fade_step = None
			self.display_fade_end_mode = None
			self.display_fade_end_parameters = None
			if end_mode is not None:
				self.set_mode(end_mode, end_parameters)

	# sound functions

	def load_sounds(self, path: str) -> dict:
		""" Loads sounds from path. Called here and also in Mode. """

		sounds = {}
		sound_types = ['.wav']
		if os.path.isdir(path) is False:
			return sounds
		for filename in (f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in sound_types):
			full_filename = os.path.join(path, filename)
			name = os.path.splitext(filename)[0].lower()
			try:
				sound = self.load_sound(full_filename)
				if sound is not None:
					sounds[name] = sound
				else:
					Log.error(f'Sound {full_filename} failed to load')
			except Exception as e:
				Log.error(f'Exception loading sound {full_filename}: {e}')
		return sounds

	def load_sound(self, sound) -> Sound:
		""" Loads a sound by filename or buffer and returns pygame Sound object. """

		if isinstance(sound, str) and not os.path.isfile(sound):
			Log.error(f'No file named {sound}')
			return None
		try:
			return pygame.mixer.Sound(sound)
		except Exception as e:
			Log.error(e)
			return None

	def get_sound(self, sound: str|Sound):
		""" Finds a sound by name. """

		if isinstance(sound, Sound):
			return sound
		if isinstance(sound, str) is False:
			Log.error(f'Could not identify sound of type {type(sound)}')
			return None
		# in order: check mode sound library, then app sound library, and lastly try to load
		s = self.mode.sounds.get(sound, None) if self.mode is not None else None
		s = s or self.sounds.get(sound, None)
		s = s or self.load_sound(sound)
		return s

	def play_sound(self, sound: str|Sound, loops: int=None, volume: int|float=None):
		""" Plays sound. Sound can be a pygame Sound, the filename of a sound
				in the mode sound library or app sound library, or a filename.
				Volume can be specified (range 0.0-1.0) to override
				sound volume; otherwise, sound will play at preset sound volume. """

		sound = self.get_sound(sound)
		if sound is None:
			Log.error(f'Could not get sound {sound}')
			return
		volume = volume or self.sound_volume
		if volume is not None and volume != 100:
			sound.set_volume(volume / 100.0)
		sound.play(loops=loops or 0)

	def play_sound_on_channel(self, sound: str|Sound, loops: int=None, volume: int|float=None) -> Channel|None:
		""" Plays sound on open channel. Same logic as play_sound(),
				except that it returns the channel of the sound. """

		sound = self.get_sound(sound)
		if sound is None:
			Log.error(f'Could not get sound {sound}')
			return None
		volume = volume or self.sound_volume
		if volume is not None and volume != 100:
			sound.set_volume(volume / 100.0)
		channel = pygame.mixer.find_channel()
		if channel is None:
			Log.error('Could not find open channel')
			return None
		channel.play(sound, loops=loops or 0)
		return channel

	def set_volume(self, volume: int|float, sound_volume: int|float=None):
		""" Set volume level (range 0-100). Specifying one value will
				change volume level for both music and sound; specifying
				two values will set separate volume for music and sound.
				Volume changes for currently playing music will occur
				immediately, but currently playing sounds are not affected. """

		self.music_volume = volume
		pygame.mixer.music.set_volume(volume / 100.0)
		self.sound_volume = sound_volume or volume

	def set_sound_retainer(self, enable: bool=True):
		""" Sets a retainer sound that plays a 1-second loop of very
				quiet noise to keep a sound channel active. """

		if enable:
			filename = os.path.join(self.base_path, 'sounds', 'sound_retainer.wav')
			if os.path.isfile(filename) is False:
				Log.error(f'{filename} does not exist')
				return
			self.sound_retainer = pygame.mixer.Sound(filename)
			self.sound_retainer.play(loops=-1)
		elif self.sound_retainer is not None:
			self.sound_retainer.stop()
			self.sound_retainer = None

	# music functions

	def get_music(self, music_name: str):
		""" Finds music by name. """

		if isinstance(music_name, str) is False:
			Log.error(f'Could not identify music of type {type(music_name)}')
			return None

		mode_path = os.path.join(self.base_path, self.mode.name, 'music', music_name)
		app_path = os.path.join(self.base_path, 'music', music_name)
		music = next(filter(os.path.isfile, (mode_path, app_path, music_name)), None)
		return music

	def play_music(self, filename: str, loops: int=0, volume: int|float=None):
		""" Plays music file.
				Loops can indicate a specific number, or -1 for indefinite repeat.
				Volume can be specified for this music (range 0-100) or will play at default.
				"""

		music = self.get_music(filename)
		if music is None:
			Log.error(f'No file named {filename}')
			return
		volume = volume or self.music_volume
		pygame.mixer.music.set_volume(volume / 100.0)
		try:
			pygame.mixer.music.load(music)
			pygame.mixer.music.play(loops=loops)
		except Exception as e:
			Log.error(e)

	def stop_music(self):
		""" Stops music. """

		pygame.mixer.music.stop()
		self.music_fade_steps = self.music_fade_step = None

	def is_music_playing(self):
		""" Returns whether music is playing. """

		return pygame.mixer.music.get_busy()

	def start_music_fade(self, steps: int):
		""" Starts a music fade over a given number of steps. """

		self.music_fade_steps = steps
		self.music_fade_step = 0

	def apply_music_fade(self):
		""" Applies music fade, if it exists. """

		if self.music_fade_steps is None or self.music_fade_step is None:
			return

		if pygame.mixer.music.get_busy() is False:
			self.music_fade_steps = self.music_fade_step = None
			return

		self.music_fade_step += 1
		level = max(0.0, 1.0 - (self.music_fade_step / float(self.music_fade_steps)))
		pygame.mixer.music.set_volume((self.music_volume * level) / 100.0)
		if self.music_fade_step >= self.music_fade_steps:
			pygame.mixer.music.stop()
			pygame.mixer.music.set_volume(self.music_volume / 100.0)
			self.music_fade_steps = self.music_fade_step = None

	# app state methods

	def load_app_state(self):
		""" Loads app state. """

		filename = self.app_state_filename
		if os.path.isfile(filename) is False:
			filename = self.app_state_start_filename
			if os.path.isfile(filename) is False:
				Log.info('No app_state or app_state_start - using empty state dict')
				self.app_state = {}
				return
		with open(filename, 'rt', encoding='UTF-8') as f:
			try:
				self.app_state = json.loads(f.read().strip())
				Log.info('Loaded app state')
			except Exception as e:
				Log.error(e)
				self.app_state = {}

	def set_app_state(self, key, value):
		""" Sets app state key/value pair and saves state. """

		self.app_state[key] = value
		if self.persist_app_state is True:
			self.save_app_state()

	def save_app_state(self):
		""" Saves script state. """

		with open(self.app_state_filename, 'wt', encoding='UTF-8') as f:
			f.write(json.dumps(self.app_state, ensure_ascii=True))
		Log.debug('Saved app state')

	# script and scene methods

	def init_script(self):
		""" Loads script and script state. """

		# load script
		self.script = []
		script_filename = os.path.join(self.base_path, 'script.txt')
		if os.path.isfile(script_filename) is False:
			return
		with open(script_filename, 'rt', encoding='UTF-8') as f:
			lines = list(line.strip() for line in f.readlines() if len(line.strip()) > 0 and line[0] != '#')
			for line in lines:
				tokens = list(t.strip() for t in line.split() if len(t.strip()) > 0)
				token_pairs = list(t.split('=') for t in tokens if len(t.split('=')) == 2)
				if len(token_pairs) > 0:
					token_pairs = {t[0].strip(): t[1].strip() for t in token_pairs}
					self.script.append(token_pairs)

		# set scene number in app state
		self.app_state.setdefault('scene', 0)

		Log.debug('Loaded and initialized script')

	def run_script(self):
		""" Begins script execution. """

		self.select_scene(self.app_state['scene'])

	def select_scene(self, scene_id: str|int):
		""" Selects scene by name or number. """

		if self.script is None:
			Log.error('No loaded script')
			return
		scene_number = None
		if isinstance(scene_id, int):
			if scene_id >= len(self.script):
				Log.error(f'Scene number {scene_id} cannot be selected ({len(self.script)} scenes)')
				return
			scene_number = scene_id
		else:
			matches = list(i for i, s in enumerate(self.script) if s.get('name') == scene_id)
			if len(matches) == 0:
				Log.error(f'Unknown scene {scene_id}')
				return
			scene_number = matches[0]
		self.set_app_state('scene', scene_number)
		scene = self.script[scene_number]
		mode_name = scene.get('mode')
		if mode_name not in self.modes:
			Log.error(f'No mode named {mode_name}')
			return
		self.set_mode(mode_name, mode_parameters=scene.copy())
		Log.debug(f'Selected scene {scene_number} ({scene})')

	def advance_scene(self, delta: int=1):
		""" Advances to indicated scene. """

		self.select_scene(self.app_state['scene'] + delta)

	# pointer input methods

	def on_click(self, x: int|float, y: int|float):
		""" Mode click event handler. """

		# debouncing check
		if self.pointer_input_last is not None and time.monotonic() < self.pointer_input_last + self.pointer_input_debouncing / 1000:
			return

		if x is None or y is None:
			return

		self.pointer_input_last = time.monotonic()
		self.mode.on_click(x, y)

	# keyboard input methods

	def start_keyboard_buffering(self):
		""" Starts keyboard buffering and clears buffer. """

		self.keyboard_buffering = True
		self.clear_keyboard_buffer()

	def clear_keyboard_buffer(self):
		""" Resets keyboard buffer for new text input. """

		self.keyboard_buffer_chars = []
		self.keyboard_buffer = ''

	def stop_keyboard_buffering(self):
		""" Stops keyboard buffering. """

		self.keyboard_buffering = False

	# other primitives

	def create_rect(self, width: int|float, height: int|float):
		""" Returns a pygame.Rect. """

		return Rect(0, 0, int(width), int(height))

	def create_font(self, name='Arial', size=12):
		""" Creates a font from a path or a system font name. """

		if os.path.isfile(name):
			try:
				return pygame.font.SysFont(name, size)
			except Exception as e:
				Log.error(f'Exception loading font {name}: {e}')
		else:
			try:
				return pygame.font.SysFont(name, size)
			except Exception as e:
				Log.error(f'Exception creating font {name}: {e}')

	def set_standard_font(self):
		""" Sets default font, including a range of sizes. """

		self.standard_font_name = self.config.get('font', None) or self.font_list[0]
		self.standard_font = pygame.font.SysFont(self.standard_font_name, self.standard_font_size)
		self.standard_font_sizes = {i: pygame.font.SysFont(self.standard_font_name, i) for i in range(4, 65)}

	def change_font(self):
		""" Chooses next font in the font list as the default font. """

		current_index = len(self.font_list) if self.standard_font_name not in self.font_list else self.font_list.index(self.standard_font_name)
		new_standard_font = self.font_list[(current_index + 1) % len(self.font_list)]
		self.update_config('font', new_standard_font)
		Log.info(f'Changed font to {new_standard_font}')

	def update_config(self, key, value):
		""" Updates config key/value pair by sending a message to worker. """

		message = {'action': 'update config', 'key': key, 'value': value}
		for name in (name for name, worker in self.workers.items() if worker.config_manager):
			self.send_message(message, name)
		Log.info(f'Setting {key} to {value}')

	# exit functions

	def register_exit_handlers(self):
		""" Registers handlers to ensure that pygame.quit() is called. """

		atexit.register(self.exit)
		for s in [signal.SIGABRT, signal.SIGINT, signal.SIGTERM]:
			signal.signal(s, lambda *_: sys.exit(0))

	def exit(self, code=0):
		""" Exits application. """

		Log.info('Exiting')
		for worker in self.workers.values():
			if worker.worker_process is not None:
				self.send_message('exit', worker.name)
		if self.pointer is not None:
			self.pointer.release()
		try:
			pygame.quit()
		finally:
			sys.exit(code)

	def reboot(self):
		""" Reboots device. """

		Log.info('Rebooting device')
		self.fill_screen()
		pygame.display.flip()
		os.system('sudo shutdown -r now')

	def shut_down(self):
		""" Shuts down device. """

		Log.info('Shutting down device')
		self.fill_screen()
		pygame.display.flip()
		os.system('sudo shutdown now')

	@staticmethod
	def check_running_process(process_name: str=None) -> bool:
		""" Checks for another running process of the same name. """

		script_name = os.path.basename(__main__.__file__)
		with subprocess.Popen(f'ps -ef | grep -v grep | grep {process_name or script_name}', shell=True, stdout=subprocess.PIPE) as ps:
			output = ps.stdout.read(); ps.stdout.close(); ps.wait()
			output = list(o.strip() for o in output.decode('UTF-8').split('\n') if len(o.strip()) > 0)
			running_processes = list(list(o.strip() for o in line.split(' ') if len(o.strip()) > 0) for line in output if 'python' in line)
		return len(running_processes) > 1

if __name__ == '__main__':
	App().run()
