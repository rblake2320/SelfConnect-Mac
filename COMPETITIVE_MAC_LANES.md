# SelfConnect Mac — Competitive Lanes & Prior-Art Record

**Date of record:** 2026-06-17
**Repository:** https://github.com/rblake2320/SelfConnect-Mac
**Author:** R. Blake (rblake2320)
**Purpose:** Document which macOS-native primitives SelfConnect employs (and the date of first commit), specifically those that lie outside the surface of competing AI-agent-control SDKs targeting the same problem space.

This document complements `PATENT_PROCESS_RECORD.md` (which records the v1 verification) and `MAC_V2_ARCHITECTURE.md` (which describes the v2 design). It exists so the prior-art trail on these Mac-specific lanes is unambiguous in date, author, and implementation specifics.

---

## What SelfConnect is

A multi-agent terminal-mesh system: independent Claude/Codex/Gemini terminal processes coordinated by OS-native input/IPC/observation primitives, with no inter-agent API calls. Each agent is a self-contained TUI process; the controller injects and observes via the OS.

## What competing systems are

Surveyed 2026-06-17 from public materials:

### Project Lancelot — UAB Bridge (Universal App Bridge)
Source: https://projectlancelot.dev/uab.html, https://projectlancelot.dev/competitive-matrix/

- **Architecture:** localhost HTTP server on port 3100, TypeScript SDK + CLI.
- **Substrate:** desktop application control via framework-specific hooks (Excel COM automation, VS Code Electron CDP, Chrome DevTools Protocol, Qt for FreeCAD, Win32 UI Automation fallback).
- **Platforms named:** Windows and macOS installers; public technical examples emphasize app-control hooks such as COM/UIA/CDP/Electron/Qt rather than terminal-resident OS-substrate mesh coordination.
- **Claims:** "62 action types across 9+ frameworks", "50-100× faster than screenshots", "6-tier cascade control", "17 native MCP tools".
- **Not in scope per their documentation:** terminal-as-substrate, multi-agent mesh, peer-to-peer / multi-machine, AXUIElement for terminal text extraction, CGEvent, MultipeerConnectivity, biometric per-action approval, audio inter-agent signaling, APFS-snapshot checkpointing, unified-logging mesh bus, FSEvents-driven inbox, tmux-based headless mesh.
- **HIVE governance layer** (referenced in their competitive matrix): "soul-inheriting sub-agent spawning with monotonic narrowing", "Receipt/Audit DAG", "Pause-inspect-modify-resume at any receipt in the execution DAG". Operates at the orchestration level above app control. Different problem from terminal mesh.

### LangGraph, CrewAI, OpenAI SDK, Microsoft Agents, NemoClaw
Each is an orchestration framework (DAGs, agents, handoffs, guardrails). None target the OS-native terminal-mesh substrate that SelfConnect occupies.

---

## SelfConnect Mac lanes — implementations and dates

Each row identifies a macOS primitive employed by SelfConnect on the date noted, with file path and a one-line description.

### v1 verified record (2026-05-13 → 2026-05-18, commit `c7380b5`)

| # | Primitive | File | Description |
|---|---|---|---|
| 1 | AppleScript via `osascript` | `self_connect.py` | Targeted Terminal window control: `tell application "Terminal"`, `keystroke`, `key code 36`. |
| 2 | `screencapture` CLI | `self_connect.py`, `screenshot_*.py` | Window screenshots. |
| 3 | `pbcopy` / `pbpaste` | `self_connect.py`, `inject_clipboard.py` | Clipboard transport as a fallback IPC channel. |
| 4 | Terminal.app `contents of window` | `self_connect.py` | Buffer readback without screenshots. |

### v2 expanded record (2026-06-17, this commit)

