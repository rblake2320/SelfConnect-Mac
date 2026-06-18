# SelfConnect Mac — Prior-Art Search Log

**Search date:** 2026-06-17
**Searcher:** automated research agent (general-purpose subagent of Claude Code Opus 4.7)
**Methodology:** Multiple WebSearch and WebFetch queries per lane across Google Scholar, USPTO patent search, GitHub code search, arXiv, and vendor documentation. Each lane received at least three distinct query phrasings.

This document records the search log and findings. The conclusions are reflected in `PATENT_CLAIMS_DRAFT.md`.

---

## Lane 1 — Multi-agent terminal mesh on macOS, AI-CLI processes coordinated via OS-native I/O

### Search queries used
- "multi-agent terminal mesh"
- "AI CLI orchestration tmux"
- "Claude Code multi-agent"
- "AppleScript AI agent control"

### Findings — saturated prior art for the generic concept

| Source | URL | Relevance |
|---|---|---|
| Anthropic — Claude Code Agent Teams (official) | https://code.claude.com/docs/en/agent-teams | Production multi-agent CLI orchestration with auto-detect of tmux / iTerm2 backends. |
| awslabs/cli-agent-orchestrator | https://github.com/awslabs/cli-agent-orchestrator | tmux + MCP supervisor/worker mesh. |
| Martian-Engineering/claude-team | https://github.com/Martian-Engineering/claude-team | MCP server orchestrating Claude Code through the iTerm2 Python API. |
| mixpeek/amux | https://github.com/mixpeek/amux | tmux-backed multi-agent dashboard. |
| smtg-ai/claude-squad | https://github.com/smtg-ai/claude-squad | Multi-Claude Code orchestration. |
| pouriamrt/claude-mesh | https://github.com/pouriamrt/claude-mesh | Multi-Claude mesh. |

### Differentiator that survives
All cited prior-art systems use **application-layer RPC** (MCP server, HTTP supervisor relay, shared broker, or message bus) for at least one inter-agent channel. SelfConnect's *exclusive use of OS-native substrates* (CGEventPostToPid for input, os_log/AXUIElement/pasteboard for output, FSEvents-watched filesystem for async) is the surviving novel limitation. See Claim 1 in `PATENT_CLAIMS_DRAFT.md`.

---

## Lane 2 — MultipeerConnectivity / AWDL as transport for an LLM agent mesh

### Search queries used
- "MultipeerConnectivity LLM"
- "MultipeerConnectivity agent"
- "Bonjour AI mesh"
- "peer-to-peer LLM coordination"

### Findings — negative search

| Source | URL | Why it does not anticipate |
|---|---|---|
| Olib-AI/ConnectionPool | https://github.com/Olib-AI/ConnectionPool | Generic WebSocket P2P mesh; not LLM-specific and does not use MPC. |
| PAISHackathon/team4 | https://github.com/PAISHackathon/team4 | Hackathon MPC project for a different domain (not LLM mesh). |
| Apple MultipeerConnectivity docs | https://developer.apple.com/documentation/multipeerconnectivity | Reference doc, not an LLM mesh application. |
| Yggdrasil — On AWDL | https://yggdrasil-network.github.io/2019/08/19/awdl.html | Yggdrasil over AWDL; not LLM-specific. |

**No surveyed LLM-mesh project uses MultipeerConnectivity or AWDL.** Claim 3 is supported.

---

## Lane 3 — LocalAuthentication / Touch ID as per-action approval gate

### Search queries used
- "Touch ID AI agent approval"
- "biometric autonomous agent gate"
- "LocalAuthentication LLM"

### Findings — partial overlap; novel sub-variant survives

| Source | URL | Overlap |
|---|---|---|
| Biometric Update — agent identity at RSAC 2026 | https://www.biometricupdate.com/202603/ai-agent-identity-and-next-gen-enterprise-authentication-prominent-at-rsac-2026 | Auth0 + YubiKey out-of-band biometric agent approval. |
| Nametag — "Agents Can Act. Only You Should Authorize." | https://getnametag.com/newsroom/ai-can-act-you-should-authorize | Out-of-band mobile-device approval flow. |
| VeryAI palm biometric agent binding | https://www.biometricupdate.com/202605/veryai-leverages-palm-biometrics-to-bind-ai-agents-to-users | Out-of-band palm biometric. |
| Touch ID for `sudo` via `pam_tid.so` | https://dev.to/siddhantkcode/enable-touch-id-authentication-for-sudo-on-macos-sonoma-14x-4d28 | Same-device biometric but for `sudo`, not an agent-policy gate. |

