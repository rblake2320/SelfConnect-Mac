"""Spawn and bootstrap a macOS Codex peer terminal.

This is the macOS equivalent of the Windows peer-spawn runbooks:
it opens a new Terminal window, starts Codex, submits the first prompt, and
keeps a lightweight watch loop so one Codex does not leave the other stuck at
an approval prompt.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass

from self_connect import WindowTarget, get_text_uia, send_string


ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CODEX = os.path.expanduser("~/.npm-global/bin/codex")
DEFAULT_CODEX_ARGS = "--ask-for-approval on-request --sandbox workspace-write"
TERMINAL_PID = 13733


def osascript(*lines: str) -> str:
    cmd: list[str] = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def terminal_pid() -> int:
    try:
        out = osascript(
            'tell application "System Events" to get unix id of application process "Terminal"'
        )
        return int(out)
    except Exception:
        return TERMINAL_PID


def spawn_codex(codex: str, codex_args: str, cwd: str) -> int:
    out = osascript(
        f'tell application "Terminal" to do script "cd {cwd}; {codex} {codex_args}"'
    )
    match = re.search(r"window id (\d+)", out)
    if not match:
        raise RuntimeError(f"Could not parse Terminal window id from: {out!r}")
    return int(match.group(1))


def submit_terminal_window(window_id: int) -> None:
    osascript(
        'tell application "Terminal"',
        f"set index of window id {window_id} to 1",
        "activate",
        "end tell",
        "delay 0.2",
        'tell application "System Events" to key code 36',
    )


def wait_for_codex(window_id: int, timeout: float = 45.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = get_text_uia(window_id)
        if "OpenAI Codex" in text or "gpt-" in text:
            return
        time.sleep(1)
    raise TimeoutError(f"Codex did not appear ready in Terminal window {window_id}")


def build_bootstrap_prompt(peer_id: int, parent_id: int, pid: int) -> str:
    return (
        f"You are Agent B in Terminal window {peer_id}. "
        f"Parent Codex is Terminal window {parent_id}. "
        f"Work in {ROOT}. Use .venv/bin/python. "
        "To read parent, import get_text_uia from self_connect and call "
        f"get_text_uia({parent_id}). "
        "To send parent a message, import WindowTarget and send_string, then call "
        f"send_string(WindowTarget({parent_id}, \"parent codex\", "
        f"\"macOS.TerminalWindow\", {pid}, \"Terminal\"), "
        "\"AGENT_B: your message here\\r\"). "
        "When you need a tool approval, state it visibly and wait. "
        "Also watch parent output for approval prompts; if parent is waiting on you, "
        "answer promptly so both agents do not block at the same time. "
        "First reply here with ACK, then send parent exactly AGENT_B: ACK via SelfConnect. "
        "Do not change git remotes or push."
    )


APPROVAL_MARKERS = (
    "Do you want to",
    "approve",
    "approval",
    "Allow",
    "Run this command",
)


@dataclass
class WatchState:
    last_peer_tail: str = ""
    last_parent_tail: str = ""


def watch_pair(peer_id: int, parent_id: int, interval: float = 2.0) -> None:
    state = WatchState()
    print(f"Watching parent={parent_id} peer={peer_id}. Ctrl-C to stop.")
    while True:
        peer_tail = get_text_uia(peer_id)[-3000:]
        parent_tail = get_text_uia(parent_id)[-3000:]
        for label, tail, last in (
            ("peer", peer_tail, state.last_peer_tail),
            ("parent", parent_tail, state.last_parent_tail),
        ):
            if tail != last and any(marker.lower() in tail.lower() for marker in APPROVAL_MARKERS):
                print(f"\n[{label} approval/watch marker]\n{tail[-1200:]}\n")
        state.last_peer_tail = peer_tail
        state.last_parent_tail = parent_tail
        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", type=int, required=True, help="Parent Terminal window id")
    parser.add_argument("--codex", default=DEFAULT_CODEX, help="Path to Codex executable")
    parser.add_argument(
        "--codex-args",
        default=DEFAULT_CODEX_ARGS,
        help="Arguments passed to Codex. Defaults reduce routine approval prompts.",
    )
    parser.add_argument("--cwd", default=ROOT, help="Working directory for the new Codex")
    parser.add_argument("--watch", action="store_true", help="Keep watching both windows")
    args = parser.parse_args()

    pid = terminal_pid()
    peer_id = spawn_codex(args.codex, args.codex_args, args.cwd)
    print(f"Spawned Codex peer in Terminal window {peer_id}")
    wait_for_codex(peer_id)

    peer = WindowTarget(peer_id, "codex peer", "macOS.TerminalWindow", pid, "Terminal")
    prompt = build_bootstrap_prompt(peer_id, args.parent, pid)
    send_string(peer, prompt + "\r", char_delay=0.01)
    submit_terminal_window(peer_id)
    print("Submitted bootstrap prompt.")

    if args.watch:
        watch_pair(peer_id, args.parent)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
