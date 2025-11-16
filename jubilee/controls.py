""" Jubilee controls. """

from pygame.font import Font
from .misc import Log

class Control:
	""" Jubilee user control base class. """

	def __init__(self, x: int|float, y: int|float, width: int|float, height: int|float,
			click=None, hold=None, release=None, name: str=None, parameters: dict=None):
		self.app = None			# this is set in mode.add_control()
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.provided_click_handler = click
		self.provided_hold_handler = hold
		self.provided_release_handler = release
		self.name = name or 'Control'
		self.parameters = parameters or {}

	def bind(self, app):
		""" Control bind method for adding to a mode. """

		self.app = app

	def collide(self, x: int|float, y: int|float):
		""" Control collision detection method. """

		return (self.x <= x < self.x + self.width and self.y <= y < self.y + self.height)

	def on_click(self):
		""" Control click event receiver. """

		if self.provided_click_handler is not None:
			self.provided_click_handler()

	def on_hold(self):
		""" Control hold event receiver. """

		if self.provided_hold_handler is not None:
			self.provided_hold_handler()

	def on_release(self):
		""" Control release event receiver. """

		if self.provided_release_handler is not None:
			self.provided_release_handler()

	def draw(self):
		""" Draw method. """

	def exit_handler(self):
		""" Control handler method for exiting app. """

		self.app.exit()

class LabeledControl(Control):
	""" Wrapper to add a left-side label to a control.
			Optionally specify an x offset for the control; default uses text width.
	"""

	def __init__(self, caption: str, control: Control, offset: int=None,
		font: Font|str=None, color='white', name: str=None, parameters: dict=None):
		super().__init__(control.x, control.y, control.width, control.height,
			name=name, parameters=parameters)
		self.control = control
		self.caption = caption
		self.label_font = font
		self.color = color
		self.offset = offset
		self.name = name or f'LabeledControl: {self.control.name}'
		self.is_initilized = False

	def bind(self, app):
		""" Control bind method for adding to a mode. """

		super().bind(app)
		self.set_layout()
		if self.control is not None:
			self.control.bind(app)

	def set_layout(self):
		""" Sets position of control based on layout. """

		offset = self.offset
		label_height = self.control.height
		if offset is None:		# calculate offset from caption size
			try:
				offset, label_height = self.app.get_text_size(self.caption, font=self.label_font)
			except Exception as e:
				Log.error(f'get_text_size failed: {e}')
				return
		self.control.x = self.x + offset
		self.width = offset + self.control.width
		self.height = max(label_height, self.control.height)

	def set_caption(self, caption: str):
		""" Sets caption. """

		self.caption = caption
		self.set_layout()

	def collide(self, x: int|float, y: int|float):
		""" LabeledControl collide function - tests only against underlying control. """

		return self.control.collide(x, y)

	def on_click(self):
		""" LabeledControl on_click event receiver. """

		self.control.on_click()

	def on_hold(self):
		""" LabeledControl on_hold event receiver. """

		self.control.on_hold()

	def on_release(self):
		""" LabeledControl on_release event receiver. """

		self.control.on_release()

	def draw(self):
		""" LabeledControl draw function. """

		try:
			y = self.control.y + (self.control.height / 2)
			self.app.draw_text(self.caption, self.x, y, color=self.color, font=self.label_font, alignment='left')
			self.control.draw()
		except Exception as e:
			Log.error(e)

class Button(Control):
	""" Button user control. """

	def __init__(self, caption: str, x: int|float, y: int|float, width: int|float,
			height: int|float, target_mode=None, target_mode_parameters: dict=None,
			click=None, hold=None, release=None, app_exit: bool=False,
			font: Font|str=None, color='white', background_color='black',
			name: str=None, parameters: dict=None):
		super().__init__(x, y, width, height, click=click, hold=hold, release=release,
			name=name, parameters=parameters)
		# note: the provided_click_handler is saved so that if user later sets or changes
		# target_mode or app_exit, the button-specific click handler included in this class
		# will correctly hand off to the correct function.
		# specifying target_mode or app_exit will override click
		self.caption = caption
		self.target_mode = target_mode
		self.target_mode_parameters = target_mode_parameters
		self.app_exit = app_exit
		self.font = font
		self.color = color
		self.name = name or f'Button: {caption}'
		self.background_color = background_color

	def on_click(self):
		""" Button click event receiver. """

		if self.target_mode:
			self.app.set_mode(self.target_mode, mode_parameters=self.target_mode_parameters)
		elif self.app_exit:
			self.app.exit()
		else:
			super().on_click()

	def draw(self):
		""" Button draw method. """

		try:
			if self.background_color is not None:
				self.app.fill_rect(self.x, self.y, self.width, self.height, color=self.background_color)
			self.app.draw_rect(self.x, self.y, self.width, self.height, line_width=self.app.button_border, color=self.color)
			x = int(self.x + self.width / 2)
			y = int(self.y + self.height / 2)
			self.app.draw_text(self.caption, x, y, color = self.color, font = self.font, alignment = 'center')
		except Exception as e:
			Log.error(e)

