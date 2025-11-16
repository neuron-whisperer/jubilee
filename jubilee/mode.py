""" Jubilee base classes. """

import inspect, os
from .controls import Control
from .misc import Log

class Mode:
	""" Jubilee Mode class. """

	def __init__(self, background_color: str='black'):

		# app and mode settings
		self.app = None
		self.name='Unnamed Mode'
		self.mode_timer = None
		self.submode = None
		self.submode_timer = None
		self.background_color = background_color
		self.selected_control = None

		# find submodes by introspection
		method_names = list(m[0] for m in inspect.getmembers(self, predicate=inspect.ismethod))
		self.submodes = []
		for method_type in ['enter', 'click', 'process', 'draw', 'exit']:
			for m in (m for m in method_names if m.startswith(f'{method_type}_')):
				submode_name = m[len(method_type) + 1:]
				if len(submode_name) > 0 and submode_name not in self.submodes:
					self.submodes.append(submode_name)

		# controls
		self.controls = []		# Z-ordered from highest to lowest

		# load resources
		self.images_path = None
		self.images = {}
		self.animations = {}
		self.sounds_path = None
		self.sounds = {}
		self.sprites = []
		self.sprite_positions = 'bottom'		# can be topleft, center, or bottom

	def init(self):
		""" Mode-specific initializer. """

	def load_resources(self):
		""" Mode resource loading. Called during app.add_mode() after init(). """

		self.images_path = os.path.join(self.app.base_path, self.name, 'images')
		self.images, self.animations = self.app.load_images(self.images_path)
		self.sounds_path = os.path.join(self.app.base_path, self.name, 'sounds')
		self.sounds = self.app.load_sounds(self.sounds_path)

	def on_enter(self, mode_parameters: dict=None):
		""" Mode enter receiver method. """

		self.mode_timer = 0
		try:
			self.enter(mode_parameters=mode_parameters)
		except Exception as e:
			Log.error(e)

	def enter(self, mode_parameters: dict=None):
		""" Mode enter method. """

	def set_submode(self, name: str|None, mode_parameters: dict=None):
		""" Sets submode and resets submode timer. """

		# call exit_submode on current submode if it exists
		if self.submode is not None and hasattr(self, f'exit_{self.submode}'):
			try:
				getattr(self, f'exit_{self.submode}')()
			except Exception as e:
				Log.error(f'Exception exiting submode {self.submode}: {e}')
		self.submode = None
		self.submode_timer = None

		if name not in self.submodes:
			if name is not None:
				Log.error(f'No known submode {name}')
			return

		self.submode = name
		self.submode_timer = 0
		if hasattr(self, f'enter_{name}'):
			try:
				getattr(self, f'enter_{name}')(mode_parameters)
			except Exception as e:
				Log.error(f'Exception entering submode {self.submode}: {e}')

	def add_control(self, control) -> Control:
		""" Add control to mode. """

		control.bind(self.app)
		self.controls.append(control)
		return control

	def remove_control(self, control):
		""" Remove control from mode. Can either pass in the control or its caption. """

		if isinstance(control, str):
			matching_controls = list(c for c in self.controls if c.caption == control)
			if len(matching_controls) > 0:
				for b in matching_controls:
					self.controls.remove(b)
			else:
				Log.error(f'No control with caption {control} in mode')
		else:
			if control in self.controls:
				self.controls.remove(control)
			else:
				Log.error(f'Control {control} is not in mode.controls')

	def remove_controls(self):
		""" Remove all controls from mode. """

		self.controls = []

	def on_click(self, x: int|float, y: int|float):
		""" Mode click event receiver. """

		# test controls first
		for control in self.controls:
			if control.collide(x, y):
				self.selected_control = control
				try:
					control.on_click()
				except Exception as e:
					Log.error(f'Exception clicking control {control.name}: {e}')
				return

		# send to click mode or submode
		if self.submode is not None and hasattr(self, f'click_{self.submode}'):
			try:
				getattr(self, f'click_{self.submode}')(x, y)
			except Exception as e:
				Log.error(f'Exception clicking mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.click(x=x, y=y)
			except Exception as e:
				Log.error(e)

	def click(self, x: int|float, y: int|float):
		""" Mode click event method. """

	def on_hold(self):
		""" Mode hold event receiver. """

		if self.selected_control is not None:
			try:
				self.selected_control.on_hold()
			except Exception as e:
				Log.error(f'Exception holding control {self.selected_control.name}: {e}')
		else:
			try:
				self.hold()
			except Exception as e:
				Log.error(e)

	def hold(self):
		""" Mode hold event method. """

	def on_release(self):
		""" Mode release event method. """

		if self.selected_control is not None:
			try:
				self.selected_control.on_release()
			except Exception as e:
				Log.error(f'Exception releasing control {self.selected_control.name}: {e}')
			self.selected_control = None
		else:
			try:
				self.release()
			except Exception as e:
				Log.error(e)

	def release(self):
		""" Mode release event method. """

	def on_process(self):
		""" Mode process receiver method. """

		if self.submode is not None and hasattr(self, f'process_{self.submode}'):
			try:
				try:
					getattr(self, f'process_{self.submode}')()
				except Exception as e:
					Log.error(f'Error processing mode {self.name} submode {self.submode}: {e}')			
			except Exception as e:
				Log.error(f'Exception processing mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.process()
			except Exception as e:
				Log.error(f'Error processing mode {self.name}: {e}')

	def process(self):
		""" Mode process method. """

	def on_draw(self):
		""" Mode draw receiver method. """

		self.mode_timer += 1
		if self.background_color is not None:
			self.app.fill_screen(self.background_color)
		if self.submode is not None and hasattr(self, f'draw_{self.submode}'):
				self.submode_timer += 1
				try:
					getattr(self, f'draw_{self.submode}')()
				except Exception as e:
					Log.error(f'Exception drawing mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.draw()
			except Exception as e:
				Log.error(e)

		# draw controls in reverse order, i.e., back-to-front if overlapping
		for control in reversed(self.controls):
			try:
				control.draw()
			except Exception as e:
				Log.error(f'Exception drawing mode {self.name} control {control.name}: {e}')

	def draw(self):
		""" Mode draw method. """

	def add_sprite(self, sprite):
		""" Adds sprite. """

		self.sprites.append(sprite)

	def remove_sprite(self, sprite):
		""" Removes sprite. """

		if sprite not in self.sprites:
			Log.error('Sprite is not in mode.sprites')
			return
		self.sprites.remove(sprite)

	def render_sprites(self, auto_animate: bool=True):
		""" Draws sprites on window, optionally calling auto_animate on each.
				Sprites are drawn in the order defined by sprite_positions: top-left, center,
				or bottom. """

		self.sprites.sort(key=lambda s: (s.y or 0) * self.app.screen_width + (s.x or 0))
		for s in self.sprites:
			if auto_animate:
				s.auto_animate()
			if s.animation is None or s.frame_number is None:
				continue
			frame = s.get_animation_frame()
			if frame is not None:
				self.app.blit(frame.image, s.x, s.y, position=self.sprite_positions)

	def on_exit(self):
		""" Mode exit receiver method. """

		self.mode_timer = None

		if self.selected_control is not None:
			try:
				self.selected_control.on_release()
			except Exception as e:
				Log.error(f'Exception calling on_release() on control {self.selected_control.name}: {e}')
			self.selected_control = None

		# call exit_submode on current submode if it exists, and set submode to None
		if self.submode is not None and hasattr(self, f'exit_{self.submode}'):
				try:
					getattr(self, f'exit_{self.submode}')()
				except Exception as e:
					Log.error(f'Exception exiting mode {self.name} submode {self.submode}: {e}')
		try:
			self.exit()
		except Exception as e:
			Log.error(e)

		self.submode = None

	def exit(self):
		""" Mode exit method. """
