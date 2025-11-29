""" Jubilee base classes. """

import enum
from pygame import Surface
from pygame.event import Event
from .misc import Log

class Animation:
	""" Animation class. Stores a set of frames and a set of sequences. """

	def __init__(self, name: str=None, frames: list=None, sequences: dict=None):
		self.name = name
		self.frames = frames or []
		self.sequences = sequences or {}			# {'sequence name': [frame numbers]}

class SpritePosition(enum.Enum):
	""" Sprite positions enum. """

	TopLeft = 1															# x/y maps to top-left
	Center = 2															# x/y maps to center
	Bottom = 3															# x/y maps to bottom

class Sprite:
	""" Sprite class. """

	def __init__(self, name: str=None, static_image: str=None, animation: str|Animation=None, auto_animate_rate: int=None):
		self.app = None
		self.name = name
		self.x = None
		self.y = None
		self.z = None											# Z-order overrides positioning; None = layer 255
		self.static_image = static_image	# set to Surface or image name for static image
		self.animation = animation				# set to an Animation or animation name
		self.sequence_name = None					# set to a sequence name for animation
		self.sequence_frame = None
		self.auto_animate_rate = max(1, int(auto_animate_rate) if auto_animate_rate is not None else 0)
		self.auto_animate_step = 0
		self.scale = None									# set to either a float or a two-tuple
		self.flip_x = False								# flip horizontally
		self.flip_y = False								# flip vertically
		self.rotate = None								# set to a float
		self.hue_shift = None							# set to hue delta, range 0-360
		self.image = None									# this is set by set_image()
		self.width = None									# this is set by set_image()
		self.height = None								# this is set by set_image()

	def bind(self, app):
		""" Binds sprite to app. """

		self.app = app
		# try to find animation from string passed as animation name
		if self.animation is not None and isinstance(self.animation, str):
			self.animation = self.app.get_animation(self.animation)
		# if animation is still None, try to find animation from sprite name
		if self.animation is None and self.name is not None:
			self.animation = self.app.get_animation(self.name)

	def set_static_image(self, image: str|Surface|None):
		""" Sets self.static_image based on image lookup. """

		self.static_image = self.app.get_image(image)

	def set_image(self) -> Surface|None:
		""" Sets current image for sprite based on self.static_image or
				self.sequence_name/self.sequence_frame. Also applies transformations
				and calls set_size(). """

		try:
			self.image = None
			if self.static_image is not None:
				self.image = self.app.get_image(self.static_image)
			else:
				animation = self.app.get_animation(self.animation)
				if animation is None:
					return None
				if self.sequence_name is None:
					if self.sequence_frame is None:
						self.sequence_frame = 0
					if self.sequence_frame >= 0 and self.sequence_frame < len(animation.frames):
						self.image = animation.frames[self.sequence_frame]
				else:
					if self.sequence_name not in animation.sequences:
						return None
					sequence = animation.sequences.get(self.sequence_name)
					if self.sequence_frame is None:
						self.sequence_frame = 0
					if self.sequence_frame < 0 or self.sequence_frame >= len(sequence):
						return None
					sequence_frame = sequence[self.sequence_frame]
					if sequence_frame >= 0 and sequence_frame < len(animation.frames):
						self.image = animation.frames[sequence_frame]

			if self.image is None:
				return None

			# apply transformations
			if self.scale is not None:
				if isinstance(self.scale, float):
					self.image = self.app.scale_image(self.image, self.scale)
				elif isinstance(self.scale, (tuple, list)) and len(self.scale) == 2:
					self.image = self.app.scale_image(self.image, self.scale[0], self.scale[1])
			if self.flip_x is True or self.flip_y is True:
				self.image = self.app.flip_image(self.image, horizontal=self.flip_x, vertical=self.flip_y)
			if self.rotate is not None:
				self.image = self.app.rotate_image(self.image, self.rotate)
			if self.hue_shift is not None:
				self.image = self.app.shift_image_hue(self.image, self.hue_shift)

			# set size and return image
			self.width, self.height = self.image.get_size()
			return self.image

		except Exception as e:
			Log.error(e)
			return None

	def set_sequence(self, sequence_name: str, auto_animate_rate: int=None, reset_sequence_frame: bool=True) -> bool:
		""" Sets an animation sequence, optionally with an animation rate. """

		try:
			animation = self.app.get_animation(self.animation)
			if animation is None:
				Log.error('No animation to set')
				return False
			if sequence_name not in animation.sequences:
				Log.error(f'No sequence named {sequence_name} in animation')
				self.sequence_name = None
				return False
			self.sequence_name = sequence_name
			self.auto_animate_rate = 0 if auto_animate_rate is None else max(1, int(self.auto_animate_rate))
			if reset_sequence_frame is True or self.sequence_frame >= len(animation.sequences[sequence_name]):
				self.sequence_frame = None
				self.auto_animate_step = 0
			return True
		except Exception as e:
			Log.error(e)
			return False

	def auto_animate(self):
		""" Performs auto-animation. """

		if self.static_image is not None or self.animation is None or self.auto_animate_rate == 0:
			return
		self.auto_animate_step = self.auto_animate_step + 1
		if self.auto_animate_step >= self.auto_animate_rate:
			self.auto_animate_step = 0
			self.animate()

	def animate(self, sequence_frame: int=None) -> bool:
		""" Advances animation to the next frame in the sequence. """

		try:
			if self.static_image is not None:
				Log.debug(f'Not animating sprite {self.name} because set to static image')
				return True

			# find animation
			animation = self.app.get_animation(self.animation)
			if animation is None:
				Log.error('No animation to set')
				return False
			if len(animation.frames) == 0:
				Log.error(f'Animation {animation.name} has no frames')
				return False

			if self.sequence_name is None:		# animate through all frames
				if sequence_frame is not None:
					self.sequence_frame = sequence_frame
				else:
					self.sequence_frame = 0 if self.sequence_frame is None else (self.sequence_frame + 1) % len(animation.frames)

			else:	# animate based on specified sequence
				sequence = animation.sequences.get(self.sequence_name)
				if sequence is None:
					Log.error(f'No sequence named {self.sequence_name}')
					return False
				if len(sequence) == 0:
					Log.error(f'Sequence {self.sequence_name} has no frames')
					return False
				if sequence_frame is not None:
					self.sequence_frame = sequence_frame
				else:
					self.sequence_frame = 0 if self.sequence_frame is None else (self.sequence_frame + 1) % len(sequence)
				if self.sequence_frame is None or self.sequence_frame < 0 or self.sequence_frame >= len(sequence) or sequence[self.sequence_frame] >= len(animation.frames):
					Log.error(f'Invalid frame number {self.sequence_frame} for animation {animation.name} and sequence {self.sequence_name}')
					return False

			return True

		except Exception as e:
			Log.error(e)
			return False

	def process(self):
		""" Sprite process stub method. """

class PointerInterface:
	""" Jubilee pointer interface class - base class for MouseInterface and TouchInterface. """

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