### Differentiator that survives
All published agent biometric approval systems route through a *cloud out-of-band* channel: the agent contacts a remote service that contacts the user's mobile device. SelfConnect's inline `LAContext.evaluatePolicy` on the *same machine* as the intercepted command, with command-bound attestation logged into the unified-logging mesh bus, is unattested. See Claim 4.

---

## Lane 4 — APFS clonefile(2) per-step rollback

### Search queries used
- "APFS clone agent checkpoint"
- "clonefile LLM rollback"
- "copy-on-write agent state"

### Findings — partial overlap

| Source | URL | Overlap |
|---|---|---|
| arXiv 2511.18323 — Crash-Consistent Checkpointing for AI Training on macOS/APFS | https://arxiv.org/abs/2511.18323 | APFS clones used for ML training checkpoints, not per-tool-call agent rollback. |
| joeinnes/cow | https://github.com/joeinnes/cow | APFS clonefile for parallel agent worktrees. Closest prior art to a per-step variant. |
| Replit Snapshot Engine | https://replit.com/blog/inside-replits-snapshot-engine | Block-level CoW for agents; not APFS-specific. |
| Hermes Agent — checkpoints and rollback | https://hermes-agent.nousresearch.com/docs/user-guide/checkpoints-and-rollback | Shadow-git on destructive commands. |
| Crab (arXiv 2604.28138) | https://arxiv.org/html/2604.28138v1 | CRIU + OpenZFS C/R for agent sandboxes. |

### Differentiator that survives
`joeinnes/cow` uses APFS clonefile but for parallel worktrees, not per-tool-call snapshot. SelfConnect's "clone before every tool call, discard on success, retain N most recent" cadence is narrower. Patentability is marginal; treat as a dependent claim. See Claim 5.

---

## Lane 5 — macOS unified logging (os_log + log stream) as inter-agent message bus

### Search queries used
- "os_log inter-agent bus"
- "unified logging IPC mesh"
- "log stream multi-process coordination"

### Findings — negative search

| Source | URL | Why it does not anticipate |
|---|---|---|
| skartek.dev — Unified Logging introduction | https://skartek.dev/2022/05/04/unified-logging-for-macos-an-introduction/ | Treats unified logging strictly as observability. |
| derflounder.wordpress.com — subsystem/category log predicates | https://derflounder.wordpress.com/2025/08/24/using-subsystem-and-category-log-predicates-when-searching-the-unified-system-log-on-macos-sequoia/ | Predicates documentation for observability. |
| MaxSchaefer/macos-log-stream | https://github.com/MaxSchaefer/macos-log-stream | Go wrapper for monitoring use, not IPC. |
| nicobailon/pi-messenger | https://github.com/nicobailon/pi-messenger | File-based IPC for agents; does not use os_log. |

**No surveyed project uses os_log as the primary mesh bus.** This is the strongest single novelty candidate. See Claim 2.

---

## Lane 6 — CGEventPostToPid for targeted, terminal-agnostic inject

### Search queries used
- "CGEventPostToPid terminal automation"
- "Quartz Event Services targeted PID"
- "targeted synthetic keyboard event macOS"

### Findings — partial overlap

| Source | URL | Overlap |
|---|---|---|
| Apple `CGEventPostToPid` docs | https://developer.apple.com/documentation/coregraphics/1454804-cgeventposttopid | API reference. |
| pyatom/pyatom | https://github.com/pyatom/pyatom | General PID-targeted automation. |
| micmonay/keybd_event PR #37 | https://github.com/micmonay/keybd_event/pull/37 | Background-app event injection. |
| andelf/axcli | https://github.com/andelf/axcli | Accessibility CLI for agents. |
| Cited Claude orchestrators (Lane 1) | (various) | Use `tmux send-keys` or iTerm2 API, **not** `CGEventPostToPid`. |

### Differentiator that survives
Use of `CGEventPostToPid` as the **primary** terminal-agnostic agent-mesh inject channel — instead of tmux send-keys, AppleScript, or the iTerm2 API — is unattested in surveyed agent meshes. Dependent claim. See Claim 6.

---

## Lane 7 — Audio (say / TTS + system sounds) as cross-room mesh signaling

