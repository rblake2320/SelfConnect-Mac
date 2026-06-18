"""
CGEvent backend — direct twin of Win32 PostMessage(WM_CHAR).

Uses Quartz Event Services to synthesize HID keyboard events and post them
either to the system tap (global) or to a specific PID. CGEventPostToPid is
the closest Mac analog to PostMessage(hwnd, WM_CHAR, ...).

Versus AppleScript `keystroke`:
  - ~10x faster per call (no osascript fork).
  - Direct Unicode injection via CGEventKeyboardSetUnicodeString — no per-
    keycode lookup, no dead-key surprises.
  - Targets a specific PID instead of "whatever's focused right now".

Versus pynput:
  - Same underlying mechanism but exposes the targeted-post option.

Read path uses AXUIElement (via atomacos if installed) — the Mac analog of
UIAutomation that you get_text_uia() on Windows.

Requires: `pip install pyobjc-framework-Quartz`. For read(), optional
`pip install atomacos` gives clean Pythonic AX access; without it we fall
back to AppleScript `contents of window`.
"""

from __future__ import annotations

import os
import subprocess
from typing import Optional

from .base import Backend, Target

try:
    import Quartz  # pyobjc-framework-Quartz  # type: ignore

    _HAS_QUARTZ = True
except ImportError:
    _HAS_QUARTZ = False

try:
    import atomacos  # type: ignore

    _HAS_AX = True
except ImportError:
    _HAS_AX = False


class CGEventBackend(Backend):
    name = "cgevent"

    @classmethod
    def is_available(cls) -> bool:
        return _HAS_QUARTZ

    def enumerate(self) -> list[Target]:
        # Use CGWindowListCopyWindowInfo — the EnumWindows equivalent.
        if not _HAS_QUARTZ:
            return []
        opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
        infos = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID)
        targets: list[Target] = []
        terminal_owners = {"Terminal", "iTerm2", "iTerm", "Warp", "WezTerm", "kitty", "Ghostty"}
        for info in infos:
            owner = info.get("kCGWindowOwnerName", "")
            if owner not in terminal_owners:
                continue
            wid = int(info.get("kCGWindowNumber", 0))
            pid = int(info.get("kCGWindowOwnerPID", 0))
            title = info.get("kCGWindowName") or f"{owner} window {wid}"
            targets.append(
                Target(
                    ident=str(wid),
                    title=str(title),
                    pid=pid,
                    backend=self.name,
                    extra={"owner": owner, "cg_window_id": wid},
                )
            )
        return targets

    def send(self, target: Target, text: str, submit: bool = True) -> None:
        if not _HAS_QUARTZ:
            raise RuntimeError("CGEvent backend requires pyobjc-framework-Quartz")
        pid = target.pid
        if pid <= 0:
            raise RuntimeError("CGEvent backend needs target.pid; enumerate() first")

        source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)

        # Inject the literal Unicode string in one event — analog of
        # PostMessage(WM_CHAR) burst mode.
        ev_down = Quartz.CGEventCreateKeyboardEvent(source, 0, True)
        Quartz.CGEventKeyboardSetUnicodeString(ev_down, len(text), text)
        Quartz.CGEventPostToPid(pid, ev_down)

        ev_up = Quartz.CGEventCreateKeyboardEvent(source, 0, False)
        Quartz.CGEventKeyboardSetUnicodeString(ev_up, len(text), text)
        Quartz.CGEventPostToPid(pid, ev_up)

        if submit:
            # Virtual keycode 36 == kVK_Return.
            ret_down = Quartz.CGEventCreateKeyboardEvent(source, 36, True)
            Quartz.CGEventPostToPid(pid, ret_down)
            ret_up = Quartz.CGEventCreateKeyboardEvent(source, 36, False)
            Quartz.CGEventPostToPid(pid, ret_up)

    def read(self, target: Target, tail: int = 4000) -> str:
        if _HAS_AX and target.pid > 0:
            try:
                app = atomacos.getAppRefByPid(target.pid)
                # Walk AXTextArea / AXStaticText descendants for text content.
                buf: list[str] = []

                def _walk(el, depth=0):
                    if depth > 6:
                        return
                    try:
                        role = el.AXRole
                    except Exception:
                        return
                    if role in ("AXTextArea", "AXStaticText"):
                        try:
                            val = el.AXValue
                            if isinstance(val, str):
                                buf.append(val)
                        except Exception:
                            pass
                    try:
                        children = el.AXChildren or []
                    except Exception:
                        children = []
                    for c in children:
                        _walk(c, depth + 1)

                for w in app.windows():
                    _walk(w)
                joined = "\n".join(buf)
                if joined:
                    return joined[-tail:]
            except Exception:
                pass  # fall through to AppleScript

        # AppleScript fallback for Terminal.app.
        owner = target.extra.get("owner", "Terminal") if target.extra else "Terminal"
        if owner not in ("Terminal", "iTerm2", "iTerm"):
            return ""
        script = f'tell application "{owner}" to return contents of window id {target.ident}'
        try:
            out = subprocess.check_output(
                ["osascript", "-e", script], text=True, timeout=10, stderr=subprocess.DEVNULL
            )
            return out[-tail:]
        except Exception:
            return ""

    def capture(self, target: Target, out_path: str) -> Optional[str]:
        from ..capture import capture_cg_window

        try:
            wid = int(target.extra.get("cg_window_id") or target.ident)
        except (ValueError, AttributeError):
            return None
        return capture_cg_window(wid, out_path)
