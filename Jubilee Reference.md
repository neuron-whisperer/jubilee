# Jubilee Reference

- [Jubilee Reference](#jubilee-reference)
  - [App Class Reference](#app-class-reference)
    - [Example App](#example-app)
    - [App Class Fields and Methods](#app-class-fields-and-methods)
    - [Drawing](#drawing)
    - [Surfaces and Images](#surfaces-and-images)
    - [Sound](#sound)
    - [Music](#music)
    - [Pointer (Touch or Mouse) Input](#pointer-touch-or-mouse-input)
    - [Keyboard Input](#keyboard-input)
    - [App State](#app-state)
    - [Scripting](#scripting)
    - [Fonts](#fonts)
  - [Mode Class Reference](#mode-class-reference)
    - [Example Mode](#example-mode)
    - [Mode Class Fields and Methods](#mode-class-fields-and-methods)
    - [Controls](#controls)
    - [Submodes](#submodes)
  - [Worker Class Reference](#worker-class-reference)
    - [Example Worker](#example-worker)
    - [Worker Class Fields and Methods](#worker-class-fields-and-methods)
  - [config.txt](#config-txt)
  - [misc.py Reference](#misc-py-reference)
    - [Config](#config)
    - [Log](#log)
    - [Color](#color)
    - [Misc](#misc)

## App Class Reference

### Example App

```
class Example_App(App):

    def init(self):
        """ Main app initializer. """
        self.add_worker(Example_Worker)
        self.add_mode(Example_Mode)

    def process_message(self, message, sender: str=None):
        """ Process a message from worker. """
			
        action = message.get('action')
        if action == 'pong':  						# custom message handling
            pass
        else:										# default message handlers
            super().process_message(message, sender)
```

### App Class Fields and Methods

```
config: dict                              # application configuration
update_config(key, value)			      # message worker to update config
headless: bool=False                      # headless mode (defaults to False)
screen_width, screen_height: int          # screen width and height
screen_center: int                        # horizontal center (x/2)
screen_middle: int                        # screen vertical middle (y/2)
base_path: str                            # application base path
init()                                    # called after base class __init__()
add_worker(Worker: type)                  # add worker class to app
add_workers([Worker, Worker])             # add several workers to app
add_mode(Mode: type|Mode)                 # add mode (class or instance) to app
add_modes([Mode, Mode])                   # add several modes to app
set_mode(mode, mode_parameters=None)      # mode = name or Mode object
mode: Mode                                # current Mode
send_message(message, worker_name=None)   # str or dict; default=send to first worker
	# messages are sent as dicts - a string will be sent as {'action': message}
reboot()                                  # device reboot
shut_down()                               # device shutdown
exit(code = 0)                            # app exit function
```

### Drawing
All methods draw to a given dest surface, or None for screen.
Colors can be a name, an RGB tuple, or an enum like Color.BLACK. See misc.py for a full list of colors.
Fonts can be a pygame.font.SysFont, a font name, or None for default font.

```
fill_screen(color='white')
fill_color(color='white', dest=None)
fill_static(dest=None)                                        # fill with white noise
draw_text(text, x, y, color=None, font=None, alignment='left', dest=None)
center_text(text, y=None, color=None, font=None, dest=None)   # default=screen center
get_text_size(text, font=None) -> (int, int)
draw_pixel(x, y, color='white', dest=None)
draw_line(x1, y1, x2, y2, width=1, color='white', dest=None)
draw_rect(left, top, width, height, line_width=1, color='white', dest=None)
fill_rect(left, top, width, height, color='white', dest=None)
draw_polygon(coordinates, width=1, color='white', dest=None)  # list of coord tuples
draw_circle(x, y, radius=1, width=1, color='white', dest=None)
fill_circle(x, y, radius=1, color='white', dest=None)
draw_arc(x, y, width, height, start_angle, stop_angle, line_width=1,
   color='white', dest=None)
create_rect(width, height)			                          # creates pygame.Rect
```

### Surfaces and Images

```
images: dict                              # indexed by filename without extension
animations: dict                          # contains .frames and .sequences
load_images(path) -> (dict, dict)         # loads images and animations as libraries
load_image(path)                          # loads an individual image at path 
get_image(image_name)   # finds image by checking mode library, app library, and path
create_surface(x, y, color='black', alpha_blend=False, flags=0)
copy_surface(surface)
blit(image, x, y, position=None, scale=None, area=None, flags=None, dest=None)
scale_image(image, x_scale, y_scale=None) # default=proportional; y=per-axis
flip_image(image, horizontal=False, vertical=False)
rotate_image(image, degrees)
shift_image_hue(image, delta)             # delta = value from 0 to 360
set_popover(message, steps=None)          # displays popover message for given steps
start_display_fade(steps=None, color='black', end_mode=None, end_parameters=None)
  # positive duration fades out; negative duration fades in and then calls set_mode()
  # optionally, switch to mode with parameters when fade concludes
```

### Sound
Volume is specified as a range from 0 to 100.
Loops are specified as 0 (play once) or -1 (repeat forever).

```
sounds: dict        				       # indexed by filename without extension
load_sounds(path) -> dict                  # loads sounds as library
load_sound(path)                           # loads an individual sound at path 
get_sound(sound_name)	# finds sound by checking mode library, app library, and path
set_volume(volume, sound_volume=None)      # default=sound and music volume
set_sound_retainer(enable=True) 	       # loops a quiet noise to keep sound active
play_sound(sound, loops=None, volume=None)
play_sound_on_channel(sound, loops=None, volume=None)
    # plays sound on dedicated channel; use channel for .stop(), .get_busy(), etc.	
```

### Music
Volume is specified as a range from 0 to 100.

```
get_music(music_name)	# finds music by checking mode library, app library, and path
play_music(filename, loops=0, volume=None)
stop_music()
is_music_playing()
start_music_fade(steps)
```

### Pointer (Touch or Mouse) Input

```
pointer: Pointer				# interface to pointer object (mouse or touch)
pointer.x, pointer.y: int		# current coordinates
pointer.down: bool				# True during first frame of touch or click
pointer.held: bool				# True throughout touch or click
on_click(x, y)     				# runs click handler function with coordinate
```

### Keyboard Input
Keys are represented by names: 'up', 'down', 'left', 'right', 'space', etc. See misc.py for full list.

```
new_keys: list			  		# array of keys that are newly pressed this frame
held_keys: list					# array of keys that are currently down
start_keyboard_buffering()	    # clears buffer and starts buffering keyboard input
clear_keyboard_buffer()			# clears keyboard buffer for new text input
keyboard_buffering				# True when keyboard input is being buffered	
keyboard_buffer: str			# string of text input since clear_keyboard_buffer()
keyboard_buffer_chars: list 	# array of keys since clear_keyboard_buffer()
stop_keyboard_buffering()		# stops buffering keyboard input
```

### App State

The App stores an `app_state` dict for app-wide data that should be available to all Modes. The App automatically saves the state dict at exit (in `app_state.txt`) and reloads it at startup to persist the state of the app. Because the app state uses `json.dumps` and `json.loads`, any such data must be JSON-serializable. If the App does not find an `app_state.txt` file at startup, it will look for an `app_state_start.txt` file and read it into an initial app state.

```
app_state: dict
persist_app_state: bool         # whether to save and load app_state automatically
load_app_state()                # loads app state
set_app_state(key, value)       # saves parameter in app state
save_app_state()				# saves script state
```

### Scripting
A script defines a set of scenes with names, modes, and optionally submodes and parameters. Scripting is useful for complex applications with a large number of modes and submodes, where the logic for defining application flow is easier to manage in a centralized document than in mode-specific button handlers. A script for a Tic-Tac-Toe app might look like this:

```
# script.txt
    
name=Title              mode=Title
name=Main_Menu          mode=Main_Menu         submode=top
name=Main_Menu_Opts     mode=Main_Menu         submode=options
name=Game_Board         mode=Game_Board        submode=playing
name=Game_Over          mode=Game_Board        submode=complete
```

The App can load a script (ignoring whitespace and comments), sequentially number the scenes starting from zero, and initiate execution at the first scene. Call `select_scene()` or `advance_scene()` to navigate through the script.

```
run_script()			            # call this in app.init() to run the script
select_scene(scene_id)	            # scene_id = scene number or name
advance_scene(delta=1)              # advance scene number relative to current scene
```

### Fonts

```
create_font(name='Arial', size=12)	# create font from system name or path
fonts = {'freeserif': ... }         # array of fonts by name in default size
standard_font: Font					# standard (default) Font object
standard_font_name: str				# name of standard font
standard_font_sizes: dict			# standard Font objects indexed by sizes (4-64)
change_font()						# cycles to next font in font list as current font
```

## Mode Class Reference

### Example Mode

```
class Example_Mode(Mode):
	
    def init(self):
        self.name = 'Example_Mode'

    def enter(self, mode_parameters: dict=None):
        """ Mode entry method, with mode_parameters for context. """

    def click(self, x: int|float, y: int|float):
        """ Click handler method for custom mode. """

    def process(self):
        """ Process method for custom mode. """
	      
        self.app.send_message('ping')      # send message (str or dict) to worker
		
    def draw(self):
        """ Draw method for custom mode. """

    def exit(self):
        """ Mode exit method. """
```

### Mode Class Fields and Methods

```
app: App
name: str
init()                             # stub method for mode initialization 
enter(mode_parameters: dict)       # stub method for mode entry
click(x: int|float, y: int|float)  # stub method for mode click event handler
process()                          # stub method for mode process
draw()                             # stub method for mode draw
exit()                             # stub method for mode exit
mode_timer: int                    # draw cycles since mode.enter()
add_control(control: Control)
remove_control(control: Control)
remove_controls()	
images: dict                       # images library for mode, same as app.images
animations: dict                   # animations library for mode, same as app.animations
sounds: dict                       # sounds library for mode, same as app.sounds
sprites: list					   # mode sprites collection
add_sprite(sprite: Sprite)
remove_sprite(sprite: Sprite)
render_sprites(auto_animate=True)  # renders sprites - not called automatically
```
	
### Controls

The Control base class is a placeholder for control-specific functionality:

```
Control(x, y, width, height, click=None, hold=None, release=None, name=None,
    parameters=None)
```

Notable control subclasses:

```
LabeledControl(caption, control, offset=None, font=None,
    color='white', name=None, parameters=None)
    """ Wrapper to add a left-side label to a control.
		Optionally specify an x offset for the control; default uses text width. """

Button(caption, x, y, width, height,
    target_mode=None, target_mode_parameters=None,
    click=None, hold=None, release=None, app_exit=False,
    font=None, color='white', background_color='black',
    name=None, parameters=None)
    
HoldButton(caption, x, y, width, height, hold_color='red',
    hold_steps=12, click=None, hold=None, release=None,
    target_mode=None, target_mode_parameters=None, app_exit=False,
    font=None, color='white', background_color=None,
    name=None, parameters=None)
    """ Hold button user control that calls .click() after a hold period. """
    
CheckButton(x, y, width, height, checked=False, 
    box_color='white', check_color='red', check_width=5, background_color=None,
    click=None, hold=None, release=None, name=None, parameters=None)
	 """ Check button user control that toggles self.checked. """
    
ToggleButton(x, y, width, height, toggled=False,
    color='white', toggled_color='green', background_color='black',
    click=None, hold=None, release=None, name=None, parameters=None)
	 """ Toggle button user control that toggles self.toggled. """
	
SelectButton(x, y, width, height,
    items: list, values: list=None, selected_index: int=0,
    color='white', background_color='black', font=None,
    click=None, hold=None, release=None, name=None, parameters=None)
    """ Select button that iterates through a list of items and sets
        .selected_index and .selected_item. If values list is provided,
        .value = values[selected_index]; otherwise, .value = None. """
```

### Submodes

When a submode is set for a Mode, the stub methods for the Mode will invoke corresponding `[method_name]_[submode_name]` methods if they exist. For example, a submode called `main_menu` can be created by adding at least one of the following methods to a Mode: `init_main_menu`, `enter_main_menu`, `click_main_menu`, `draw_main_menu`, `process_main_menu`, and/or `exit_main_menu`.

```
submodes: list					               # submode names, determined by inspection
submode: str   						           # current submode
submode_timer: int     					       # draw cycles since mode.enter()
set_submode(name, mode_parameters: dict=None)  # also exits previous submode
```

A few specific details about submode methods:

* `enter_{submode}` is called during `set_submode`, not during or in place of `mode.enter`. Of course, `mode.enter` will usually call `mode.set_submode` to select the initial submode, which results in `enter_{submode}` being called. `enter_{submode}` is also called while changing to the submode at a later time during the presentation of the mode.
* `click_{submode}`, `process_{submode}`, and `draw_{submode}` are called **instead of** the mode method. Since the submode method can call the corresponding mode method, this logic provides greater control over if and when that happens - e.g., the submode can draw before, after, and/or instead of the `mode.draw` method.
* When App switches away from a mode, `exit_{submode}` is called **as well as** the `mode.exit` method. This logic fulfills the expectation that the selection of a mode will always begin with `mode.enter` and always end with `mode.exit`, while also providing a current submode an opportunity to perform cleanup when the mode exits. `exit_{submode}` is also called when switching from the submode to a different submode during the presentation of the mode.
* Any methods can be omitted for a submode. However, a submode only exists if at least one submode method is implemented. Setting a submode with no submode methods produces a Log.error in case of typographical errors.

## Worker Class Reference

### Example Worker

```
class Example_Worker(Worker):

    def init(self):
        self.name = 'Worker'

    def process(self):
        """ Regular (high-frequency) worker processing. """

    def process_periodic(self):
        """ Periodic (low-frequency) worker processing. """
			
        self.send_message('pong')	         # send message (str or dict) to app

    def process_message(self, message, sender: str=None):
        """ Process a message from app. """
			
        action = message.get('action')
        if action == 'ping':  				 # custom message handling
            self.send_message('pong')
        else:								 # default message handlers
            super().process_message(message, sender)
```

### Worker Class Fields and Methods

```
name: str									 # worker name
config: dict								 # config
config_manager: bool						 # whether this worker manages the config
log_manager: bool						     # whether this worker manages the log
init()                                       # stub method for pre-start initialization
start_worker()                               # stub method for post-start initialization
process()                                    # stub method for high-frequency processing
process_periodic()                           # stub method for low-frequency processing
send_message(message: str|dict)
	# messages are sent as dicts - a provided string will be sent as {'action': message}
send_updated_config()		    			 # sends config to app
write_config()								 # writes config and sends to app
update_config(key, value)					 # writes updated config; sends to app
```

## config.txt

This file contains high-level Jubilee application configuration features. App loads this file into App.config at startup; if the file does not exist, default values provided in Worker are used. A first Worker process periodically checks this file for updates and automatically reloads it. 

```
"screen_resolution": [320, 240] 			 # screen resolution for drawing
"screen_rotation": 0                         # 90/180/270-degree rotations
"headless": false                            # display vs. no-display configurations
"pointer_input": true						 # receive pointer (mouse or touch) events
"keyboard_input": false						 # receive keyboard events 
"screen_scale": [[0, 319, -1], [0, 239, 1]]  # screen range/direction for pointer input
"app_process_fps": 10       			     # app.process() fps
"app_draw_fps": 10							 # app.draw() fps 
"nosound": false                             # sound vs. no-sound configurations
"modal": false								 # app_process => current mode or all modes
"worker_process_fps": 20			         # worker.process() fps
"worker_process_periodic_fps": 1             # worker.process_periodic() fps
"persist_app_state": true					 # automatically save/load app_state
"app_state_filename": "app_state.txt"		 # file to store app_state dict
"app_state_start_filename": "app_state_start.txt"  # file to store initial app_state dict
"rotate_log": "daily"                        # log rotation: monthly, daily, hourly
"font": "freeserif"	    					 # default font name
"font_size": 14								 # standard size (overridden as 15 on macOS)
```

## misc.py Reference

The following classes and functions are available in jubilee.misc:

### Config
Operations default to get_filename() filename, which is usually `config.txt`.
```
load(filename: str=None, defaults: dict=None) -> dict  # combines file data and defaults
save(config: dict=None, filename: str=None)
get_filename() -> str
```

### Log
Operations default to get_filename() filename, which is usually `log.txt`. The first worker usually rotates the log during process_periodic at a frequency defined in `config.txt`.
```
ERROR, WARNING, INFO, DEBUG                             # const levels
reset(filename: str=None)
backup(filename: str=None, backup_folder: str=None)     # defaults='log_{time}', '.logs/'
set_file_level(level, filename: str=None)               # specify const level
set_console_level(level, filename: str=None)            # specify const level
error(message, filename: str=None)                      # converts to str(message)
warning(message, filename: str=None)                    # converts to str(message)
info(message, filename: str=None)                       # converts to str(message)
debug(message, filename: str=None)                      # converts to str(message)
read(filename: str=None) -> list
get_modification_date(filename: str=None)
get_filename() -> str
parse(record: str) -> dict
    # parses log string to {'dt', 'class', 'function', 'level', 'message'}
```

### Color

This enum maps color constants to tuples (e.g.: Color.BLACK.value = (0, 0, 0)).

### Misc

Random common functionality.

```
key_names                                   # from pygame: ('backspace', 'tab', etc.)
key_symbols: dict                           # unshifted typable key symbols
key_shift_symbols: dict                     # {'a': 'A', ...}
null_date = datetime.utcfromtimestamp(0)    # date represented by 0
user_agent                                  # user_agent selected for this session
choose_user_agent()                         # chooses a popular user_agent
calculate_hashcode(data: dict) -> str       # sha256 hash for json.dumps(data)
http_request(url: str, method: str=None, headers: dict=None,
    data: dict=None, password: str=None, timeout: int=30,
    randomize_user_agent: bool=False, timestamp: str=None) -> (int|None, str)
        # if data=dict, uses HTTP POST and json.dumps(data); otherwise, GET by default
sign_request(url, password, timestamp: int=None) -> (bool, str)
        # calculates a URL with "&hash={sha256 hashcode}" appended
get_local_ip_address() -> (bool, str)       # success, result or error message
test_internet() -> (bool, float|str)        # success, latency or error message
get_hostname() -> str                       # get local hostname
get_color(color: str|int|tuple, color_scale: float=None) -> tuple|None
        # color=string (case-insensitive), Color.enum, or tuple; can scale by 0.0-1.0
