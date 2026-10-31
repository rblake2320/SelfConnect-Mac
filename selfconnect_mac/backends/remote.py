"""
remote backend — the same five operations, on a *second Mac*, over SSH.

Why this exists
---------------
The tmux and AppleScript backends only reach terminals on the machine they
run on. A two-Mac agent mesh (e.g. MacBook Pro + Mac mini on one Wi-Fi) needs
the hop to be part of the SDK, not an ad-hoc `ssh host 'osascript ...'`.

This backend wraps one of two remote substrates:

  kind="tmux"      ssh host tmux list-panes / send-keys / capture-pane
                   (headless, lossless, works for sessions started over SSH)
  kind="terminal"  ssh host osascript → Terminal.app windows *by window id*
                   "do script ... in window id N"   = type + Enter (no focus
                   change, no Accessibility permission needed)
                   "contents of selected tab of window id N" = read back

Proven 2026-10-31 (macOS 27 mini, macOS 15 MacBook): both directions worked
from a key-only SSH session with no TCC prompt, as long as the SSH user is the
same user that owns the GUI session. Addressing by window id, never by
"front window": the front window changes under you.

Target idents are `host/<remote ident>`, e.g. `mini/mesh:0.0` or `mini/1436`.

Limitations
-----------
* terminal kind: `submit=False` falls back to System Events keystrokes, which
  needs Accessibility for sshd-keygen-wrapper and raises if denied. Prefer
  tmux targets when you need partial input.
* No pixel capture over SSH; `capture()` writes the text buffer.
"""

from __future__ import annotations

import shlex
import subprocess

from .base import Backend, Target

_SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=6"]
# Non-interactive SSH sessions on macOS get a minimal PATH: Homebrew / user-built
# tmux (and uv, claude) are invisible unless we say where to look.
_REMOTE_PATH = "PATH=/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"


