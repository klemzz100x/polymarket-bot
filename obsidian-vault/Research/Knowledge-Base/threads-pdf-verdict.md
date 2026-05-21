# Verdict — threads_twitter.pdf (20 threads analysés)

**Analysé le :** 2026-05-20  
**Source :** resources/twitter-threads/threads_twitter.pdf (141 pages)

---

## Gardé — Signal réel (9 threads)

| Thread | Auteur | Contenu de valeur |
|---|---|---|
| T1 | @stacyonchain | Architecture agent sports consensus (Firecrawl + Claude) |
| T2 | @RohOnChain | ARIMA + GARCH time series stack, unit root, walk-forward |
| T3 | @crptAtlas | Fundamental Law IR = IC × √N, multi-signal systems |
| T10 | @polysuccubus | **Aniki case study** : barbell market making, $700K Musk tweets |
| T13 | @0x_Punisher | **6-layer websocket system** + bot playbook complet |
| T14 | @0xMovez | 4 formules copy-trading + Becker calibration + wallets |
| T15 | @AlterEgo_eth | **API endpoints cheat sheet** complet (mai 2026) |
| T16 | @L1vsun | 5 tools @rn1 : raw WS + Claude + Kelly + Bayesian + systemd |
| T18 | @LunarResearcher | **Système complet** : Claude oracle + Becker + Markov + scanner |
| T20 | @0xRicker | Markov entry filter (diagonal >= 0.87) + top 5 BTC bots |

---

## Signal moyen (4 threads — formules correctes mais génériques)

| Thread | Auteur | Pourquoi medium |
|---|---|---|
| T4 | @phosphenq | Empirical Kelly bootstrap — valide mais pas Polymarket-spécifique |
| T5 | @ZeroCortexAI | Kalman Filter — correct mais overkill pour notre stade |
| T12 | @DextersSolab | Rust vs Python — déjà traité, point valide |
| T19 | @adiix_official | $25 gap BTC pattern — empirique, intéressant mais limité |

---

## Bullshit supprimé (7 threads)

| Thread | Auteur | Raison |
|---|---|---|
| T6 | @0xPhantomDefi | Promo wallet/bridge app, zéro contenu |
| T7 | @stacyonchain | "How to be faster" → pitch centpro.bot |
| T8 | @stacyonchain | "Results documented" → pitch centpro.bot |
| T9 | @stacyonchain | "Start small" vague → pitch centpro.bot |
| T11 | @RetroChainer | Weather traders ranking → pitch Parity platform |
| T17 | @stacyonchain | Résumé → pitch centpro.bot + github Jonmaa |

**Note sur centpro.bot :** @stacyonchain poste du contenu partiellement valide (T1 sur sports consensus a une vraie architecture) mais le modèle économique est de convertir vers son service. L'architecture T1 reste exploitable indépendamment.

---

## Ce que les threads disent VRAIMENT (consensus cross-threads)

1. **L'edge n'est pas dans le prompting mais dans l'infrastructure** : WS propre, sizing discipliné, biais Becker, exécution limit orders
2. **Claude est utile comme moteur de probabilité**, pas comme trader
3. **91% des traders Polymarket perdent** (Becker, 72M trades) — concentrated dans longshots YES < 10¢
4. **Les bots gagnants** : tous automatisés, tous sur marchés spécifiques (BTC 5-min, market making), tous limit orders
5. **Sizing = where you die** : Kelly ou rien, flat betting = perte garantie sur le long terme

---

## Nouveaux fichiers créés

- [[becker-calibration-72m-trades]]
- [[quant-formulas-reference]]
- [[claude-probability-oracle-prompt]]
- [[websocket-6-layer-system]]
- [[api-endpoints-reference]]
- [[wallets-to-watch]]
- Strategy-Candidates registry : 6 nouvelles stratégies (SC-001 à SC-006)
