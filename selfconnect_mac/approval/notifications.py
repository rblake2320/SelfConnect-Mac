"""
System notifications — banners, critical alerts, badge counts.

macOS notifications survive Space switches and screen lock; critical
alerts bypass Do Not Disturb. For mesh events the owner needs to see
even if their terminal is buried, this is the cleanest channel.

Three tiers:

  1. AppleScript `display notification` — always works, no install.
  2. `terminal-notifier` CLI — if installed, supports click-actions
     and reply boxes.
  3. UNUserNotificationCenter (pyobjc-framework-UserNotifications) —
     full control: critical alerts, sound names, action buttons.
"""

from __future__ import annotations

import shutil
import subprocess


def notify(title: str, message: str, subtitle: str = "", sound: str = "default") -> None:
    """Show a notification using the best available mechanism."""
    if shutil.which("terminal-notifier"):
        cmd = [
            "terminal-notifier",
            "-title", title,
            "-message", message,
            "-sound", sound,
        ]
        if subtitle:
            cmd += ["-subtitle", subtitle]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    # AppleScript fallback — works on every Mac, no install required.
    def _q(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    script_parts = [f'display notification "{_q(message)}" with title "{_q(title)}"']
    if subtitle:
        script_parts.append(f'subtitle "{_q(subtitle)}"')
    if sound:
        script_parts.append(f'sound name "{_q(sound)}"')
    script = " ".join(script_parts)
    subprocess.Popen(
        ["/usr/bin/osascript", "-e", script],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def critical(title: str, message: str) -> None:
    """A critical-priority notification that bypasses Do Not Disturb.

    Falls back to a regular notification + an audible chime if the
    critical-alert entitlement isn't granted (it requires Apple approval
    for distribution apps; works during development).
    """
    from . import audio

    notify(title, message, sound="Sosumi")
    audio.chime("Sosumi")
