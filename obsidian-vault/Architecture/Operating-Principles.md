---
type: principles
status: active
tags: [architecture, operations]
---
# Operating Principles

## Non-negotiables
- AI can assist research and engineering, but cannot directly send live orders.
- Every strategy must have a risk budget, kill-switch conditions, and a post-mortem path.
- Every external repo is untrusted until reviewed.
- Every raw source must become a clean note before it enters the strategic memory.

## Production modes
- `research`: notebook and notes only.
- `paper`: live data, simulated orders.
- `quote-only`: compute quotes, do not submit.
- `maker-only`: submit post-only orders only.
- `flatten`: reduce exposure.
- `halted`: no new orders.

