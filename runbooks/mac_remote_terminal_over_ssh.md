# Runbook: drive a Claude Code session on a second Mac over SSH

**Verified:** 2026-10-31, MacBook Pro (macOS 15.8.2) → M4 Mac mini (macOS 27.0.1), key-only SSH, same user on both.
**Backend:** `selfconnect_mac/backends/remote.py` (`sc-mac --host <alias>`).

## Commands

```bash
sc-mac --host mini list                              # tmux panes on the mini
sc-mac --host mini --backend terminal list           # Terminal.app windows (id, tty, busy, frontmost, title)
sc-mac --host mini --backend terminal read 1436      # last 4000 chars of window id 1436
sc-mac --host mini --backend terminal send 1436 --submit "status?"   # do script: text + Enter, no focus change
# NB: `send` WITHOUT --submit on a Terminal target uses System Events keystrokes: slow, TCC-gated, and it
#     brings the window to the front. For Claude Code prompts always pass --submit.
sc-mac --host mini send mesh:0.0 "echo hi"           # tmux pane
```

## What was proved

1. `osascript` over SSH can drive **Terminal.app** on macOS 27 with **no TCC prompt** when the SSH user
   owns the GUI session: `do script "..." in window id N` and `contents of selected tab of window id N`.
   No Accessibility permission is needed for this path. `System Events keystroke` *does* need it and is
   not used for `submit=True`.
2. Address windows by **window id**, never "front window". The front window changed under us within
   minutes (16 windows open on the mini; two other Claude sessions and a Codex session were live).
3. `do script` into a Claude Code window delivers the text as a prompt and submits it. The reply shows
   up in `contents of selected tab` a few seconds later.
4. tmux targets are the better choice when the remote session was started over SSH; Terminal targets
   are the only choice for sessions the user opened in GUI Terminal windows.

## Always verify the message was *sent*

A message that lands in the prompt box but is not submitted looks done from here and blocks the other
session until a human presses Enter. After every `send --submit`, read the window back ~5 s later:
the text must appear in the transcript (after a `⏺`/`⎿` marker), not after the `❯` prompt line.
If it is still in the box, press Enter with `sc-mac --host mini --backend terminal submit 1436`
(`do script ""` = a bare Return; verified on 2026-10-31).

**Busy sessions swallow Enter.** If the target Claude Code session is mid-turn (a spinner line such as
`✶ Working… (esc to interrupt)` is visible above the prompt), the injected text stays in the box and
neither `do script` nor a bare CR submits it. Wait until the spinner is gone (poll `read` every ~10 s),
then run `submit` again and re-read. Verified 2026-10-31: an ACK sat in the box for ~2 min until the
mini finished its turn, then submitted.

## Gotchas

- Inside `tell application "Terminal"`, the AppleScript word `tab` is Terminal's *tab class*, not the
  tab character. Use `character id 9`. Symptom: output literally contains the word `tab`.
- Use mDNS names (`RONALDs-Mac-mini.local`) or an ssh-config alias; DHCP hostnames (`Mac-69.lan`,
  `Mac-610.lan`) change on every reboot.
- Before the reverse direction works, the *other* Mac must have this Mac's host key in
  `known_hosts` and a key in `authorized_keys`; the symptom is `Host key verification failed`.
- `submit=False` on a Terminal target falls back to keystrokes and raises if Accessibility is denied
  for `sshd-keygen-wrapper`.
