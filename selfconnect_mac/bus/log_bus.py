"""
Unified logging as a mesh bus.

macOS unified logging (`os_log`) is structured, queryable, and signed-
timestamped. Each SelfConnect agent emits to its own subsystem
(`com.selfconnect.<agent_id>`) and the controller subscribes via
`log stream --predicate ...`.

This gives the mesh a built-in OS-level pub/sub bus with:
  - zero install / zero port / zero file
  - structured filtering by subsystem, category, level
  - survives reboots (persisted to the system log archive)
  - works across user sessions, across SSH, across users

There is no Win32 equivalent. Windows ETW exists but is dramatically
harder to use and requires admin to subscribe.

Lancelot/UAB has no analog — their architecture is a port-3100 HTTP
server, not an OS-native channel.
"""

from __future__ import annotations

import json
import shlex
import subprocess
import threading
from typing import Callable, Optional


SUBSYSTEM_PREFIX = "com.selfconnect"


def emit(agent_id: str, category: str, message: str, **fields) -> None:
    """Emit a structured log line to this agent's subsystem.

    Uses `/usr/bin/logger -p` so it works without any framework imports
    and from any process. On macOS, logger lines are picked up by
    unified logging and queryable via `log stream`.
    """
    payload = {"message": message, **fields} if fields else {"message": message}
    line = json.dumps(payload, ensure_ascii=False, default=str)
    tag = f"{SUBSYSTEM_PREFIX}.{agent_id}:{category}"
    subprocess.run(
        ["/usr/bin/logger", "-t", tag, "--", line],
        check=False, capture_output=True, timeout=2,
    )


def subscribe(
    on_message: Callable[[str, str, dict], None],
    agent_id: str = "*",
    category: str = "*",
    follow: bool = True,
) -> "Subscription":
    """Subscribe to the bus. `on_message(agent_id, category, payload)` fires per line.

    Returns a Subscription you can .stop().
    """
    predicate = f'eventMessage CONTAINS "{SUBSYSTEM_PREFIX}."'
    cmd = ["log", "stream", "--style", "ndjson", "--predicate", predicate]
    if not follow:
        cmd.append("--last")
        cmd.append("5m")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1
    )

    sub = Subscription(proc)

    def _pump():
        assert proc.stdout is not None
        for raw in proc.stdout:
            if sub._stopped:
                break
            try:
                line = json.loads(raw)
            except json.JSONDecodeError:
                continue
            msg = line.get("eventMessage", "")
            if SUBSYSTEM_PREFIX not in msg:
                continue
            # Best-effort parse: `<subsystem>.<agent>:<category>: <json>`
            try:
                head, body = msg.split(": ", 1)
                tag = head.rsplit(" ", 1)[-1]
                subsys_agent, cat = tag.split(":", 1)
                agent = subsys_agent.removeprefix(SUBSYSTEM_PREFIX + ".")
                payload = json.loads(body)
            except (ValueError, json.JSONDecodeError):
                continue
            if agent_id != "*" and agent != agent_id:
                continue
            if category != "*" and cat != category:
                continue
            try:
                on_message(agent, cat, payload)
            except Exception:
                pass

    threading.Thread(target=_pump, daemon=True).start()
    return sub


class Subscription:
    def __init__(self, proc: subprocess.Popen):
        self._proc = proc
        self._stopped = False

    def stop(self) -> None:
        self._stopped = True
        try:
            self._proc.terminate()
        except Exception:
            pass


def query(agent_id: str = "*", category: str = "*", last: str = "5m") -> list[dict]:
    """One-shot query: return matching messages from the last `last` window."""
    predicate = f'eventMessage CONTAINS "{SUBSYSTEM_PREFIX}."'
    try:
        out = subprocess.check_output(
            ["log", "show", "--style", "ndjson", "--last", last, "--predicate", predicate],
            text=True, timeout=20,
        )
    except subprocess.SubprocessError:
        return []
    results = []
    for raw in out.splitlines():
        try:
            line = json.loads(raw)
        except json.JSONDecodeError:
            continue
        msg = line.get("eventMessage", "")
        if SUBSYSTEM_PREFIX not in msg:
            continue
        try:
            head, body = msg.split(": ", 1)
            tag = head.rsplit(" ", 1)[-1]
            subsys_agent, cat = tag.split(":", 1)
            agent = subsys_agent.removeprefix(SUBSYSTEM_PREFIX + ".")
            payload = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            continue
        if agent_id != "*" and agent != agent_id:
            continue
        if category != "*" and cat != category:
            continue
        results.append({"agent": agent, "category": cat, "payload": payload, "ts": line.get("timestamp")})
    return results
