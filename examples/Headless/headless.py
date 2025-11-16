""" Headless Jubilee app. """

import random, sys
from jubilee import App, Mode
from jubilee.misc import Log
from headless_worker import HeadlessWorker

class HeadlessApp(App):
	""" Headless app. """

	def init(self):
		Log.set_console_level(Log.INFO)
		self.add_workers([HeadlessWorker, HeadlessWorker])
		self.add_mode(HeadlessMode)
		self.pings = {}

	def process_message(self, message, sender: str=None):
		""" Process message from worker. """

		action = message.get('action')
		if action == 'pong':		# process message
			ping_id = message.get('id')
			if ping_id not in self.pings:
				Log.error(f'Ping ID {ping_id} not pings')
			else:
				self.pings[ping_id] = True
				Log.info(f'Received pong: {ping_id} from {sender}')
		else:
			super().process_message(message, sender)

class HeadlessMode(Mode):
	""" No_Display mode. """

	def init(self):
		self.name = 'Headless'

	def process(self):
		""" Process method for No_Display mode. """
		
		if random.randint(0, 0) > 0:
			return
		try:
			worker = random.choice(list(self.app.workers.keys()))
			ping_id = len(self.app.pings)
			ping_message = {'action': 'ping', 'id': ping_id}
			self.app.send_message(ping_message, worker)
			Log.info(f'Sent ping {ping_id}')
			self.app.pings[ping_id] = False
		except Exception as e:
			print(e)

if __name__ == '__main__':
	HeadlessApp().run()
