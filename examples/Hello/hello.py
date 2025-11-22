""" Hello Jubilee app. """

from jubilee import App, Mode
from jubilee.controls import Button
from hello_worker import HelloWorker

class HelloApp(App):
	""" Hello app. """

	def init(self):
		self.add_worker(HelloWorker)
		self.add_mode(HelloMode)
		self.set_mode('Hello')						# note: first mode is selected by default

	def process_message(self, message, sender: str=None):
		""" Process message from worker. """

		action = message.get('action')
		if action == 'custom action':		# process message
			pass
		else:
			super().process_message(message, sender)

class HelloMode(Mode):
	""" Hello mode. """

	def init(self):
		self.name = 'Hello'
		self.click_count = 0
		x = self.app.screen_center - 50; y = self.app.screen_middle - 30
		self.add_control(Button('Hello, World!', x, y, 100, 60, click=self.clicked_hello))

	def clicked_hello(self):
		""" Click handler for Hello button. """
		self.click_count += 1

	def enter(self, mode_parameters: dict=None):
		""" Enter method for Hello mode. """
		super().enter(mode_parameters)

	def set_submode(self, name: str=None, mode_parameters: dict=None):
		""" Set_submode method for Hello mode. """
		super().set_submode(name, mode_parameters)

	def click(self, x: int|float, y: int|float):
		""" Click event handler for Hello mode. """
		super().click(x, y)											# this can be skipped to override control input

	def process(self):
		""" Process method for Hello mode. """

	def draw(self):
		""" Draw method for Hello mode. """

		# draw text in default font to show click count
		text = f'Click Count: {self.click_count}'
		self.app.center_text(text, self.app.screen_middle + 50)

if __name__ == '__main__':
	HelloApp().run()
