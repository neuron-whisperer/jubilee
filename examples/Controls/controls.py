""" Controls Jubilee app. """

from jubilee import App, Mode
from jubilee.controls import Button, LabeledControl, HoldButton, CheckButton, ToggleButton, SelectButton

class ControlsApp(App):
	""" Controls app. """

	def init(self):
		self.add_mode(ControlsMode)

class ControlsMode(Mode):
	""" Controls mode. """

	def init(self):
		""" ControlsMode init method. """

		self.click_timer = 0
		self.name = 'Controls'
		self.add_control(Button('Button', 10, 50, 100, 40, click=self.set_click))
		self.add_control(HoldButton('HoldButton', 130, 50, 100, 40, click=self.set_click))
		check_button = CheckButton(10, 100, 20, 20, click=self.set_click)
		self.add_control(LabeledControl('Labeled CheckButton', check_button, offset=150))
		toggle_button = ToggleButton(10, 130, 20, 20, click=self.set_click)
		self.add_control(LabeledControl('Labeled ToggleButton', toggle_button, offset=150))
		select_button = SelectButton(10, 170, 100, 40, ['Option 1', 'Option 2', 'Option 3'], click=self.set_click)
		self.add_control(LabeledControl('Labeled SelectButton', select_button, offset=150))

	def set_click(self):
		""" Starts timer to display "click" message. """

		self.click_timer = 8

	def draw(self):
		""" ControlsMode draw method. """

		self.app.draw_text('Status:', 100, 20)
		if self.click_timer > 0:
			color = int(255 * self.click_timer / 8) 
			self.click_timer -= 1
			self.app.draw_text('Click!', 180, 20, color=(color, color, color))

if __name__ == '__main__':
	ControlsApp().run()
