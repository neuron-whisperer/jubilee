""" Modes Jubilee app. """

import sys
from jubilee import App
from jubilee.base_classes import Button, Mode
from jubilee.misc import Log

class Modes_App(App):
	""" Modes app. """

	def init(self):
		self.add_modes([Main_Mode, Submode_Mode])

	def process_message(self, message):
		""" Process message from worker. """

		action = message.get('action')
		if action == 'custom action':		# process message
			pass
		else:
			super().process_message(message)

class Main_Mode(Mode):
	""" Main mode. """

	def init(self):
		self.name = 'Main'
		x = self.app.screen_center-50; y = self.app.screen_middle-30; w=100; h=60
		self.add_control(Button(self.app, x, y, w, h, 'Submode', target_mode='Submode'))

	def draw(self):
		""" Draw method for Main mode. """

		x = self.app.screen_center; y = self.app.screen_middle-50
		self.app.draw_text('Main Mode', x, y, alignment='center')

class Submode_Mode(Mode):
	""" Submode mode. """

	def init(self):
		self.name = 'Submode'
		x = self.app.screen_center-50; y = self.app.screen_middle-50; w=100; h=60
		self.add_control(Button(self.app, x, y, w, h, 'Main Mode', target_mode='Main'))

	def draw(self):
		""" Draw method for Submode mode. """

		x = self.app.screen_center; y = self.app.screen_middle+30
		self.app.draw_text('Submode', x, y, alignment='center')

if __name__ == '__main__':
	Modes_App().run()
