"""
Per-window capture — the Mac equivalents of Win32 PrintWindow.

  Tier 1: CGWindowListCreateImage(rect, listOption, windowID, imageOption)
          Direct twin of PrintWindow. One window by ID, even if occluded.

  Tier 2: `screencapture -l <windowID>` CLI fallback — same result, no
          PyObjC dep required.

  Tier 3: ScreenCaptureKit (SCStream + SCContentFilter) for macOS 12.3+.
          CGWindowListCreateImage is being deprecated in favor of this.
          We don't wire SCStream here yet — placeholder note for v2.1.

  Tier 4: Vision framework OCR over a captured image — extracts text
          even when AXUIElement and iTerm2 readback both fail.
"""

from __future__ import annotations

import os
import shutil
import subprocess

try:
    import Quartz  # type: ignore

    _HAS_QUARTZ = True
except ImportError:
    _HAS_QUARTZ = False


def capture_cg_window(window_id: int, out_path: str) -> str | None:
    """Capture a single window by CGWindowID. Returns out_path or None."""
    # Prefer the CLI form — same result, no PyObjC needed, always available.
    if shutil.which("screencapture"):
        try:
            subprocess.run(
                ["screencapture", "-l", str(window_id), "-x", "-o", out_path],
                check=True, capture_output=True, timeout=10,
            )
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                return out_path
        except subprocess.SubprocessError:
            pass

    # PyObjC fallback (and the future home for SCStream).
    if _HAS_QUARTZ:
        try:
            img = Quartz.CGWindowListCreateImage(
                Quartz.CGRectNull,
                Quartz.kCGWindowListOptionIncludingWindow,
                int(window_id),
                Quartz.kCGWindowImageBoundsIgnoreFraming | Quartz.kCGWindowImageNominalResolution,
            )
            if img is None:
                return None
            url = Quartz.CFURLCreateWithFileSystemPath(None, out_path, Quartz.kCFURLPOSIXPathStyle, False)
            dest = Quartz.CGImageDestinationCreateWithURL(url, "public.png", 1, None)
            if dest is None:
                return None
            Quartz.CGImageDestinationAddImage(dest, img, None)
            if Quartz.CGImageDestinationFinalize(dest):
                return out_path
        except Exception:
            return None

    return None


def capture_iterm2_session(session_uuid: str, out_path: str) -> str | None:
    """Best-effort capture of an iTerm2 window.

    `session_uuid` is accepted for API stability but is NOT used for
    disambiguation yet: without the iTerm2 Python API connected there is
    no reliable uuid -> CGWindowID mapping, so this captures the
    frontmost iTerm2 window. Per-session precision requires the iterm2
    backend (`backends/iterm2.py`) — use its capture path when available.
    """
    from .windows import list_cg_windows

    candidates = [w for w in list_cg_windows() if w.owner == "iTerm2"]
    # Without the iTerm2 API present we can't disambiguate cleanly; take
    # the frontmost iTerm2 window as the best-effort answer.
    if not candidates:
        return None
    target = candidates[0]
    return capture_cg_window(target.window_id, out_path)


def ocr_image(image_path: str) -> str:
    """Run macOS Vision framework OCR on `image_path`. Returns extracted text.

    Last-resort buffer-read fallback when every API-level path is blocked.
    Requires pyobjc-framework-Vision.
    """
    try:
        import Vision  # type: ignore
        from Cocoa import NSURL  # type: ignore
    except ImportError:
        return ""

    url = NSURL.fileURLWithPath_(image_path)
    handler = Vision.VNImageRequestHandler.alloc().initWithURL_options_(url, None)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
    request.setUsesLanguageCorrection_(False)
    success, _err = handler.performRequests_error_([request], None)
    if not success:
        return ""
    lines = []
    for obs in (request.results() or []):
        top = obs.topCandidates_(1)
        if top:
            lines.append(str(top[0].string()))
    return "\n".join(lines)
