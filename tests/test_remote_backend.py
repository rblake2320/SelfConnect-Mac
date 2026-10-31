"""RemoteBackend — SSH-wrapped tmux / Terminal.app on a second Mac (no network in tests)."""
from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from selfconnect_mac.backends import remote
from selfconnect_mac.backends.base import Target
from selfconnect_mac.backends.remote import RemoteBackend
from selfconnect_mac.backends.selector import find_backend_for_target


def _ok(stdout: str = ""):
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def test_kind_validation():
    with pytest.raises(ValueError):
        RemoteBackend("mini", kind="iterm2")


def test_tmux_enumerate_wraps_host():
    out = "%1\tmesh:0.0\t123\tzsh\n%2\tmesh:1.0\t456\tclaude\n"
    with mock.patch.object(subprocess, "run", return_value=_ok(out)) as run:
        targets = RemoteBackend("mini", "tmux").enumerate()
    assert [t.ident for t in targets] == ["mini/mesh:0.0", "mini/mesh:1.0"]
    assert targets[1].title == "claude" and targets[1].pid == 456
    cmd = run.call_args[0][0]
    assert cmd[0] == "ssh" and "mini" in cmd and "tmux list-panes" in cmd[-1]


def test_tmux_send_literal_then_enter():
    with mock.patch.object(subprocess, "run", return_value=_ok()) as run:
        RemoteBackend("mini", "tmux").send(Target("mini/mesh:0.0", "x"), "hi there")
    cmds = [c[0][0][-1] for c in run.call_args_list]
    assert cmds[0].endswith("tmux send-keys -t mesh:0.0 -l 'hi there'")
    assert cmds[1].endswith("tmux send-keys -t mesh:0.0 Enter")
    assert cmds[0].startswith("PATH=")  # non-interactive ssh needs Homebrew tmux on PATH


def test_tmux_send_no_submit():
    with mock.patch.object(subprocess, "run", return_value=_ok()) as run:
        RemoteBackend("mini", "tmux").send(Target("mesh:0.0", "x"), "partial", submit=False)
    assert len(run.call_args_list) == 1


def test_terminal_enumerate_parses_window_ids():
    out = "1436\t/dev/ttys014\ttrue\ttrue\tclaude — 80×24\n673\t/dev/ttys011\tfalse\tfalse\tzsh\n"
    with mock.patch.object(subprocess, "run", return_value=_ok(out)) as run:
        targets = RemoteBackend("mini", "terminal").enumerate()
    assert targets[0].ident == "mini/1436" and targets[0].extra["frontmost"] is True
    assert targets[1].extra["busy"] is False and targets[1].extra["tty"] == "/dev/ttys011"
    assert "osascript" in run.call_args[0][0][-1]


def test_terminal_send_uses_do_script_by_window_id():
    with mock.patch.object(subprocess, "run", return_value=_ok()) as run:
        RemoteBackend("mini", "terminal").send(Target("mini/1436", "x"), 'say "hi"')
    cmd = run.call_args[0][0][-1]
    assert "do script" in cmd and "in window id 1436" in cmd and '\\"hi\\"' in cmd
    assert "System Events" not in cmd  # no keystroke path, no Accessibility needed


def test_terminal_read_by_window_id():
    with mock.patch.object(subprocess, "run", return_value=_ok("a" * 5000)):
        text = RemoteBackend("mini", "terminal").read(Target("1436", "x"), tail=100)
    assert len(text) == 100


def test_ssh_failure_raises():
    bad = subprocess.CompletedProcess(args=[], returncode=255, stdout="", stderr="Host key verification failed.")
    with mock.patch.object(subprocess, "run", return_value=bad):
        with pytest.raises(RuntimeError, match="Host key"):
            RemoteBackend("mini", "tmux").read(Target("mini/mesh:0.0", "x"))


def test_selector_routes_host_prefixed_idents():
    b = find_backend_for_target("mini/mesh:0.0")
    assert isinstance(b, RemoteBackend) and b.kind == "tmux" and b.host == "mini"
    b = find_backend_for_target("mini/1436")
    assert isinstance(b, RemoteBackend) and b.kind == "terminal"


def test_osa_builder_quotes_each_line():
    cmd = remote._osa('tell application "Terminal"\n  return 1\nend tell')
    assert cmd.startswith("osascript -e ") and cmd.count(" -e ") == 3


def test_terminal_send_without_submit_times_out_cleanly():
    def _hang(*a, **k):
        raise subprocess.TimeoutExpired(cmd="ssh", timeout=1)
    with mock.patch.object(subprocess, "run", side_effect=_hang):
        with pytest.raises(RuntimeError, match="submit=True"):
            RemoteBackend("mini", "terminal").send(Target("mini/1436", "x"), "partial", submit=False)
