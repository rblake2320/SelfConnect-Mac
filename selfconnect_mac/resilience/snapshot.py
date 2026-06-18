"""
APFS clones for atomic mesh checkpoints.

On APFS volumes, `cp -c source dest` creates a copy-on-write clone in
constant time (microseconds), regardless of file size. The clone shares
storage with the original until either side is modified.

This makes per-step mesh checkpointing essentially free:

  before each mesh step:
      checkpoint("workspace", "step_42")

  if step fails:
      rollback("workspace", "step_42")

Win32 has no equivalent at the filesystem level (Volume Shadow Copy is
admin-only and heavyweight). HFS+ doesn't support this either — APFS is
required (default since 10.13 / 2017).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


SNAPSHOT_DIR_NAME = ".selfconnect_snapshots"


def is_apfs(path: str | os.PathLike) -> bool:
    """True if `path` is on an APFS volume."""
    target = Path(path).resolve()
    while not target.exists() and target != target.parent:
        target = target.parent
    try:
        out = subprocess.check_output(["/sbin/mount"], text=True, timeout=5)
    except subprocess.SubprocessError:
        return False

    best_mount = ""
    best_type = ""
    for line in out.splitlines():
        if " on " not in line or " (" not in line:
            continue
        _, rest = line.split(" on ", 1)
        mount_point, options = rest.split(" (", 1)
        try:
            mount_path = Path(mount_point).resolve()
            target.relative_to(mount_path)
        except (OSError, ValueError):
            continue
        if len(str(mount_path)) > len(best_mount):
            best_mount = str(mount_path)
            best_type = options.split(",", 1)[0].strip().lower()
    return best_type == "apfs"


def checkpoint(workspace: str | os.PathLike, label: str) -> Path:
    """Clone `workspace` directory tree into a labeled snapshot.

    On APFS this is O(1) and storage-free until divergence. Off APFS
    this falls back to a regular recursive copy.
    """
    src = Path(workspace).resolve()
    snap_root = src.parent / SNAPSHOT_DIR_NAME
    snap_root.mkdir(parents=True, exist_ok=True)
    dest = snap_root / label
    if dest.exists():
        shutil.rmtree(dest)

    if is_apfs(src):
        # `cp -c` does a clonefile(2) on APFS — constant-time.
        subprocess.run(["/bin/cp", "-cR", str(src), str(dest)], check=True, timeout=60)
    else:
        shutil.copytree(src, dest)

    return dest


def rollback(workspace: str | os.PathLike, label: str) -> bool:
    """Restore the workspace to the contents of a labeled snapshot."""
    src = Path(workspace).resolve()
    snap = src.parent / SNAPSHOT_DIR_NAME / label
    if not snap.exists():
        return False

    # Atomic-ish: rename current out, rename snapshot in, delete old.
    bak = src.parent / f"{src.name}.rollback_bak"
    if bak.exists():
        shutil.rmtree(bak)
    src.rename(bak)

    if is_apfs(snap):
        subprocess.run(["/bin/cp", "-cR", str(snap), str(src)], check=True, timeout=60)
    else:
        shutil.copytree(snap, src)

    shutil.rmtree(bak)
    return True


def list_checkpoints(workspace: str | os.PathLike) -> list[str]:
    src = Path(workspace).resolve()
    snap_root = src.parent / SNAPSHOT_DIR_NAME
    if not snap_root.exists():
        return []
    return sorted(p.name for p in snap_root.iterdir() if p.is_dir())


def prune_checkpoints(workspace: str | os.PathLike, keep: int = 10) -> int:
    """Keep the most recent `keep` checkpoints (by mtime); delete the rest.

    Returns the count deleted. On APFS, pruning is the only way to
    actually reclaim space — clones stay cheap until modified.
    """
    src = Path(workspace).resolve()
    snap_root = src.parent / SNAPSHOT_DIR_NAME
    if not snap_root.exists():
        return 0
    snaps = sorted(snap_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    to_delete = snaps[keep:]
    for p in to_delete:
        shutil.rmtree(p, ignore_errors=True)
    return len(to_delete)
