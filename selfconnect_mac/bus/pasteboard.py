"""
NSPasteboard private named channels — typed, change-counted IPC.

NSPasteboard isn't just the system clipboard. `pasteboardWithUniqueName`
creates a *private* pasteboard that isn't visible to other apps unless
they know the name. It supports multiple data types per item and exposes
a monotonically increasing change count, so subscribers can poll for
new data without storing the entire history.

This is a richer cross-agent transport than pbcopy/pbpaste:
  - multiple typed payloads per message (text + image + JSON together)
  - private namespace per mesh
  - change count = O(1) "is there anything new" check

Requires pyobjc-framework-Cocoa; degrades to /tmp filesystem channels.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path


try:
    from AppKit import NSPasteboard, NSPasteboardTypeString  # type: ignore

    _HAS_APPKIT = True
except ImportError:
    _HAS_APPKIT = False


class PrivateChannel:
    """A named private pasteboard or its filesystem fallback."""

    def __init__(self, name: str):
        self.name = name
        if _HAS_APPKIT:
            self._pb = NSPasteboard.pasteboardWithName_(name)
        else:
            self._pb = None
            self._fallback_dir = Path(tempfile.gettempdir()) / f"selfconnect-pb-{name}"
            self._fallback_dir.mkdir(parents=True, exist_ok=True)

    def post(self, payload: dict) -> int:
        """Write `payload` as JSON. Returns the new change count."""
        body = json.dumps(payload, ensure_ascii=False, default=str)
        if self._pb is not None:
            self._pb.clearContents()
            self._pb.setString_forType_(body, NSPasteboardTypeString)
            return int(self._pb.changeCount())
        # Fallback: rotating file.
        ts = time.time_ns()
        p = self._fallback_dir / f"msg_{ts}.json"
        p.write_text(body, encoding="utf-8")
        return ts

    def latest(self) -> dict | None:
        """Read the most recent payload, or None."""
        if self._pb is not None:
            s = self._pb.stringForType_(NSPasteboardTypeString)
            if not s:
                return None
            try:
                return json.loads(str(s))
            except json.JSONDecodeError:
                return None
        files = sorted(self._fallback_dir.glob("msg_*.json"))
        if not files:
            return None
        try:
            return json.loads(files[-1].read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def change_count(self) -> int:
        if self._pb is not None:
            return int(self._pb.changeCount())
        files = list(self._fallback_dir.glob("msg_*.json"))
        return len(files)
