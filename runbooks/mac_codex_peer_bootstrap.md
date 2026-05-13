# macOS Codex Peer Bootstrap

## Rule

Do not just open a new Codex terminal and assume it can talk. A controller must:

1. Open the new Terminal window.
2. Start Codex in the repo.
3. Submit the first prompt after the Codex TUI is visible.
4. Tell the peer its own Terminal window id and the parent Terminal window id.
5. Give the peer exact SelfConnect read/send instructions.
6. Keep watching both terminals for approval prompts so both agents do not block at once.

## Verified Mac Pattern

SelfConnect on macOS uses real Terminal window ids. In the verified session:

- Parent Codex window: `523`
- Peer Codex window: `606`
- The peer sent back `AGENT_B: ACK`

Read a Terminal window:

```bash
.venv/bin/python -c "from self_connect import get_text_uia; print(get_text_uia(523)[-4000:])"
```

Send to a Terminal window:

```bash
.venv/bin/python -c "from self_connect import WindowTarget, send_string; send_string(WindowTarget(523, 'parent codex', 'macOS.TerminalWindow', 13733, 'Terminal'), 'AGENT_B: hello\r')"
```

## Spawn A New Peer

From the parent Codex terminal:

```bash
.venv/bin/python spawn_codex_mac_peer.py --parent 523 --watch
```

Replace `523` with the current parent Terminal window id. You can list Terminal
windows with:

```bash
.venv/bin/python -c "from self_connect import list_windows; [print(w) for w in list_windows() if w.exe_name == 'Terminal']"
```

## Routine Mesh Control

Use `mac_mesh_control.py` for normal read/send/submit/watch operations. It wraps
SelfConnect plus the required Terminal Return keypress so messages do not sit in
the TUI input box.

List Terminal windows:

```bash
.venv/bin/python mac_mesh_control.py list
```

Read a peer:

```bash
.venv/bin/python mac_mesh_control.py read 606 --tail 5000
.venv/bin/python mac_mesh_control.py read Claude --tail 5000
```

Send and submit a prompt:

```bash
.venv/bin/python mac_mesh_control.py ask 606 "Agent B: send parent a one-line status."
.venv/bin/python mac_mesh_control.py ask Claude "Claude: read parent and report status."
```

Watch several terminals for changing output and approval markers:

```bash
.venv/bin/python mac_mesh_control.py watch 523 606 639
.venv/bin/python mac_mesh_control.py watch codex Claude
```

## Approval Discipline

One agent must always remain the active controller. The controller watches the
peer after every tool request. If the peer is waiting for approval, approve or
deny it before asking the peer to do more work. The peer is instructed to watch
the parent too, but the parent remains responsible for avoiding mutual waits.

Do not make both agents wait for each other to approve the next action.

## Fewer Approval Prompts

The macOS spawn script starts Codex with:

```bash
--ask-for-approval on-request --sandbox workspace-write
```

This keeps the peer inside the workspace sandbox while avoiding approval prompts
for ordinary read/write/test commands. Escalated commands still need approval.
Use stricter settings for unknown repos, and do not use full approval bypass
unless the environment is externally sandboxed and the task is intentionally
non-interactive.
