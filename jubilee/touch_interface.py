""" Jubilee touch interface class using evdev. """

from collections import deque
import glob
import evdev
from .base_classes import PointerInterface
from .misc import Log

class TouchInterface(PointerInterface):
	""" Touch interface class. """

	def __init__(self, resolution: list=None, scale: list=None, swap_axes: bool=False):
		super().__init__()
		self.touch = None
		self.resolution = resolution
		self.scale = scale
		self.swap_axes = swap_axes
		self._events = deque()
		self._raw = [None, None]
		self._pressed = False
		if resolution is None or scale is None:
			Log.warning('resolution and/or scale not specified')
			return
		try:
			# Close rejected devices, and keep the selected descriptor rather than reopening it.
			for device in sorted(glob.glob('/dev/input/event*')):
				try:
					d = evdev.InputDevice(device)
					if d.info.bustype == 24:
						self.touch = d
						break
					d.close()
				except (OSError, FileNotFoundError):
					pass
			if self.touch is None:
				Log.error('Could not find touchscreen input among device events')
				return
			self.touch.grab()
			Log.info(f'Grabbed {device} - info: {self.touch.info}')
		except Exception as e:
			Log.error(f'Exception during grab: {e}')
			if self.touch is not None:
				self.touch.close()
			self.touch = None

	def detect_events(self) -> bool:
		""" Detect touch events. """

		if self.touch is None:
			return False
		try:
			if not self._events:
				self._events.extend(self.touch.read())
			while self._events:
				event = self._events.popleft()
				if event.type == evdev.ecodes.EV_ABS:
					if event.code == evdev.ecodes.ABS_MT_POSITION_X:
						self._raw[0] = event.value
					elif event.code == evdev.ecodes.ABS_MT_POSITION_Y:
						self._raw[1] = event.value
				elif event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.BTN_TOUCH:
					self._pressed = bool(event.value)
				elif event.type == evdev.ecodes.EV_SYN and event.code == evdev.ecodes.SYN_REPORT:
					was_down = self.down
					if self._pressed and all(value is not None for value in self._raw):
						coordinates = []
						for axis in range(2):
							low, high, direction = self.scale[axis]
							if high == low:
								raise ValueError('Touch calibration range cannot be zero')
							coordinates.append((self._raw[axis] - low) / (high - low) * direction - (direction - 1) / 2)
						if self.swap_axes:
							coordinates.reverse()
						self.x, self.y = [int(max(0, min(1, value)) * (size - 1)) for value, size in zip(coordinates, self.resolution)]
						self.down = True
					else:
						self.down = False
						self.x = self.y = None
					if self.down != was_down:
						return self.down
		except BlockingIOError:
			pass
		except Exception as e:
			Log.debug(f'Touch read error: {e}')
		return False

	def release(self):
		""" Release touch interface. """

		if self.touch is not None:
			try:
				self.touch.ungrab()
			except Exception as e:
				Log.debug(f'Touch ungrab error: {e}')
			finally:
				self.touch.close()
				self.touch = None
