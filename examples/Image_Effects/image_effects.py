""" ImageEffects Jubilee app. """

from jubilee import App, Mode
from jubilee.base_classes import Sprite

class Robot(Sprite):
	""" Robot class. Subclassed from Sprite for convenience.
			Robot image source: https://commons.wikimedia.org/wiki/File:Koronba_pixel_art.png """

	def __init__(self, app, mode):
		super().__init__(animation=app.get_animation('robot'))
		self.app = app
		self.mode = mode
		self.set_sequence('standing')
		self.x = self.app.screen_center
		self.y = self.app.screen_middle + 120
		mode.add_sprite(self)

	def process(self):
		""" Process method for Robot. Moves randomly. """

		graphics_mode = (self.mode.mode_timer // 40) % 4
		graphics_count = self.mode.mode_timer % 40
		self.scale = None
		self.flip_x = False
		self.flip_y = False
		self.rotate = None
		self.hue_shift = None
		if graphics_mode == 0:
			self.scale = 0.5 + (graphics_count + 1) / 20		# scale size from 0.5 to 1.5
		elif graphics_mode == 1:
			self.flip_x = (self.mode.mode_timer % 10 >= 5)
			self.flip_y = (self.mode.mode_timer % 20 >= 10)
		elif graphics_mode == 2:
			self.rotate = 360 * (graphics_count + 1) / 40
		elif graphics_mode == 3:
			self.hue_shift = 360 * (graphics_count + 1) / 40

class ImageEffectsApp(App):
	""" ImageEffects app. """

	def init(self):
		""" Images app initializer. """
		
		self.add_mode(ImageEffectsMode)

class ImageEffectsMode(Mode):
	""" ImageEffects mode. """

	def init(self):
		""" ImageEffects mode initializer. """
		
		self.name = 'ImageEffects'
		self.robot = Robot(self.app, self)
		self.add_sprite(self.robot)

	def process(self):
		self.robot.process()

	def draw(self):
		""" Draw method for ImageEeffects mode. """

		self.render_sprites()										# render robot

if __name__ == '__main__':
	ImageEffectsApp().run()