| # | Primitive | File | Description |
|---|---|---|---|
| 5 | **CGWindowListCopyWindowInfo** (Quartz) | `selfconnect_mac/windows.py` | Enumerate every on-screen window with PID, bounds, layer, owner. Mac equivalent of Win32 EnumWindows. |
| 6 | **CGWindowListCreateImage** (Quartz) | `selfconnect_mac/capture.py` | Per-window capture by CGWindowID. Mac equivalent of Win32 PrintWindow. |
| 7 | **AXUIElement** via `atomacos` | `selfconnect_mac/backends/cgevent.py`, `selfconnect_mac/windows.py` | Buffer reads from any accessibility-conforming app. Mac equivalent of UI Automation. |
| 8 | **CGEvent + CGEventPostToPid** (Quartz) | `selfconnect_mac/backends/cgevent.py` | Targeted keystroke injection at HID layer. Mac equivalent of Win32 PostMessage(WM_CHAR). |
| 9 | **iTerm2 Python API** (WebSocket) | `selfconnect_mac/backends/iterm2.py` | Focus-free, lossless, typed terminal control. No Win32 equivalent. |
| 10 | **tmux send-keys / capture-pane** | `selfconnect_mac/backends/tmux.py` | Headless, SSH-safe mesh substrate. No Win32 equivalent at parity. |
| 11 | **NSWorkspace.runningApplications** | `selfconnect_mac/windows.py` | Process enumeration. |
| 12 | **`os_log` + `log stream`** as mesh bus | `selfconnect_mac/bus/log_bus.py` | Structured queryable pub/sub bus built into the OS. Win32 ETW exists but requires admin and is dramatically harder; no SDK builds a mesh on top of it. |
| 13 | **FSEvents** push notifications | `selfconnect_mac/bus/fsevents_inbox.py` | Sub-second notification of inbox writes; replaces polling. |
| 14 | **NSPasteboard private named channels** | `selfconnect_mac/bus/pasteboard.py` | Typed multi-format private pasteboards (`pasteboardWithName`) as IPC channels — distinct from the system clipboard. |
| 15 | **Bonjour / mDNS** publish & browse | `selfconnect_mac/mesh/multipeer.py` | Zero-config LAN agent discovery. |
| 16 | **MultipeerConnectivity** framework hook | `selfconnect_mac/mesh/multipeer.py` | Import-gated optional upgrade path for peer-to-peer Wi-Fi/BT/AWDL mesh; full `MCSession` delegate wiring is v2.1 work. No Win32 equivalent at the OS-framework level. |
| 17 | **LocalAuthentication** (Touch ID / Face ID) | `selfconnect_mac/approval/touch_id.py` | Biometric per-action approval gate for destructive mesh actions. |
| 18 | **`say` / `afplay` / NSSound** | `selfconnect_mac/approval/audio.py` | Audio channel for cross-room mesh status announcement. |
| 19 | **AppleScript `display notification` + `terminal-notifier`** | `selfconnect_mac/approval/notifications.py` | System-wide banner alerts including critical-priority. |
| 20 | **APFS `cp -c` clones** | `selfconnect_mac/resilience/snapshot.py` | O(1) constant-time per-step mesh checkpoints. Win32 has no filesystem-level analog at parity. |
| 21 | **Vision framework OCR** (`VNRecognizeTextRequest`) | `selfconnect_mac/capture.py` | Last-resort text extraction over screenshot pixels. |

---

## Differentiation by category

