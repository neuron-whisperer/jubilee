""" Screen_Rotation Jubilee app. """

from jubilee import App, Mode

class ScreenRotationApp(App):
	""" ScreenRotation app. """

	def init(self):
		self.add_mode(ScreenRotationMode)

class ScreenRotationMode(Mode):
	""" ScreenRotation mode. """

	def init(self):
		self.name = 'Screen Rotation'

	def draw(self):
		""" Draw method for ScreenRotation mode. """

		self.app.center_text('Rotation', self.app.screen_middle - 20)

if __name__ == '__main__':
	ScreenRotationApp().run()