def _ssh(host: str, command: str, timeout: float = 15.0) -> str:
    proc = subprocess.run(
        ["ssh", *_SSH_OPTS, host, f"{_REMOTE_PATH} {command}"],
        capture_output=True, text=True, timeout=timeout, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ssh {host} failed ({proc.returncode}): {proc.stderr.strip()}")
    return proc.stdout


def _osa(script: str) -> str:
    """Build a remote `osascript` invocation for a multi-line AppleScript."""
    lines = [ln for ln in script.strip().splitlines() if ln.strip()]
    return "osascript " + " ".join("-e " + shlex.quote(ln) for ln in lines)


def _as_str(text: str) -> str:
    """Escape text for inclusion inside an AppleScript double-quoted string."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


class RemoteBackend(Backend):
    name = "remote"

    def __init__(self, host: str, kind: str = "tmux") -> None:
        if kind not in ("tmux", "terminal"):
            raise ValueError("kind must be 'tmux' or 'terminal'")
        self.host = host
        self.kind = kind
        self.name = f"remote-{kind}@{host}"

    @classmethod
    def is_available(cls) -> bool:
        # Availability is per-host; checked lazily by `ping()`.
        import shutil
        return shutil.which("ssh") is not None

    def ping(self) -> bool:
        try:
            return _ssh(self.host, "echo ok", timeout=10).strip() == "ok"
        except (RuntimeError, subprocess.TimeoutExpired):
            return False

    # -- ident helpers -----------------------------------------------------
    def _local_ident(self, target: Target) -> str:
        ident = target.ident
        prefix = f"{self.host}/"
        return ident[len(prefix):] if ident.startswith(prefix) else ident

    def _wrap(self, ident: str) -> str:
        return f"{self.host}/{ident}"

    # -- enumerate ---------------------------------------------------------
    def enumerate(self) -> list[Target]:
        if self.kind == "tmux":
            try:
                out = _ssh(self.host, "tmux list-panes -a -F "
                           "'#{pane_id}\t#{session_name}:#{window_index}.#{pane_index}\t#{pane_pid}\t#{pane_title}'")
            except RuntimeError:
                return []
            targets: list[Target] = []
            for line in out.strip().splitlines():
                parts = line.split("\t")
                if len(parts) < 4:
                    continue
                pane_id, addr, pid, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
                targets.append(Target(ident=self._wrap(addr), title=title or addr,
                                      pid=int(pid) if pid.isdigit() else 0,
                                      backend=self.name, extra={"pane_id": pane_id, "host": self.host}))
            return targets
        # NB: inside `tell application "Terminal"`, `tab` is Terminal's *tab class*,
        # not the tab character — use `character id 9` explicitly.
        script = '''
set d to character id 9
tell application "Terminal"
set out to ""
repeat with w in windows
set t to selected tab of w
set out to out & (id of w) & d & (tty of t) & d & (busy of t) & d & (frontmost of w) & d & (name of w) & linefeed
end repeat
return out
end tell'''
        try:
            out = _ssh(self.host, _osa(script))
        except RuntimeError:
            return []
        targets = []
        for line in out.strip().splitlines():
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            wid, tty, busy, front, title = parts[0], parts[1], parts[2], parts[3], "\t".join(parts[4:])
            targets.append(Target(ident=self._wrap(wid), title=title, backend=self.name,
                                  extra={"tty": tty, "busy": busy == "true",
                                         "frontmost": front == "true", "host": self.host}))
        return targets

    # -- send --------------------------------------------------------------
    def send(self, target: Target, text: str, submit: bool = True) -> None:
        ident = self._local_ident(target)
        if self.kind == "tmux":
            _ssh(self.host, f"tmux send-keys -t {shlex.quote(ident)} -l {shlex.quote(text)}")
            if submit:
                _ssh(self.host, f"tmux send-keys -t {shlex.quote(ident)} Enter")
            return
        if submit:
            # `do script ... in window id N` types the text and presses Return in
            # that window without changing focus and without Accessibility.
            script = f'tell application "Terminal" to do script "{_as_str(text)}" in window id {int(ident)}'
            _ssh(self.host, _osa(script))
            return
        # Partial input needs keystrokes into the focused window. This is
        # TCC-gated (Accessibility for sshd-keygen-wrapper) and slow (one
        # keystroke per character), so it is bounded and fails loudly.
        # Prefer `submit=True` (do script) or a tmux target.
        script = f'''
tell application "Terminal" to set index of window id {int(ident)} to 1
tell application "System Events" to keystroke "{_as_str(text)}"'''
        try:
            _ssh(self.host, _osa(script), timeout=10 + 0.1 * len(text))
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"keystroke into {self.host} window {ident} timed out: System Events "
                "needs Accessibility for the SSH session, or the text is long. "
                "Use submit=True (sc-mac send --submit) or a tmux target.") from e

    # -- read --------------------------------------------------------------
    def read(self, target: Target, tail: int = 4000) -> str:
        ident = self._local_ident(target)
        if self.kind == "tmux":
            out = _ssh(self.host, f"tmux capture-pane -p -t {shlex.quote(ident)} -S -3000")
        else:
            out = _ssh(self.host, _osa(
                f'tell application "Terminal" to return contents of selected tab of window id {int(ident)}'))
        return out[-tail:]

    # -- spawn -------------------------------------------------------------
    def spawn(self, title: str, cwd: str, command: str = "claude") -> Target:
        sess = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
        if self.kind == "tmux":
            _ssh(self.host, f"tmux new-session -d -s {shlex.quote(sess)} -c {shlex.quote(cwd)} {shlex.quote(command)}")
            return Target(ident=self._wrap(f"{sess}:0.0"), title=title, backend=self.name,
                          extra={"session": sess, "host": self.host})
        script = f'''
tell application "Terminal"
set w to do script "cd {_as_str(cwd)} && {_as_str(command)}"
return id of (first window whose selected tab is w)
end tell'''
        wid = _ssh(self.host, _osa(script)).strip()
        return Target(ident=self._wrap(wid), title=title, backend=self.name, extra={"host": self.host})

    def capture(self, target: Target, out_path: str) -> str | None:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(self.read(target, tail=100000))
        return out_path
