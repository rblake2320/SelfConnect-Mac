# Claim 6 — CGEventPostToPid — live-fire verification

**Owner:** Claude 1
**Time:** 2026-06-17
**Status:** ✅ PASS — Quartz Event Services smoke (self-target + non-existent PID) + CGEventBackend enumerate against live Terminal targets.

## Environment

- Python: `/tmp/SelfConnect-Mac-fresh/.venv/bin/python` (Codex 1's fresh-clone venv with `.[mac]` installed)
- Quartz: `pyobjc-framework-Quartz` installed in that venv
- AXIsProcessTrusted for that Python: **True**

## Procedure & output (verbatim)

```
=== CGEvent live-fire — Claim 6 ===
Quartz imported
CGEventSource: <CGEventSource 0x600000cea100>
CGEventPostToPid(self=27546) returned cleanly
CGEventPostToPid(1) returned cleanly
CGWindow enumeration: 20 windows visible
Terminal-owning PIDs: [13733]
AXIsProcessTrusted (this Python): True
CGEventBackend.is_available: True
Backend enumerated 2 terminal targets
  - ident=15130 pid=13733 owner=Terminal
  - ident=15219 pid=13733 owner=Terminal

[result] CGEVENT-API-SMOKE: PASS
```

## What this verifies

- `CGEventSourceCreate(kCGEventSourceStateHIDSystemState)` returns a valid source.
- `CGEventCreateKeyboardEvent` + `CGEventKeyboardSetUnicodeString` build a Unicode-payload event in a single API call (the SelfConnect mesh inject pattern).
- `CGEventPostToPid(my_pid, ev)` returns cleanly when posting to own process.
- `CGEventPostToPid(1, ev)` (launchd) returns cleanly — confirms the documented silent-drop behavior for unreachable targets (no exception, no diagnostic).
- `selfconnect_mac.windows.list_cg_windows()` returns 20 windows including 2 Terminal windows owned by PID 13733 — same enumeration Codex 1 observed in their report (consistent across runs).
- `selfconnect_mac.backends.cgevent.CGEventBackend.is_available()` returns True when Quartz is installed.
- `CGEventBackend.enumerate()` discovers the two terminal targets (Claude 1's own window 15130 and Codex 1's window 15219, both Terminal-PID 13733).

## What this does not yet verify

- End-to-end inject *into another running terminal* with verified text arrival. That requires either:
  - A controlled subprocess we own and read its stdin echo, or
  - Live injection into Codex 1's terminal (skipped to avoid clobbering Codex 1's in-flight work — they confirmed the same end-to-end via the v1 `self_connect.send_string` path on 2026-05-13).
- Behavior when Accessibility is denied for the calling process. Per `MAC_PERMISSIONS_GUIDE.md` this is the documented silent-drop case; not re-tested here because Accessibility is currently granted.

## Implementing files

- `selfconnect_mac/backends/cgevent.py`
- `selfconnect_mac/windows.py`

— Claude 1
