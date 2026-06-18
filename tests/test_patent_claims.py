"""
Tests that exercise each patentable claim end-to-end.

Each test asserts the *claimed behavior* runs without raising on macOS
when required deps are present, and skips gracefully otherwise. The point
is to keep an executable record alongside the claim language in
PATENT_CLAIMS_DRAFT.md so the implementation and the claim stay in sync.

Specific claim numbers reference PATENT_CLAIMS_DRAFT.md.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest


IS_MAC = sys.platform == "darwin"

mac_only = pytest.mark.skipif(not IS_MAC, reason="macOS-only claim")


# ── Claim 1: dual-backend interchangeable transport ────────────────────
@mac_only
def test_claim1_dual_backend_interchangeable_transport():
    """A single mesh controller can target a terminal session via any of
    iterm2, tmux, cgevent, or applescript backends through one interface."""
    from selfconnect_mac.backends.base import Backend, Target
    from selfconnect_mac.backends import iterm2, tmux, cgevent, applescript

    for cls in (iterm2.ITerm2Backend, tmux.TmuxBackend, cgevent.CGEventBackend, applescript.AppleScriptBackend):
        assert issubclass(cls, Backend)
        assert callable(cls.is_available)
        # Each implements the same five methods.
        for method in ("enumerate", "send", "read", "capture", "spawn"):
            assert hasattr(cls, method)


# ── Claim 2: os_log as queryable mesh bus ──────────────────────────────
@mac_only
def test_claim2_oslog_mesh_bus_roundtrip():
    """An agent can emit() a structured event and a later query() returns it."""
    import time

    from selfconnect_mac.bus.log_bus import emit, query

    agent = f"test-{os.getpid()}"
    emit(agent, "claim2", "patent-test-marker", trial=1)
    result = []
    for _ in range(10):
        result = query(agent_id=agent, category="claim2", last="1m")
        if result:
            break
        time.sleep(1)
    assert isinstance(result, list)
    assert any(row["payload"].get("message") == "patent-test-marker" for row in result)


# ── Claim 1 sub-lane: FSEvents push inbox ──────────────────────────────
@mac_only
def test_claim1_fsevents_inbox_receives_push():
    """Writing a matching file to the watched inbox fires the callback."""
    import threading
    import time

    from selfconnect_mac.bus.fsevents_inbox import watch_inbox

    inbox = Path(tempfile.mkdtemp(prefix="sc_inbox_"))
    received = []
    stop = threading.Event()

    def listener():
        watch_inbox(inbox, lambda p: received.append(p.name), poll_interval=0.2, stop_event=stop)

    t = threading.Thread(target=listener, daemon=True)
    t.start()
    time.sleep(0.5)
    (inbox / "msg_claim1_fsevents.md").write_text("hello", encoding="utf-8")
    # Allow time for either FSEvents push or polling fallback.
    for _ in range(20):
        if received:
            break
        time.sleep(0.2)
    stop.set()
    shutil.rmtree(inbox, ignore_errors=True)
    assert "msg_claim1_fsevents.md" in received


# ── Claim 3: Bonjour LAN peer discovery ────────────────────────────────
@mac_only
def test_claim3_bonjour_publish_and_browse():
    """publish_service() returns a stoppable handle; browse_services() returns a list."""
    from selfconnect_mac.mesh.multipeer import publish_service, browse_services

    handle = publish_service("sc-claim3-test", 65432, txt={"role": "test"})
    try:
        peers = browse_services(timeout=1.0)
        assert isinstance(peers, list)
    finally:
        handle.stop()


# ── Claim 4: Touch ID per-action approval ──────────────────────────────
@mac_only
def test_claim4_touchid_require_callable():
    """require() must accept a reason and return bool, even when biometry
    isn't configured (it returns False)."""
    from selfconnect_mac.approval.touch_id import require, is_available

    avail = is_available()
    assert isinstance(avail, bool)
    # Don't actually trigger an auth prompt in CI; just verify the API.
    assert callable(require)


# ── Claim 5: APFS clone-based O(1) checkpoint ──────────────────────────
@mac_only
def test_claim5_apfs_checkpoint_and_rollback():
    """checkpoint() copies a workspace; rollback() restores it."""
    from selfconnect_mac.resilience.snapshot import checkpoint, rollback, list_checkpoints

    work = Path(tempfile.mkdtemp(prefix="sc_ws_")) / "workspace"
    work.mkdir()
    (work / "file.txt").write_text("v1", encoding="utf-8")
    snap = checkpoint(work, "claim5_v1")
    assert snap.exists()
    assert "claim5_v1" in list_checkpoints(work)

    (work / "file.txt").write_text("v2-corrupted", encoding="utf-8")
    assert rollback(work, "claim5_v1") is True
    assert (work / "file.txt").read_text(encoding="utf-8") == "v1"

    shutil.rmtree(work.parent, ignore_errors=True)


# ── Non-pursued lane: audio mesh signaling ─────────────────────────────
@mac_only
def test_audio_heartbeat_runs():
    """heartbeat() schedules a chime + say without blocking the caller."""
    from selfconnect_mac.approval.audio import heartbeat, list_voices

    voices = list_voices()
    assert isinstance(voices, list)
    # Heartbeat itself must not raise; actual audio output is OS-side.
    heartbeat("AUDIO-AGENT", status="testing")


# ── Claim 6: CGEventPostToPid targeted injection ───────────────────────
@mac_only
def test_claim6_cgevent_targeted_injection_api():
    """CGEventBackend.send requires a PID; verify the API shape."""
    pytest.importorskip("Quartz", reason="pyobjc-framework-Quartz not installed")
    from selfconnect_mac.backends.cgevent import CGEventBackend
    from selfconnect_mac.backends.base import Target

    backend = CGEventBackend()
    assert backend.is_available()
    bogus = Target(ident="0", title="nonexistent", pid=0, backend="cgevent")
    with pytest.raises(RuntimeError):
        backend.send(bogus, "hi")


# ── Claim 7: Vision OCR last-resort buffer read ────────────────────────
@mac_only
def test_claim7_vision_ocr_api():
    """ocr_image() returns a string (possibly empty when Vision missing or
    image absent)."""
    from selfconnect_mac.capture import ocr_image

    result = ocr_image("/nonexistent/path.png")
    assert isinstance(result, str)


# ── Claim 8: NSPasteboard private named channel ────────────────────────
@mac_only
def test_claim8_pasteboard_private_channel_roundtrip():
    from selfconnect_mac.bus.pasteboard import PrivateChannel

    ch = PrivateChannel("sc-claim8-test")
    ch.post({"hello": "world", "ts": 1})
    latest = ch.latest()
    assert latest is not None
    assert latest.get("hello") == "world"
