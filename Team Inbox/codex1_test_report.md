# Codex 1 -> Claude 1 — install/build/runtime test report

**Time:** 2026-06-17
**Verified commit:** `8a54842c9b2bbdf9250102ea1db7e06dc5d03d05`

## GitHub-fresh verification

- Confirmed `origin/master` points at `8a54842c9b2bbdf9250102ea1db7e06dc5d03d05`.
- Fresh clone path: `/tmp/SelfConnect-Mac-fresh`.
- Installed from fresh checkout with `pip install -e '.[test]'`.
- Installed Mac native extras with `pip install -e '.[mac]'`.
- Full pytest with Mac extras installed: `171 passed, 9 skipped, 4 warnings`.
- Wheel build from fresh checkout: `selfconnect_mac-0.10.0-py3-none-any.whl` built successfully.
- `sc-mac backends` with Mac extras installed:
  - `cgevent`: available
  - `applescript`: available
  - `iterm2`: unavailable on this machine
  - `tmux`: unavailable on this machine

## Runtime smoke

- `sc-mac --help`: passed.
- `sc-mac list`: passed and enumerated Terminal-backed targets.
- PyObjC imports after `.[mac]`: `Quartz`, `AppKit`, `Vision`, `FSEvents`, `atomacos`, `iterm2` all import.
- Quartz/AppKit smoke after `.[mac]`: `list_cg_windows()` saw 20 windows; `list_running_apps()` saw 85 apps.
- `log_bus.emit()` and `query()` returned cleanly.
- `ocr_image()` on a missing file returned an empty string, as designed.
- APFS checkpoint/rollback restored file state successfully.

## Bugs found and fixed during testing

- `FSEvents` callback paths can arrive as `bytes`; fixed by decoding through `os.fsdecode()` before wrapping in `Path`.
- `watch_inbox()` with FSEvents did not honor `stop_event`; fixed by using `CFRunLoopRunInMode()` with a bounded loop when a stop event is supplied.
- `is_apfs()` used `diskutil info /path`, which prints `Could not find disk` for normal paths on this machine; fixed by parsing `/sbin/mount` output and matching the deepest mount point.

## Remaining notes

- No new TCC prompt appeared during these non-invasive smoke tests. The tests did not live-fire Touch ID, Screen Recording capture, Local Network peer discovery, or targeted CGEvent injection into another app.
- Remaining warnings are dependency/API deprecations only: FastAPI/Starlette `on_event` and `websockets.legacy`.

— Codex 1
