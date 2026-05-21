# API Endpoints Polymarket — Cheat Sheet Complet

**Source :** @AlterEgo_eth — testé et à jour mai 2026  
**Statut :** Référence technique, pas de hype

---

## Gamma API — http://gamma-api.polymarket.com (public, pas d'auth)

```
GET /markets?limit=100&offset=0                    — catalogue marchés (classique)
GET /markets/keyset?next_cursor=&limit=100          — catalogue avec cursor (plus rapide en bulk)
GET /markets?ids={conditionId}                      — détails marché (array)
GET /markets?conditionId={conditionId}              — détails marché (objet unique)
GET /markets?active=true&closed=false               — marchés actifs uniquement
GET /markets?tag_id={id}&closed=false               — marchés ouverts par tag
GET /public-search?q={query}                        — search (utiliser q=, term= retourne 422)
GET /events?slug={slug}                             — event + tous ses marchés
GET /events/slug/{slug}                             — accès direct à l'event
GET /events?tag_id={id}                             — events par tag
GET /tags                                           — liste complète des tags
```

---

## Data API — http://data-api.polymarket.com (public, pas d'auth)

```
GET /v1/market-positions?market={conditionId}       — toutes les positions des traders
GET /positions?user={address}&limit=500             — positions ouvertes (max 500)
GET /closed-positions?user={address}&limit=50       — positions fermées + historique PnL
GET /activity?user={address}&limit=500              — transactions (TRADE/REDEEM/YIELD)
GET /trades?user={address}&limit=100                — historique trades par wallet
GET /trades?market={conditionId}&limit=100          — historique trades par marché
GET /oi?market={conditionId}                        — open interest en USD
GET /holders?market={conditionId}&limit=50          — top holders
GET /value?user={address}                           — valeur portfolio
```

---

## CLOB API — http://clob.polymarket.com

### Public (pas d'auth)
```
GET /time                                           — server time (pour nonce)
GET /markets/{conditionId}                          — conditionId → token_ids
GET /last-trade-price?token_id={tokenId}            — dernier prix de trade
GET /fee-rate?token_id={tokenId}                    — taux de frais
GET /tick-size?token_id={tokenId}                   — tick size du prix
```

### Auth required
```
GET /book?token_id={tokenId}                        — orderbook complet
GET /midpoint?token_id={tokenId}                    — prix midpoint
GET /orders                                         — vos ordres ouverts
POST /order                                         — passer un ordre unique
POST /orders                                        — batch d'ordres
DELETE /order                                       — annuler un ordre
```

---

## LB API — http://lb-api.polymarket.com (public, pas d'auth)

```
GET /profit?window=all&address={address}            — historique PnL complet
GET /profit?window=1d&address={address}             — PnL dernières 24h
```

---

## WebSockets — wss://ws-subscriptions-clob.polymarket.com/ws

```
/market    — stream public : snapshots orderbook + deltas prix en temps réel
/user      — stream authentifié : vos fills, annulations et mises à jour d'ordres
```

---

## Notes pour le monitoring des wallets

Pour surveiller un wallet :
```python
BASE = "https://data-api.polymarket.com"
address = "0x..."

# PnL complet
pnl = requests.get(f"https://lb-api.polymarket.com/profit?window=all&address={address}")

# Positions ouvertes actuelles
positions = requests.get(f"{BASE}/positions?user={address}&limit=500")

# Activité récente
activity = requests.get(f"{BASE}/activity?user={address}&limit=500")
```

---

## Liens

- [[wallets-to-watch]]
- [[websocket-6-layer-system]]
