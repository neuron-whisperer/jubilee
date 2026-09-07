# Changelog

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
process-name scan. Physical Raspberry Pi peripherals/recovery and signed macOS
operation are not certified by dummy-SDL tests. GitHub publication does not imply
a corresponding PyPI publication or authorize consumer migration/deployment.
