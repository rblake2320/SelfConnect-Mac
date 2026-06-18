"""
Backend abstract base class.

A Backend is the macOS equivalent of one slice of the Win32 selfconnect SDK:
it can enumerate terminal targets, inject text into one, read its visible
buffer, and capture a per-window image. Different backends trade off speed,
permission requirements, and substrate (GUI Terminal vs tmux vs PTY).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Target:
    """An addressable terminal session.

    `ident` is the backend-specific identifier (CGWindowID, tmux pane id,
    iTerm2 session uuid, PID, etc.). `title` is human-readable.
    """

    ident: str
    title: str
    pid: int = 0
    backend: str = ""
    extra: dict = field(default_factory=dict)


class Backend(ABC):
    """The five operations every backend must support, plus a self-check."""

    name: str = "abstract"

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if this backend's dependencies are installed AND its
        substrate (iTerm2 process, tmux server, etc.) is running."""

    @abstractmethod
    def enumerate(self) -> list[Target]:
        """List all terminal sessions this backend can reach."""

    @abstractmethod
    def send(self, target: Target, text: str, submit: bool = True) -> None:
        """Inject `text` into `target`. If `submit`, also press Enter."""

    @abstractmethod
    def read(self, target: Target, tail: int = 4000) -> str:
        """Return the most recent visible buffer content, last `tail` chars."""

    def spawn(self, title: str, cwd: str, command: str = "claude") -> Target:
        """Create a new terminal session running `command` in `cwd`.

        Default implementation raises — backends that can spawn override.
        """
        raise NotImplementedError(f"{self.name} backend does not implement spawn()")

    def capture(self, target: Target, out_path: str) -> Optional[str]:
        """Save a per-window image to `out_path`. Returns the path or None.

        Default implementation returns None — backends that can capture override.
        """
        return None

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Backend name={self.name!r} available={self.is_available()}>"
