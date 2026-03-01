""" Jubilee Mode class. """

import inspect, os
from .base_classes import Sprite, SpritePosition
from .controls import Control
from .misc import Log

class Mode:
	""" Jubilee Mode class. """

	def __init__(self, background_color: str='black'):

		# app and mode settings
		self.app = None
		if hasattr(self, 'name') is False:		# preserve name declared in subclass
			self.name = 'Unnamed Mode'
		self.background_color = background_color
		self.mode_timer = None
		self.submode = None
		self.submode_timer = None

		# find submodes by introspection
		method_names = list(m[0] for m in inspect.getmembers(self, predicate=inspect.ismethod))
		self.submodes = []
		for method_type in ['enter', 'click', 'hold', 'release', 'process', 'draw', 'exit']:
			for m in (m for m in method_names if m.startswith(f'{method_type}_')):
				submode_name = m[len(method_type) + 1:]
				if len(submode_name) > 0 and submode_name not in self.submodes:
					self.submodes.append(submode_name)

		# controls
		self.controls = []		# Z-ordered from highest to lowest
		self.show_controls = True
		self.selected_control = None

		# load resources
		self.images_path = None
		self.images = {}
		self.animations = {}
		self.sounds_path = None
		self.sounds = {}
		self.sprites = []
		self.sprite_positions = SpritePosition.Bottom		# topleft, center, bottom, or None

	def init(self):
		""" Mode-specific stub initializer. """

	def load_resources(self):
		""" Mode resource loading. Called during app.add_mode() after init(). """

		self.images_path = os.path.join(self.app.project_path, self.name, 'images')
		self.images, self.animations = self.app.load_images(self.images_path)
		self.sounds_path = os.path.join(self.app.project_path, self.name, 'sounds')
		self.sounds = self.app.load_sounds(self.sounds_path)

	def on_enter(self, mode_parameters: dict=None):
		""" Mode enter event receiver. """

		self.mode_timer = 0
		try:
			self.enter(mode_parameters=mode_parameters)
		except Exception as e:
			Log.error(e)

	def enter(self, mode_parameters: dict=None):
		""" Mode enter event stub method. """

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

	def get_control(self, name: str) -> Control|None:
		""" Gets control by name. If several controls have the name, returns the first one. """

		matching_controls = list(c for c in self.controls if c.name == name)
		return matching_controls[0] if len(matching_controls) > 0 else None

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
		if self.show_controls is True:
			for control in self.controls:
				if control.visible is True and control.collide(x, y):
					if control.enabled is True:
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
		""" Mode click event stub method. """

	def on_hold(self):
		""" Mode hold event receiver. """

		if self.selected_control is not None:
			try:
				self.selected_control.on_hold()
			except Exception as e:
				Log.error(f'Exception holding control {self.selected_control.name}: {e}')
		elif self.submode is not None and hasattr(self, f'hold_{self.submode}'):
			try:
				getattr(self, f'hold_{self.submode}')()
			except Exception as e:
				Log.error(f'Exception holding mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.hold()
			except Exception as e:
				Log.error(e)

	def hold(self):
		""" Mode hold event stub method. """

	def on_release(self):
		""" Mode release event receiver. """

		if self.selected_control is not None:
			try:
				self.selected_control.on_release()
			except Exception as e:
				Log.error(f'Exception releasing control {self.selected_control.name}: {e}')
			self.selected_control = None
		elif self.submode is not None and hasattr(self, f'release_{self.submode}'):
			try:
				getattr(self, f'release_{self.submode}')()
			except Exception as e:
				Log.error(f'Exception releasing mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.release()
			except Exception as e:
				Log.error(e)

	def release(self):
		""" Mode release event stub method. """

	def on_process(self):
		""" Mode process event receiver. """

		if self.mode_timer is not None:
			self.mode_timer += 1
		if self.submode is not None and self.submode_timer is not None:
			self.submode_timer += 1

		if self.submode is not None and hasattr(self, f'process_{self.submode}'):
			try:
				getattr(self, f'process_{self.submode}')()
			except Exception as e:
				Log.error(f'Error processing mode {self.name} submode {self.submode}: {e}')
		else:
			try:
				self.process()
			except Exception as e:
				Log.error(f'Error processing mode {self.name}: {e}')
		for sprite in self.sprites:
			sprite.process()

	def process(self):
		""" Mode process stub method. """

	def on_draw(self):
		""" Mode draw event receiver. """

		if self.background_color is not None:
			self.app.fill_screen(self.background_color)
		if self.submode is not None and hasattr(self, f'draw_{self.submode}'):
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
		if self.show_controls is True:
			for control in reversed(self.controls):
				if control.visible is True:
					try:
						control.draw()
					except Exception as e:
						Log.error(f'Exception drawing mode {self.name} control {control.name}: {e}')

	def draw(self):
		""" Mode draw stub method. """

	def add_sprite(self, sprite) -> Sprite:
		""" Adds sprite. """

		sprite.bind(self.app)
		self.sprites.append(sprite)
		return sprite

	def get_sprite(self, name: str) -> Sprite|None:
		""" Gets sprite by name. If several sprites have the name, returns the first one. """

		matching_sprites = list(s for s in self.sprites if s.name == name)
		return matching_sprites[0] if len(matching_sprites) > 0 else None

	def render_sprites(self, auto_animate: bool=True):
		""" Draws sprites on window, optionally calling auto_animate on each.
				Sprites are drawn in the order defined by sprite_positions: topleft, center,
				bottom, or None. """

		# first auto-animate all sprites to set sizes
		for s in self.sprites:
			if auto_animate:
				s.auto_animate()
			s.set_image()

		# sort by sprite positions, with Z-order taking priority
		if self.sprite_positions is not None:
			self.sprites.sort(key=lambda s: (s.y or 0) * self.app.screen_width + (s.x or 0))
		if any(s.z is not None for s in self.sprites):
			self.sprites.sort(key=lambda s: 100 if s.z is None else s.z, reverse=True)

		# render
		for s in self.sprites:
			if s.image is not None:
				self.app.blit(s.image, s.x, s.y, position=self.sprite_positions)

	def remove_sprite(self, sprite):
		""" Removes sprite. """

		if sprite not in self.sprites:
			Log.error('Sprite is not in mode.sprites')
			return
		self.sprites.remove(sprite)

	def remove_sprites(self):
		""" Removes all sprites. """

		self.sprites = []

	def on_exit(self):
		""" Mode exit event receiver. """

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
		""" Mode exit event stub method. """
