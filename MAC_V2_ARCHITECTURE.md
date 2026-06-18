# SelfConnect Mac v2 Architecture

Date drafted: 2026-06-17
Status: initial commit of the v2 package alongside the v1 (`self_connect.py`) compatibility layer.

## Why v2

The v1 Mac compatibility path documented in `PATENT_PROCESS_RECORD.md` used four primitives:

1. AppleScript via `osascript`
2. `screencapture` CLI
3. `pbcopy` / `pbpaste`
4. Python `subprocess`

That was sufficient to prove the operational model on macOS (verified live 2026-05-13 → 2026-05-18, commit `c7380b5`). It was **not** sufficient to claim parity with the Win32 SDK surface, and it ignored entire categories of macOS-native capability that have no Win32 analog at all.

v2 adds a `selfconnect_mac/` Python package that:

- preserves the v1 module (`self_connect.py`) unchanged for backward compatibility and prior-art continuity;
- exposes a pluggable `Backend` interface with four implementations covering different runtime substrates;
- adds Mac-only "moat" modules — log bus, FSEvents inbox, biometric approval, peer-to-peer mesh, audio channel, APFS snapshots — that Win32 (and competing app-control SDKs such as UAB/Lancelot) cannot replicate at parity.

## Layout

```
selfconnect_mac/
├── __init__.py                  facade: get_backend(), list_backends()
├── cli.py                       sc-mac unified CLI
├── windows.py                   CGWindowListCopyWindowInfo + AXUIElement
├── capture.py                   CGWindowListCreateImage + Vision OCR fallback
├── backends/
│   ├── base.py                  Backend ABC: enumerate/send/read/capture/spawn
│   ├── iterm2.py                iTerm2 Python API
│   ├── tmux.py                  tmux send-keys / capture-pane
│   ├── cgevent.py               CGEvent + CGEventPostToPid (PostMessage twin)
│   ├── applescript.py           wraps the v1 path as a Backend
│   └── selector.py              auto-detect best available
├── bus/
│   ├── log_bus.py               os_log as queryable mesh bus
│   ├── fsevents_inbox.py        push-driven inbox (replaces polling)
│   └── pasteboard.py            NSPasteboard private named channels
├── mesh/
│   └── multipeer.py             Bonjour publish/browse + MultipeerConnectivity stub
├── approval/
│   ├── touch_id.py              LocalAuthentication biometric gate
│   ├── audio.py                 say / afplay heartbeat + announcements
│   └── notifications.py         AppleScript / terminal-notifier banners
└── resilience/
    └── snapshot.py              APFS clone-based checkpoint / rollback
```

## Backend matrix

| Backend | Substrate | Focus required | TCC prompts at runtime | Headless / SSH safe | Speed vs AppleScript | Reads buffer how |
|---|---|---|---|---|---|---|
| **iterm2** | iTerm2 | No | None | No | Fastest | `async_get_screen_contents` (cell-accurate) |
| **tmux** | tmux server | No | None | **Yes** | Fastest | `capture-pane -p` |
| **cgevent** | any terminal GUI | No (targeted to PID) | Accessibility once | No | ~10× faster | AXUIElement or AppleScript |
| **applescript** | Terminal.app | Yes (steals focus) | Accessibility + Automation | No | Baseline | `contents of window` |

`backends.selector.auto_select()` picks iterm2 → tmux → cgevent → applescript in priority order based on `is_available()`.

## Win32 parity table

| Win32 SDK function (`self_connect.py`) | v2 Mac equivalent |
|---|---|
| `list_windows()` (EnumWindows) | `windows.list_cg_windows()` (CGWindowListCopyWindowInfo) |
| `send_string(target, text, mode="turbo")` | `Backend.send(target, text)` — iTerm2 over WebSocket, or tmux send-keys, or CGEventPostToPid |
| `get_text_uia(hwnd)` | `Backend.read(target)` — `async_get_screen_contents`, `capture-pane`, or AXUIElement |
| `capture_window(hwnd)` (PrintWindow) | `capture.capture_cg_window(window_id)` |
| `PostMessageW(hwnd, 0x0102, 0x000D, ...)` (nuclear Enter) | `CGEventPostToPid(pid, kVK_Return)` in `backends.cgevent` |
| Spawn via `wt.exe -w new` + `DETACHED_PROCESS` | `Backend.spawn()` — `tmux new-session -d`, `iterm2.Window.async_create`, or `open -na Terminal` |

