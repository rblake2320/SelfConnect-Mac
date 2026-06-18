# Claim 5 live-fire verification — APFS checkpoint and rollback

**Agent:** Codex 1
**Time:** 2026-06-17

## Result

PASS.

## Commanded behavior

- Created a temporary workspace with ten approximately 1 MB files.
- Verified the workspace path is on APFS.
- Created an APFS-backed checkpoint.
- Mutated all files.
- Rolled back from the checkpoint.
- Verified every file was restored.
- Pruned the checkpoint.

## Observed output

```text
is_apfs True
snapshot_exists True
labels ['stress1']
rollback_ok True
restored True
pruned 1
```

## Prior correction already in repo

Earlier testing showed `diskutil info /path` prints `Could not find disk` for normal paths on this machine. The implementation now parses `/sbin/mount` and matches the deepest mount point, which made this live-fire run clean.

— Codex 1
