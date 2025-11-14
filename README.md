# README.md

## Introduction

Raspberry Pi devices and other single-board computers (SBCs) provide an exciting platform for small-scale computing for hobbyist projects.

A common problem with such projects is the gap between a newly configured device, such as a fresh install of Raspberry Pi OS, and a component that is ready to be programmed for a project. That gap includes a host of basic questions like:

* How do I render text and use fonts?

* How do I draw graphics and display images?

* How do I render basic UI elements, like buttons that detect and respond to user input?

* How do I factor an application into modes with mode-specific processing and drawing?

* How do I separate UI rendering and input event handling from background processing?

* How do I enable communication among a UI-rendering process and background processes?

* How do I enforce desired frame rates for the UI and background processing?

* How do I load images, sounds, and other assets into usable libraries?

* How do I render sprites with animation sequences?

* How do I apply visual effects like popover messages and fade transitions?

* How do I play sounds and music?

* How do I receive and handle keyboard input?

* How do I create a scripted application that transitions among a set of modes and submodes?

* How do I maintain a shared and persistent application state?

* How do I handle application configuration and logging?

* How do I design an application for development on a workstation with mouse input, and for deployment on a device with touch input?

Many of these questions are addressed by libraries like pygame, but the features of such libraries are often too low-level for the sophisticated functionality of many applications. As a result, developers often need to spend time on infrastructure code - time which would be more effectively (and enjoyably) devoted to writing code for the project.

Jubilee is a lightweight app engine built on pygame. The purpose of Jubilee is to enable the rapid development of applications that typically have a main GUI process and one or more background worker processes, with support for graphical UI features, interprocess messaging, and application modes.

## Hello, World

Here is a simple Jubilee application with one mode and one background worker:

```
import jubilee

class HelloMode(jubilee.Mode):

    def init(self):
        self.name = 'Hello Mode'

    def process(self):
        pass        # mode-specific UI processing can occur here

    def draw(self):
        self.app.center_text('Hello, World!')

class HelloWorker(jubilee.Worker):
    
    def init(self):
        self.name = 'Hello Worker'
    
    def process(self):
        pass        # high-frequency background processing can occur here

    def process_periodic(self):
        pass        # low-frequency background processing can occur here

class HelloApp(jubilee.App):

    def init(self):
        self.name = 'Hello App'
        self.add_mode(HelloMode)
        self.add_worker(HelloWorker)

if __name__ == '__main__':
    HelloApp().run()
```
This application contains one defined mode, which is automatically selected as the initial mode of the application. The App executes a loop that calls the `process` and `draw` methods of the mode (default 10 Hz each). The mode `draw` method displays "Hello, World!" in the center of the screen. The application also creates a background worker that runs as a separate process. The worker calls `process` frequently (default 20 Hz) and `process_periodic` occasionally (default 1 Hz).

Jubilee applications can include a rich set of modes with UI elements and navigation, multiple workers, and features like submodes, scripting, and sprite-based animations - while maintaining the simple architecture and stylistic readability shown above.

## Examples

The Examples folder contains a variety of example projects that run right out of the box:

* **Hello** - A Hello, World! project with an App class and a Worker (background) class.
* **Headless** - A project with no display. (Can still play sound and music.)
* **Pointer** - A project that demonstrates pointer input (and simple graphics).
* **Images** - A project that demonstrates images and sprite animations.
* **Sound** - A project that demonstrates sound and music.
* **Controls** - A project that demonstrates various UI controls.
* **Modes** - A project that demonstrates two modes, packaged into two Mode classes.
* **Submodes** - A project that demonstrates submodes.
* **Script** - A project that demonstrates mode scripting.

These projects can be used for quick reference, as sandboxes to experiment with the features, or as templates for new projects with similar features.

## Overview of Architecture and Features

Jubilee executes one process (App) that handles the display and input events, and one or more Worker processes that independently execute background processing, typically on different CPU cores.

App runs in a loop that calls `process` to handle UI processing and `draw` to draw to the screen (unless App is declared as headless). The Worker runs in a loop that frequently calls `process` (e.g., at 20 Hz) and occasionally calls `process_periodic` (e.g., at 1 Hz).

The App communicates with each Worker using a pair of message queues - an `app_queue` for transmitting messages from the App to the Worker, and a `worker_queue` for transmitting messages from the Worker to the App. Every message is a JSON object that is automatically serialized (via `json.dumps`) for transmission and deserialized (via `json.loads`) upon receipt.

