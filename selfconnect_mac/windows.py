"""
Window enumeration via the *actual* Mac equivalents of Win32 EnumWindows.

  - CGWindowListCopyWindowInfo (Quartz) — the on-screen window list with
    PID, bounds, layer, owner, title. No Accessibility prompt required to
    *enumerate*; only required if you later read window content via AX.

  - AXUIElementCreateApplication(pid) + kAXWindowsAttribute — the Mac
    analog of UIA: walks every window of an app with the full element
    tree. Requires Accessibility permission.

  - NSWorkspace.runningApplications — every running app with PID,
    bundleID, frontmost flag. Useful for resolving the right PID to AX into.

Each function degrades to [] if its framework isn't installed.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import Quartz  # type: ignore

    _HAS_QUARTZ = True
except ImportError:
    _HAS_QUARTZ = False

try:
    from AppKit import NSWorkspace  # pyobjc-framework-Cocoa  # type: ignore

    _HAS_APPKIT = True
except ImportError:
    _HAS_APPKIT = False

try:
    import atomacos  # type: ignore

    _HAS_AX = True
except ImportError:
    _HAS_AX = False


@dataclass(frozen=True)
class CGWindow:
    """A row from CGWindowListCopyWindowInfo."""

    window_id: int
    pid: int
    owner: str
    title: str
    bounds: tuple[int, int, int, int]
    layer: int
    on_screen: bool


def list_cg_windows(on_screen_only: bool = True) -> list[CGWindow]:
    """The direct Mac equivalent of Win32 EnumWindows."""
    if not _HAS_QUARTZ:
        return []
    opts = Quartz.kCGWindowListOptionAll
    if on_screen_only:
        opts = Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements
    infos = Quartz.CGWindowListCopyWindowInfo(opts, Quartz.kCGNullWindowID)
    out: list[CGWindow] = []
    for info in infos:
        b = info.get("kCGWindowBounds", {})
        bounds = (
            int(b.get("X", 0)),
            int(b.get("Y", 0)),
            int(b.get("Width", 0)),
            int(b.get("Height", 0)),
        )
        out.append(
            CGWindow(
                window_id=int(info.get("kCGWindowNumber", 0)),
                pid=int(info.get("kCGWindowOwnerPID", 0)),
                owner=str(info.get("kCGWindowOwnerName", "")),
                title=str(info.get("kCGWindowName") or ""),
                bounds=bounds,
                layer=int(info.get("kCGWindowLayer", 0)),
                on_screen=bool(info.get("kCGWindowIsOnscreen", False)),
            )
        )
    return out


def list_terminal_windows() -> list[CGWindow]:
    """All visible windows belonging to known terminal emulators."""
    terminal_owners = {"Terminal", "iTerm2", "iTerm", "Warp", "WezTerm", "kitty", "Ghostty", "Alacritty"}
    return [w for w in list_cg_windows() if w.owner in terminal_owners]


def list_running_apps() -> list[tuple[int, str, str]]:
    """Return (pid, bundle_id, localized_name) for every running app."""
    if not _HAS_APPKIT:
        return []
    ws = NSWorkspace.sharedWorkspace()
    apps = ws.runningApplications()
    out = []
    for app in apps:
        try:
            out.append((int(app.processIdentifier()), str(app.bundleIdentifier() or ""), str(app.localizedName() or "")))
        except Exception:
            continue
    return out


def running_applications() -> list[tuple[int, str, str]]:
    """Alias using Apple's NSWorkspace.runningApplications terminology."""
    return list_running_apps()


def ax_window_titles(pid: int) -> list[str]:
    """Use AXUIElement to read titles of every window owned by `pid`.

    Mac equivalent of UIAutomation's GetCurrentName at the window level.
    Requires Accessibility permission for the *caller* process.
    """
    if not _HAS_AX:
        return []
    try:
        app = atomacos.getAppRefByPid(pid)
        titles = []
        for w in app.windows():
            try:
                titles.append(str(w.AXTitle or ""))
            except Exception:
                titles.append("")
        return titles
    except Exception:
        return []


def find_terminal_by_title(needle: str) -> CGWindow | None:
    needle_l = needle.lower()
    for w in list_terminal_windows():
        if needle_l in w.title.lower():
            return w
    return None
