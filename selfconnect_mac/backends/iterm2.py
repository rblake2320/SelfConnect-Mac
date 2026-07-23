"""
iTerm2 Python API backend.

This is the single biggest upgrade over the legacy AppleScript path:

  - No Accessibility permission required at runtime (uses iTerm2's own
    WebSocket protocol, not synthetic key events).
  - No focus stealing — the controller terminal stays foreground.
  - Lossless screen reads via async_get_screen_contents (cell-accurate).
  - Per-session uuid identifiers that survive tab/window reorders.

Closest Win32 analog: there is none. iTerm2's API surface exceeds anything
the Windows Terminal exposes today.

Requires: iTerm2 (with "Enable Python API" in Preferences > General > Magic),
          `pip install iterm2`.
"""

from __future__ import annotations

import asyncio
import os

from .base import Backend, Target

try:
    import iterm2  # type: ignore

    _HAS_ITERM2 = True
except ImportError:
    _HAS_ITERM2 = False


def _run(coro):
    """Run an async coroutine to completion in a fresh loop."""
    return asyncio.new_event_loop().run_until_complete(coro)


class ITerm2Backend(Backend):
    name = "iterm2"

    @classmethod
    def is_available(cls) -> bool:
        if not _HAS_ITERM2:
            return False
        # iTerm2 must be running with Python API enabled.
        return os.path.exists(os.path.expanduser("~/Library/Application Support/iTerm2"))

    def _connect(self):
        return iterm2.Connection.async_create()

    def enumerate(self) -> list[Target]:
        async def _go():
            conn = await self._connect()
            app = await iterm2.async_get_app(conn)
            out: list[Target] = []
            for window in app.windows:
                for tab in window.tabs:
                    for session in tab.sessions:
                        title = await session.async_get_variable("session.name") or session.name
                        out.append(
                            Target(
                                ident=session.session_id,
                                title=str(title),
                                backend=self.name,
                                extra={"window_id": window.window_id, "tab_id": tab.tab_id},
                            )
                        )
            return out

        return _run(_go())

    def send(self, target: Target, text: str, submit: bool = True) -> None:
        payload = text + ("\n" if submit else "")

        async def _go():
            conn = await self._connect()
            app = await iterm2.async_get_app(conn)
            session = app.get_session_by_id(target.ident)
            if session is None:
                raise RuntimeError(f"iTerm2 session {target.ident} not found")
            await session.async_send_text(payload)

        _run(_go())

    def read(self, target: Target, tail: int = 4000) -> str:
        async def _go():
            conn = await self._connect()
            app = await iterm2.async_get_app(conn)
            session = app.get_session_by_id(target.ident)
            if session is None:
                raise RuntimeError(f"iTerm2 session {target.ident} not found")
            contents = await session.async_get_screen_contents()
            lines = []
            for i in range(contents.number_of_lines):
                line = contents.line(i)
                lines.append("".join(seg.string for seg in line))
            return "\n".join(lines)[-tail:]

        return _run(_go())

    def spawn(self, title: str, cwd: str, command: str = "claude") -> Target:
        async def _go():
            conn = await self._connect()
            await iterm2.async_get_app(conn)
            window = await iterm2.Window.async_create(conn, command=f"/bin/zsh -lc 'cd {cwd!r} && {command}'")
            session = window.current_tab.current_session
            await session.async_set_name(title)
            return Target(
                ident=session.session_id,
                title=title,
                backend=self.name,
                extra={"window_id": window.window_id, "tab_id": window.current_tab.tab_id},
            )

        return _run(_go())

    def capture(self, target: Target, out_path: str) -> str | None:
        # iTerm2's API doesn't expose pixel capture directly; fall back to
        # CGWindowListCreateImage via the capture module.
        from ..capture import capture_iterm2_session

        return capture_iterm2_session(target.ident, out_path)
