# Patent Supplemental Research — round 2

**Date:** 2026-06-17
**Searcher:** Claude 1 (live during the live-fire verification round)
**Companion:** `PATENT_CLAIMS_PRIOR_ART.md` (round 1, by automated subagent)

This second round of public-source research was triggered by user direction to "use the internet because a lot is going on and I am trying to defend patent claims." It focuses on recent (2024-2026) USPTO and arXiv material that could affect the primary claims.

---

## New findings affecting the primary claims

### Claim 1 — Pure-OS-substrate (no application-layer RPC) inter-agent transport

| Source | URL | Effect |
|---|---|---|
| Apple agentic-AI strategy 2026 (technosports.co.in) | https://technosports.co.in/apple-agentic-ai-strategy-2026/ | **Strengthens novelty.** Reports Apple's 2026 strategy explicitly "avoids the agentic hype" and uses App Intents to keep Siri context rather than building autonomous agents. Apple is unlikely to file in this space themselves, so an applicant building Mac-native autonomous mesh has a cleaner field. |
| "AgentMesh: A Cooperative Multi-Agent Generative AI Framework" — arXiv 2507.19902 | https://arxiv.org/abs/2507.19902 | **Does not anticipate.** The framework names Planner/Coder/Debugger/Reviewer agents communicating through a Python framework; not OS-substrate, not macOS-specific. |
| "Mesh Memory Protocol: Semantic Infrastructure for Multi-Agent LLM Systems" — arXiv 2604.19540 | https://arxiv.org/abs/2604.19540 | **Does not anticipate.** Defines a semantic memory protocol layer; transport is network/HTTP-based; not OS-substrate. |
| "Beyond DNS: Unlocking the Internet of AI Agents via the NANDA Index" — arXiv 2507.14263 | https://arxiv.org/pdf/2507.14263 | **Does not anticipate Claim 3.** Proposes an *alternative* to DNS-centered discovery for agent registries; explicitly not using Bonjour/mDNS. |

**Conclusion:** Claim 1 remains the recommended umbrella. The "no-RPC" limitation distinguishes from every framework above.

### Claim 2 — `os_log` as inter-agent mesh bus

| Source | URL | Effect |
|---|---|---|
| USPTO general search "log stream predicate inter-process bus 2024-2025" | (no direct hits) | No newer prior art surfaced. |
| US 5367681, US 6408328 (1990s-2000s) | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/5367681 / 6408328 | Pre-existing general IPC patents; do not anticipate the specific `os_log` + NSPredicate filter combination claimed. |
| US 7526550, US 7653633 (2007-2009) | https://patents.google.com/patent/US7526550 / US7653633B2 | Generic log-collection patents; treat unified log as observability, not as IPC. |

**Conclusion:** No update needed. Claim 2 retains negative prior-art search status.

### Claim 3 — MultipeerConnectivity / AWDL for LLM agent mesh

| Source | URL | Effect |
|---|---|---|
| US 9774563 — Packet transmission in mDNS | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9774563 | General mDNS-transport patent; does not bind to LLM agents. |
| US 10680885 — mDNS support in unified access networks | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10680885 | General networking patent. |
| Apple smartphone Bonjour patents (US 8831279 / 8762852 / 9218530 / 9547873) | (various) | Smartphone-app service-discovery patents; not LLM agents. |
| **sym-bot/sym-swift** (surfaced by Codex 1 round 2; verified via WebFetch) | https://github.com/sym-bot/sym-swift | **MATERIAL prior art** for the broad "Bonjour AI agent mesh on macOS" angle. Ships an iOS/macOS Swift SDK that joins a decentralized mesh via Bonjour (`_sym._tcp.`), integrates LLM-based decision-making (CAT7 fields + SVAF attention fusion), and claims production deployment (MeloTune, App Store since Nov 2025) and verified macOS↔macOS↔Windows↔Node.js interop (April 2026). |

