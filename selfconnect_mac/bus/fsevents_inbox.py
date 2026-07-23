"""
FSEvents-driven inbox — push notifications instead of file polling.

The legacy "Team Inbox" pattern polls a directory every 15 seconds. On
macOS, FSEvents delivers a kernel-level notification when files change.
That converts a busy poll loop into an event-driven listener with sub-
second latency and no wasted CPU.

There is no Win32 equivalent of comparable latency without ReadDirectory-
ChangesW boilerplate.

Requires pyobjc-framework-FSEvents; falls back to a polling stub if
unavailable so the import never hard-fails.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path

try:
    from CoreFoundation import (  # type: ignore
        CFRunLoopGetCurrent,
        CFRunLoopRun,
        CFRunLoopRunInMode,
        kCFRunLoopDefaultMode,
    )
    from FSEvents import (  # type: ignore
        FSEventStreamCreate,
        FSEventStreamInvalidate,
        FSEventStreamRelease,
        FSEventStreamScheduleWithRunLoop,
        FSEventStreamStart,
        FSEventStreamStop,
        kFSEventStreamCreateFlagFileEvents,
        kFSEventStreamEventIdSinceNow,
    )

    _HAS_FSEVENTS = True
except ImportError:
    _HAS_FSEVENTS = False


def watch_inbox(
    inbox_dir: str | os.PathLike,
    on_message: Callable[[Path], None],
    file_glob: str = "msg_*.md",
    poll_interval: float = 1.0,
    stop_event=None,
) -> None:
    """Watch `inbox_dir`; call `on_message(path)` for each new matching file.

    Blocks the calling thread. If FSEvents is available, uses it (push,
    sub-second). Otherwise falls back to polling at `poll_interval`.
    Pass a threading.Event as `stop_event` to terminate cleanly.
    """
    inbox = Path(inbox_dir)
    inbox.mkdir(parents=True, exist_ok=True)
    seen = {p.name for p in inbox.glob(file_glob)}

    def _scan_new() -> None:
        for p in inbox.glob(file_glob):
            if p.name not in seen:
                seen.add(p.name)
                try:
                    on_message(p)
                except Exception:
                    pass

    if not _HAS_FSEVENTS:
        # Polling fallback.
        while stop_event is None or not stop_event.is_set():
            _scan_new()
            time.sleep(poll_interval)
        return

    def _event_path(raw_path) -> Path:
        if isinstance(raw_path, bytes):
            raw_path = os.fsdecode(raw_path)
        return Path(raw_path)

    def _callback(_stream, _client_info, num_events, paths, _flags, _ids):
        for i in range(num_events):
            d = _event_path(paths[i])
            if d == inbox or d.parent == inbox:
                _scan_new()

    stream = FSEventStreamCreate(
        None,
        _callback,
        None,
        [str(inbox.resolve())],
        kFSEventStreamEventIdSinceNow,
        1.0,  # latency
        kFSEventStreamCreateFlagFileEvents,
    )
    runloop = CFRunLoopGetCurrent()
    FSEventStreamScheduleWithRunLoop(stream, runloop, kCFRunLoopDefaultMode)
    FSEventStreamStart(stream)
    try:
        if stop_event is None:
            CFRunLoopRun()
        else:
            while not stop_event.is_set():
                CFRunLoopRunInMode(kCFRunLoopDefaultMode, poll_interval, True)
                _scan_new()
    finally:
        FSEventStreamStop(stream)
        FSEventStreamInvalidate(stream)
        FSEventStreamRelease(stream)
