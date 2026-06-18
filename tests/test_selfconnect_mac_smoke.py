"""Import smoke tests for the v2 selfconnect_mac package.

Every module must import without hard-failing even when optional Mac
frameworks aren't installed. Backends report themselves unavailable; they
don't crash the import.
"""

from __future__ import annotations

import sys

import pytest


pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_top_level_imports():
    import selfconnect_mac

    assert selfconnect_mac.__version__.startswith("2.")
    assert callable(selfconnect_mac.get_backend)
    assert callable(selfconnect_mac.list_backends)


def test_backend_modules_import():
    from selfconnect_mac.backends import applescript, base, cgevent, iterm2, selector, tmux

    for mod in (applescript, base, cgevent, iterm2, selector, tmux):
        assert hasattr(mod, "__name__")


def test_capture_module_imports():
    from selfconnect_mac import capture, windows

    assert callable(capture.capture_cg_window)
    assert callable(windows.list_cg_windows)
    assert callable(windows.running_applications)


def test_bus_modules_import():
    from selfconnect_mac.bus import fsevents_inbox, log_bus, pasteboard

    assert callable(log_bus.emit)
    assert callable(log_bus.subscribe)
    assert callable(fsevents_inbox.watch_inbox)
    assert hasattr(pasteboard, "PrivateChannel")


def test_mesh_modules_import():
    from selfconnect_mac.mesh import multipeer

    assert callable(multipeer.publish_service)
    assert callable(multipeer.browse_services)


def test_approval_modules_import():
    from selfconnect_mac.approval import audio, notifications, touch_id

    assert callable(audio.say)
    assert callable(audio.chime)
    assert callable(notifications.notify)
    assert callable(touch_id.require)


def test_resilience_module_imports():
    from selfconnect_mac.resilience import snapshot

    assert callable(snapshot.checkpoint)
    assert callable(snapshot.rollback)
    assert callable(snapshot.list_checkpoints)


def test_cli_help_works():
    from selfconnect_mac import cli

    parser = cli.build_parser()
    # --help shouldn't crash; capture SystemExit.
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--help"])
    assert exc.value.code == 0


def test_backend_selector_lists_known_backends():
    from selfconnect_mac.backends.selector import available_names

    names = available_names()
    # On any platform, this returns a (possibly empty) list of strings
    # from {iterm2, tmux, cgevent, applescript}. No exceptions.
    assert isinstance(names, list)
    for n in names:
        assert n in {"iterm2", "tmux", "cgevent", "applescript"}


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only")
def test_at_least_one_backend_available_on_mac():
    """On a real Mac, at least the applescript backend should be reachable
    because self_connect.py is part of this repo."""
    from selfconnect_mac.backends.selector import available_names

    # We don't enforce a specific backend — the user may not have iTerm2
    # installed — but `applescript` should always be available on Mac
    # since it just needs the existing self_connect module.
    names = available_names()
    assert names, "Expected at least one backend available on macOS"
