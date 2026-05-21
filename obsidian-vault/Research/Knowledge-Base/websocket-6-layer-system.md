# Système WebSocket 6 Couches — 0x_Punisher

**Source :** @0x_Punisher (thread le plus technique du PDF)  
**Wallet public :** https://polymarket.com/@pbot-6  
**Claim :** $100K PnL. Non auditable mais architecture cohérente et détaillée.

---

## Pourquoi ce système

Le WS Polymarket brut contient :
- Snapshots stales
- Ticks manqués
- Jitter
- Disconnects brefs

Ces 6 couches transforment un feed brut en stream ultra-propre, ultra-rapide.

---

## Layer 1 — Warmup & Quality Gate

```
- Démarrer chaque connexion 15 secondes avant l'ouverture de la fenêtre de trading
- Dans les 5 dernières secondes : exiger au moins 3 ticks par token
- Rejeter si un saut > 5¢ détecté
- Si échec → skip la fenêtre entière
```

**Pourquoi :** les premières secondes sont inondées de bids stales.

---

## Layer 2 — Volume & Dynamic Spawning

```
- Spawner 100–300 websockets en parallèle (selon hardware)
- Toutes les 4 secondes : tuer et respawner les 10% les plus lents
- Toujours prendre le premier tick unique (dédupliqué) qui arrive
```

**Pourquoi :** plus de volume = probabilité plus haute de battre tous les autres bots sur le premier tick.

---

## Layer 3 — Stale Tick Guard

```python
# Comparer chaque nouveau tick au prix du warmup
if abs(new_tick - warmup_price) > 0.15:  # delta > 15¢
    log("STALE TICK REJECTED")
    continue
```

---

## Layer 4 — First-Tick Skip

```
- Dropper le tout premier tick de chaque nouvelle connexion
- Il est presque toujours un snapshot en cache
```

---

## Layer 5 — Staggered Startup

```
- Ne jamais démarrer toutes les connexions exactement au même milliseconde
- Les étaler uniformément sur 1 seconde
- Chaque socket a la meilleure chance de recevoir des ticks différents et uniques
```

---

## Layer 6 — Anti-Jitter Reaper

```python
# Tracker la variance de timing avec un EMA de jitter par connexion
jitter_ema[conn_id] = alpha * current_jitter + (1 - alpha) * jitter_ema[conn_id]

# Règles :
# - Éliminer les connexions les plus erratiques en premier
# - Nouvelles connexions : grace period de 8 secondes
# - Budget : max 20 respawns/minute, max 2 par cycle
# - Les connexions culled perdent leur tracking data
```

---

## Règles critiques supplémentaires (0x_Punisher)

### Win rate vs prix d'entrée
```
Entrer à 57¢ → besoin de 57%+ win rate pour être rentable
Entrer à 40¢ → besoin de 40%+ win rate
Règle : > 5¢ pour break-even, > 10¢ pour vraiment profiter
```

### BTC markets spécifiques
- Ne jamais parier aveuglément au-dessus de 85¢
- Stop losses : tester si no-stop performe mieux (souvent oui sur courtes fenêtres)
- Tester par coin ET par timeframe séparément

### Workflow de validation
```
1. Test manuel rapide (20 min)
2. Sweeps multivariés + cross-validation 3-fold + contrôle overfitting (2h)
3. Code dans template propre (30 min)
4. Dry-run live avec vrai wallet (balance zéro)
5. Traiter chaque NSF error comme un signal réel → re-backtest avec inclus
6. Déployer SEULEMENT si backtest ≈ live ± 3%
```

---

## Sur Python vs Rust (conclusion 0x_Punisher)

> "Keep Python for strategy research, backtesting and data analysis. Rewrite ONLY the execution layer in Rust or C++. The hot path (signal detection → order submission) is the only part where language speed actually matters."

Optimisations valables en Python aussi :
- Batcher les ordres
- Pre-build signatures et headers avant l'ouverture des fenêtres
- `TCP_NODELAY`
- Zéro sérialisation sur le hot path

---

## Liens

- [[wallets-to-watch]]
- [[quant-formulas-reference]]
- [[api-endpoints-reference]]
