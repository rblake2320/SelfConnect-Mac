"""
Audio channels — heartbeat, status, voice announcement.

Sometimes the right "is the mesh still alive" signal is an audible chime
in the next room. This module provides three layers:

  1. `say(text, voice)`         — built-in TTS announcement.
  2. `chime(name)`              — short system sound for status.
  3. `voice_loop()`             — STT input (optional, requires Speech).

Win32 has TTS but no equivalent for inter-room mesh signaling that
"just works" without setup. macOS ships voices and system sounds.
"""

from __future__ import annotations

import shutil
import subprocess


SYSTEM_SOUND_DIR = "/System/Library/Sounds"


def say(text: str, voice: str = "Daniel", rate: int = 220, async_: bool = True) -> None:
    """Speak `text` aloud. Returns immediately if async_=True (default)."""
    if not shutil.which("/usr/bin/say"):
        return
    cmd = ["/usr/bin/say", "-v", voice, "-r", str(rate), text]
    if async_:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(cmd, check=False, capture_output=True, timeout=30)


def chime(name: str = "Glass") -> None:
    """Play a system sound by name (e.g. Glass, Funk, Ping, Submarine)."""
    import os

    path = os.path.join(SYSTEM_SOUND_DIR, f"{name}.aiff")
    if not os.path.exists(path):
        return
    subprocess.Popen(
        ["/usr/bin/afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def heartbeat(agent_id: str, status: str = "alive") -> None:
    """Default mesh heartbeat: a soft chime + spoken status."""
    chime("Tink")
    say(f"Agent {agent_id} {status}.", async_=True)


def announce_completion(agent_id: str, task: str) -> None:
    chime("Glass")
    say(f"Agent {agent_id} finished {task}.", async_=True)


def announce_attention(agent_id: str, reason: str) -> None:
    """For approval prompts and human-attention requests."""
    chime("Funk")
    say(f"Agent {agent_id} needs attention. {reason}.", async_=True)


def list_voices() -> list[str]:
    if not shutil.which("/usr/bin/say"):
        return []
    try:
        out = subprocess.check_output(["/usr/bin/say", "-v", "?"], text=True, timeout=5)
    except subprocess.SubprocessError:
        return []
    voices = []
    for line in out.splitlines():
        name = line.split(maxsplit=1)[0] if line else ""
        if name:
            voices.append(name)
    return voices
