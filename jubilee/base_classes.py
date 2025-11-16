""" Jubilee base classes. """

from pygame.event import Event
from .misc import Log

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
		self.auto_animate_rate = max(1, int(auto_animate_rate) if auto_animate_rate is not None else 0)
		self.auto_animate_step = 0
		self.sequence = None
		self.frame_number = None
		self.x = None
		self.y = None
		self.width = None
		self.height = None

	def set_sequence(self, sequence_name: str, auto_animate_rate: int=None) -> bool:
		""" Sets an animation sequence, optionally with an animation rate. """

		if self.animation is None or sequence_name not in self.animation.sequences:
			Log.error(f'No sequence named {sequence_name} in animation')
			self.sequence = None
			return False
		self.sequence = sequence_name
		self.auto_animate_step = 0
		if auto_animate_rate is not None:
			self.auto_animate_rate = max(1, int(self.auto_animate_rate))
		self.animate(frame_number=0)
		return True

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

		if self.animation is None or len(self.animation.frames) == 0:
			return
		if self.sequence is None:
			if frame_number is not None:
				self.frame_number = frame_number
			else:
				self.frame_number = 0 if self.frame_number is None else (self.frame_number + 1) % len(self.animation.frames)
			self.set_size()
			return

		sequence = self.animation.sequences.get(self.sequence)
		if sequence is None:
			Log.error(f'No sequence named {self.sequence}')
			return
		if len(sequence) == 0:
			Log.error(f'Sequence {self.sequence} has no frames')
			return
		if frame_number is not None:
			self.frame_number = frame_number
		else:
			self.frame_number = 0 if self.frame_number is None else (self.frame_number + 1) % len(sequence)
		if self.frame_number is None or self.frame_number < 0 or self.frame_number >= len(sequence) or sequence[self.frame_number] >= len(self.animation.frames):
			Log.error(f'Invalid frame number {self.frame_number} for sprite {self.animation} and sequence {self.sequence}')
			return
		self.set_size()

	def get_animation_frame(self) -> AnimationFrame|None:
		""" Finds animation frame based on self.frame_number and self.sequence. """

		if self.frame_number is None or self.animation is None:
			return None
		if self.sequence is None:
			if self.frame_number < 0 or self.frame_number >= len(self.animation.frames):
				return None
			return self.animation.frames[self.frame_number]
		if self.sequence not in self.animation.sequences:
			return None
		sequence = self.animation.sequences.get(self.sequence)
		if self.frame_number < 0 or self.frame_number >= len(sequence):
			return None
		frame_number = sequence[self.frame_number]
		if frame_number < 0 or frame_number >= len(self.animation.frames):
			return None
		return self.animation.frames[frame_number]

	def set_size(self):
		frame = self.get_animation_frame()
		if frame is None:
			return
		size = frame.image.get_size()
		self.width = size[0]
		self.height = size[1]

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