> **Note (2026-06-17 reconciliation):** an automated prior-art search (recorded in `PATENT_CLAIMS_PRIOR_ART.md`) found that several lanes initially listed here as "Mac-only territory" or "unoccupied by competing SDKs" are in fact documented in the broader AI-agent-tooling ecosystem (e.g., Anthropic Claude Code Agent Teams ships a pluggable tmux/iTerm2 backend; multiple Claude Code hook projects use `say`/`afplay` for status; `joeinnes/cow` uses APFS clonefile for agent worktrees). The categorization below is restated to reflect those findings. The implementation file pointers above (rows #1–#21) remain factually correct.

### Lanes documented as fully novel by the prior-art search
- **`os_log` unified-logging as primary inter-agent bus** (#12) — unified logging is universally documented as observability; no surveyed project uses it as the IPC bus.

### Lanes with partial prior-art overlap; novelty depends on narrowing
- **MultipeerConnectivity / AWDL / Bonjour transport for LLM agent mesh** (#15/#16) — `sym-bot/sym-swift` is material 2026 prior art for Bonjour/native Swift agent mesh. SelfConnect's defensible angle is the narrower combination with terminal-control agents and OS-substrate buses/checkpoints/approval gates.
- **LocalAuthentication per-action approval** (#17) — same-device inline Secure-Enclave gate is unattested; existing biometric agent approval systems are cloud out-of-band (Auth0, Nametag, VeryAI).
- **APFS clone per-step rollback** (#20) — `joeinnes/cow` uses `clonefile` for parallel worktrees; SelfConnect's per-tool-call snapshot-and-discard cadence is narrower but not orthogonal.
- **`CGEventPostToPid` as primary mesh inject** (#8) — the API is documented; use as the primary mesh transport (vs `tmux send-keys` / iTerm2 API) is unattested.

### Lanes with Win32 functional parity, implemented via different primitives
- Window enumeration: `CGWindowListCopyWindowInfo` (#5) vs EnumWindows.
- Per-window capture: `CGWindowListCreateImage` (#6) vs PrintWindow.
- Text extraction: `AXUIElement` (#7) vs UI Automation.
- Per-process input: `CGEventPostToPid` (#8) vs PostMessage(WM_CHAR).

These reach functional parity with the Win32 surface; they are not standalone claim candidates.

### Lanes with saturated prior art (documented in the broader agent ecosystem; not pursued as claims)
- **Terminal-as-substrate AI agent mesh (generic concept)** — Anthropic Claude Code Agent Teams, awslabs/cli-agent-orchestrator, Martian-Engineering/claude-team, smtg-ai/claude-squad, mixpeek/amux. SelfConnect's differentiator is the *exclusive use of OS-native substrates with no application-layer RPC* — see Claim 1 in `PATENT_CLAIMS_DRAFT.md`.
- **Pluggable tmux + iTerm2 dual-backend** — `anthropics/claude-code` issue #26572 names and ships exactly this abstraction; Martian-Engineering/claude-team and mixpeek/amux implement it.
- **Audio mesh signaling** (`say`/`afplay`) — Kitty Giraudel (2026-04), cfngc4594/agent-notify, ybouhjira/claude-code-tts, Benny Cheung "Hear Your AI Agents Work" all ship this for Claude Code today, with per-agent voice differentiation included.

### Lanes vs surveyed app-control SDKs (Lancelot/UAB, LangGraph, CrewAI, OpenAI SDK, NemoClaw, MS Agents)
None of the surveyed app-control or orchestration SDKs occupy any of the above lanes, because their problem space is different (DAG orchestration, app-action APIs, governance receipts) rather than OS-substrate terminal mesh. The lane distinction is between SelfConnect and other terminal-mesh systems, not between SelfConnect and these SDKs.

---

## Conclusion

The Mac v2 implementation contains one lane documented as fully novel against the public prior art (`os_log` as inter-agent bus), several lanes with narrowing-defensible partial-overlap (Bonjour/Multipeer agent mesh combined with OS-substrate terminal control, Secure-Enclave inline gate, per-tool-call APFS snapshot, `CGEventPostToPid` as primary mesh transport), four lanes that reach Win32 parity via different macOS primitives, and several lanes that are saturated prior art (generic terminal mesh, dual-backend abstraction, audio signaling) where the surviving SelfConnect contribution is the *combination* with the pure-OS-substrate, no-RPC limitation (Claim 1 in `PATENT_CLAIMS_DRAFT.md`).

The factual implementation record (rows #1–#21 above, with file paths) is unchanged by this reconciliation; only the patent-novelty categorization has been adjusted to match the prior-art evidence in `PATENT_CLAIMS_PRIOR_ART.md`.

This document, together with the verifiable git history at https://github.com/rblake2320/SelfConnect-Mac, establishes the date, author, file, and mechanism for each lane as of the commit containing this file.
