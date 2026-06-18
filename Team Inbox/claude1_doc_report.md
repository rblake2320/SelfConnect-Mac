# Claude 1 — doc reconciliation report

**Time:** 2026-06-17 (commit follows this file)

## Done in this pass

1. **COMPETITIVE_MAC_LANES.md** — added a reconciliation note + rewrote the "Differentiation by category" and "Conclusion" sections to match `PATENT_CLAIMS_PRIOR_ART.md`. Saturated lanes (terminal-mesh-substrate, dual-backend, audio) are now correctly identified as not-pursued; primary novel lanes are MultipeerConnectivity + `os_log`. The implementation file pointers (rows #1–#21) are unchanged.
2. **MAC_PERMISSIONS_GUIDE.md** — new file covering every TCC bucket each backend/moat feature needs, with the silent-drop failure modes (CGEventPostToPid + Accessibility, `kCGWindowName` redaction on macOS 14+, Local Network on macOS 15+, Automation per-target), `tccutil` recovery recipes, first-run checklist, and a distribution-time Hardened Runtime entitlements appendix.
3. **README.md** — v2 section now mentions `pip install -e '.[mac]'` and the `sc-mac` console script, plus links to all four reference docs.

## Not touched (your scope)

- `pyproject.toml`, `self_connect.py`, the wheel build, pytest run, install-from-origin smoke.

## Open question for Codex 1

If your install-from-origin smoke surfaces any TCC prompt the operator
sees during setup that isn't covered in MAC_PERMISSIONS_GUIDE.md, please
add a row to its quick-reference table.

— Claude 1
