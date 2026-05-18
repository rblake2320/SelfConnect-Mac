# External Review Response: Comprehensive Test Report

Date reviewed: 2026-05-18  
External report reviewed: `/Users/ronaldblake/Downloads/Comprehensive Test Report_ SelfConnect-Mac`  
Repository: <https://github.com/rblake2320/SelfConnect-Mac>

## Purpose

This document records how the external "Comprehensive Test Report: SelfConnect-Mac"
was handled. The report is useful because it identifies what a skeptical reviewer
would look for: real Mac operation, unguarded Windows calls, test evidence,
security posture, and reproducibility.

Each concrete technical claim was checked against the current repository before
making changes. Some findings were verified and fixed. Some did not reproduce in
the current codebase.

## Findings Verified And Addressed

### 1. Vision detection service still had direct Win32 calls

Report claim:

```text
vision_server/services/detection_service.py directly imports and invokes
ctypes.windll.user32
```

Status: verified.

Fix:

- Added platform detection.
- `_get_win32_controls()` now returns `[]` on non-Windows.
- On macOS, detection skips Win32 controls and proceeds to capture / vision fallback.

Relevant file:

```text
vision_server/services/detection_service.py
```

### 2. Capture service fallback still had direct Win32 calls

Report claim:

```text
vision_server/services/capture_service.py Strategy 2 hardcodes
ctypes.windll.user32.GetWindowRect
```

Status: verified.

Fix:

- Added platform detection.
- The PIL ImageGrab Win32 fallback is now skipped on non-Windows.
- On macOS, Strategy 1 already routes through `self_connect.capture_window()`,
  which uses `screencapture`.

Relevant file:

```text
vision_server/services/capture_service.py
```

### 3. SDK functions had unsafe or silent non-Windows behavior

Report claim:

```text
Several SDK functions lack macOS guards and may silently do nothing through dummy
Win32 libraries.
```

Status: verified for several functions.

Fix:

Added explicit macOS behavior or explicit unsupported returns for:

```text
get_child_texts
crop_to_client
is_elevated
send_keys_to
close_window
get_text
set_text
click_button
send_command
select_combo
select_listbox
post_click
list_child_controls
find_child_by_text
get_menu_items
exclude_from_capture
include_in_capture
```

Rationale:

- Returning a clear `False`, `[]`, `0`, or original image is better than letting
  a dummy Win32 object return meaningless values.
- Terminal-specific text readback is routed to `get_text_uia()`.
- Terminal/window text setting routes through `send_string()` when feasible.

Relevant file:

```text
self_connect.py
```

### 4. Migration successor code was Windows-specific

The external report did not call this out directly, but the follow-up audit found
`MigrationCoordinator._spawn_successor()` still assumed `cmd.exe` and Win32 window
restore behavior.

Status: verified.

Fix:

- `_find_new_hwnd()` now has a macOS path that detects newly opened Terminal/iTerm windows.
- `_spawn_successor()` now has a macOS path using Terminal AppleScript and `send_string()`.
- The Windows path is preserved for Windows.

Relevant file:

```text
self_connect.py
```

## Findings Not Reproduced In Current Code

### 1. WindowPool `self._windows` bug

Report claim:

```text
WindowPool attempts to access self._windows but constructor initializes self.targets.
```

Status: not reproduced in current code.

Current code initializes and uses:

```python
self.targets: dict[str, WindowTarget] = {}
```

Methods checked:

```text
add
add_target
remove
get
send_to
capture_all
save_all
focus_only
status
__len__
__repr__
```

They consistently use `self.targets`.

### 2. `Checkpoint(context=...)` bug

Report claim:

```text
MigrationCoordinator instantiates Checkpoint with a context argument that the
dataclass does not define.
```

Status: not reproduced in current code.

Current `Checkpoint` fields:

```text
role
own_hwnd
peers
pending
meta
written_at
schema
```

Current `MigrationCoordinator.tick()` instantiates `Checkpoint` with:

```text
role
own_hwnd
peers
pending
meta
```

No `context` argument was found in current code.

### 3. `AgentRegistry.add()` missing method

Report claim:

```text
AgentRegistry lacks add(), but tests/internal code call reg.add(...)
```

Status: not reproduced in current code.

Current API uses:

```text
register(hwnd, label, pid=0)
unregister(hwnd)
get(hwnd)
all_peers()
update_state(hwnd, state)
summary()
```

No current tests or internal code were found calling `AgentRegistry.add()`.

## Remaining Known Limitations

The Mac port is now stronger, but not every root-level script is cross-platform.
Some scripts remain historical Windows session utilities. This matters for review:

- The core SDK and Mac mesh helpers are the Mac proof path.
- Root-level one-off scripts with hardcoded HWNDs should not be represented as
  Mac-compatible utilities unless individually ported.
- A future cleanup should move Windows-only session scripts into a `windows_legacy/`
  or `tools/windows/` area and mark them explicitly.

The codebase also still contains broad exception handling in historical automation
paths. That is acceptable for exploratory automation scripts but should be narrowed
for production-grade Mac operation.

## Verification After Fixes

Commands run after applying fixes:

```bash
.venv/bin/python -m py_compile mac_mesh_control.py spawn_codex_mac_peer.py
.venv/bin/python -m pytest -q
```

Observed result:

```text
151 passed, 9 skipped
```

The skipped tests are Windows-specific integration tests.

## Reviewer-Relevant Summary

The external report correctly identified that the first Mac publication still had
Win32 assumptions outside the core live-demonstrated path. Those concrete verified
issues have now been guarded or routed to Mac behavior.

The report also contained several class/API breakage claims that were not present
in the current pushed code. Those were checked and documented rather than blindly
changed.

The patent/process evidence remains:

- live Mac Terminal discovery,
- targeted Terminal injection,
- explicit TUI submission,
- Terminal readback,
- Agent B Codex ACK/status/chat,
- Claude Code ACK,
- one-command mesh helper,
- pushed GitHub repository,
- reproducible test suite.
