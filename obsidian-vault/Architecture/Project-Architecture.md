---
type: architecture
status: active
tags: [architecture, polymarket, system-design]
---
# Project Architecture

## Boundaries
- `resources` is the raw inbox.
- `obsidian-vault` is the clean strategic memory.
- `external-agents` stores downloaded external repositories.
- `src` contains production code.
- `n8n` orchestrates automation through webhooks and scheduled workflows.

## Planes
- Research: parse sources, extract hypotheses, create notes.
- Knowledge: maintain linked Markdown notes.
- Data: ingest market events and build features.
- Strategy: isolate alpha logic behind typed interfaces.
- Risk: validate exposure, sizing, modes, and kill switches.
- Execution: submit, cancel, reconcile, and monitor orders.
- AI: summarize, document, generate hypotheses, and write post-mortems outside the live order path.

## Links
- [[Research Loop]]
- [[Risk Framework]]
- [[Execution]]
- [[Market Making]]
- [[Arbitrage]]