## Moat modules (no Win32 equivalent)

| Module | What it enables | Win32 analog |
|---|---|---|
| `bus/log_bus.py` | OS-native pub/sub via `os_log` + `log stream` predicates | ETW (admin-only, much harder) |
| `bus/fsevents_inbox.py` | Sub-second push notification on inbox writes | ReadDirectoryChangesW (manual) |
| `bus/pasteboard.py` | Typed multi-format private channels via NSPasteboard | None |
| `mesh/multipeer.py` | LAN peer discovery (Bonjour) + zero-config Wi-Fi/BT mesh (MultipeerConnectivity) | None |
| `approval/touch_id.py` | Biometric per-action approval | Windows Hello biometric API exists but no mesh primitive built on it |
| `approval/audio.py` | TTS heartbeat / inter-room status signal | TTS exists; not used as mesh primitive |
| `resilience/snapshot.py` | O(1) APFS clone checkpoints | Volume Shadow Copy (admin, heavyweight) |

## Permissions

The v2 package requires the same TCC permissions as v1 plus optional ones for the new lanes:

| TCC bucket | Required for |
|---|---|
| Accessibility | `cgevent` backend, `applescript` backend, AXUIElement reads |
| Automation | `applescript` backend |
| Screen Recording | `capture_cg_window` of *other apps'* windows |
| Input Monitoring | (future) global CGEventTap-based hotkeys |

Reset a single grant: `tccutil reset Accessibility com.apple.Terminal`.

## Install

```bash
# Core (always)
pip install Pillow psutil

# Pick your backend(s):
pip install iterm2                       # iTerm2 backend
brew install tmux                        # tmux backend
pip install pyobjc-framework-Quartz      # cgevent backend + capture
pip install atomacos                     # AXUIElement Python wrapper (richer reads)

# Mac-only moat:
pip install pyobjc-framework-Cocoa       # NSPasteboard, NSWorkspace
pip install pyobjc-framework-FSEvents    # push inbox
pip install pyobjc-framework-LocalAuthentication  # Touch ID
pip install pyobjc-framework-Vision      # OCR fallback
```

## Usage

```bash
# Which backends does this Mac currently support?
python -m selfconnect_mac.cli backends

# List terminal targets (auto-picks best backend)
python -m selfconnect_mac.cli list

# Spawn a new agent in tmux (headless)
python -m selfconnect_mac.cli --backend tmux spawn AGENT-A ~/work/repo

# Send + submit
python -m selfconnect_mac.cli send AGENT-A "status report" --submit

# Watch
python -m selfconnect_mac.cli watch AGENT-A AGENT-B

# Mesh bus
python -m selfconnect_mac.cli bus-emit AGENT-A status "build complete"
python -m selfconnect_mac.cli bus-tail --agent AGENT-A

# Biometric approval gate
python -m selfconnect_mac.cli approve "Agent wants to push to main"

# APFS snapshot
python -m selfconnect_mac.cli checkpoint ~/work/repo step_42

# Peer discovery
python -m selfconnect_mac.cli peer-publish "AGENT-A" 5566 --role worker
python -m selfconnect_mac.cli peer-browse
```

## Roadmap (v2.1+)

- ScreenCaptureKit (`SCStream`) replacing `CGWindowListCreateImage` for macOS 12.3+.
- Full MultipeerConnectivity session wiring (currently Bonjour discovery only).
- CGEventTap-based global panic-stop hotkey.
- Status-bar app (`rumps`) as a mesh dashboard.
- launchd plist generation for agent persistence.
- Sparkle-powered self-update channel for a signed `.app` bundle.
