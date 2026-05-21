---
tags: [sc-012, reflexivity, whale-detection, 2026-05-21]
date: 2026-05-21
signals: 3
sm_boosted: 0
---

# SC-012 Reflexivity — 2026-05-21

**Source** : @0xChaseTM 'Iceberg' thread — Réflexivité (Soros)
**Signaux** : 3 | **SM actif** : 0

## Logique
Whale entre → X amplifie → crowd suit → prix monte → edge : entrer tôt, sortir quand volume s'effondre.
Proxies : imbalance book + spike volatilité 24h vs semaine précédente + smart money cross-ref.

## Signaux

| # | Question | Side | Prix | Move% | Imbal | VolSpike | SM | Score | Vol |
|---|----------|------|------|-------|-------|----------|----|-------|-----|
| 1 | MicroStrategy sells any Bitcoin by June 30, 2026? | NO | 0.570 | -21.8% | +0.70 | 2.0× | - | 70 | $3,334,590 |
| 2 | Will the Colorado Avalanche win the 2026 NHL Stanl | NO | 0.694 | -9.0% | -0.99 | 6.5× | - | 48 | $14,793,620 |
| 3 | Will the Vegas Golden Knights win the 2026 NHL Sta | YES | 0.199 | +6.8% | -0.96 | 3.7× | - | 44 | $2,246,696 |

## Règles de sortie
- Volume/jour retombe sous baseline → loop brisée → exit
- Prix revient au niveau pré-entrée → stop
- Smart money vend (détectable via scan_smart_money) → exit

## Warning
Ce pattern est momentum pur. Sans signal Twitter/X externe, la détection est imparfaite.
Combiner avec Smart Money scan pour les meilleurs setups.

→ `tmp\reflexivity_signals.json`