**Updated conclusion:** Claim 3 as originally drafted (broad MultipeerConnectivity/Bonjour for LLM agent mesh) is **anticipated** by sym-swift for the discovery layer. The surviving narrow distinction is sym-swift's **in-app SDK integration model** vs SelfConnect's **terminal-resident agent processes coordinated via pure-OS-substrate transport** (Claim 1's limitation). Recommended:

1. Demote the standalone Claim 3 tier from Primary to Secondary in the triage table.
2. Rewrite Claim 3 to explicitly include the terminal-resident + Claim 1 limitation: each peer being a terminal-resident agent process coordinated by Bonjour-discovered peers AND by the pure-OS-substrate transports of Claim 1.
3. Note for counsel: the sym-swift finding is from 2025/2026 — predates SelfConnect-Mac v2 (this commit) but **postdates** the v1 verified record (`PATENT_PROCESS_RECORD.md`, 2026-05-13).

### Claim 4 — LocalAuthentication inline Secure-Enclave gate

| Source | URL | Effect |
|---|---|---|
| Touch ID Patents (PatentPC blog) | https://patentpc.com/blog/touch-id-patents-the-legal-strategies-behind-apples-fingerprint-authentication-technology | Apple's Touch ID patent portfolio — biometric authentication broadly. Does not anticipate the *inline same-device per-agent-action* variant. |
| sudo-touchid GitHub (Matt Rajca) | https://github.com/mattrajca/sudo-touchid | Same-device biometric for `sudo` — closest practical prior art. Does not bind to AI agents or to a policy-classified action stream. |
| Apple Developer Forum thread on TouchID authorization | https://developer.apple.com/forums/thread/106386 | Notes that `LocalAuthentication` is for apps, not authorization plug-ins. Constrains the implementation surface but does not affect SelfConnect's app-process use. |

**Conclusion:** Claim 4 narrowing remains defensible — the agent-policy + command-bound-attestation + unified-log-recording combination is unattested.

### Claim 5 — APFS clonefile per-tool-call rollback (dependent)

No new findings. The closest prior art remains `joeinnes/cow` and arXiv 2511.18323; SelfConnect's per-tool-call snapshot-and-discard cadence remains the surviving sub-element.

---

## Cross-cutting observation

Multiple results in this round confirm that the AI-agent patent space is **active but oriented toward orchestration, governance, and DAG semantics** (Lancelot HIVE receipts, LangGraph time-travel, AgentMesh framework, Mesh Memory Protocol). **The OS-substrate-transport lane SelfConnect occupies is not contested** — even Anthropic's own Claude Code agent-teams ships at the orchestration layer, using MCP for transport.

This reinforces the recommendation in `PATENT_CLAIMS_DRAFT.md`: Claim 1 (umbrella, pure-OS-substrate, no-RPC) is the strongest filing position; Claim 2 is the strongest narrow standalone candidate; Claim 4 is the next defensible standalone narrow. Claim 3 should be narrowed or made dependent under Claim 1 after the `sym-bot/sym-swift` finding.

## Recommendation for the attorney (updated post-sym-swift)

1. File **Claim 1** as the umbrella (pure-OS-substrate, terminal-resident, no-RPC).
2. File **Claim 2** (`os_log` bus) as the strongest standalone narrow — still negative prior art.
3. File **Claim 4** (inline Secure-Enclave gate) as a second standalone narrow.
4. **Claim 3** as drafted is anticipated by sym-swift. Either:
   - Withdraw as standalone and re-cast as a dependent under Claim 1 ("the method of Claim 1 wherein peer discovery uses Bonjour …"), **or**
   - Re-narrow to the combination: terminal-resident agents discovered via Bonjour AND transported via the pure-OS-substrate channels of Claim 1, distinguishing from sym-swift's in-app SDK model.
5. Bundle Claims 5–8 (APFS clones, CGEventPostToPid, Vision-OCR cascade, NSPasteboard channels) as dependent claims under Claim 1.
6. Do not file on Lanes 7 (audio) or 8 (dual-backend) — saturated prior art.

— Claude 1
