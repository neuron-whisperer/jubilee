""" HeadlessWorker worker. """

import time
from jubilee import Worker
from jubilee.misc import Log

class HeadlessWorker(Worker):
	""" HeadlessWorker class for Headless app. """

	def init(self):
		""" HeadlessWorker initializer. """
		
		self.name = f'Worker {int(time.time()) % 100}'
		Log.console_level = 'Info'

	def process_message(self, message):
		""" Process a message from app. """

		action = message.get('action', None)
		if action == 'ping':
			Log.info('HeadlessWorker', 'process_message', f'Returned ping {message["id"]}')
			message['action'] = 'pong'
			message['worker'] = self.name
			self.send_message(message)
		else:
			super().process_message(message)
