""" Jubilee base classes. """

import inspect, os
from pygame.event import Event
from pygame.font import Font
from .misc import Log

class Mode:
	""" Jubilee Mode class. """

	def __init__(self, name: str='unnamed', background_color: str='black'):

		self.name = name
		self.background_color = background_color

		# app and mode settings
		self.app = None
		self.mode_timer = None
		self.submode = None
		self.submode_timer = None

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
		self.on_click = self.click
		self.on_hold = self.hold
		self.on_release = self.release

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

	def load_resources(self, app):
		""" Mode resource loading. Called during app.add_mode(). """

		self.app = app
		self.images_path = os.path.join(self.app.base_path, self.name, 'images')
		self.images, self.animations = self.app.load_images(self.images_path)
		self.sounds_path = os.path.join(self.app.base_path, self.name, 'sounds')
		self.sounds = self.app.load_sounds(self.sounds_path)

	def enter(self, mode_parameters: dict=None):
		""" Mode enter method. """

	def set_submode(self, name: str, mode_parameters: dict=None):
		""" Sets submode and resets submode timer. """

		# call exit_submode on current submode if it exists
		if self.submode is not None and hasattr(self, f'exit_{self.submode}'):
			try:
				getattr(self, f'exit_{self.submode}')()
			except Exception as e:
				Log.error('Mode', 'set_submode', f'Exception exiting submode {self.submode}: {e}')

		if name is not None and name not in self.submodes:
			Log.error('Mode', 'set_submode', f'No known submode {name}')
			return

		self.submode = name
		self.submode_timer = 0
		if hasattr(self, f'enter_{name}'):
			try:
				getattr(self, f'enter_{name}')(mode_parameters)
			except Exception as e:
				Log.error('Mode', 'set_submode', f'Exception entering submode {self.submode}: {e}')

	def add_control(self, control):
		""" Add control to mode. """

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
				Log.error('Mode', 'remove_control', f'No control with caption {control} in mode')
		else:
			if control in self.controls:
				self.controls.remove(control)
			else:
				Log.error('Mode', 'remove_control', f'Control {control} is not in mode.controls')

	def remove_controls(self):
		""" Remove all controls from mode. """

		self.controls = []

	def click(self, x: int|float, y: int|float):
		""" Mode click event method. """

		# call click_submode on current submode if it exists
		if self.submode is not None:
			try:
				if hasattr(self, f'click_{self.submode}'):
					submode_click_method = getattr(self, f'click_{self.submode}')
					submode_click_method(x, y)
			except Exception as e:
				Log.error('Mode', 'click', str(e))

	def hold(self):
		""" Mode hold event method. """

	def release(self):
		""" Mode release event method. """

	def process(self):
		""" Mode process method. """

	def draw(self):
		""" Mode draw method. """

	def add_sprite(self, sprite):
		""" Adds sprite. """

		self.sprites.append(sprite)

	def remove_sprite(self, sprite):
		""" Removes sprite. """

		self.sprites.remove(sprite)

	def render_sprites(self, auto_animate: bool=True):
		""" Draws sprites on window, optionally calling auto_animate on each.
				Sprites are drawn in the order defined by sprite_positions: top-left, center,
				or bottom. """

		self.sprites.sort(key=lambda s: (s.y or 8) * self.app.screen_width + (s.x or 0))
		for s in (s for s in self.sprites):
			if auto_animate:
				s.auto_animate()
			if s.animation is None or s.frame_number is None:
				return
			self.app.blit(s.animation.frames[s.frame_number].image, s.x, s.y, position=self.sprite_positions)

	def exit(self):
		""" Mode exit method. """

		self.mode_timer = None

		# call exit_submode on current submode if it exists, and set submode to None
		if self.submode is not None:
			if hasattr(self, f'exit_{self.submode}'):
				try:
					getattr(self, f'exit_{self.submode}')()
				except Exception as e:
					Log.error('Mode', 'exit', str(e))
			self.submode = None

class AnimationFrame:
	""" Animation frame. """

	def __init__(self, name=None, image=None):
		self.name = name
		self.image = image

class Animation:
	""" Animation class. Stores a set of frames and a set of sequences. """

	def __init__(self, frames=None, sequences=None):
		self.frames = frames or []
		self.sequences = sequences or {}			# {'sequence name': [frame numbers]}

class Sprite:
	""" Sprite class. """

	def __init__(self, animation=None, auto_animate_rate=None):
		self.animation = animation
		self.auto_animate_rate = auto_animate_rate
		self.auto_animate_step = 0
		self.sequence = None
		self.frame_number = None
		self.x = None
		self.y = None
		self.width = None
		self.height = None

	def set_sequence(self, sequence_name: str, auto_animate_rate: int=None):
		""" Sets an animation sequence, optionally with an animation rate. """

		if sequence_name not in self.animation.sequences:
			return
		self.sequence = sequence_name
		self.auto_animate_step = 0
		self.auto_animate_rate = auto_animate_rate or self.auto_animate_rate
		self.animate(frame_number=0)

	def auto_animate(self):
		""" Performs auto-animation. """

		if self.animation is None or self.auto_animate_rate is None:
			return
		self.auto_animate_step = self.auto_animate_step + 1
		if self.auto_animate_step >= self.auto_animate_rate:
			self.auto_animate_step = 0
			self.animate()

	def animate(self, frame_number: int=None):
		""" Advances animation to the next frame in the sequence. """

		if self.animation is None:
			return
		if self.sequence is None:
			self.frame_number = frame_number or (0 if self.frame_number is None else (self.frame_number + 1) % len(self.animation.frames))
		else:
			sequence = self.animation.sequences[self.sequence]
			self.frame_number = sequence[frame_number or (0 if self.frame_number is None else self.frame_number + 1) % len(sequence)]
		if self.frame_number < 0 or self.frame_number >= len(self.animation.frames):
			Log.error('Sprite', 'animate', f'Invalid frame number {self.frame_number} for sprite {self.animation} ({len(self.animation.frames)} frames)')
			return
		self.set_size()

	def set_size(self):
		if self.animation is None or self.frame_number is None:
			return
		size = self.animation.frames[self.frame_number].image.get_size()
		self.width = size[0]
		self.height = size[1]

