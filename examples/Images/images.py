""" Images Jubilee app. """

import random
from jubilee import App, Mode
from jubilee.base_classes import Sprite

class Bubble:
	""" Bubble class.
			Bubble image source: https://freesvg.org/img/food-blue-bubble.png """

	def __init__(self, app):
		self.app = app
		self.x = random.randint(0, self.app.screen_width)
		self.y = self.app.screen_height + 50

	def process(self):
		""" Process method for Bubble. Moves up the screen until it vanishes off the top. """

		self.x = max(0, min(self.app.screen_width, self.x + random.randint(-1, 1)))
		self.y -= 3
		return (self.y < -10)

	def draw(self):
		""" Draw method for Robot. """

		self.app.blit('bubble', self.x, self.y, position='center')

class Robot(Sprite):
	""" Robot class. Subclassed from Sprite for convenience.
			Robot image source: https://commons.wikimedia.org/wiki/File:Koronba_pixel_art.png """

	def __init__(self, app, mode):
		super().__init__(app.animations['robot'])
		self.app = app
		self.set_sequence('standing')
		self.x = random.randint(0, self.app.screen_width)
		self.y = random.randint(0, self.app.screen_height)
		mode.add_sprite(self)

	def process(self):
		""" Process method for Robot. Moves randomly. """
		
		if random.randint(0, 20) == 0:
			self.x = max(0, min(self.app.screen_width, self.x + random.randint(-5, 5)))
		elif random.randint(0, 20) == 0:
			self.y = max(0, min(self.app.screen_height, self.y + random.randint(-5, 5)))

class Player(Sprite):
	""" Player class. Subclassed from Sprite for convenience. """

	def __init__(self, app, mode):
		super().__init__(app.animations['player'])
		self.app = app
		self.x = app.screen_center
		self.y = app.screen_middle
		mode.add_sprite(self)

	def process(self):
		""" Process method for Player. Moves and animates based on keyboard input. """
		
		moving = False
		speed = 5
		for direction in ['up', 'down', 'left', 'right']:
			if direction not in self.app.held_keys:
				continue
			moving = True
			if self.sequence == direction:
				self.animate()
			else:
				self.set_sequence(direction)
			if direction == 'up':
				self.y = max(10, self.y - speed)
			elif direction == 'down':
				self.y = min(self.app.screen_height, self.y + speed)
			elif direction == 'left':
				self.x = max(50, self.x - speed)
			elif direction == 'right':
				self.x = min(self.app.screen_width - 50, self.x + speed)
		if moving is False:
			self.set_sequence('standing')

class ImagesApp(App):
	""" Images app. """

	def init(self):
		""" Images app initializer. """
		
		self.add_mode(ImagesMode)

class ImagesMode(Mode):
	""" Images mode. """

	def init(self):
		""" Images mode initializer. """
		
		self.name = 'Images'
		self.bubbles = []
		self.robots = list(Robot(self.app, self) for _ in range(5))			# create 5 robots
		self.player = Player(self.app, self)														# create player

	def process(self):
		""" Process method for Images mode. """

		# process bubbles
		for s in self.sprites:									# process robots and player
			s.process()

		for b in self.bubbles:
			if b.process():
				self.bubbles.remove(b)
		if random.randint(0, 40) == 0:
			self.bubbles.append(Bubble(self.app))

	def draw(self):
		""" Draw method for Images mode. """
		
		self.render_sprites()										# render robots and player
		for b in self.bubbles:									# draw bubbles after (on top of) sprites
			b.draw()

if __name__ == '__main__':
	ImagesApp().run()
