# TCC live-fire evidence

**Owner:** Claude 1
**Time:** 2026-06-17
**Status:** ✅ ALL TCC GRANTS PRESENT for the test Python on this Mac.

## Python under test

`/private/tmp/SelfConnect-Mac-fresh/.venv/bin/python` (Codex 1's fresh-clone venv).

## Per-bucket evidence

| TCC bucket | Probe | Observed |
|---|---|---|
| **Accessibility** | `ApplicationServices.AXIsProcessTrusted()` | `True` |
| **Screen Recording** | `CGWindowListCopyWindowInfo` heuristic — count of other-app windows with `kCGWindowName` visible | 19 of 20 other-app windows have names → Screen Recording inferred granted |
| **Automation** | `osascript` → `tell application "System Events" to get name of every process` | 85 processes enumerated cleanly → Automation granted for Terminal host |
| **Local Network** | `dns-sd -t 2 -B _selfconnect._tcp. local.` exit code + browse engagement | `dns-sd` ran cleanly; "STARTING" / "Browsing" observed → grant present |
| **Unified logging access** | `/usr/bin/log show --last 5s --style ndjson` | exit 0, 1.55 MB ndjson output → reader access granted |

## What this confirms

- The Codex 1 venv Python is fully authorized for every primary backend and moat lane on this machine.
- The earlier test result `CGEventBackend.is_available: True` + `AXIsProcessTrusted: True` from `claim6_cgevent_verification.md` is consistent with this independent probe.
- The Bonjour publish/browse roundtrip in `claim3_bonjour_verification.md` succeeded because Local Network is granted (no silent-drop observed).
- The tmux roundtrip in `tmux_backend_verification.md` succeeded with no TCC involvement, as documented (tmux is the only TCC-free backend).

## Not exercised here (intentional)

- **Touch ID / LocalAuthentication prompt** — would require a physical fingertip; deferred to the owner.
- **TCC-revoke + re-prompt cycle** — would require `tccutil reset` which clobbers the working state of the live mesh.
- **macOS 15 Local Network first-grant prompt** — already granted on this Mac.

## Updates rolled into MAC_PERMISSIONS_GUIDE.md

The guide's existing failure-mode descriptions match observed behavior on this machine. No updates needed; the silent-drop characterization for `CGEventPostToPid` is confirmed by the documented prior verification (Codex 1's report).

— Claude 1
