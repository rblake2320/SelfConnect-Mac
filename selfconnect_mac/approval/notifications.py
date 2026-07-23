"""
System notifications — banners for mesh events.

macOS notifications survive Space switches and screen lock. For mesh
events the owner needs to see even if their terminal is buried, this is
the cleanest channel.

Two implemented tiers:

  1. AppleScript `display notification` — always works, no install.
  2. `terminal-notifier` CLI — if installed, supports click-actions
     and reply boxes.

A third tier — UNUserNotificationCenter (pyobjc-framework-
UserNotifications) with true critical alerts, sound names, and action
buttons — is a v2.1 follow-up. True Do-Not-Disturb bypass requires the
critical-alert entitlement and is intentionally not represented as
implemented or live-fired here.
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
    """A high-urgency notification: regular banner + an audible chime.

    This does NOT bypass Do Not Disturb. True critical alerts require
    UNUserNotificationCenter plus the Apple-granted critical-alert
    entitlement — a v2.1 follow-up. Until then this is a best-effort
    "loud" notification only.
    """
    from . import audio

    notify(title, message, sound="Sosumi")
    audio.chime("Sosumi")
