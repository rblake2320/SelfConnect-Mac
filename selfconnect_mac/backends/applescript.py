"""
AppleScript backend — wraps the legacy self_connect.py Mac path.

Preserved as a backend (rather than deleted) for two reasons:

  1. Prior-art continuity: the AppleScript path is what was verified live
     on 2026-05-13..18 and recorded in PATENT_PROCESS_RECORD.md. Keeping
     it importable from the v2 facade lets that record stay valid.

  2. Last-resort fallback: when iTerm2 isn't installed, tmux isn't running,
     and Accessibility for CGEventPostToPid isn't granted, AppleScript via
     System Events still works on Terminal.app out of the box.

This module is a thin adapter — it does not reimplement what self_connect.py
already does.
"""

from __future__ import annotations

import sys
from typing import Optional

from .base import Backend, Target

_IS_MAC = sys.platform == "darwin"


class AppleScriptBackend(Backend):
    name = "applescript"

    @classmethod
    def is_available(cls) -> bool:
        if not _IS_MAC:
            return False
        try:
            # Verify the legacy module imports cleanly on this Mac.
            import self_connect  # noqa: F401
        except ImportError:
            return False
        return True

    def _legacy(self):
        import self_connect

        return self_connect

    def enumerate(self) -> list[Target]:
        sc = self._legacy()
        wins = sc.list_windows()
        out: list[Target] = []
        for w in wins:
            if getattr(w, "exe_name", "") != "Terminal":
                continue
            out.append(
                Target(
                    ident=str(w.hwnd),
                    title=getattr(w, "title", "") or f"Terminal {w.hwnd}",
                    pid=getattr(w, "pid", 0),
                    backend=self.name,
                    extra={"legacy_window_target": True},
                )
            )
        return out

    def send(self, target: Target, text: str, submit: bool = True) -> None:
        sc = self._legacy()
        # Reuse the legacy WindowTarget by re-resolving from hwnd.
        wt = next((w for w in sc.list_windows() if str(w.hwnd) == target.ident), None)
        if wt is None:
            raise RuntimeError(f"AppleScript target {target.ident} not found")
        sc.send_string(wt, text + ("\r" if submit else ""), char_delay=0.01)

    def read(self, target: Target, tail: int = 4000) -> str:
        sc = self._legacy()
        text = sc.get_text_uia(int(target.ident)) or ""
        return text[-tail:]

    def capture(self, target: Target, out_path: str) -> Optional[str]:
        sc = self._legacy()
        try:
            return sc.save_capture(int(target.ident), out_path, crop=False)
        except Exception:
            return None
