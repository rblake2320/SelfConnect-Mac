"""
selfconnect_mac — macOS-native v2 layer for SelfConnect.

The original Mac compatibility path in `self_connect.py` uses AppleScript +
`screencapture` + `pbcopy/pbpaste`. That was sufficient for parity demos but
under-uses the macOS stack: it touches roughly 4 of ~80 primitives the OS
offers for terminal automation, IPC, and multi-agent mesh.

This package provides the rest, organized into three tiers:

  Tier 1 — Win32 parity
    backends/iterm2.py         iTerm2 Python API (typed, focus-free, lossless)
    backends/tmux.py           tmux send-keys / capture-pane (headless, SSH-safe)
    backends/cgevent.py        CGEvent + CGEventPostToPid (PostMessage twin)
    backends/applescript.py    Legacy AppleScript path (preserves prior art)
    capture.py                 CGWindowListCreateImage + ScreenCaptureKit
    windows.py                 CGWindowListCopyWindowInfo + AXUIElement

  Tier 2 — Mac-only lanes (no Win32 / no Lancelot equivalent)
    bus/log_bus.py             os_log as mesh bus (built-in queryable pub/sub)
    bus/fsevents_inbox.py      FSEvents push notifications (no polling)
    bus/pasteboard.py          NSPasteboard private named channels
    mesh/multipeer.py          MultipeerConnectivity peer-to-peer mesh
    approval/touch_id.py       LocalAuthentication biometric approval
    approval/audio.py          say / NSSound / AVSpeechSynthesizer heartbeats
    approval/notifications.py  UNUserNotificationCenter critical alerts
    resilience/snapshot.py     APFS clones for atomic mesh checkpoints

  Tier 3 — Orchestration
    cli.py                     `sc-mac` unified CLI with --backend selector

Each module degrades gracefully: missing optional deps (iterm2, atomacos,
pyobjc-framework-Quartz, etc.) cause the affected backend to report itself
unavailable, not the package to fail to import.

See MAC_V2_ARCHITECTURE.md for design and COMPETITIVE_MAC_LANES.md for the
record of Mac-only differentiators vs. Win32 and competing app-control SDKs.
"""

from __future__ import annotations

__version__ = "2.0.0-dev"

__all__ = [
    "get_backend",
    "list_backends",
    "BackendUnavailable",
]


def get_backend(name: str | None = None):
    """Return a Backend instance. None auto-selects the best available."""
    from .backends.selector import auto_select, get_named

    return get_named(name) if name else auto_select()


def list_backends() -> list[str]:
    """Return names of all backends that report themselves available."""
    from .backends.selector import available_names

    return available_names()


class BackendUnavailable(RuntimeError):
    """Raised when a requested backend's dependencies are not installed."""
