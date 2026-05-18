# SelfConnect Mac Patent / Process Verification Record

Date of Mac verification work: 2026-05-13 through 2026-05-18  
Repository published: <https://github.com/rblake2320/SelfConnect-Mac.git>  
Verified branch: `master`  
Verified commit: `c7380b5 Add macOS compatibility backend`

## Purpose

This record documents the Mac implementation and live verification of SelfConnect:
OS-native inter-terminal communication between independent AI agent terminals without
direct API calls between the agents.

The original SelfConnect implementation targeted Windows using Win32 primitives such as
`PostMessage(WM_CHAR)`, `PrintWindow`, and UI Automation. The Mac implementation preserves
the same operational model while using macOS-native facilities:

- AppleScript / Terminal.app scripting for targeted Terminal window control.
- System Events for foregrounding and submit-key behavior.
- Terminal buffer readback through AppleScript.
- `screencapture` for screenshot capture.
- Optional Python helpers for orchestration.

## What Was Proved

The Mac implementation was not only made importable; it was exercised live on a Mac.
The following were verified:

1. `self_connect.py` imports on macOS without failing on `ctypes.windll`.
2. macOS Terminal windows can be enumerated.
3. Real Terminal window IDs can be resolved.
4. Text can be sent to a specific Terminal window by ID.
5. TUI submission requires a separate Return/Enter action after injection.
6. Terminal contents can be read back programmatically.
7. A second Codex process can be launched in another Terminal window.
8. The second Codex process can receive a bootstrap prompt.
9. The second Codex process can send a message back to the parent Codex terminal.
10. Claude Code can be briefed into the same mesh and can send an ACK back through SelfConnect.
11. A helper command can reduce repeated manual steps for read/send/submit/watch operations.

## Verified Live Windows

During verification, Terminal windows were observed with these roles:

```text
523  parent Codex terminal
606  Agent B Codex terminal
639  Claude Code terminal
599  dedicated shell smoke-test terminal
```

Terminal IDs can change between sessions. The committed helper supports both numeric IDs
and title fragments to reduce brittleness.

## Core Files

These files are central to the Mac process:

- `self_connect.py`
  - Adds macOS compatibility.
  - Avoids import-time Win32 crashes.
  - Implements macOS Terminal discovery, targeted send, readback, screenshot, clipboard,
    and focus helpers.

- `mac_mesh_control.py`
  - CLI wrapper for routine mesh operations.
  - Supports `list`, `read`, `send`, `ask`, `submit`, and `watch`.
  - Accepts either Terminal window IDs or title fragments.

- `spawn_codex_mac_peer.py`
  - Opens a new Terminal window.
  - Starts Codex in the repo.
  - Waits for the TUI.
  - Injects the initial peer briefing.
  - Explicitly submits the prompt.
  - Can watch parent and peer windows for approval markers.

- `runbooks/mac_codex_peer_bootstrap.md`
  - Documents the operational rule: spawn, wait, inject, submit, watch approvals.

- `README.md`
  - Documents Mac status, dependencies, permissions, and verification.

## macOS Permissions Required

macOS requires Accessibility permission for UI scripting and TUI submission.

Observed requirement:

- Approving only Terminal was not enough in all cases.
- `/usr/bin/osascript` also needed Accessibility permission for direct System Events
  window queries.

Relevant settings path:

```text
System Settings -> Privacy & Security -> Accessibility
```

Add or enable:

```text
Terminal.app or the terminal host running the session
/usr/bin/osascript
```

Screen Recording permission may be required for screenshot/capture workflows:

```text
System Settings -> Privacy & Security -> Screen & System Audio Recording
```

## Exact Commands Used Or Equivalent

List current Terminal windows:

```bash
.venv/bin/python mac_mesh_control.py list
```

Read a Terminal/agent window by ID:

```bash
.venv/bin/python mac_mesh_control.py read 606 --tail 7000
```

Read a Terminal/agent window by title fragment:

```bash
.venv/bin/python mac_mesh_control.py read Claude --tail 3000
```

Send text and submit it to a peer:

```bash
.venv/bin/python mac_mesh_control.py ask 606 "Agent B: send parent a one-line status."
```

Watch multiple windows for changing output and approval markers:

```bash
.venv/bin/python mac_mesh_control.py watch 523 606 639
```

Spawn a new Codex peer:

```bash
.venv/bin/python spawn_codex_mac_peer.py --parent 523 --watch
```

## Live Verification Observations

### Smoke Test: Dedicated Shell Window

A Terminal test window was opened and targeted. SelfConnect sent:

```text
echo SELFCONNECT_MAC_TYPE_OK
```

The same window buffer read back:

```text
SELFCONNECT_MAC_TYPE_OK
```

### Back-And-Forth Test: Shell Responder

A tiny stdin responder was started in a dedicated Terminal window. SelfConnect sent:

```text
ping one
ping two
```

The readback showed:

```text
SELFCONNECT_AGENT_REPLY:PING ONE
SELFCONNECT_AGENT_REPLY:PING TWO
```

