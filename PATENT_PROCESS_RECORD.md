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

## v2 Verification Addendum (2026-06-17)

The v2 Mac expansion was verified live on 2026-06-17 by two independent terminal
agents operating in separate Terminal.app windows:

- Codex 1: Terminal window `15219`
- Claude 1: Terminal window `15130`

The agents coordinated through the shared repository working tree and the
`Team Inbox/` filesystem channel. No direct Codex-to-Claude API, MCP, HTTP,
WebSocket, or model-provider channel was used for coordination.

### Published v2 commits

The following commits were pushed to `origin/master` during the v2 verification
round:

- `f525b13` — pluggable macOS backends and native moat lanes.
- `8a54842` — README/doc reconciliation and TCC permissions guide.
- `9287f5f` — fresh-clone verification report.
- `17feb32` — Bonjour, tmux, and CGEvent live-fire reports.
- `09440b3` — `os_log`, FSEvents, and APFS live-fire reports.
- `2649a66` — TCC live-fire sweep and supplemental patent research.
- `640af69` — `sym-swift` prior-art follow-up.
- `9916ebd` — Claim 3 narrowed against current prior art.
- `4c51a82` — Claude 1 ACK that the `9916ebd` narrowing is consistent.

At the time Codex 1's claim-correction commit was pushed:

```text
origin/master = 9916ebdb161a8dbce36236ccdf68fcb3314a9e63
working tree  = clean
```

Claude 1 subsequently acknowledged that correction in commit `4c51a82`.

### v2 test result

The final post-claim-correction validation run used:

```bash
.venv/bin/python -m pytest
```

Observed result:

```text
171 passed, 9 skipped, 4 warnings in 5.89s
```

### Live-fire v2 evidence files

The following `Team Inbox/` records contain the v2 live-fire evidence:

Note: several `Team Inbox/claim*_verification.md` filenames reflect the initial
verification order before the `sym-swift` prior-art correction. The final claim
numbering is the one in `PATENT_CLAIMS_DRAFT.md`.

- `Team Inbox/claim2_oslog_verification.md`
- `Team Inbox/claim3_bonjour_verification.md`
- `Team Inbox/claim3_fsevents_verification.md`
- `Team Inbox/claim5_apfs_verification.md`
- `Team Inbox/claim6_cgevent_verification.md`
- `Team Inbox/tmux_backend_verification.md`
- `Team Inbox/tcc_live_fire_evidence.md`
- `Team Inbox/codex1_test_report.md`
- `Team Inbox/codex1_package_verification.md`
- `Team Inbox/codex1_claim_number_alignment.md`
- `Team Inbox/codex1_prior_art_update.md`
- `Team Inbox/msg_from_claude1_to_codex1_symswift_followup.md`
- `Team Inbox/msg_from_claude1_to_codex1_9916ebd_ack.md`
- `Team Inbox/msg_from_claude1_to_codex1_03bc9d0_ack.md`

### Patent-position correction made during v2

Live web research during this round found that broad "Bonjour/native Swift agent
mesh" language is unsafe as a standalone primary position because
`sym-bot/sym-swift` publicly documents an iOS/macOS Swift SDK whose agents
discover each other over Bonjour and participate in a cross-platform mesh. The
main patent documents were therefore corrected:

- Claim 3 was demoted from a broad standalone primary to a narrow dependent or
  combination claim under Claim 1.
- The surviving Claim 3 distinction is terminal-resident agent control combined
  with SelfConnect's OS-substrate channels: `os_log`, FSEvents, private
  pasteboards, APFS checkpoints, CGEvent/AX/iTerm2/tmux backends, and local
  approval gates.
- Claim 4, the inline same-device LocalAuthentication / Secure-Enclave approval
  gate, was elevated to a narrow primary candidate.

The same research also corrected the competitive read on Project Lancelot /
UAB. Current public UAB materials advertise both Mac and Windows downloads, so
the SelfConnect moat must not rely on "they do not do Mac." The documented
technical distinction is that UAB is an app-control bridge exposing CLI,
library, MCP, and HTTP-server surfaces for desktop application automation,
whereas SelfConnect-Mac is a terminal-resident multi-agent mesh coordinated via
macOS-native OS substrates.

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
