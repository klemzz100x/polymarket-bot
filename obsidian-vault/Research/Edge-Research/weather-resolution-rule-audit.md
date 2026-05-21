---
type: "weather-resolution-rule-audit"
tags: ["research", "weather", "rules", "paper-only"]
---
# Weather Resolution Rule Audit

Generated at: `2026-05-13T14:19:36.388428+00:00`

Mode: `research_read_only`. This audit checks whether proxy forecast edges are aligned with Polymarket resolution language.

## Verdict
- `RULES_EXTRACTED` means the market text contains enough source/rule detail to design a replay.
- `SOURCE_MISMATCH_RISK` means the proxy may disagree with the resolution source. Do not promote these to live until replayed against the exact source.
- `RULE_SOURCE_MISSING` means no live consideration.

## State Counts
- RULES_EXTRACTED: 4
- RULES_PARTIAL: 1

## Candidate Rules
| Rule State | Bias | Market | Primary Source | Risk Notes |
|---|---|---|---|---|
| RULES_EXTRACTED | NONE | Will the highest temperature in Austin be 78°F or higher on May 13? | https://www.wunderground.com/history/daily/us/tx/austin/KAUS |  |
| RULES_EXTRACTED | NO | Will the highest temperature in London be 13°C on May 13? | https://www.wunderground.com/history/daily/gb/london/EGLC |  |
| RULES_EXTRACTED | NONE | Will the highest temperature in London be 15°C on May 13? | https://www.wunderground.com/history/daily/gb/london/EGLC |  |
| RULES_EXTRACTED | NO | Will the highest temperature in Seoul be 20°C on May 13? | https://www.wunderground.com/history/daily/kr/incheon/RKSI |  |
| RULES_PARTIAL | YES | Will the highest temperature in Hong Kong be 30°C on May 13? | The resolution source for this market will be information from the Hong Kong Observatory, specif | location/station rule not extracted |
