""" Pointer Jubilee app. """

import random
from jubilee import App
from jubilee.base_classes import Mode

class Circle:
	""" Pointer Circle class. """

	max_radius = 50

	def __init__(self, app, x, y):
		self.app = app
		self.x = x
		self.y = y
		self.radius = 2
		self.color = (random.randint(64, 255), random.randint(64, 255), random.randint(64, 255))

	def process(self) -> bool:
		""" Process function for Circle - expands and incrementally fades colors. """

		self.radius += 1
		return (self.radius == self.max_radius)		# return True if circle should be removed

	def draw(self):
		""" Draw method for Circle - draws filled circle on surface, then blits with alpha. """

		c = self.app.create_surface(self.radius*2, self.radius*2, color=None, alpha_blend=True)
		c.set_alpha(255 * (1.0 - (self.radius / self.max_radius)))
		self.app.fill_circle(self.radius, self.radius, self.radius, color=self.color, dest=c)
		self.app.blit(c, self.x-self.radius, self.y-self.radius)

class Pointer_App(App):
	""" Pointer app. """

	def init(self):
		self.add_mode(Pointer_Mode)

class Pointer_Mode(Mode):
	""" Pointer mode. """

	def init(self):
		self.name = 'Pointer'
		self.circles = []

	def click(self, x, y):
		""" Click event handler for Pointer mode. """

		self.circles.append(Circle(self.app, x, y))

	def process(self):
		""" Process method for Hello mode. """

		for c in self.circles:
			if c.process():
				self.circles.remove(c)

	def draw(self):
		""" Draw method for Hello mode. """

		for c in self.circles:
			c.draw()
		self.app.draw_text_center('Click anywhere!')

if __name__ == '__main__':
	Pointer_App().run()
