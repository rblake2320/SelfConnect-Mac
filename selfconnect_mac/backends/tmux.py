"""
tmux backend — headless, SSH-safe, no GUI required.

This is the lane Windows literally cannot match: a multi-agent mesh that
runs over SSH, inside CI, on a server with no display. tmux sessions are
addressable from anywhere, and send-keys / capture-pane bypass the OS
input layer entirely.

Closest Win32 analog: none. Windows Terminal does not have a comparable
control surface.

Requires: `tmux` on PATH. Optional: `libtmux` for richer parsing.
"""

from __future__ import annotations

import shutil
import subprocess

from .base import Backend, Target


def _tmux(*args: str, check: bool = True, timeout: float = 5.0) -> str:
    proc = subprocess.run(
        ["tmux", *args], capture_output=True, text=True, timeout=timeout, check=False
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"tmux {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


class TmuxBackend(Backend):
    name = "tmux"

    @classmethod
    def is_available(cls) -> bool:
        if not shutil.which("tmux"):
            return False
        # Server may not be running yet; absence of a server is fine — we
        # can start one on first spawn(). Availability == binary present.
        return True

    def enumerate(self) -> list[Target]:
        try:
            out = _tmux("list-panes", "-a", "-F",
                        "#{pane_id}\t#{session_name}:#{window_index}.#{pane_index}\t#{pane_pid}\t#{pane_title}")
        except RuntimeError:
            return []
        targets: list[Target] = []
        for line in out.strip().splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            pane_id, addr, pid, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
            try:
                pid_i = int(pid)
            except ValueError:
                pid_i = 0
            targets.append(
                Target(
                    ident=addr,
                    title=title or addr,
                    pid=pid_i,
                    backend=self.name,
                    extra={"pane_id": pane_id},
                )
            )
        return targets

    def send(self, target: Target, text: str, submit: bool = True) -> None:
        # -l (literal) avoids tmux's key-name interpretation; perfect for
        # arbitrary text. Submit is a separate send-keys with the literal
        # `Enter` key name so it works inside any TUI including Claude Code.
        _tmux("send-keys", "-t", target.ident, "-l", text)
        if submit:
            _tmux("send-keys", "-t", target.ident, "Enter")

    def read(self, target: Target, tail: int = 4000) -> str:
        # -p prints to stdout; -S -3000 starts 3000 lines back from the
        # current bottom of scrollback. We then slice the tail.
        out = _tmux("capture-pane", "-p", "-t", target.ident, "-S", "-3000")
        return out[-tail:]

    def spawn(self, title: str, cwd: str, command: str = "claude") -> Target:
        # Use the title as the tmux session name (sanitized).
        sess = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
        # -d detached; -s session-name; -c starting cwd.
        _tmux("new-session", "-d", "-s", sess, "-c", cwd, command)
        # Set pane title (visible in status bar / TUI).
        try:
            _tmux("select-pane", "-t", f"{sess}:0.0", "-T", title)
        except RuntimeError:
            pass  # pane title is decorative; failure is non-fatal
        return Target(
            ident=f"{sess}:0.0",
            title=title,
            backend=self.name,
            extra={"session": sess},
        )

    def capture(self, target: Target, out_path: str) -> str | None:
        # No pixel output from tmux; write the text buffer instead.
        text = self.read(target, tail=100000)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return out_path
