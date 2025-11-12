""" Script Jubilee app. """

import random, sys
from jubilee import App
from jubilee.base_classes import Button, Mode
from jubilee.misc import Log, Misc

class Script_App(App):
	""" Script app. """

	def init(self):
		self.add_modes([Main_Mode, Graphic_Mode, Sound_Mode])
		self.run_script()

class Main_Mode(Mode):
	""" Main mode. """

	def init(self):
		self.name = 'Main'
		self.submodes = ['ask_graphic', 'ask_sound', 'finish']
		self.set_submode('ask_graphic')

	def enter_ask_graphic(self, mode_parameters: dict=None):
		""" ask_graphic submode enter method. """

		self.remove_controls()
		button_cat = Button(self.app, self.app.screen_center - 150, 50, 100, 50, 'Cat', click=lambda: self.select_graphic('cat'))
		self.add_control(button_cat)
		button_dog = Button(self.app, self.app.screen_center + 50, 50, 100, 50, 'Dog',  click=lambda: self.select_graphic('dog'))
		self.add_control(button_dog)
		self.graphic = None
	
	def draw_ask_graphic(self):
		""" ask_graphic submode draw method. """
		
		self.app.draw_text_center('Select Graphic', 20)

	def select_graphic(self, graphic):
		""" Select graphic method. """
		
		self.app.advance_scene(1 if graphic == 'cat' else 2)

	def enter_ask_sound(self, mode_parameters: dict=None):
		""" ask_sound submode enter method. """

		self.remove_controls()
		button_meow = Button(self.app, self.app.screen_center - 150, 50, 100, 50, 'Meow', click=lambda: self.select_sound('meow'))
		self.add_control(button_meow)
		button_woof = Button(self.app, self.app.screen_center + 50, 50, 100, 50, 'Woof',  click=lambda: self.select_sound('woof'))
		self.add_control(button_woof)
		self.graphic = None

	def draw_ask_sound(self):
		""" ask_sound submode draw method. """
		
		self.app.draw_text_center('Select Sound', 20)

	def select_sound(self, sound):
		self.app.advance_scene(1 if sound == 'meow' else 2)

	def draw_finish(self):
		""" finish submode draw method. """
		
		self.app.draw_text_center('The End', 20)

	def enter_finish(self, mode_parameters: dict=None):
		""" finish submode enter method. """

		self.remove_controls()
		button_restart = Button(self.app, self.app.screen_center - 50, 50, 100, 50, 'Restart', click=self.restart_mode)
		self.add_control(button_restart)

	def restart_mode(self):
		""" Restart mode. """

		self.app.select_scene('Select_Graphic')

class Graphic_Mode(Mode):
	""" Graphic mode. """

	def init(self):
		self.name = 'Graphic'

	def enter(self, mode_parameters: dict=None):
		""" Mode graphic enter method. """

		self.graphic = mode_parameters.get('graphic')

	def click(self, x, y):
		""" Mode graphic click handler. """
		
		self.app.select_scene('Select_Sound')

	def draw(self):
		""" Mode graphic draw method. """
		
		if self.graphic == 'dog':
			self.app.blit('dog', 0, 0)
		elif self.graphic == 'cat':
			self.app.blit('cat', 0, 0)

class Sound_Mode(Mode):
	""" Sound mode. """

	def init(self):
		self.name = 'Sound'

	def enter(self, mode_parameters: dict=None):
		""" Mode sound enter method. """

		self.sound = mode_parameters.get('sound')
		self.remove_controls()
		button_play = Button(self.app, self.app.screen_center - 50, 50, 100, 50, 'Play Sound', click=self.play_sound)
		self.add_control(button_play)
		button_continue = Button(self.app, self.app.screen_center - 50, 120, 100, 50, 'Continue', click=lambda: self.app.select_scene('Finish'))
		self.add_control(button_continue)

	def play_sound(self):
		""" Play sound method. """

		self.app.play_sound(self.sound)
			
	def draw(self):
		""" Mode sound draw method. """

		self.app.draw_text_center(f'Ready to play sound: {self.sound}', 20)

if __name__ == '__main__':
	Script_App().run()