### Agent B Codex Test

A new Codex peer was opened in Terminal window `606`. The peer was briefed with:

- Its own Terminal window ID.
- The parent Terminal window ID.
- The working repo path.
- Exact SelfConnect read and send commands.
- The instruction to ACK and message the parent.

Agent B replied in its own window:

```text
ACK
```

Agent B then used SelfConnect to send the parent:

```text
AGENT_B: ACK
```

Later, Agent B was asked for a live chat confirmation and replied:

```text
B_CHAT_OK
```

Agent B sent the parent:

```text
AGENT_B_CHAT: B_CHAT_OK
```

### Claude Code Test

A Claude Code terminal was opened in Terminal window `639`. Claude received a mesh briefing
describing:

- Parent Codex: Terminal window `523`.
- Agent B Codex: Terminal window `606`.
- Claude's own role in the Mac SelfConnect mesh.
- Exact read/send commands.
- Approval-discipline rules.

Claude sent back:

```text
CLAUDE: ACK
```

Claude also observed that targeting by title fragment is safer than targeting only by raw
Terminal ID when Terminal tabs/windows shift. That recommendation was incorporated into
`mac_mesh_control.py`.

## Important Failure Modes Observed

### Text Injection Is Not The Same As Submission

Codex and Claude TUIs can show text in the input area without processing it. The controller
must explicitly submit with Return/Enter after injection.

This is why `mac_mesh_control.py ask` performs both:

1. text send,
2. submit.

### Approval Prompts Can Deadlock A Mesh

If two agents are both waiting on approvals, neither can progress. The operational rule is:

- one controller must stay active,
- inspect peer windows after tool requests,
- approve or deny before issuing more work,
- avoid making both agents wait on each other.

### Raw IDs Can Be Brittle

Terminal window IDs were reliable during direct tests, but title-based targeting is useful
when TUI titles change or when there are multiple windows/tabs. The helper now accepts both:

```bash
.venv/bin/python mac_mesh_control.py read 606
.venv/bin/python mac_mesh_control.py read Claude
```

### macOS Accessibility Is Mandatory

Without Accessibility permission, direct AppleScript window queries failed with an error like:

```text
osascript is not allowed assistive access
```

After granting Accessibility permission to `osascript`, System Events could enumerate visible
GUI applications and Terminal windows.

## Approval Reduction

Future Codex peers are spawned with:

```text
--ask-for-approval on-request --sandbox workspace-write
```

This is a practical middle ground:

- routine workspace reads/writes/tests can proceed with fewer prompts,
- the workspace sandbox remains active,
- escalated commands still require approval.

Full approval bypass was deliberately not enabled as the default because it is too broad for
general operation and would weaken the safety story.

## Automated Verification

Before publication, the test suite was run:

```bash
.venv/bin/python -m pytest -q
```

Observed result:

```text
151 passed, 9 skipped
```

The skipped tests are Windows-specific integration tests.

The helper scripts were also syntax-checked:

```bash
.venv/bin/python -m py_compile mac_mesh_control.py spawn_codex_mac_peer.py
```

## Publication Record

The Mac version was pushed to:

```text
https://github.com/rblake2320/SelfConnect-Mac.git
```

The original Windows repo was preserved as upstream:

```text
https://github.com/rblake2320/selfconnect.git
```

Local remotes after publication:

```text
origin    git@github.com:rblake2320/SelfConnect-Mac.git
upstream  https://github.com/rblake2320/selfconnect.git
```

## Reproduction Checklist

On a Mac:

1. Clone the repo:

   ```bash
   git clone https://github.com/rblake2320/SelfConnect-Mac.git
   cd SelfConnect-Mac
   ```

2. Create and install into a virtual environment:

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -e . pytest pytest-asyncio pydantic fastapi httpx
   ```

3. Grant Accessibility permission to:

   ```text
   Terminal.app or the current terminal host
   /usr/bin/osascript
   ```

4. Verify tests:

   ```bash
   .venv/bin/python -m pytest -q
   ```

5. List Terminal windows:

   ```bash
   .venv/bin/python mac_mesh_control.py list
   ```

6. Open a second Codex or Claude terminal.

7. Send a test prompt:

   ```bash
   .venv/bin/python mac_mesh_control.py ask <window-id-or-title> "Reply with SELFCONNECT_MAC_OK."
   ```

8. Read the same window:

   ```bash
   .venv/bin/python mac_mesh_control.py read <window-id-or-title> --tail 5000
   ```

## Summary

The Mac implementation demonstrates the same essential SelfConnect claim as the Windows
implementation: independent terminal-hosted AI agents can be coordinated through OS-native
window/input/readback mechanisms without direct API calls between the agents.

The implementation uses a different platform substrate, but preserves the key process:

```text
discover terminal -> inject instruction -> submit -> read response -> coordinate approvals
```

This record captures the live verification details, the relevant files, observed outputs,
permissions, failure modes, and reproduction steps needed for independent review.
