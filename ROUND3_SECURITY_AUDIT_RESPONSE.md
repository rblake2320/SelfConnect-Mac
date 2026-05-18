# Round 3 Security Audit Response

Date reviewed: 2026-05-18  
External report: `/Users/ronaldblake/Downloads/SelfConnect-Mac_ Round 3 Test Report & Security Audit.md`  
Commit reviewed by report: `88439dd Address Mac external review findings`

## Summary

The Round 3 report verified the Mac compatibility fixes from Round 2 and identified
additional runtime and security issues. The concrete issues below were checked against
the current repository and patched where valid.

## Fixed Findings

### 1. LLaVA fallback `NameError`

Report finding:

```text
_detect_via_llava() uses config.DETECTION_VL_CONFIDENCE but does not import config.
```

Status: verified and fixed.

Change:

```text
vision_server/services/detection_service.py
```

`_detect_via_llava()` now imports:

```python
from vision_server import config
```

This keeps the existing `config.DETECTION_VL_CONFIDENCE` reference valid during
vision fallback.

### 2. Destructive shell denylist regex

Report finding:

```text
r'\b:>\s*/' does not match :> /path because : is not a word character.
```

Status: verified and fixed.

Change:

```text
local_agent.py
```

Pattern changed from:

```python
r'\b:>\s*/'
```

to:

```python
r':>\s*/'
```

This closes the specific bypass identified by the report.

### 3. MD5 state hash

Report finding:

```text
WatchdogLoop._classify() uses hashlib.md5 for text state hashing.
```

Status: verified and fixed.

Change:

```text
self_connect.py
```

The hash was changed from MD5 to SHA-256:

```python
_hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
```

The hash is not used for secrets, but SHA-256 avoids scanner failures and removes
unnecessary cryptographic weakness.

### 4. Checkpoint durability before migration threshold

Report finding:

```text
MigrationCoordinator.tick() only writes a checkpoint when migration threshold is reached.
```

Status: accepted as a durability improvement and fixed.

Change:

```text
self_connect.py
```

`MigrationCoordinator.tick()` now writes a checkpoint on every below-threshold tick
before returning `False`. The checkpoint metadata includes:

```text
context_current
context_capacity
context_ratio
```

Migration still only spawns a successor and broadcasts `PEER_MIGRATING` when the
configured threshold is reached.

## Finding Clarified

### `Checkpoint.written_at` is a Unix epoch float

Report finding:

```text
Checkpoint.written_at is a float, but consumers might expect ISO 8601.
```

Status: clarified, not changed.

The current schema intentionally stores `written_at` as a Unix epoch float using
`time.time()`. This is already documented in the dataclass field description:

```text
written_at: Unix timestamp when the checkpoint was written
```

Changing it to an ISO string would break existing checkpoint readers. If ISO time
is needed later, it should be added as a new metadata field rather than changing
the type of `written_at`.

## Remaining Security Notes

The report also flags broad exception swallowing and historical Windows utility
scripts that pass strings through `cmd.exe`. Those are valid hardening targets,
but they are broader cleanup work and not part of the verified Mac Terminal mesh
path. The Mac proof path uses:

```text
self_connect.py
mac_mesh_control.py
spawn_codex_mac_peer.py
runbooks/mac_codex_peer_bootstrap.md
```

Future production hardening should separate historical Windows scripts into a
clearly marked legacy area and narrow broad `except Exception: pass` blocks in
core modules.

## Verification

After applying the fixes:

```bash
.venv/bin/python -m py_compile self_connect.py local_agent.py vision_server/services/detection_service.py
.venv/bin/python -m pytest -q
```

Observed result:

```text
151 passed, 9 skipped
```
