"""Small macOS control CLI for SelfConnect Terminal meshes.

Use this instead of separate read/send/submit AppleScript calls. It keeps the
operator flow simple and lowers approval friction for routine mesh operations.
"""

from __future__ import annotations

import argparse
import subprocess
import time

from self_connect import WindowTarget, get_text_uia, list_windows, send_string


TERMINAL_PID = 13733
APPROVAL_MARKERS = (
    "Do you want to",
    "approve",
    "approval",
    "Allow",
    "Running…",
    "Running...",
    "press enter",
)


def osascript(*lines: str) -> str:
    cmd: list[str] = ["osascript"]
    for line in lines:
        cmd.extend(["-e", line])
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    return proc.stdout.strip()


def resolve_window(spec: str) -> WindowTarget:
    windows = [w for w in list_windows() if w.exe_name == "Terminal"]
    try:
        wanted_id = int(spec)
    except ValueError:
        wanted_id = None
    if wanted_id is not None:
        match = next((w for w in windows if w.hwnd == wanted_id), None)
        if match:
            return match
        return WindowTarget(wanted_id, f"terminal {wanted_id}", "macOS.TerminalWindow", TERMINAL_PID, "Terminal")

    needle = spec.lower()
    matches = [w for w in windows if needle in w.title.lower()]
    if not matches:
        raise SystemExit(f"No Terminal window title contains {spec!r}")
    if len(matches) > 1:
        print(f"Multiple matches for {spec!r}; using first:")
        for win in matches:
            print(win)
    return matches[0]


def submit(window: str) -> None:
    window_id = resolve_window(window).hwnd
    osascript(
        'tell application "Terminal"',
        f"set index of window id {window_id} to 1",
        "activate",
        "end tell",
        "delay 0.4",
        'tell application "System Events" to key code 36',
    )


def send(window: str, text: str, do_submit: bool) -> None:
    send_string(resolve_window(window), text + "\r", char_delay=0.01)
    if do_submit:
        submit(window)


def read(window: str, tail: int) -> str:
    text = get_text_uia(resolve_window(window).hwnd)
    return text[-tail:] if tail else text


def watch(windows: list[str], interval: float, cycles: int, tail: int) -> None:
    last: dict[str, str] = {}
    count = 0
    while cycles <= 0 or count < cycles:
        for window in windows:
            target = resolve_window(window)
            key = str(target.hwnd)
            text = read(str(target.hwnd), tail)
            if text != last.get(key, ""):
                print(f"\n--- window {target.hwnd}: {target.title} ---\n{text}")
                if any(marker.lower() in text.lower() for marker in APPROVAL_MARKERS):
                    print(f"\n[watch] window {target.hwnd} may need attention")
                last[key] = text
        count += 1
        time.sleep(interval)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")

    p_read = sub.add_parser("read")
    p_read.add_argument("window", help="Terminal window id or title fragment")
    p_read.add_argument("--tail", type=int, default=5000)

    p_submit = sub.add_parser("submit")
    p_submit.add_argument("window", help="Terminal window id or title fragment")

    p_send = sub.add_parser("send")
    p_send.add_argument("window", help="Terminal window id or title fragment")
    p_send.add_argument("text")
    p_send.add_argument("--submit", action="store_true")

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("window", help="Terminal window id or title fragment")
    p_ask.add_argument("text")

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("windows", nargs="+", help="Terminal window ids or title fragments")
    p_watch.add_argument("--interval", type=float, default=2.0)
    p_watch.add_argument("--cycles", type=int, default=0, help="0 means run forever")
    p_watch.add_argument("--tail", type=int, default=3000)

    args = parser.parse_args()

    if args.cmd == "list":
        for win in list_windows():
            if win.exe_name == "Terminal":
                print(win)
    elif args.cmd == "read":
        print(read(args.window, args.tail))
    elif args.cmd == "submit":
        submit(args.window)
    elif args.cmd == "send":
        send(args.window, args.text, args.submit)
    elif args.cmd == "ask":
        send(args.window, args.text, True)
    elif args.cmd == "watch":
        watch(args.windows, args.interval, args.cycles, args.tail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