class HoldButton(Button):
	""" Hold button user control that calls .click() after a hold period.
			This is a wrapper class for the basic button. This class accepts the usual button
			parameters, including target_mode and app_exit, but overrides click and only
			calls it when .hold_steps == .hold_step. A completion of the hold event calls
			the Button click function, which handles target_mode and app_exit.
			hold_steps indicates how many frames the hold should take for activation.
			hold_color indicates the color to fill the button as a progress bar. """

	def __init__(self, caption: str, x: int|float, y: int|float, width: int|float,
			height: int|float, hold_color='red', hold_steps: int=12, click=None, hold=None,
			release=None, target_mode=None, target_mode_parameters: dict=None,
			app_exit: bool=False, font: Font|str=None, color='white', background_color=None,
			name: str=None, parameters: dict=None):

		super().__init__(caption, x, y, width, height, target_mode=target_mode,
			target_mode_parameters=target_mode_parameters,
			click=click, hold=hold, release=release,
			app_exit=app_exit, font=font, color=color, background_color=background_color,
			name=name, parameters=parameters)
		self.hold_steps = max(1, int(hold_steps))
		self.hold_step = 0
		self.hold_color = hold_color
		self.name = name or f'HoldButton: {caption}'

	def on_click(self):
		""" HoldButton click event receiver. """

		self.hold_step = 0

	def on_hold(self):
		""" HoldButton hold event receiver. """

		if self.hold_step + 1 == self.hold_steps:
			super().on_click()
		else:
			super().on_hold()
		self.hold_step = min(self.hold_step + 1, self.hold_steps)

	def on_release(self):
		""" HoldButton release event receiver. """

		self.hold_step = 0
		super().on_release()

	def draw(self):
		""" HoldButton draw method. """

		try:
			if self.background_color is not None:
				self.app.fill_rect(self.x, self.y, self.width, self.height, color=self.background_color)
			self.app.draw_rect(self.x, self.y, self.width, self.height, line_width=self.app.button_border, color=self.color)
			progress = int((self.width - 4) * self.hold_step / max(1, self.hold_steps))
			progress = max(0, min(self.width - 4, progress))
			if progress > 0 and self.hold_color is not None:
				self.app.fill_rect(self.x + 2, self.y + 2, progress, self.height - 4, color=self.hold_color)
			x = int(self.x + self.width / 2)
			y = int(self.y + self.height / 2)
			self.app.draw_text(self.caption, x, y, color = self.color, font = self.font, alignment = 'center')
		except Exception as e:
			Log.error(e)

class CheckButton(Control):
	""" Check button user control that toggles self.checked. """

	def __init__(self, x: int|float, y: int|float, width: int|float, height: int|float,
	             box_color='white', check_color='red', check_width=5, background_color=None,
	             checked: bool=False, click=None, hold=None, release=None,
	             name: str=None, parameters: dict=None):
		super().__init__(x, y, width, height, click=click, hold=hold, release=release,
			name=name, parameters=parameters)
		self.checked = bool(checked)
		self.box_color = box_color
		self.check_color = check_color
		self.check_width = check_width
		self.background_color = background_color
		self.name = name or 'CheckButton'

	def on_click(self):
		""" CheckButton click event receiver. """

		self.checked = not self.checked
		super().on_click()

	def set_checked(self, checked: bool, do_click: bool=False):
		""" Programmatically set check state; optionally call the click handler
				if the check state changes. """

		if self.checked == checked:
			return
		if do_click is True:
			self.on_click()
		else:
			self.checked = checked

	def draw(self):
		""" CheckButton draw method."""

		try:
			if self.background_color is not None:
				self.app.fill_rect(self.x, self.y, self.width, self.height, color=self.background_color)
			self.app.draw_rect(self.x, self.y, self.width, self.height, line_width=self.app.button_border, color=self.box_color)
			if self.checked:		# draw x
				x1 = int(self.x + 3)
				y1 = int(self.y + 4)
				x2 = int(self.x + self.width - 6)
				y2 = int(self.y + self.height - 4)
				self.app.draw_line(x1, y1, x2, y2, width=self.check_width, color=self.check_color)
				self.app.draw_line(x1, y2, x2, y1, width=self.check_width, color=self.check_color)
		except Exception as e:
			Log.error(e)

