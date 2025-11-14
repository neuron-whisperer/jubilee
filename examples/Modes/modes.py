""" Modes Jubilee app. """

import sys
from jubilee import App, Mode
from jubilee.controls import Button
from jubilee.misc import Log

class ModesApp(App):
	""" Modes app. """

	def init(self):
		self.add_modes([MainMode, SubmodeMode])

	def process_message(self, message):
		""" Process message from worker. """

		action = message.get('action')
		if action == 'custom action':		# process message
			pass
		else:
			super().process_message(message)

class MainMode(Mode):
	""" Main mode. """

	def init(self):
		self.name = 'Main'
		x = self.app.screen_center-50; y = self.app.screen_middle-30; w=100; h=60
		self.add_control(Button('Submode', x, y, w, h, target_mode='Submode'))

	def draw(self):
		""" Draw method for Main mode. """

		self.app.center_text('Main Mode', self.app.screen_middle-50)

class SubmodeMode(Mode):
	""" Submode mode. """

	def init(self):
		self.name = 'Submode'
		x = self.app.screen_center-50; y = self.app.screen_middle-50; w=100; h=60
		self.add_control(Button('Main Mode', x, y, w, h, target_mode='Main'))

	def draw(self):
		""" Draw method for Submode mode. """

		self.app.center_text('Submode', self.app.screen_middle+30)

if __name__ == '__main__':
	ModesApp().run()
