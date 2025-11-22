""" Rotation Jubilee app. """

from jubilee import App, Mode
from jubilee.controls import Button

class RotationApp(App):
	""" Rotation app. """

	def init(self):
		self.add_mode(RotationMode)

class RotationMode(Mode):
	""" Rotation mode. """

	def init(self):
		self.name = 'Rotation'

	def draw(self):
		""" Draw method for Hello mode. """

		self.app.center_text('Rotation', self.app.screen_middle - 20)

if __name__ == '__main__':
	RotationApp().run()
