""" Jubilee Shut Down mode class. """

from .mode import Mode
from .controls import Button, HoldButton
from .misc import Log

class ShutDownMode(Mode):
	""" Shutdown mode class. """

	def __init__(self):
		super().__init__()
		self.return_mode = None

	def init(self):
		""" Shut Down mode initializer. """

		self.name = 'Shut Down'
		button_width = 150
		hold_steps = int(self.app.config.get('app_process_fps', 10) * 0.75)
		self.add_control(HoldButton('Yes', self.app.button_margin, self.app.screen_height - 60, button_width, 60, click=self.app.shut_down, hold_color='red', hold_steps=hold_steps))
		self.add_control(Button('Cancel', self.app.screen_width - self.app.button_margin - button_width, self.app.screen_height - 60, button_width, 60, click=self.cancel_shutdown))

	def enter(self, mode_parameters: dict=None):
		""" Shut Down mode enter method. """

		self.return_mode = (mode_parameters or {}).get('previous_mode', None)

	def draw(self):
		""" Shut Down mode draw method. """

		try:
			self.app.center_text('Confirm Shutdown', self.app.screen_middle - 30)
			self.app.center_text('Hold to confirm')
		except Exception as e:
			Log.error(e)

	def cancel_shutdown(self):
		""" Cancel shutdown and return to previous mode. """

		if self.return_mode is None:
			Log.error('return_mode is None')
		else:
			self.app.set_mode(self.return_mode)
