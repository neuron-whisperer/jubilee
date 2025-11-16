""" Jubilee mouse interface class. """

import pygame
from pygame.event import Event
from .base_classes import PointerInterface
from .misc import Log

class MouseInterface(PointerInterface):
	""" Mouse interface class. """

	def handle_event(self, event: Event) -> bool:
		""" Handle mouse events. """

		if event.type == pygame.MOUSEBUTTONDOWN:
			self.down = True
			self.x, self.y = pygame.mouse.get_pos()
			return (self.x is not None and self.y is not None)
		if event.type == pygame.MOUSEBUTTONUP:
			self.down = False
			self.x = None; self.y = None
			return False
		Log.warning(f'Could not handle event of type {event.type}')
		return False
