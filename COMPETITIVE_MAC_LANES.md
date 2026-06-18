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
- **Platforms named:** Windows and macOS installers; specific framework hooks named are Windows-centric (COM, Win32 UIA).
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
| 16 | **MultipeerConnectivity** framework | `selfconnect_mac/mesh/multipeer.py` | Peer-to-peer Wi-Fi/BT/AWDL mesh without router. No Win32 equivalent. |
| 17 | **LocalAuthentication** (Touch ID / Face ID) | `selfconnect_mac/approval/touch_id.py` | Biometric per-action approval gate for destructive mesh actions. |
| 18 | **`say` / `afplay` / NSSound** | `selfconnect_mac/approval/audio.py` | Audio channel for cross-room mesh status announcement. |
| 19 | **AppleScript `display notification` + `terminal-notifier`** | `selfconnect_mac/approval/notifications.py` | System-wide banner alerts including critical-priority. |
| 20 | **APFS `cp -c` clones** | `selfconnect_mac/resilience/snapshot.py` | O(1) constant-time per-step mesh checkpoints. Win32 has no filesystem-level analog at parity. |
| 21 | **Vision framework OCR** (`VNRecognizeTextRequest`) | `selfconnect_mac/capture.py` | Last-resort text extraction over screenshot pixels. |

---

## Differentiation by category

### Lanes that have no Win32 parity (claimable Mac-only territory)
- MultipeerConnectivity peer-to-peer mesh (#16)
- LocalAuthentication biometric per-action approval (#17)
- APFS clone-based O(1) checkpointing (#20)
- `os_log` queryable mesh bus (#12)
- Bonjour-based zero-config LAN discovery (#15)
- Vision-OCR fallback as a primary read path (#21)

### Lanes that have Win32 parity but operate via fundamentally different primitives
- Window enumeration: CGWindowListCopyWindowInfo (#5) vs EnumWindows
- Per-window capture: CGWindowListCreateImage (#6) vs PrintWindow
- Keystroke injection: CGEventPostToPid (#8) vs PostMessage(WM_CHAR)
- Text extraction: AXUIElement (#7) vs UI Automation

### Lanes that the surveyed competing SDKs (Lancelot/UAB, LangGraph, CrewAI, OpenAI SDK, NemoClaw, MS Agents) do not occupy as of 2026-06-17
- Terminal-as-substrate AI agent mesh (entire problem space)
- tmux-driven headless multi-agent mesh
- iTerm2 Python API as agent transport
- Audio channel for inter-agent / inter-room status
- Biometric per-action approval
- Multi-machine LAN peer mesh via Bonjour/MultipeerConnectivity
- APFS clone-based mesh checkpointing
- `os_log` unified-logging mesh bus

---

## Conclusion

The Mac v2 implementation occupies six lanes the surveyed competing systems do not touch at all (terminal mesh substrate, tmux/iTerm2 backends, audio mesh signaling, biometric approval, multi-machine peer mesh, APFS checkpointing). The remaining lanes (window enumeration, capture, keystroke injection, text extraction) employ macOS-native primitives that differ in implementation from Win32 even where they reach functional parity.

This document, together with the verifiable git history at https://github.com/rblake2320/SelfConnect-Mac, establishes the date, author, file, and mechanism for each lane as of the commit containing this file.
