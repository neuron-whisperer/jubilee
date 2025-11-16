""" Jubilee Log mode class. """

import math, platform, time
try:
	import psutil
except:
	psutil = None
from .mode import Mode
from .controls import Button
from .misc import Log

class LogMode(Mode):
	""" Log mode class. """

	def __init__(self, background_color: str='black'):
		self.log_date = None
		self.log_text = []
		self.log_line_height = 11
		self.log_lines_per_page = 25
		self.date_width = 75
		self.font_size = 12
		self.class_name_width = 125
		self.method_name_width = 125
		self.level_name_width = 40
		self.log_page = 0
		self.max_log_size = 100
		self.button_font = None
		self.return_mode = None
		self.return_mode_parameters = None
		self.back_button = None
		self.last_process = None
		self.cpu_load = []
		self.cpu_temp = []
		super().__init__(background_color=background_color)

	def init(self):
		""" LogMode initializer. """

		self.name = 'Log'

		# add page size from app
		self.log_lines_per_page = int((self.app.screen_height - 180) / self.log_line_height)

		# create controls for log mode
		button_width = 77
		self.add_control(Button('Font', self.app.button_margin, self.app.screen_height - 60,
			button_width, 60, font=self.button_font, click=self.change_font))
		self.add_control(Button('Up', button_width + self.app.button_margin * 2,
			self.app.screen_height - 60, button_width, 60, font=self.button_font,
			click=self.log_page_up))
		self.add_control(Button('Down', button_width * 2 + self.app.button_margin * 3,
			self.app.screen_height - 60, button_width, 60, font=self.button_font,
			click=self.log_page_down))

		# create Back button
		self.back_button = Button('Back', self.app.screen_width-77-self.app.button_margin,
			self.app.screen_height-60, 77, 60, font=self.button_font,
			click=self.back_click)
		self.add_control(self.back_button)

		# By default, the Back button causes the app to return to the mode from which it
		# was called. The return mode can be set statically in this initializer, or
		# dynamically using this code:
		# 	self.app.modes['Log'].back_button.target_mode = return_mode

	def enter(self, mode_parameters: dict=None):
		""" Log mode enter method. """

		super().enter(mode_parameters)
		self.return_mode = mode_parameters.get('previous_mode', self.return_mode)
		self.log_page = 0
		self.check_log()

	def back_click(self):
		""" Handles Back button click. """

		mode = self.back_button.target_mode or self.return_mode
		if mode is None:
			Log.error('No mode to switch back to')
		else:
			self.app.set_mode(mode, mode_parameters=self.return_mode_parameters)

	def process(self):
		""" Log mode process method. Runs at 1 Hz. """

		try:
			now = time.time()
			if self.last_process is not None and now - self.last_process < 1:
				return
			self.last_process = now
			self.check_log()
			self.record_cpu_temperatures()
		except Exception as e:
			Log.error(e)

	def check_log(self):
		""" Check status of log and reload if changed. """

		try:
			modification_date = Log.get_modification_date()
			if modification_date == self.log_date:
				return
			self.log_date = modification_date
			log_lines = Log.read()[-self.max_log_size:]
			self.log_text = list(reversed(log_lines))
		except Exception as e:
			Log.error(e)

	def record_cpu_temperatures(self):
		""" Record CPU temperatures. """

		if psutil is None:
			return
		try:
			max_graph_points = self.app.screen_width - 180
			try:
				self.cpu_load.append(int(psutil.cpu_percent()))
				self.cpu_load = self.cpu_load[-max_graph_points:]
			except:
				pass
			temperature = None
			if platform.system() != 'Darwin':
				temperature_metrics = psutil.sensors_temperatures() or {}
				for key in ('cpu-thermal', 'cpu_thermal', 'coretemp', 'k10temp', 'soc_thermal'):
					if temperature_metrics.get(key) is not None:
						temperature = int(temperature_metrics[key][0].current)
						break
			if temperature is not None:
				self.cpu_temp.append(temperature)
				self.cpu_temp = self.cpu_temp[-max_graph_points:]
		except Exception as e:
			Log.error(e)

	def draw(self):
		""" Log mode draw method. """

		try:
			# draw CPU load
			graph_x = 90
			if len(self.cpu_load) > 0:
				self.app.draw_text(f'CPU: {self.cpu_load[-1]}%', self.app.margin, 20)
				self.app.draw_line(graph_x, 10, graph_x, 49)
				self.app.draw_line(graph_x, 49, self.app.screen_width - 20, 49)
				for i in range(1, len(self.cpu_load)):
					cpu = 48 - int(self.cpu_load[i] / 100.0 * 38.0)
					self.app.draw_pixel(graph_x + i + 1, cpu)
	
			# draw CPU temp
			if len(self.cpu_temp) > 0:
				self.app.draw_text(f'Temp: {self.cpu_temp[-1]} C', self.app.margin, 70)
				self.app.draw_line(graph_x, 60, graph_x, 99)
				self.app.draw_line(graph_x, 99, self.app.screen_width - 20, 99)
				for i, temp in enumerate(self.cpu_temp):
					cpu = 98 - int(temp / 100.0 * 38.0)
					self.app.draw_pixel(graph_x + i + 1, cpu)
	
			# check page_down and ensure that it has not gone past end of log
			if self.log_lines_per_page < 1:
				Log.debug(f'log_lines_per_page = {self.log_lines_per_page}')
				return
			num_pages = math.ceil(len(self.log_text) / self.log_lines_per_page)
			self.log_page = max(0, min(self.log_page, num_pages - 1))
	
			# draw log
			y = 95 + self.log_line_height
			self.app.draw_text('Log', self.app.margin, y)
			y += self.app.underscore_position
			self.app.draw_line(self.app.margin, y, self.app.screen_width - self.app.margin, y)
			font = self.app.standard_font_sizes[self.font_size]
			for i in range(self.log_lines_per_page):
				line_number = self.log_page * self.log_lines_per_page + i
				if line_number >= len(self.log_text):
					break
				record_fields = Log.parse(self.log_text[line_number])
				if record_fields is None:
					continue
				y += self.log_line_height
				self.app.draw_text(record_fields['dt'].strftime('%Y%m%d %H:%M:%S'), self.app.margin, y, font=font)
				x = self.app.margin + self.date_width
				self.app.draw_text(record_fields['class'], x, y, font=font)
				x += self.class_name_width
				self.app.draw_text(record_fields['method'], x, y, font=font)
				x += self.method_name_width
				self.app.draw_text(record_fields['level'], x, y, font=font)
				x += self.level_name_width
				self.app.draw_text(record_fields['message'], x, y, font=font)
		except Exception as e:
			Log.error(e)

	def change_font(self):
		""" Changes font. """

		self.app.change_font()
		self.app.set_popover(f'Changed font to {self.app.standard_font}')

	def log_page_up(self):
		""" Scrolls log up one page. """

		self.log_page = max(self.log_page - 1, 0)

	def log_page_down(self):
		""" Scrolls log down one page. """

		self.log_page = self.log_page + 1
