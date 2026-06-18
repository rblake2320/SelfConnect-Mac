# tmux backend — live-fire verification

**Owner:** Claude 1
**Time:** 2026-06-17
**Status:** ✅ PASS — full spawn/send/read roundtrip against a fresh tmux session.

## Setup

```bash
brew install tmux        # installed cleanly
```

## Procedure

```python
from selfconnect_mac.backends.tmux import TmuxBackend
b = TmuxBackend()
t = b.spawn('AGENT-TEST', '/tmp', command='bash -lc "echo SELFCONNECT_TMUX_READY; exec bash -i"')
b.send(t, 'echo hello-from-claude-1', submit=True)
time.sleep(1.0)
text = b.read(t, tail=2000)
```

## Observed output (verbatim)

```
SELFCONNECT_TMUX_READY

The default interactive shell is now zsh.
To update your account to use zsh, please run `chsh -s /bin/zsh`.
For more details, please visit https://support.apple.com/kb/HT208050.
bash-3.2$ echo hello-from-claude-1
hello-from-claude-1
bash-3.2$
```

`[result] TMUX-ROUNDTRIP-PASS: True`

## What this verifies

- `TmuxBackend.is_available()` returns True when the `tmux` binary is on PATH.
- `TmuxBackend.spawn(title, cwd, command)` creates a detached named session with the given working directory, running the given command.
- `TmuxBackend.send(target, text, submit=True)` delivers the text via `tmux send-keys -t <pane> -l <text>` followed by `tmux send-keys -t <pane> Enter`. Both the spawn-marker and the injected echo are present in the captured buffer.
- `TmuxBackend.read(target, tail=N)` returns the last N chars of `tmux capture-pane -p -S -3000`.

## Implementing files

- `selfconnect_mac/backends/tmux.py`

## Notes

- Test ran headless (no GUI tmux). This confirms the headless-mesh lane works as designed — a key differentiator vs the AppleScript / iTerm2 paths.
- Session was cleaned up with `tmux kill-session -t AGENT-TEST` at the end of the test.

— Claude 1
