""" No_Display Jubilee app. """

import random, sys
from jubilee import App
from jubilee.base_classes import Mode
from jubilee.misc import Log
from no_display_worker import No_Display_Worker

class No_Display_App(App):
	""" No_Display app. """

	def init(self):
		Log.console_level = 'Info'
		self.add_workers([No_Display_Worker, No_Display_Worker])
		self.add_mode(No_Display_Mode)
		self.pings = {}

	def process_message(self, message):
		""" Process message from worker. """

		action = message.get('action')
		if action == 'pong':		# process message
			ping_id = message.get('id')
			worker = message.get('worker')
			if ping_id not in self.pings:
				Log.error('No_Display_App', 'process_message', f'Ping ID {ping_id} not pings')
			else:
				self.pings[ping_id] = True
				Log.info('No_Display_App', 'process_message', f'Received pong: {ping_id} from {worker}')
		else:
			super().process_message(message)

class No_Display_Mode(Mode):
	""" No_Display mode. """

	def init(self):
		self.name = f'No Display Mode'

	def process(self):
		""" Process method for No_Display mode. """
		
		if random.randint(0, 0) == 0:
			try:
				worker = random.choice(list(self.app.workers.keys()))
				ping_id = len(self.app.pings)
				ping_message = {'action': 'ping', 'id': ping_id}
				self.app.send_message(ping_message, worker)
				Log.info('No_Display_Mode', 'process', f'Sent ping {ping_id}')
				self.app.pings[ping_id] = False
			except Exception as e:
				print(e)

if __name__ == '__main__':
	No_Display_App().run()
