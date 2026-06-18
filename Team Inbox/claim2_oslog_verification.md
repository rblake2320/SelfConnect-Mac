# Claim 2 live-fire verification — os_log / unified logging bus

**Agent:** Codex 1
**Time:** 2026-06-17

## Result

PASS.

## Commanded behavior

- Emitted five events through `selfconnect_mac.bus.log_bus.emit()`.
- Queried them back through `selfconnect_mac.bus.log_bus.query()`.
- Verified all five event payloads returned from macOS unified logging.

## Observed output

```text
agent CODEX1-OSLOG-27557
rows 5
messages ['event-0', 'event-1', 'event-2', 'event-3', 'event-4']
```

## Implementation correction made during test

`logger(1)` writes into unified logging, but `log show` does not preserve `logger -t` as a queryable subsystem/category on this machine. The implementation now embeds reserved JSON fields:

```json
{"sc_bus":"selfconnect","sc_agent":"...","sc_category":"...","message":"..."}
```

`query()` and `subscribe()` filter on those fields. The claim draft was updated to match this evidence.

— Codex 1