class ToggleButton(Control):
	""" Toggle button user control that toggles self.toggled. """

	def __init__(self, x: int|float, y: int|float, width: int|float, height: int|float,
		toggled: bool=False, color='white', toggled_color='green', background_color='black',
		click=None, hold=None, release=None, name: str=None, parameters: dict=None):

		super().__init__(x, y, width, height, click=click, hold=hold, release=release,
			name=name, parameters=parameters)
		self.toggled = bool(toggled)
		self.color = color
		self.toggled_color = toggled_color
		self.background_color = background_color
		self.name = name or 'ToggleButton'

	def on_click(self):
		""" ToggleButton click event receiver. """

		self.toggled = not self.toggled
		super().on_click()

	def set_toggled(self, toggled: bool, do_click: bool=False):
		""" Programmatically set toggle state; optionally call the click handler
				if the toggle state changes."""

		if self.toggled == toggled:
			return
		if do_click is True:
			self.on_click()
		else:
			self.toggled = toggled

	def draw(self):
		""" ToggleButton draw method."""

		try:
			color = self.toggled_color if self.toggled else self.background_color
			if color is not None:
				self.app.fill_rect(self.x + 2, self.y + 2, self.width - 4, self.height - 4, color=color)
			self.app.draw_rect(self.x, self.y, self.width, self.height, line_width=self.app.button_border, color=self.color)
		except Exception as e:
			Log.error(e)

class SelectButton(Control):
	""" Select button control that cycles through a list of items.
			items can include a list of ints, strings, or None.
			If a values list is provided, then the items list provides the captions for the
			control, and .value is the entry in the .values list corresponding the selected item.
			Click advances to the next item, with wraparound.
			Current selection is available as .selected_index, .selected_item, and .value.
	"""

	def __init__(self, x: int|float, y: int|float, width: int|float, height: int|float,
		items: list, values: list=None, selected_index: int=0,
		color='white', background_color='black', font: Font|str=None,
		click=None, hold=None, release=None,
		name: str=None, parameters: dict=None):

		super().__init__(x, y, width, height, click=click, hold=hold, release=release,
			name=name, parameters=parameters)

		self.items = list(items) if items is not None else []
		self.values = values
		self.selected_index = None
		self.selected_item = None
		self.value = None
		self.color = color
		self.background_color = background_color
		self.font = font
		self.name = self.name or 'SelectButton'

		if self.values is not None and len(self.items) != len(self.values):
			Log.error(f'len(self.items) ({len(self.items)}) != len(self.values) ({len(self.values)})')
			return
		self.set_selected_index(selected_index)

	def set_items(self, items: list, values: list=None, reset_to_first: bool=True):
		""" Replace the items list; by default, reset selection to the first item. """

		self.items = list(items) if items is not None else []
		if len(self.items) == 0:
			self.selected_index = None
		elif reset_to_first or self.selected_item not in self.items or (self.selected_index is not None and self.selected_index >= len(self.items)):
			self.selected_index = 0
		elif self.selected_item in self.items:
			self.selected_index = self.items.index(self.selected_item)
		self.values = values if values is not None else self.values
		if self.values is not None and len(self.items) != len(self.values):
			Log.error(f'len(self.items) ({len(self.items)}) != len(self.values) ({len(self.values)})')
			self.selected_index = None
			self.selected_item = None
			self.value = None
			self.values = None
			return
		self.set_selected_index(self.selected_index)

	def on_click(self):
		""" SelectButton on_click event receiver. """

		if len(self.items) > 0:
			self.set_selected_index(0 if self.selected_index is None else (self.selected_index + 1) % len(self.items), do_click=True)

	def set_selected_item(self, item, do_click: bool=False):
		""" Programmatically set selection by item. Optionally calls the click handler
				if the selection changes. """

		if item not in self.items:
			Log.error(f'Item not in items: {item}')
			return
		index = self.items.index(item)
		self.set_selected_index(index, do_click=do_click)

	def set_selected_index(self, index: int, do_click: bool=False):
		""" Programmatically set selection by index. Optionally calls the click handler
				if the selection changes. """

		if index is None:
			self.selected_index = None
			self.selected_item = None
			self.value = None
			return
		if len(self.items) == 0:
			Log.error('No items to select')
			return
		if index < 0 or index >= len(self.items):
			Log.error(f'Index out of range: {index}')
			return
		if self.selected_index == index:
			return
		self.selected_index = index
		self.selected_item = self.items[index]
		self.value = self.values[self.selected_index] if self.values is not None else None
		if do_click is True:
			super().on_click()

	def draw(self):
		""" SelectButton draw method. """

		try:
			if self.background_color is not None:
				self.app.fill_rect(self.x, self.y, self.width, self.height,
					color=self.background_color)
			self.app.draw_rect(self.x, self.y, self.width, self.height,
				line_width=self.app.button_border, color=self.color)
			if self.selected_index is None:
				return
			label = str(self.selected_item).strip()
			if len(label) == 0:
				return
			cx = int(self.x + self.width / 2)
			cy = int(self.y + self.height / 2)
			self.app.draw_text(label, cx, cy, color=self.color, font=self.font, alignment='center')
		except Exception as e:
			Log.error(e)
