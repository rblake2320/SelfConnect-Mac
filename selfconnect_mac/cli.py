"""
sc-mac — unified CLI with --backend selector.

Compatible with mac_mesh_control.py command names (list/read/send/ask/submit/
watch) and adds: spawn, capture, backends, bus-emit, bus-tail, notify, say,
checkpoint, rollback, peer-publish, peer-browse, approve.

Auto-selects the best available backend if --backend is not given.

Usage:
    python -m selfconnect_mac.cli backends
    python -m selfconnect_mac.cli --backend tmux list
    python -m selfconnect_mac.cli send AGENT-A "hello" --submit
    python -m selfconnect_mac.cli spawn AGENT-B /path/to/repo
    python -m selfconnect_mac.cli bus-tail --agent AGENT-A
    python -m selfconnect_mac.cli notify "Mesh" "All agents online"
    python -m selfconnect_mac.cli approve "Push to main"
    python -m selfconnect_mac.cli checkpoint /path/to/ws step_1
"""

from __future__ import annotations

import argparse
import sys
import time


def _resolve_target(backend, ident: str):
    """Try ident as a literal identifier first; if not found, treat as title fragment."""
    targets = backend.enumerate()
    for t in targets:
        if t.ident == ident:
            return t
    needle = ident.lower()
    matches = [t for t in targets if needle in t.title.lower()]
    if not matches:
        raise SystemExit(f"No target matched {ident!r}. Try `sc-mac list`.")
    if len(matches) > 1:
        sys.stderr.write(f"Multiple matches for {ident!r}; using first: {matches[0].title}\n")
    return matches[0]


def cmd_backends(_args, _backend) -> int:
    from . import list_backends

    available = set(list_backends())
    for name in ["iterm2", "tmux", "cgevent", "applescript"]:
        flag = "[AVAILABLE]" if name in available else "[unavailable]"
        print(f"  {flag}  {name}")
    return 0


def cmd_list(_args, backend) -> int:
    for t in backend.enumerate():
        print(f"  {t.backend:10s}  {t.ident:40s}  pid={t.pid:6d}  {t.title}")
    return 0


def cmd_read(args, backend) -> int:
    target = _resolve_target(backend, args.target)
    print(backend.read(target, tail=args.tail))
    return 0


def cmd_send(args, backend) -> int:
    target = _resolve_target(backend, args.target)
    backend.send(target, args.text, submit=args.submit)
    return 0


def cmd_ask(args, backend) -> int:
    """send + submit + brief read."""
    target = _resolve_target(backend, args.target)
    backend.send(target, args.text, submit=True)
    time.sleep(args.wait)
    print(backend.read(target, tail=args.tail))
    return 0


def cmd_submit(args, backend) -> int:
    target = _resolve_target(backend, args.target)
    backend.send(target, "", submit=True)
    return 0


def cmd_watch(args, backend) -> int:
    targets = [_resolve_target(backend, ident) for ident in args.targets]
    last: dict[str, str] = {}
    cycle = 0
    while args.cycles == 0 or cycle < args.cycles:
        for t in targets:
            text = backend.read(t, tail=args.tail)
            if text != last.get(t.ident, ""):
                print(f"\n--- {t.title} ({t.ident}) ---\n{text}")
                last[t.ident] = text
        cycle += 1
        time.sleep(args.interval)
    return 0


def cmd_spawn(args, backend) -> int:
    target = backend.spawn(args.title, args.cwd, command=args.command)
    print(f"Spawned: {target.title}  ident={target.ident}  backend={target.backend}")
    return 0


def cmd_capture(args, backend) -> int:
    target = _resolve_target(backend, args.target)
    out = backend.capture(target, args.out)
    print(out or "(capture returned nothing)")
    return 0


def cmd_bus_emit(args, _backend) -> int:
    from .bus.log_bus import emit

    emit(args.agent, args.category, args.message)
    return 0


def cmd_bus_tail(args, _backend) -> int:
    from .bus.log_bus import subscribe

    sub = subscribe(
        lambda a, c, p: print(f"[{a}/{c}] {p.get('message','')}"),
        agent_id=args.agent or "*",
        category=args.category or "*",
    )
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sub.stop()
    return 0


def cmd_notify(args, _backend) -> int:
    from .approval.notifications import critical, notify

    (critical if args.critical else notify)(args.title, args.message)
    return 0


def cmd_say(args, _backend) -> int:
    from .approval.audio import say

    say(args.text, voice=args.voice, async_=False)
    return 0


def cmd_approve(args, _backend) -> int:
    from .approval.touch_id import require

    ok = require(args.reason, allow_password=not args.biometric_only, timeout=args.timeout)
    print("approved" if ok else "denied")
    return 0 if ok else 1


def cmd_checkpoint(args, _backend) -> int:
    from .resilience.snapshot import checkpoint

    dest = checkpoint(args.workspace, args.label)
    print(str(dest))
    return 0


