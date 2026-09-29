# Changelog

## 0.45

- Worker.update_config() changes only the requested key in config.toml and
  keeps the file's other settings, comments and permissions (new
  Config.update()). A config.toml that fails to parse at Worker start is never
  overwritten with defaults; write_config() is refused until a reload succeeds.
- Worker processing and manager errors are logged without ending the Worker.
- WiFi recovery runs interface, NetworkManager and driver commands through
  non-interactive sudo when not root, and logs failed steps as warnings.
- Scene selection changes Mode even when app state cannot be persisted.
- Rotated log archives are named for the period they contain.
- Keys that add no text (such as Tab) no longer desynchronize the keyboard buffer.
- blit() accepts a list as a per-axis scale. change_font() and update_config()
  report whether a config-manager Worker received the request.
- Worker processes use the App's log levels, so `debug` and `console_debug`
  apply to Workers as well.
- A launch rejected as a duplicate exits without writing to the running
  instance's log. The duplicate check itself is unchanged.
- The unused packaged `jubilee/config.toml` is no longer shipped; each project's
  `config.toml` is the only configuration file.
- The Reference documents event receivers and internal methods; examples
  include CREDITS.md with recorded asset sources.
- Include 114 tests covering regressions, example runtimes and packaging.

## 0.44

Source release following the 0.42 GitHub version. Prepared 0.43 was not published.

- Harden App initialization/shutdown and Worker cleanup, queue handling and
  callback isolation. Use monotonic clocks for scheduling and input debouncing.
- Preserve last-good configuration on reload failures and validate JSON IPC
  compatibility before writing. Strict reads fail for missing files.
- Block state persistence after a failed load until successful recovery/reload.
- Correct mode/submode transitions, pointer gesture ownership, keyboard state,
  controls, sprite resource ownership, animation validation and drawing order.
- Correct alpha/effect handling, sound volume, music fades and headless fades.
- Correct touchscreen packet processing, mouse coordinates, logging/rotation,
  HTTP headers/signing and example behavior.
- Persist WiFi reboot budgets before reboot. Initialize an absent budget while
  refusing malformed/unreadable state and broken symlinks. Restore networking
  when graceful exit interrupts an interface/driver recovery sequence.
- Include 107 tests covering regressions, example runtimes and packaging.

Compatibility notes: mode transitions cancel old pointer gestures; sprites use
their owning Mode's resource library; strict missing-file reads raise; failed
state loads block saving; headless music fades count process cycles. Internal
elapsed-time fields are monotonic values, not wall-clock timestamps.

Singleton detection is intentionally unchanged: it remains a best-effort
process-name scan. Physical Raspberry Pi peripherals and WiFi recovery are not
certified by dummy-SDL tests.
