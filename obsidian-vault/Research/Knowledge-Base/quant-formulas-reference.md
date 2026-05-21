# Formules Quant — Référence Polymarket

**Sources :** @LunarResearcher, @0xMovez, @crptAtlas, @RohOnChain, @polysuccubus  
**Statut :** Formules mathématiques vérifiées, extraites de threads à contenu réel

---

## 1. Quarter-Kelly avec correction longshot (formule principale)

```
f* = (p_corrigé × b − q_corrigé) / b
bet = f* × 0.25 × bankroll
cap dur : jamais > 3% du bankroll par position
```

Où :
- `p_corrigé` = probabilité Claude après `apply_longshot_correction()`
- `b` = (1 − market_price) / market_price (odds implicites)
- `q_corrigé` = 1 − p_corrigé

**Seuil minimal :** edge brut > 2% avant correction. En dessous → ne pas trader.

```python
def kelly_size(p_model, market_price, bankroll, kelly_fraction=0.25):
    from becker_calibration import apply_longshot_correction
    p = apply_longshot_correction(p_model)
    q = 1 - p
    b = (1 - market_price) / market_price
    raw_edge = p - market_price
    kelly_f = (p * b - q) / b
    if kelly_f <= 0 or raw_edge < 0.02:
        return {"bet": 0, "edge": raw_edge, "reason": "no_edge"}
    bet = bankroll * kelly_f * kelly_fraction
    return {"bet": round(bet, 2), "edge": round(raw_edge, 4), "kelly_raw": round(kelly_f, 4)}
```

---

## 2. Fundamental Law of Active Management (Grinold)

```
IR = IC × √N
```

- IR = Information Ratio du système combiné (edge risk-ajusté)
- IC = Information Coefficient moyen des signaux individuels (corrélation signal/réalité)
- N = nombre de signaux genuinement indépendants

**Exemple :** 50 signaux avec IC=0.05 → IR = 0.354. Un seul signal IC=0.10 → IR = 0.10.
**Leçon :** multiplier les signaux indépendants vaut mieux qu'améliorer un seul signal.

---

## 3. Markov 3-états pour Polymarket

```python
def classify_state(price: float) -> tuple[int, str]:
    if 0.35 <= price <= 0.65:
        return 0, "CONTESTED"      # Zone max incertitude, max edge potentiel
    elif price > 0.75:
        return 1, "RESOLVED_YES"   # Momentum bias
    else:
        return 2, "RESOLVED_NO"    # Longshot bias maximal

def build_transition_matrix(price_history: list[float]) -> np.ndarray:
    states = [classify_state(p)[0] for p in price_history]
    T = np.zeros((3, 3))
    for i in range(len(states) - 1):
        T[states[i], states[i+1]] += 1
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    return T / row_sums
```

**Filtre d'entrée :** entrer seulement si diagonale de la matrice ≥ 0.87 (état persistant).

```python
def should_enter(P, current_state, market_price, tau=0.87, eps=0.05):
    j_star = np.argmax(P[current_state])
    persistence = P[current_state, j_star]
    gap = abs(market_price - 0.5)
    return persistence >= tau and gap >= eps
```

---

## 4. Mise à jour bayésienne sur chocs de prix

```
P(H|D) = P(D|H) × P(H) / P(D)
```

En pratique : si le marché saute > 8% en 60 secondes sans explication dans l'orderbook → news quelque part. Repricing immédiat au lieu de saigner sur une position stale.

---

## 5. Kelly pour market making (Barbell Aniki)

**Market making side :**
```
f* = (p × b − q) / b
p = haute (taker prévisible), b = petit mais consistant → trader souvent, petite taille
```

**Lottery ticket side :**
```
p = négligeable, b = énorme → bet presque rien MAIS bet
```

Règle : p(lottery) × 400 > coût position → acheter. Sur les ranges extrêmes des marchés multi-range.

---

## 6. ARIMA + GARCH — Time series quant stack

**Test de stationnarité avant tout :**
```python
from statsmodels.tsa.stattools import adfuller
result = adfuller(returns)
# p-value < 0.05 → série stationnaire → modélisable
# Toujours modéliser les RETURNS, jamais les prix bruts
```

**Formule GARCH(1,1) pour sizing dynamique :**
```
σ²_t = ω + α₁ε²_(t-1) + β₁σ²_(t-1)
```
Quand σ²_t élevé → réduire la taille. Quand σ²_t bas → prendre plus de risque.

---

## 7. Slippage copy-trading (formule critique)

```python
def copy_check(whale_price, your_price, true_prob):
    ev_whale = true_prob * (1 - whale_price) - (1 - true_prob) * whale_price
    ev_you = true_prob * (1 - your_price) - (1 - true_prob) * your_price
    slippage = your_price - whale_price
    pct_eaten = (slippage / ev_whale * 100) if ev_whale > 0 else 999
    # > 70% mangé → RISQUÉ, 100%+ → SKIP
```

---

## 8. Filtre BTC 5-min — $25 gap threshold

Constat empirique (adiix_official, 24h de trading live) :
- Gap < $10 entre prix actuel et prix de début → flip de dernière seconde fréquent → **NE PAS ENTRER**
- Gap > $25 → résultat quasi-décidé, spikes ne traversent pas → **ENTRÉE SÛRE**
- Uniquement visible sur tick data live (le chart Polymarket lisse les micro-spikes)

---

## Liens

- [[becker-calibration-72m-trades]]
- [[claude-probability-oracle-prompt]]
- [[wallets-to-watch]]
- [[websocket-6-layer-system]]