def cmd_rollback(args, _backend) -> int:
    from .resilience.snapshot import rollback

    ok = rollback(args.workspace, args.label)
    return 0 if ok else 1


def cmd_peer_publish(args, _backend) -> int:
    from .mesh.multipeer import publish_service

    h = publish_service(args.name, args.port, txt={"role": args.role} if args.role else None)
    print(f"Publishing {args.name!r} on port {args.port}. Ctrl-C to stop.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        h.stop()
    return 0


def cmd_peer_browse(args, _backend) -> int:
    from .mesh.multipeer import browse_services

    for peer in browse_services(timeout=args.timeout):
        print(f"  {peer.name:30s}  {peer.host}:{peer.port}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sc-mac")
    p.add_argument("--backend", choices=["iterm2", "tmux", "cgevent", "applescript"])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backends", help="show which backends are available")
    sub.add_parser("list", help="list addressable terminal targets")

    r = sub.add_parser("read", help="read last N chars of a target's buffer")
    r.add_argument("target")
    r.add_argument("--tail", type=int, default=4000)

    s = sub.add_parser("send", help="inject text into a target")
    s.add_argument("target")
    s.add_argument("text")
    s.add_argument("--submit", action="store_true")

    a = sub.add_parser("ask", help="send + submit + read result")
    a.add_argument("target")
    a.add_argument("text")
    a.add_argument("--wait", type=float, default=4.0)
    a.add_argument("--tail", type=int, default=2000)

    sb = sub.add_parser("submit", help="press Enter in a target")
    sb.add_argument("target")

    w = sub.add_parser("watch", help="tail multiple targets")
    w.add_argument("targets", nargs="+")
    w.add_argument("--interval", type=float, default=2.0)
    w.add_argument("--cycles", type=int, default=0)
    w.add_argument("--tail", type=int, default=2000)

    sp = sub.add_parser("spawn", help="create a new agent terminal")
    sp.add_argument("title")
    sp.add_argument("cwd")
    sp.add_argument("--command", default="claude")

    cap = sub.add_parser("capture", help="screenshot a target's window")
    cap.add_argument("target")
    cap.add_argument("out")

    be = sub.add_parser("bus-emit", help="emit a structured event to the os_log mesh bus")
    be.add_argument("agent")
    be.add_argument("category")
    be.add_argument("message")

    bt = sub.add_parser("bus-tail", help="tail the os_log mesh bus")
    bt.add_argument("--agent")
    bt.add_argument("--category")

    no = sub.add_parser("notify", help="show a system notification")
    no.add_argument("title")
    no.add_argument("message")
    no.add_argument("--critical", action="store_true")

    sy = sub.add_parser("say", help="speak text aloud")
    sy.add_argument("text")
    sy.add_argument("--voice", default="Daniel")

    ap = sub.add_parser("approve", help="biometric approval gate")
    ap.add_argument("reason")
    ap.add_argument("--biometric-only", action="store_true")
    ap.add_argument("--timeout", type=float, default=30.0)

    ch = sub.add_parser("checkpoint", help="APFS-clone a workspace into a labeled snapshot")
    ch.add_argument("workspace")
    ch.add_argument("label")

    rb = sub.add_parser("rollback", help="restore a workspace to a labeled snapshot")
    rb.add_argument("workspace")
    rb.add_argument("label")

    pp = sub.add_parser("peer-publish", help="advertise this agent on the LAN via Bonjour")
    pp.add_argument("name")
    pp.add_argument("port", type=int)
    pp.add_argument("--role")

    pb = sub.add_parser("peer-browse", help="discover other agents on the LAN")
    pb.add_argument("--timeout", type=float, default=3.0)

    return p


DISPATCH = {
    "backends": cmd_backends,
    "list": cmd_list,
    "read": cmd_read,
    "send": cmd_send,
    "ask": cmd_ask,
    "submit": cmd_submit,
    "watch": cmd_watch,
    "spawn": cmd_spawn,
    "capture": cmd_capture,
    "bus-emit": cmd_bus_emit,
    "bus-tail": cmd_bus_tail,
    "notify": cmd_notify,
    "say": cmd_say,
    "approve": cmd_approve,
    "checkpoint": cmd_checkpoint,
    "rollback": cmd_rollback,
    "peer-publish": cmd_peer_publish,
    "peer-browse": cmd_peer_browse,
}

# Commands that don't need a terminal backend.
NO_BACKEND = {
    "backends", "bus-emit", "bus-tail", "notify", "say", "approve",
    "checkpoint", "rollback", "peer-publish", "peer-browse",
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    backend = None
    if args.cmd not in NO_BACKEND:
        from . import BackendUnavailable, get_backend

        try:
            backend = get_backend(args.backend)
        except BackendUnavailable as e:
            sys.stderr.write(f"error: {e}\n")
            return 2
    return DISPATCH[args.cmd](args, backend)


if __name__ == "__main__":
    raise SystemExit(main())
