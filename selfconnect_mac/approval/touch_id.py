"""
Biometric approval via LocalAuthentication framework.

For dangerous mesh actions ("agent wants to `rm -rf build`", "agent wants
to push to main"), gate them behind Touch ID / Face ID. This is stronger
and faster than any rules-engine: the owner physically authenticates per
action, in milliseconds.

Win32 has nothing comparable. Lancelot has no biometric story.

Requires pyobjc-framework-LocalAuthentication. If unavailable or biometry
isn't configured on this Mac, falls back to a CLI password prompt via
`sudo -k -p`.
"""

from __future__ import annotations

import os
import subprocess


try:
    from LocalAuthentication import (  # type: ignore
        LAContext,
        LAPolicyDeviceOwnerAuthenticationWithBiometrics,
        LAPolicyDeviceOwnerAuthentication,
    )

    _HAS_LA = True
except ImportError:
    _HAS_LA = False


def require(reason: str, allow_password: bool = True, timeout: float = 30.0) -> bool:
    """Block until the owner approves via biometric (or password if allowed).

    Returns True on success, False on failure/cancel/timeout.

    Use generously — calls are sub-second when biometry is set up, and
    failure is recoverable. The point is to make destructive actions
    require a physical presence proof.
    """
    if _HAS_LA:
        ctx = LAContext.alloc().init()
        policy = (
            LAPolicyDeviceOwnerAuthentication
            if allow_password
            else LAPolicyDeviceOwnerAuthenticationWithBiometrics
        )
        can, _err = ctx.canEvaluatePolicy_error_(policy, None)
        if can:
            import threading

            done = threading.Event()
            result = {"ok": False}

            def _reply(success, _err):
                result["ok"] = bool(success)
                done.set()

            ctx.evaluatePolicy_localizedReason_reply_(policy, reason, _reply)
            if not done.wait(timeout):
                return False
            return result["ok"]

    # Fallback path: prompt via sudo password if running in a TTY.
    if allow_password and os.isatty(0):
        try:
            proc = subprocess.run(
                ["/usr/bin/sudo", "-k", "-p", f"[selfconnect] {reason}: ", "/usr/bin/true"],
                check=False, timeout=timeout,
            )
            return proc.returncode == 0
        except subprocess.SubprocessError:
            return False
    return False


def is_available() -> bool:
    """True if Touch ID / Face ID is configured and ready."""
    if not _HAS_LA:
        return False
    ctx = LAContext.alloc().init()
    can, _ = ctx.canEvaluatePolicy_error_(
        LAPolicyDeviceOwnerAuthenticationWithBiometrics, None
    )
    return bool(can)
