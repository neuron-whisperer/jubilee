""" Hello worker. """

from jubilee import Worker

class Hello_Worker(Worker):
	""" Worker class for Hello app. """

	def init(self):
		""" Hello_Worker initializer. """
		
		self.name = 'Hello_Worker'

	def process(self):
		""" Regular (high-frequency) worker processing. """
		super().process()

	def process_periodic(self):
		""" Periodic (low-frequency) worker processing. """
		super().process_periodic()

	def process_message(self, message):
		""" Process a message from app. """

		action = message.get('action', None)
		if action == 'custom action':
			pass
		else:
			super().process_message(message)
