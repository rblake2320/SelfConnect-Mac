"""
Backend selector — auto-detect the best available backend.

Priority order (highest ROI first):

  1. iterm2     — typed, focus-free, lossless; the Mac SDK equivalent.
  2. tmux       — headless, SSH-safe; only one with no GUI dependency.
  3. cgevent    — direct PostMessage twin for any terminal app.
  4. applescript — legacy fallback; always last because of focus-stealing.
"""

from __future__ import annotations

from typing import Optional

from .applescript import AppleScriptBackend
from .base import Backend
from .cgevent import CGEventBackend
from .iterm2 import ITerm2Backend
from .tmux import TmuxBackend

_REGISTRY: dict[str, type[Backend]] = {
    "iterm2": ITerm2Backend,
    "tmux": TmuxBackend,
    "cgevent": CGEventBackend,
    "applescript": AppleScriptBackend,
}

_PRIORITY = ["iterm2", "tmux", "cgevent", "applescript"]


def get_named(name: str) -> Backend:
    from .. import BackendUnavailable

    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown backend {name!r}; known: {sorted(_REGISTRY)}")
    if not cls.is_available():
        raise BackendUnavailable(f"Backend {name!r} reports unavailable on this system")
    return cls()


def auto_select() -> Backend:
    from .. import BackendUnavailable

    for name in _PRIORITY:
        cls = _REGISTRY[name]
        if cls.is_available():
            return cls()
    raise BackendUnavailable(
        "No SelfConnect Mac backend is available. Install one of: "
        "iterm2 (pip install iterm2 + enable in iTerm2 prefs), "
        "tmux (brew install tmux), "
        "or pyobjc-framework-Quartz (pip install pyobjc-framework-Quartz) for cgevent."
    )


def available_names() -> list[str]:
    return [name for name in _PRIORITY if _REGISTRY[name].is_available()]


def find_backend_for_target(ident_hint: str) -> Optional[Backend]:
    """Best-effort: pick a backend that can address `ident_hint`.

    tmux ids look like 'session:window.pane' or '%N';
    iTerm2 session uuids are 36-char dashed;
    CG window IDs are plain integers.
    """
    if ":" in ident_hint or ident_hint.startswith("%"):
        if TmuxBackend.is_available():
            return TmuxBackend()
    if len(ident_hint) == 36 and ident_hint.count("-") == 4:
        if ITerm2Backend.is_available():
            return ITerm2Backend()
    if ident_hint.isdigit():
        if CGEventBackend.is_available():
            return CGEventBackend()
        if AppleScriptBackend.is_available():
            return AppleScriptBackend()
    return None
