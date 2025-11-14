""" Submodes Jubilee app. """

import random, sys
from jubilee import App, Mode
from jubilee.misc import Log, Misc

class SubmodesApp(App):
	""" Submodes app. """

	def init(self):
		self.add_mode(MainMode)

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
		self.set_submode('generating')
		self.buffer = []
		self.buffer_size = 100

	def enter_generating(self, mode_parameters: dict=None):
		self.buffer = []
	
	def process_generating(self):
		""" Process method for generating submode. """

		color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
		self.buffer.append(color)
		if len(self.buffer) == self.buffer_size:
			self.set_submode('showing')

	def draw_generating(self):
		""" Draw method for generating submode. """
		
		self.app.center_text(f'Generating: {len(self.buffer)} / 100', 20)
		self.show_buffer()

	def process_showing(self):
		""" Process mode for showing submode. """
		
		rotate = self.buffer.pop()
		self.buffer.insert(0, rotate)

	def click_showing(self, x, y):
		""" Click handler for showing submode. """

		self.set_submode('generating')
	
	def draw_showing(self):
		""" Draw method for showing submode. """

		self.app.center_text(f'Complete (click/touch to restart)', 20)
		self.show_buffer()

	def show_buffer(self):
		""" Draw buffer on display. """
		
		left = self.app.screen_center - self.buffer_size
		self.app.fill_rect(left-2, 48, self.buffer_size*2+4, 54, color='white')
		for i in range(len(self.buffer)):
			color = Misc.get_color(self.buffer[i])
			self.app.fill_rect(left+i*2, 50, 2, 50, color=color)
	
if __name__ == '__main__':
	SubmodesApp().run()