### Search queries used
- "TTS AI agent heartbeat"
- "say command agent status"
- "audio inter-agent signaling"

### Findings — saturated prior art

| Source | URL | Relevance |
|---|---|---|
| Kitty Giraudel — Play Sound When Claude Idles | https://kittygiraudel.com/2026/04/13/play-sound-on-claude-idle/ | Same domain, same `afplay` mechanism, public. |
| cfngc4594/agent-notify | https://github.com/cfngc4594/agent-notify | Sound/voice/macOS alerts for Claude/Cursor/Codex. |
| ybouhjira/claude-code-tts (MCP plugin) | https://github.com/ybouhjira/claude-code-tts | TTS for Claude Code. |
| Benny Cheung — Hear Your AI Agents Work | https://bennycheung.github.io/hear-your-ai-agents-work | Explicitly assigns different voices per agent. |
| alexop.dev — sound effects with Claude Code hooks | https://alexop.dev/posts/how-i-added-sound-effects-to-claude-code-with-hooks/ | Sound-effect hooks for Claude Code. |

**Not pursuable.** Per-agent voice differentiation and `afplay`/`say`-on-completion are documented and widely shipped. No claim drafted.

---

## Lane 8 — iTerm2 Python API + tmux send-keys dual-backend transport

### Search queries used
- "iTerm2 Python API LLM"
- "tmux send-keys AI agent"
- "iTerm2 multi-agent"

### Findings — saturated prior art

| Source | URL | Relevance |
|---|---|---|
| Anthropic — Claude Code Agent Teams | https://code.claude.com/docs/en/agent-teams | Production dual-backend auto-detection. |
| anthropics/claude-code Issue #26572 — "CustomPaneBackend protocol — decouple from tmux CLI" | https://github.com/anthropics/claude-code/issues/26572 | Anthropic explicitly names and ships the backend abstraction. |
| Martian-Engineering/claude-team | https://github.com/Martian-Engineering/claude-team | iTerm2 API backend. |
| mixpeek/amux | https://github.com/mixpeek/amux | tmux backend with dashboard. |

**Not pursuable.** Anthropic itself ships exactly this dual-backend abstraction. No claim drafted.

---

## Summary triage (reflected in PATENT_CLAIMS_DRAFT.md)

| Lane | Tier | Standalone or dependent |
|---|---|---|
| 1 — Pure-OS-substrate inter-agent transport | Primary | Standalone (umbrella) |
| 5 — os_log unified-logging mesh bus | Primary | Standalone |
| 2 — MultipeerConnectivity / AWDL mesh | Primary | Standalone |
| 3 — Inline Secure-Enclave per-action gate | Primary, narrow | Standalone |
| 4 — APFS clonefile per-tool-call snapshot | Secondary | Dependent under Claim 1 |
| 6 — CGEventPostToPid as primary mesh inject | Secondary | Dependent under Claim 1 |
| Vision-OCR fallback in readback cascade | Secondary | Dependent under Claim 1 |
| Private NSPasteboard channels | Secondary | Dependent under Claim 1 |
| 7 — Audio mesh signaling | Not pursued | — |
| 8 — Pluggable iTerm2+tmux dual-backend | Not pursued | — |

## Provenance and reproducibility

This search was performed by an automated research subagent of Claude Code Opus 4.7 (1M context) on 2026-06-17 over the public web. The agent used 31 tool uses and 53,030 tokens. The URL list above is the agent's reported set; an attorney repeating the search may turn up additional references. This document is a working record, not a legal opinion or a comprehensive prior-art search of the kind a registered patent searcher would conduct.

## Live mesh verification footnote

This commit was produced via the very mechanism it patents: two independent AI agents (Claude Opus 4.7 in the "Claude 1" terminal, Codex CLI in the "Codex 1" terminal) coordinated on the same repository without exchanging any application-layer RPC. Claude 1 produced the v2 package and these documents; Codex 1 independently ran the pytest suite (170 passed, 10 skipped), patched the legacy README/test to reflect the current 61-item `__all__` export, added the `mac` extras and `sc-mac` console script to `pyproject.toml`, and verified the wheel builds clean. The coordination occurred entirely through the macOS filesystem state of `/tmp/SelfConnect-Mac/`, observed by both agents without any inter-agent network call. This is the same operational model described in `PATENT_PROCESS_RECORD.md` for the v1 verification on 2026-05-13 → 2026-05-18, now extended to v2 on 2026-06-17.
