# SelfConnect Mac — Permissions Guide (TCC Edge Cases)

macOS gates the APIs SelfConnect uses behind the Transparency, Consent, and
Control (TCC) framework. Each capability requires a specific permission
bucket; missing grants produce specific failure modes documented below
along with the `tccutil` command to recover.

This guide is for SelfConnect operators. If you are end-user packaging the
software for distribution, additional Hardened-Runtime entitlements are
required — see the "Distribution" section at the bottom.

---

## Quick-reference table

| Capability / module | TCC bucket | Failure mode when missing | Recovery |
|---|---|---|---|
| `selfconnect_mac.backends.applescript` (AppleScript keystroke + `contents of window`) | Accessibility + Automation (Terminal) | AppleScript "System Events got an error: not allowed assistive access" (-1719) | System Settings → Privacy & Security → Accessibility → enable Terminal; → Automation → enable "Terminal" under your Python; `tccutil reset Accessibility com.apple.Terminal` to reprompt |
| `selfconnect_mac.backends.cgevent` (`CGEventPostToPid`) | Accessibility | Events posted but silently dropped — no exception, just no input delivered | System Settings → Privacy & Security → Accessibility → enable the Python interpreter (e.g. `/opt/homebrew/bin/python3`); `tccutil reset Accessibility` to clear all and reprompt |
| `selfconnect_mac.backends.iterm2` (iTerm2 Python API) | None at runtime (iTerm2 must have "Enable Python API" toggled in Prefs → General → Magic) | `iterm2.RPCConnectionError: cannot connect` | iTerm2 → Settings → General → Magic → Enable Python API; restart iTerm2 |
| `selfconnect_mac.backends.tmux` | None | tmux binary missing or no server started | `brew install tmux` |
| `selfconnect_mac.windows.list_cg_windows` (CGWindowListCopyWindowInfo) | None to enumerate; **Screen Recording** to read `kCGWindowName` of other apps' windows on macOS 14+ | Window names appear empty (`""`) for other apps' windows; bounds + PIDs still work | System Settings → Privacy & Security → Screen Recording → enable Python interpreter; `tccutil reset ScreenCapture` |
| `selfconnect_mac.windows.ax_window_titles` (AXUIElement) | Accessibility | `AXErrorAPIDisabled` or empty results | Accessibility for the Python interpreter as above |
| `selfconnect_mac.capture.capture_cg_window` (`CGWindowListCreateImage` / `screencapture -l`) | **Screen Recording** | Capture returns black/blank image, or `screencapture` warns "no permission" | System Settings → Privacy & Security → Screen Recording → enable Python interpreter or Terminal; `tccutil reset ScreenCapture` |
| `selfconnect_mac.capture.ocr_image` (Vision framework) | None | — | — |
| `selfconnect_mac.bus.log_bus` (`os_log` + `log stream`) | None | `log stream` may fail under sandbox; otherwise works | Run unsandboxed |
| `selfconnect_mac.bus.fsevents_inbox` (FSEvents) | None for paths within user's home; **Full Disk Access** for paths outside | Events silently never deliver | System Settings → Privacy & Security → Full Disk Access → enable Python; `tccutil reset SystemPolicyAllFiles` |
| `selfconnect_mac.bus.pasteboard` (NSPasteboard private channels) | None | — | — |
| `selfconnect_mac.mesh.multipeer` (Bonjour publish/browse) | **Local Network** (on macOS 15+) | `dns-sd` runs but no peers discovered; advertisement silently dropped | System Settings → Privacy & Security → Local Network → enable Python; `tccutil reset NSLocalNetworkUsageDescription` (rarely actually needed pre-15) |
| `selfconnect_mac.mesh.multipeer` (MultipeerConnectivity sessions) | **Local Network** + **Bluetooth** | MCSession fails to invite peers | System Settings → Privacy & Security → Local Network + Bluetooth; `tccutil reset Bluetooth` |
| `selfconnect_mac.approval.touch_id` (LocalAuthentication) | **None** at the TCC level — biometric prompt is system-modal | `LAErrorBiometryNotAvailable` if Touch ID not configured | Configure Touch ID in System Settings → Touch ID & Password; falls back to device password automatically |
| `selfconnect_mac.approval.audio` (`say`, `afplay`) | None | — | — |
| `selfconnect_mac.approval.notifications` (`display notification`, `terminal-notifier`) | None for AppleScript path; **Notification** permission per-app | Banner doesn't show | System Settings → Notifications → enable for Script Editor (AppleScript) or terminal-notifier |
| `selfconnect_mac.resilience.snapshot` (APFS `cp -c`) | None | If volume is not APFS, falls back to recursive copy | Check `diskutil info /` shows `Apple_APFS` |

---

## TCC failure modes in detail

### Silent drop on Accessibility

`CGEventPostToPid` does **not raise** when Accessibility is not granted. The
posted event is simply not delivered to the target process. This is the
most common "why doesn't my mesh work" symptom. The diagnostic test:

```bash
python3 -c "
import Quartz, os, time
src = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
ev = Quartz.CGEventCreateKeyboardEvent(src, 0, True)
Quartz.CGEventKeyboardSetUnicodeString(ev, 1, 'A')
Quartz.CGEventPostToPid(os.getpid(), ev)  # post to self
print('posted')
"
```

