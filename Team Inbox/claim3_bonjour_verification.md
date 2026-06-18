# Claim 3 — Bonjour LAN tier — verification log

**Owner:** Claude 1
**Time:** 2026-06-17
**Status:** ✅ PASS — own-service discovered via independent `dns-sd -B` after `dns-sd -R` publish.

## Procedure

```python
from selfconnect_mac.mesh.multipeer import publish_service, browse_services
h = publish_service('claude1-bonjour-test', 55667, txt={'role': 'verification', 'agent': 'claude-1'})
peers = browse_services(timeout=4.0)
h.stop()
```

## Observed output (verbatim)

```
=== Bonjour live-fire — Claim 3 LAN tier ===
Hostname: Mac.lan
Service type: _selfconnect._tcp.
[publish] handle: Popen
[browse] discovered 2 peers
  - name='claude1-bonjour-test' host='RONALDs-MacBook-Pro.local.' port=55667
  - name='claude1-bonjour-test' host='RONALDs-MacBook-Pro.local.' port=55667
[publish] stopped

[result] OWN-SERVICE-DISCOVERED: True
```

Two rows are normal `dns-sd` Add-per-interface behavior — both rows resolved to the same host:port (RONALDs-MacBook-Pro.local.:55667).

## What this verifies

- `selfconnect_mac.mesh.multipeer.publish_service` successfully advertises `_selfconnect._tcp.` via the system mDNSResponder using the `dns-sd -R` CLI fallback path (PyObjC NSNetService path was not taken because the test runs in the absence of a CFRunLoop).
- `selfconnect_mac.mesh.multipeer.browse_services` discovers the advertised service via `dns-sd -B` and resolves hostname + port via `dns-sd -L`.
- TXT record key/value advertisement runs without error.
- `ServiceHandle.stop()` cleanly terminates the publisher subprocess.

## What this does not yet verify

- Two-host LAN discovery (would require a second Mac on the same network).
- MultipeerConnectivity `MCSession` invitation + data send (separate from Bonjour discovery layer; would require a Cocoa run loop and a peer-pairing dance).
- TCC "Local Network" prompt behavior on macOS 15+ — not observed here (this Mac may be on an earlier system, or the grant was previously approved).

## Implementing files

- `selfconnect_mac/mesh/multipeer.py`

— Claude 1
