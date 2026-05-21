# Becker Calibration — 72M Trades Empirical Data

**Source :** Jonathan Becker, étude sur 72.1M trades / $18.26B volume Polymarket + Kalshi  
**Thread :** @0xMovez, @LunarResearcher  
**Statut :** Vérifiable — chiffres cohérents entre deux threads indépendants

---

## Longshot Bias Table — Prix marché vs taux de résolution réel

| Prix marché (¢) | Proba implicite | Taux réel YES | Écart | Signal |
|---|---|---|---|---|
| 1¢ | 1.00% | 0.43% | -57% | **FADE YES fort** |
| 5¢ | 5.00% | 4.18% | -16% | FADE YES |
| 10¢ | 10.00% | 8.90% | -11% | FADE YES |
| 20¢ | 20.00% | 18.50% | -7.5% | FADE YES |
| 30¢ | 30.00% | 29.50% | -1.7% | Neutre |
| 50¢ | 50.00% | 49.80% | -0.4% | **Neutre** |
| 70¢ | 70.00% | 70.50% | +0.7% | BUY YES |
| 80¢ | 80.00% | 81.40% | +1.75% | BUY YES |
| 90¢ | 90.00% | 91.20% | +1.3% | BUY YES |
| 95¢ | 95.00% | 96.10% | +1.2% | BUY YES |

**Règle clé :** En dessous de 50¢ → contrats YES systématiquement surévalués. Au-dessus de 80¢ → contrats YES sous-évalués.

**YES vs NO asymétrie :** À 1¢, YES retourne 43¢ pour $1 investi. NO retourne 77¢. **NO outperform YES sur 69 des 99 niveaux de prix.**

---

## Code — Correction Longshot Bias

```python
LONGSHOT_BIAS_TABLE = {
    0.01: 0.0043, 0.05: 0.0418, 0.10: 0.0890, 0.20: 0.1940,
    0.30: 0.2950, 0.50: 0.4980, 0.70: 0.7050, 0.80: 0.8140,
    0.90: 0.9120, 0.95: 0.9610,
}

def apply_longshot_correction(raw_prob: float) -> float:
    import numpy as np
    prices = np.array(sorted(LONGSHOT_BIAS_TABLE.keys()))
    corrected = np.array([LONGSHOT_BIAS_TABLE[p] for p in prices])
    return float(np.interp(raw_prob, prices, corrected))
```

---

## Implications pour le bot

1. **Ne jamais acheter YES < 10¢** sans edge fondamental exceptionnel
2. **Privilégier NO sur les longshots** (1-20¢) — asymétrie favorable
3. **Zone d'intérêt principale :** contrats 10-40¢ où le biais est maximal et exploitable
4. **Filtre minimal :** volume > $50K avant de scanner cette zone

---

## Wallets qui utilisent ce framework

- [[wallets-to-watch]] — @sharky6999, @rn1, @ozpreezy