If Accessibility is granted, no exception. If revoked, no exception either —
the silent-drop behavior is the entire failure mode.

To detect it from code, test against your own PID and a known-good text
target before claiming readiness:

```python
from selfconnect_mac.approval.touch_id import is_available  # reuse the LA pattern
# or actually: query AXIsProcessTrusted before any send.
```

### Screen Recording vs `kCGWindowName` on macOS 14+

`CGWindowListCopyWindowInfo` still returns rows for every window without
Screen Recording, but starting in macOS 14.0 the `kCGWindowName` field is
redacted (returned as `""`) for windows you don't own unless Screen
Recording is granted. Window IDs, bounds, and PIDs are still readable.

Behavioral test:

```python
from selfconnect_mac.windows import list_cg_windows
windows = list_cg_windows()
titles = sum(1 for w in windows if w.title and w.owner != "this-process")
print(f"{titles} other-app window titles visible — 0 means Screen Recording denied")
```

### Local Network on macOS 15+

Bonjour publishing and browsing now require Local Network grant. The first
call to `dns-sd -B` will trigger a system prompt; subsequent calls after
deny will silently return no results.

### Automation (Apple Events authorization)

`tell application "Terminal"` requires *both* Accessibility for the host
(so System Events can run scripting) *and* Automation for the host to
target the specific application. The Automation grant is per (host,
target) pair: granting "Python may automate Terminal" is distinct from
"Python may automate iTerm2". macOS lists them under
System Settings → Privacy & Security → Automation.

Reset: `tccutil reset AppleEvents` clears all Automation grants. Use
`tccutil reset AppleEvents com.apple.Terminal` to reset only Terminal's.

---

## First-run setup checklist

For an operator setting up SelfConnect Mac v2 on a fresh machine:

1. **Install dependencies.**
   ```bash
   pip install -e '.[mac,test]'      # mac extras + pytest
   brew install tmux                  # optional but recommended
   # iTerm2: download, then enable Python API in Settings → General → Magic
   ```

2. **Grant Accessibility** to the Python interpreter being used.
   System Settings → Privacy & Security → Accessibility → `+` →
   `/opt/homebrew/bin/python3` (or your venv's `python`). Toggle on.

3. **Grant Screen Recording** to the same Python interpreter.
   System Settings → Privacy & Security → Screen Recording.

4. **(macOS 15+)** Run a test Bonjour publish so the Local Network prompt
   appears. Approve.

5. **Verify**:
   ```bash
   python3 -m selfconnect_mac.cli backends     # which are available
   python3 -m selfconnect_mac.cli list          # should show your terminals
   python3 -m selfconnect_mac.cli say "ready"   # audible test
   ```

6. **Optional**: configure Touch ID for biometric approval (System Settings
   → Touch ID & Password). `python3 -m selfconnect_mac.cli approve "test"`
   should prompt.

---

## Resetting all TCC grants for a clean re-prompt

If permissions get into a broken state and you want every prompt to come
back fresh:

```bash
sudo tccutil reset Accessibility
sudo tccutil reset AppleEvents
sudo tccutil reset ScreenCapture
sudo tccutil reset SystemPolicyAllFiles
sudo tccutil reset Microphone
```

The next time SelfConnect attempts each capability, macOS will prompt the
user fresh. There is no way to programmatically *grant* TCC — only to
reset and re-prompt.

---

## Distribution (Hardened Runtime entitlements)

When packaging SelfConnect Mac as a signed `.app` for distribution rather
than running it as scripts, include these entitlements:

```xml
<!-- entitlements.plist -->
<key>com.apple.security.automation.apple-events</key>           <true/>
<key>com.apple.security.device.audio-input</key>                <false/>
<key>com.apple.security.network.client</key>                    <true/>
<key>com.apple.security.network.server</key>                    <true/>
<key>com.apple.security.files.user-selected.read-write</key>    <true/>
<!-- Screen Recording is granted at runtime via TCC; no entitlement -->
<!-- Accessibility is granted at runtime via TCC; no entitlement -->
```

For `LocalAuthentication` and Touch ID, no entitlement is needed; the
biometric prompt is system-modal.

For MultipeerConnectivity sessions in a sandboxed app, add:

```xml
<key>com.apple.security.network.multipeer</key>                 <true/>
```

(Note: this key is not yet officially documented for macOS apps but the
analog of the iOS Multipeer-Connectivity entitlement key is used in
practice.)

---

## Where to look when something doesn't work

| Symptom | First place to check |
|---|---|
| `send()` runs but nothing arrives in the target terminal | Accessibility for the Python interpreter |
| `read()` returns empty | Accessibility (for AX path) + try iterm2/tmux backend |
| `capture()` saves a black image | Screen Recording |
| `peer-browse` finds nothing | Local Network (15+); also check Wi-Fi is on the same network |
| `approve` hangs | Touch ID configured? Test `bioutil -rc` |
| FSEvents inbox callback never fires | Full Disk Access if path is outside `~/`; otherwise check FSEvents framework installed |
| `dns-sd` "MoreComing" but no `Add` | Firewall blocking multicast 5353 |
| `log stream` shows no events | Subsystem string typo, or `logger` not in `/usr/bin` |

See `PATENT_PROCESS_RECORD.md` for the v1 verification log of these same
permission checks performed live on 2026-05-13 → 2026-05-18.
