""" Jubilee Shut Down mode class. """

from .base_classes import Button, Mode
from .misc import Log

class Shut_Down_Mode(Mode):
	""" Shutdown mode class. """

	def __init__(self, return_mode: str|Mode=None):
		super().__init__()
		self.return_mode = return_mode

	def init(self):
		""" Shut Down mode initializer. """

		self.name = 'Shut Down'
		button_width = 150
		self.add_control(Button(self.app, self.app.button_margin, self.app.screen_height - 60, button_width, 60, 'Yes', click=self.app.shut_down))
		self.add_control(Button(self.app, self.app.screen_width - self.app.button_margin - button_width, self.app.screen_height - 60, button_width, 60, 'Cancel', click=self.cancel_shutdown))

		# add this to create a button to switch back from Log to another screen
		# self.add_control(Button(self.app, self.app.screen_width - 77 - self.app.button_margin, self.app.screen_height - 60, 77, 60, 'Back', target_mode = 'Target Mode'))

	def draw(self):
		""" Shut Down mode draw method. """

		self.app.fill_screen('black')
		self.app.draw_text('Confirm Shutdown', int(self.app.screen_width / 2), int(self.app.screen_height) / 2, alignment='center')

	def cancel_shutdown(self):
		""" Cancel shutdown and return to previous mode. """

		if self.return_mode is None:
			Log.error('Shut_Down_Mode', 'cancel_suhtdown', 'self.return_mode is None')
		else:
			self.app.set_mode(self.return_mode)
