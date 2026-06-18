"""
Bonjour discovery + MultipeerConnectivity hook — room-scale peer discovery.

macOS uniquely supports peer discovery over Bonjour and peer-to-peer
links over Wi-Fi + Bluetooth + AWDL with zero networking configuration.
This module implements the Bonjour publish/browse layer now and exposes
the MultipeerConnectivity import hook for the v2.1 MCSession upgrade.

This is a primitive that Win32 has no equivalent of. Lancelot's UAB
runs on `localhost:3100` and has no peer-to-peer story.

This module provides:

  1. Bonjour service publishing/browsing for LAN discovery
     (cross-platform — Macs can also find Windows/Linux peers this way).

  2. An import-gated hook for MultipeerConnectivity (Apple-only, no routing).

Bonjour requires pyobjc-framework-Foundation. MCSession is bridged via
pyobjc-framework-MultipeerConnectivity, but full delegate wiring is a
v2.1 follow-up and is intentionally not represented as live-fired in the
verification record.
"""

from __future__ import annotations

import socket
from dataclasses import dataclass


SERVICE_TYPE = "_selfconnect._tcp."
SERVICE_DOMAIN = "local."


@dataclass(frozen=True)
class Peer:
    name: str
    host: str
    port: int
    txt: dict[str, str]


def publish_service(name: str, port: int, txt: dict[str, str] | None = None) -> "ServiceHandle":
    """Advertise this agent on the LAN via Bonjour/mDNS.

    Other Macs (and any host with mDNS) will see this service and can
    open a connection on (host, port). `txt` carries small key/value
    metadata such as agent role, capabilities, supported codecs.
    """
    try:
        from Foundation import NSNetService, NSRunLoop  # type: ignore
    except ImportError:
        # Pure-Python fallback via `dns-sd -R` CLI if pyobjc-Foundation
        # isn't available.
        return _publish_via_cli(name, port, txt or {})

    svc = NSNetService.alloc().initWithDomain_type_name_port_(SERVICE_DOMAIN, SERVICE_TYPE, name, port)
    svc.scheduleInRunLoop_forMode_(NSRunLoop.currentRunLoop(), "kCFRunLoopDefaultMode")
    if txt:
        from Foundation import NSData  # type: ignore
        # TXT records are typed; serialize naively.
        encoded = NSNetService.dataFromTXTRecordDictionary_(
            {k: NSData.dataWithBytes_length_(v.encode("utf-8"), len(v.encode("utf-8"))) for k, v in txt.items()}
        )
        svc.setTXTRecordData_(encoded)
    svc.publish()
    return ServiceHandle(svc)


def browse_services(timeout: float = 3.0) -> list[Peer]:
    """Discover peers on the LAN. One-shot scan with `timeout` seconds."""
    import subprocess

    # `dns-sd -B` for browse, then `dns-sd -L` for each found name to
    # resolve hostname+port. This avoids a long async PyObjC dance for
    # what is conceptually a sync operation.
    try:
        browse = subprocess.run(
            ["/usr/bin/dns-sd", "-t", str(int(timeout)), "-B", SERVICE_TYPE, SERVICE_DOMAIN],
            capture_output=True, text=True, timeout=timeout + 1,
        )
    except subprocess.SubprocessError:
        return []
    names: list[str] = []
    for line in browse.stdout.splitlines():
        if "Add" in line and SERVICE_TYPE.rstrip(".") in line:
            parts = line.split()
            if parts:
                names.append(parts[-1])
    peers: list[Peer] = []
    for name in names:
        try:
            resolve = subprocess.run(
                ["/usr/bin/dns-sd", "-t", "1", "-L", name, SERVICE_TYPE, SERVICE_DOMAIN],
                capture_output=True, text=True, timeout=2,
            )
        except subprocess.SubprocessError:
            continue
        host = ""
        port = 0
        for line in resolve.stdout.splitlines():
            if "can be reached at" in line:
                # "... can be reached at hostname.local.:1234 (interface 5)"
                tail = line.split("can be reached at", 1)[1].strip()
                hostport = tail.split()[0].rstrip(".")
                if ":" in hostport:
                    host, p = hostport.rsplit(":", 1)
                    try:
                        port = int(p)
                    except ValueError:
                        port = 0
                break
        if host and port:
            peers.append(Peer(name=name, host=host, port=port, txt={}))
    return peers


def _publish_via_cli(name: str, port: int, txt: dict[str, str]) -> "ServiceHandle":
    import subprocess

    cmd = ["/usr/bin/dns-sd", "-R", name, SERVICE_TYPE, SERVICE_DOMAIN, str(port)]
    for k, v in (txt or {}).items():
        cmd.append(f"{k}={v}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ServiceHandle(proc)


class ServiceHandle:
    def __init__(self, inner):
        self._inner = inner

    def stop(self) -> None:
        # NSNetService.stop() or Popen.terminate() — both have the method.
        try:
            self._inner.stop()
        except Exception:
            try:
                self._inner.terminate()
            except Exception:
                pass


def local_host_for_advertisement() -> str:
    """Best-effort local hostname/IP suitable for a peer to connect to."""
    try:
        return socket.gethostname()
    except OSError:
        return "localhost"


# ── MultipeerConnectivity skeleton ─────────────────────────────────────
#
# Full MCSession setup requires a delegate object in Objective-C; PyObjC
# can do it but the code is bulky. The recommended v2 wiring is:
#
#   1. Use Bonjour above for cross-platform peer discovery on the LAN.
#   2. When two macOS peers find each other AND both have AWDL enabled,
#      upgrade the transport to MultipeerConnectivity for higher-throughput
#      direct radio link without router.
#
# Hook point for the v2.1 follow-up:
try:
    import MultipeerConnectivity  # type: ignore  # noqa: F401

    HAS_MULTIPEER = True
except ImportError:
    HAS_MULTIPEER = False