class Control:
	""" Jubilee user control base class. """

	def __init__(self, app, x: int|float, y: int|float, width: int|float, height: int|float,
			click=None, hold=None, release=None, parameters: dict=None):
		self.app = app
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.on_click = click or self.null_handler
		self.on_hold = hold or self.null_handler
		self.on_release = release or self.null_handler
		self.parameters = parameters

	def null_handler(self):
		""" Null event handler method. """

	def exit_handler(self):
		""" Control handler method for exiting app. """

		self.app.exit()

	def collide(self, x: int|float, y: int|float):
		""" Control collision detection method. """

		return (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height)

	def draw(self):
		""" Draw method. """

class Button(Control):
	""" Jubilee button user control class. """

	def __init__(self, app, x: int|float, y: int|float, width: int|float, height: int|float,
			caption: str, target_mode: str|Mode=None, target_mode_parameters: dict=None,
			click=None, hold=None, release=None, app_exit: bool=False,
			font: Font|str=None, color='white', background_color=None, parameters: dict=None):
		super().__init__(app, x, y, width, height, click=self.click,
			hold=hold, release=release, parameters=parameters)
		# note: the provided_click_handler is saved so that if user later sets or changes
		# target_mode or app_exit, the button-specific click handler included in this class
		# will correctly hand off to the correct function.
		# specifying target_mode or app_exit will override click
		self.provided_click_handler = click
		self.caption = caption
		self.target_mode = target_mode
		self.target_mode_parameters = target_mode_parameters
		self.app_exit = app_exit
		self.font = font
		self.color = color
		self.background_color = background_color or 'black'

	def click(self):
		""" Button click method. """

		if self.target_mode:
			self.app.set_mode(self.target_mode, mode_parameters=self.target_mode_parameters)
		elif self.app_exit:
			self.app.exit()
		elif self.provided_click_handler:
			self.provided_click_handler()

	def draw(self):
		""" Button draw method. """

		try:
			if self.background_color:
				self.app.fill_rect(self.x, self.y, self.width, self.height, color=self.background_color)
			self.app.draw_rect(self.x, self.y, self.width, self.height, line_width=self.app.button_border, color=self.color)
			x = int(self.x + self.width / 2)
			y = int(self.y + self.height / 2)
			self.app.draw_text(self.caption, x, y, color = self.color, font = self.font, alignment = 'center')
		except Exception as e:
			Log.error('Button', 'draw', str(e))

class HoldButton(Button):
	""" Jubilee hold button user control class.
			This is a wrapper class for the basic button. This class accepts the usual button
			parameters, including target_mode and app_exit, but substitutes hold_complete
			for click. A completion of the hold event either calls hold_complete
			or the Button click function, which handles target_mode and app_exit.
			Also requires hold_duration, to indicate how long the hold should take for
			activation, and optionally hold_color to indicate the color to fill the button. """

	def __init__(self, app, x: int|float, y: int|float, width: int|float, height: int|float,
			caption: str, hold_duration: int=25, hold_color='red', hold_complete=None,
			target_mode: str|Mode=None, target_mode_parameters: dict=None, app_exit: bool=False,
			font: Font|str=None, color='white', background_color=None, parameters: dict=None):

		super().__init__(app, x, y, width, height, caption, target_mode=target_mode,
			target_mode_parameters=target_mode_parameters, click=self.click,
			hold=self.hold, release=self.release,
			app_exit=app_exit, font=font, color=color, background_color=None,
			parameters=parameters)
		self.hold_duration = hold_duration
		self.hold_count = 0
		self.hold_color = hold_color
		self.on_hold_complete = hold_complete or Button.click
		self.hold_background_color = background_color

	def click(self):
		""" Hold-button click event method. """

		self.hold_count = 0

	def hold(self):
		""" Hold-button hold event method. """

		# hold_count continues to increment past hold_duration, but hold_complete
		# is only triggered once.
		self.hold_count = self.hold_count + 1
		if self.hold_count == self.hold_duration:
			self.on_hold_complete()

	def release(self):
		""" Hold-button release event method. """

		self.hold_count = 0

	def draw(self):
		""" Hold-button draw method. """

		if self.hold_background_color:
			self.app.fill_rect(self.x, self.y, self.width, self.height, color=self.hold_background_color)
		if self.hold_color is not None:
			progress = min(self.width, int(self.width * self.hold_count / (self.hold_duration - 3)))
			if progress > 0:
				self.app.fill_rect(self.x, self.y, progress, self.height, color=self.hold_color)
				self.app.fill_rect(self.x, self.y, progress, self.height, color=self.hold_color)
		self.app.draw_rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4, line_width=self.app.button_border, color=self.color)
		super().draw()

class Pointer_Interface:
	""" Jubilee pointer interface class - base class for Mouse_Interface and Touch_Interface. """

	def __init__(self):
		self.x = None
		self.y = None
		self.down = False
		self.held = False

	def handle_event(self, event: Event):
		""" Event handler function for events. """

	def detect_events(self):
		""" Event detector function for polled devices. """

	def release(self):
		""" Resource release function. """
