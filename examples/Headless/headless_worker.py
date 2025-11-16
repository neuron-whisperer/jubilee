""" HeadlessWorker worker. """

import time
from jubilee import Worker
from jubilee.misc import Log

class HeadlessWorker(Worker):
	""" HeadlessWorker class for Headless app. """

	def init(self):
		""" HeadlessWorker initializer. """
		
		self.name = f'Worker {int(time.time()) % 100}'
		Log.set_console_level(Log.INFO)

	def process_message(self, message, sender: str=None):
		""" Process a message from app. """

		action = message.get('action', None)
		if action == 'ping':
			Log.info(f'Returned ping {message["id"]}')
			message['action'] = 'pong'
			message['worker'] = self.name
			self.send_message(message)
		else:
			super().process_message(message, sender)