The App can store a set of Modes, and can transition between them with `set_mode`. Each Mode includes a set of methods: `init` (called at application start), `enter` (called during `set_mode`), `click` (called to handle click events), `process`, `draw`, and `exit`. The Mode class includes a `controls` array, and instances of UI controls, such as Buttons, can be added to the mode during `init` or later. Jubilee automatically renders UI controls and handles click detection by invoking a click handler method. Buttons can be configured to execute a handler function, to switch automatically to a target mode, or to exit the application.

As shown in the Hello World app, a Jubilee app features subclasses of the App, Worker, and Mode classes that replace the stub methods with app-specific functionality. For example, each Mode subclass can provide app-specific `process` and `draw` methods, and each Worker subclass can provide app-specific `process` and `process_periodic` methods. This simple architecture simplifies and accelerates the application development process.

Additional features:

* **Configuration:** Some features of Jubilee are declared in `config.txt`, which App and Worker load during initialization. The App class features a set of default values in case `config.txt` is not present. During runtime, one Worker class (by default, the first one created) periodically checks the modification date of `config.txt` and pushes updates to the App via the messaging queue, which reduces redundant file-system operations and preserves the lifespan of flash-based storage.

* **Global, Persistent Application State:** The App stores an `app_state` dict containing application-wide data for all Modes. The App can be configured to save `app_state` in a file at app exit and to reload it at app start to persist the state of the App. The App can also provide a default `app_state` to be used when a saved `app_state` is not found on startup.

* **Mode Contexts:** Jubilee can run in a modal context, where each app process loop invokes the `process` method for the current mode, or a modeless context, where each app process loop invokes the `process` method for *every* mode. Jubilee also supports a no-display ("headless") context that runs without any graphics or mouse / touch functionality, while maintaining all `process` methods and keyboard input checking.

* **Submodes:** A Mode can include a number of submodes. Creating a submode is easy - just add relevant methods that include the name of the submode (e.g., for a submode called "menu," add methods like `enter_menu`, `click_menu`, `process_menu`, and `draw_menu`). During execution, a submode can be selected (e.g., `app.mode.set_submode('menu')`), and the App will automatically call the submode-specific methods.

* **Scripting:** For applications that require a particular sequence of states and substates, Jubilee supports the definition of a script. The script defines a set of "scenes," each indicating a mode and a set of parameters, optionally including a submode. The app or any mode can call `app.advance_scene()` to advance to the next scene in the script, or `app.select_scene(scene_id)` to jump to a particular scene by name or number.

* **Resource Libraries:** Jubilee looks for folders called images and sounds in the main app folder and automatically loads them into app-level resource libraries. For each mode, Jubilee also looks for a subfolder of the same name, looks for further images and sounds subfolders for the mode, and automatically loads mode-level resource libraries. Image `blit` and `play_sound` methods can use resources specified by names. Jubilee will look first in the library for the current mode, then in the application library, and finally will try to load the resource using the name as a path.

* **Animations and Sprites:** Each images folder can contain a subfolder for an animation as a set of images corresponding to animation frames. Each subfolder is loaded into an Animation as a set of frames. For each mode, a set of Sprites can be generated, each having an Animation object, x/y coordinates, and a current animation frame number. The mode `draw` method can render all of the sprites for the mode by calling `mode.render_sprites()`. A sprite can be configured to animate automatically through all frames of an Animation at a given rate. Further, if some frames for an Animation are named consistently and numbered - e.g.: `walk_left_1.jpg`, `walk_left_2.jpg`, etc. - then the Animation generates a Sequence, indexed by the shared name `walk_left`, and containing a list of the indexes in the Animation `frames` list that correspond to the animation sequence. A Sprite can be set to a specific Sequence in a given Animation, and can animate (automatically or on-demand) over the frames of the Sequence.

* **Input:** On Linux, Jubilee will handle touch input if the config parameter touch_input is True. On macOS, Jubilee automatically handles mouse events. Jubilee also stores and provides keyboard input on a key basis (`new_keys` for newly pressed keys and `held_keys` for all keys that are currently down) and as a keyboard buffer (`keyboard_buffer` as a string and `keyboard_buffer_chars` as an array of keys).
