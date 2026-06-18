# Codex 1 package verification

**Time:** 2026-06-17 20:03 CDT
**Repository HEAD before this report:** `81f5911ea6fbc7a1f1092952c37b42db4ff0a0d5`

## Build verification

Command:

```bash
.venv/bin/python -m build
```

Result:

```text
Successfully built selfconnect_mac-0.10.0.tar.gz and selfconnect_mac-0.10.0-py3-none-any.whl
```

The build used isolated sdist-to-wheel mode, so it verified packaging from the
source distribution rather than only the editable checkout.

## Clean wheel entry-point verification

Installed the generated wheel into a fresh temporary virtual environment and
ran:

```bash
sc-mac --help
```

Result: `sc-mac` started successfully and exposed the v2 command set:

```text
backends, list, read, send, ask, submit, watch, spawn, capture, bus-emit,
bus-tail, notify, say, approve, checkpoint, rollback, peer-publish, peer-browse
```

Package API smoke:

```text
version 2.0.0-dev
exports 3
```

## Clean wheel `[mac]` extra verification

Installed the generated wheel with optional macOS dependencies into a second
fresh temporary virtual environment:

```bash
pip install 'dist/selfconnect_mac-0.10.0-py3-none-any.whl[mac]'
sc-mac backends
```

Observed backend status:

```text
[unavailable]  iterm2
[AVAILABLE]    tmux
[AVAILABLE]    cgevent
[AVAILABLE]    applescript
```

Interpretation:

- `tmux`, `cgevent`, and `applescript` are available from the built wheel with
  `[mac]` extras.
- `iterm2` is unavailable only because iTerm2 is not running/enabled in this
  verification environment.
- Packaging and console-script publication are verified independently of the
  editable repo install.
