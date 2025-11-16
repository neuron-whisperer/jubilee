""" Jubilee touch interface class using evdev. """

import evdev
from .base_classes import PointerInterface
from .misc import Log

class TouchInterface(PointerInterface):
	""" Touch interface class. """

	def __init__(self, resolution: list=None, scale: list=None, swap_axes: bool=False):
		super().__init__()
		try:
			# probe /dev/input/event* to determine which one has bustype 24
			device_number = None
			for i in range(0, 10):
				try:
					d = evdev.InputDevice(f'/dev/input/event{i}')
					if d.info.bustype == 24:
						device_number = i
						break
				except:
					pass
			if device_number is None:
				Log.error('Could not find touchscreen input among device events')
				self.touch = None
				return
			Log.info(f'Found touchscreen on device /dev/input/event{device_number}')
			device = f'/dev/input/event{device_number}'
			self.touch = evdev.InputDevice(device)
			self.touch.grab()
			Log.info(f'Grabbed {device} - info: {self.touch.info}')
		except Exception as e:
			Log.error(f'Exception during grab: {e}')
			return
		self.resolution = resolution
		self.scale = scale
		if resolution is None or scale is None:
			Log.warning('resolution and/or scale not specified')
		self.swap_axes = swap_axes

	def detect_events(self) -> bool:
		""" Detect touch events. """

		touched = False
		try:
			for event in self.touch.read():
				if event.type == evdev.ecodes.EV_ABS:
					if event.code == 54:
						self.x = int(((event.value - self.scale[0][0]) / (self.scale[0][1] - self.scale[0][0]) * self.scale[0][2] - (self.scale[0][2] - 1) / 2) * self.resolution[0])
					elif event.code == 53:
						self.y = int(((event.value - self.scale[1][0]) / (self.scale[1][1] - self.scale[1][0]) * self.scale[1][2] - (self.scale[1][2] - 1) / 2) * self.resolution[1])
				elif event.type == evdev.ecodes.EV_KEY and event.code == 330 and event.value == 1:
					if self.x is not None and self.y is not None:

						if self.swap_axes is True:
							x = self.y
							y = self.x
							self.y = y
							self.x = x

						self.down = True
						touched = True
				elif event.type == evdev.ecodes.EV_KEY and event.code == 330 and event.value == 0:
					self.down = False
					self.x = None
					self.y = None
		except:
			pass
		return touched

	def release(self):
		""" Release touch interface. """

		self.touch.ungrab()
