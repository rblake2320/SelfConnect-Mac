# SelfConnect Mac — Patent Claim Drafts (Working Document)

**Date:** 2026-06-17
**Author:** R. Blake (rblake2320)
**Status:** Working draft for review by patent counsel. **Not** a filed application.
**Prior-art evidence:** See `PATENT_CLAIMS_PRIOR_ART.md` for the search log, URLs, and per-lane findings supporting each claim.
**Companion documents:** `MAC_V2_ARCHITECTURE.md`, `COMPETITIVE_MAC_LANES.md`, `PATENT_PROCESS_RECORD.md`.

## Triage summary

Following a structured prior-art search (2026-06-17) the candidate lanes group as:

| Lane | Tier | Reason |
|---|---|---|
| 1. Pure-OS-substrate AI agent mesh (no MCP/HTTP) | **Primary** | All known prior art (Claude Code Agent Teams, awslabs/cli-agent-orchestrator, Martian-Engineering/claude-team) uses MCP, HTTP, or other application-layer RPC. SelfConnect's exclusive use of OS-native I/O is the differentiating limitation. |
| 2. `os_log` unified-logging system as inter-agent bus | **Primary** | Unified logging is universally documented as observability. No published project uses it as the *primary* inter-process bus for an agent mesh. |
| 3. MultipeerConnectivity / AWDL for LLM agent mesh | **Primary** | P2P-LLM prior art uses gossip/DHT/WebSocket. No published project uses AWDL/MPC. |
| 4. LocalAuthentication inline Secure-Enclave gate | **Secondary** | Cloud out-of-band biometric agent approval is documented (Auth0, YubiKey, Nametag, VeryAI). The *inline, same-device, command-bound* variant is unattested in published agent systems. |
| 5. APFS `clonefile(2)` per-step rollback | **Dependent** | `joeinnes/cow` uses APFS clonefile for parallel worktrees; arXiv 2511.18323 uses it for training checkpoints. SelfConnect's per-tool-call automatic clone-and-discard is narrower but defensible only as a dependent claim. |
| 6. CGEventPostToPid as primary inject for terminal mesh | **Dependent** | The API itself is documented (`axcli`, `pyatom`). Use as the primary inject channel for an inter-agent mesh is unattested but the available scope is narrow. |
| 7. Targeted Vision-OCR readback fallback | **Dependent** | OCR over screenshots is well known. Specific use as a typed fallback in a mesh readback cascade is bundleable. |
| 8. Private NSPasteboard channels for IPC | **Dependent** | Plausibly novel for agent mesh use; bundle under a primary claim. |
| 9. Pluggable iTerm2+tmux dual-backend | **Not pursued** | Anthropic Claude Code ships this in production (issue #26572 names the abstraction). |
| 10. Audio mesh signaling | **Not pursued** | Saturated prior art (Kitty Giraudel, agent-notify, claude-code-tts MCP, Benny Cheung). |

Each claim below identifies its implementing source file in this repository so the claim can be tied to executable, dated source.

---

## Claim 1 — Pure-OS-substrate inter-agent transport (Primary)

**Independent claim 1.** A method for coordinating two or more independent terminal-resident AI agent processes on a macOS system, comprising:

1. instantiating at least two said agent processes, each executing a frontier large-language-model command-line interface;
2. exchanging at least one substantive message between said agent processes, said exchange comprising both directed input delivery and observed-output retrieval;
3. wherein each said exchange is effected *exclusively* through operating-system-provided input/output substrates selected from the group consisting of synthetic HID events directed at a specified process identifier, the operating system's unified logging facility, system-managed pasteboards, Apple Events, and filesystem-mediated message stores observed via FSEvents;
4. wherein no application-layer remote-procedure-call channel of any kind — including but not limited to MCP, HTTP, WebSocket, gRPC, ZeroMQ, or message-bus protocols — is established between said agent processes for purposes of said exchange.

**Dependent claim 1.1.** The method of claim 1, wherein the directed input delivery is performed via the Quartz Event Services API `CGEventPostToPid` keyed on the process identifier of the target agent.

**Dependent claim 1.2.** The method of claim 1, wherein the observed-output retrieval is performed via at least one of the macOS Accessibility API `AXUIElement` tree, the unified logging subscription via `log stream` with a predicate, or the macOS pasteboard server.

**Differentiation note:** Surveyed agent-mesh systems (Claude Code Agent Teams, awslabs/cli-agent-orchestrator, Martian-Engineering/claude-team, smtg-ai/claude-squad, mixpeek/amux) all employ at least one application-layer RPC channel (MCP server, HTTP supervisor relay, or shared-memory broker) for inter-agent exchange. The "no RPC, only OS substrates" limitation in step 4 is the distinguishing element.

**Implementing files:** `selfconnect_mac/backends/cgevent.py`, `selfconnect_mac/bus/log_bus.py`, `selfconnect_mac/bus/pasteboard.py`, `selfconnect_mac/bus/fsevents_inbox.py`.

---

## Claim 2 — `os_log` unified-logging as inter-agent mesh bus (Primary)

**Independent claim 2.** A method for inter-process communication between two or more autonomous AI agent processes on a macOS system, comprising:

1. assigning each agent a unique subsystem identifier of the form `com.<mesh>.<agent_id>` and one or more category identifiers describing event types;
2. each agent emitting structured event payloads, serialized as JSON, through the macOS unified logging facility under its assigned subsystem and category;
3. a controller process subscribing to event payloads matching an `NSPredicate` over the subsystem identifier, event category, and/or payload contents via `log stream --predicate`;
4. a second consumer issuing point-in-time historical queries over the same predicate via `log show --last <duration>`, the kernel-arbitrated unified log datastore providing tamper-evident persistence;
5. operating the mesh without binding an open network port, allocating a shared file inbox for the bus, or requiring an inter-agent API endpoint.

**Dependent claim 2.1.** The method of claim 2, wherein agents emit messages via the `logger(1)` command alone, without holding any process-bound framework reference to the logging API, such that agents may be implemented in any language without an `os_log` framework binding.

**Dependent claim 2.2.** The method of claim 2, wherein the unified logging facility's persistent archive serves as the auditable record of mesh activity, signed-timestamped by the operating system kernel without additional application-supplied cryptography.

**Differentiation note:** Documented use of macOS unified logging in the prior art (skartek.dev introduction, derflounder.wordpress.com predicates guide, MaxSchaefer/macos-log-stream Go wrapper) treats it strictly as system observability. No surveyed agent system uses it as the primary inter-agent bus.

**Implementing files:** `selfconnect_mac/bus/log_bus.py`.

---

## Claim 3 — MultipeerConnectivity / AWDL for LLM agent mesh (Primary)

**Independent claim 3.** A method for coordinating two or more autonomous LLM-driven agent processes residing on distinct physical macOS hosts on a local area network or local radio range, comprising:

1. each host advertising a service of type `_selfconnect._tcp.` via Bonjour / mDNS carrying TXT-record metadata describing agent identifiers, capabilities, and supported message formats;
2. remote hosts browsing for services of said type and discovering peer agents without requiring DNS, static configuration, or shared pre-pairing;
3. on hosts pairwise possessing Apple Wireless Direct Link (AWDL)-capable radios, optionally upgrading the inter-host transport to Apple's `MultipeerConnectivity` framework with `MCNearbyServiceAdvertiser` and `MCNearbyServiceBrowser`, providing direct peer-to-peer Wi-Fi, Bluetooth, or AWDL transport without router intermediation;
4. exchanging agent task descriptions, results, and coordination signals via the `MCSession` send-data primitive.

**Dependent claim 3.1.** The method of claim 3, wherein the `discoveryInfo` dictionary supplied to the `MCNearbyServiceAdvertiser` carries an agent capability vocabulary that the browsing peer evaluates against task requirements before initiating an `MCSession` invitation.

**Dependent claim 3.2.** The method of claim 3, wherein non-macOS peers participate in the mesh through the Bonjour discovery layer of step (1) but do not upgrade to the MultipeerConnectivity transport of step (3).

**Differentiation note:** Surveyed peer-to-peer LLM systems use WebSocket overlays (Olib-AI/ConnectionPool), DHT/gossip protocols, or cloud relays. No surveyed LLM-mesh project employs Apple's `MultipeerConnectivity` framework or AWDL transport.

**Implementing files:** `selfconnect_mac/mesh/multipeer.py`.

---

## Claim 4 — Inline Secure-Enclave per-action biometric gate with command-bound attestation (Primary, narrow)

**Independent claim 4.** A method for owner-in-the-loop approval of autonomous AI agent actions on a macOS system equipped with a Secure Enclave, comprising:

1. classifying a proposed agent action against a configurable policy, the classification including at least the action type, target resource, and reversibility tier;
2. for actions classified as elevated-risk, intercepting the action prior to execution;
3. constructing an `LAContext` with a localized reason string that incorporates a textual description of the specific intercepted action;
4. evaluating `LAPolicy.DeviceOwnerAuthenticationWithBiometrics` synchronously, the evaluation being satisfied solely by an on-device biometric or device-password presentation to the Secure Enclave on the same machine as the intercepted action;
5. permitting execution only upon successful evaluation;
6. recording into the unified logging mesh bus of Claim 2 the agent identifier, the action description as presented to the user, the timestamp of the user response, and a hash of the action body, said record forming a command-bound attestation.

**Dependent claim 4.1.** The method of claim 4, wherein the attestation record of step (6) is consulted by any subsequent agent in the mesh to verify that the action was authorized prior to participating in its consequences.

**Differentiation note:** Documented prior art (Auth0 + YubiKey for agents, Nametag's "Agents Can Act. Only You Should Authorize," VeryAI palm-biometric agent binding) effects approval via cloud out-of-band channels: the agent calls a remote service which contacts the user's mobile device. SelfConnect's variant evaluates the biometric on the same Mac as the agent, against the local Secure Enclave, with no network step. Touch-ID-for-`sudo` (`pam_tid.so`) is widely known but is not an agent-policy gate.

**Implementing files:** `selfconnect_mac/approval/touch_id.py`, `selfconnect_mac/bus/log_bus.py`.

---

## Claim 5 — Per-tool-call APFS clonefile checkpoint (Dependent under Claim 1)

**Independent claim 5.** A method for delimiting the persistent side-effects of an autonomous agent's individual tool invocations on a macOS system mounted on a file system supporting `clonefile(2)`, comprising:

1. prior to each agent tool invocation, invoking `clonefile(2)` on the agent's working tree to produce a labeled snapshot in constant time;
2. executing the tool invocation against the live working tree;
3. on successful completion, discarding the snapshot;
4. on declared rollback, atomically replacing the live working tree with the snapshot;
5. retaining at most N most-recent snapshots and pruning older labeled snapshots on a schedule.

**Differentiation note:** `joeinnes/cow` employs `clonefile` for parallel agent worktrees; arXiv 2511.18323 employs it for ML training checkpoints. The contribution narrowed here is the per-tool-call snapshot-and-discard cadence and discarding-on-success behavior, not the use of `clonefile` itself.

**Implementing files:** `selfconnect_mac/resilience/snapshot.py`.

---

## Claim 6 — Targeted CGEvent injection as terminal-agnostic mesh transport (Dependent under Claim 1)

**Independent claim 6.** A method for terminal-emulator-agnostic input delivery between AI agent processes on a macOS system, comprising:

1. enumerating candidate terminal-resident processes via `CGWindowListCopyWindowInfo`;
2. maintaining a registry mapping mesh agent identifiers to operating-system process identifiers;
3. for a delivery to agent identifier `A`, synthesizing keyboard events via `CGEventCreateKeyboardEvent` with `CGEventKeyboardSetUnicodeString` carrying the message payload;
4. posting the events via `CGEventPostToPid` directed at the process identifier registered for agent `A`;
5. delivering the events without changing the user's frontmost window and irrespective of which terminal emulator hosts agent `A`.

**Differentiation note:** Surveyed agent meshes use `tmux send-keys`, the iTerm2 Python API, or AppleScript — each terminal-specific. `CGEventPostToPid` is a known API used by `axcli`, `pyatom`, and `micmonay/keybd_event`, but not as the primary mesh transport. The narrowing here is "primary, identifier-keyed mesh delivery channel."

**Implementing files:** `selfconnect_mac/backends/cgevent.py`.

---

## Claim 7 — Cascade buffer-read with Vision-OCR fallback (Dependent under Claim 1)

**Independent claim 7.** A method for retrieving the visible textual buffer of a target terminal-resident agent on a macOS system, comprising attempting in priority order:

1. the iTerm2 Python API `async_get_screen_contents` when the target is hosted in iTerm2;
2. `tmux capture-pane -p` when the target is a tmux pane;
3. the macOS Accessibility API `AXUIElement` walk against the target process;
4. AppleScript `contents of window` against the target Terminal.app window;
5. only when each of (1)–(4) returns empty or errors, capturing the target via `CGWindowListCreateImage` and submitting the image to a `VNRecognizeTextRequest` of Apple's Vision framework;
6. returning the first non-empty result.

**Implementing files:** `selfconnect_mac/capture.py`, `selfconnect_mac/backends/{iterm2.py, tmux.py, cgevent.py, applescript.py}`.

---

## Claim 8 — Private NSPasteboard channels for agent IPC (Dependent under Claim 1)

**Independent claim 8.** A method for typed, multi-format inter-process message transport between AI agent processes on a macOS system, comprising:

1. allocating a private pasteboard via `NSPasteboard.pasteboardWithName` using a mesh-scoped name distinct from the system general pasteboard;
2. encoding a structured message body containing at least a text-typed payload and optionally additional payloads of types selected from image, JSON, and URL types;
3. tracking the pasteboard's monotonically increasing `changeCount` for O(1) "new message" detection without re-reading the payload;
4. reading any subset of the typed payloads independently per subscriber capability.

**Implementing files:** `selfconnect_mac/bus/pasteboard.py`.

---

## Compound system claim

**Independent claim 9.** A system comprising one or more macOS-equipped computers, each executing one or more terminal-resident autonomous AI agent processes, said system implementing the pure-OS-substrate transport of Claim 1 and at least two of the methods of Claims 2 through 8 in combination, such that two or more AI agent processes coordinate on substantive computational work without exchanging messages via any application-layer remote-procedure-call channel.

---

## Note to counsel

The two strongest standalone candidates are Claim 2 (`os_log` mesh bus) and Claim 3 (MultipeerConnectivity for LLM mesh). Both have negative prior-art search results on the specific application. Claim 1 (pure-OS-substrate, no-RPC) is the umbrella claim that distinguishes SelfConnect from documented multi-agent systems and is the recommended primary independent claim of any filing. Claim 4 (inline Secure-Enclave gate) is a defensible third primary candidate.

Claims 5–8 are appropriate dependent claims to bundle under Claim 1 and/or Claim 2.

Lanes documented in the prior-art search as saturated — pluggable iTerm2/tmux dual-backend (issue #26572 on `anthropics/claude-code`), audio mesh signaling (Kitty Giraudel, agent-notify), and the generic terminal-mesh concept (Claude Code Agent Teams) — are intentionally not claimed.

The repository history at https://github.com/rblake2320/SelfConnect-Mac, including `PATENT_PROCESS_RECORD.md` dated 2026-05-13 → 2026-05-18 (commit `c7380b5`) and this commit dated 2026-06-17, establishes date and authorship of each implementing file.
