# Wallets à Surveiller — Polymarket

**Dernière mise à jour :** 2026-05-20  
**Source :** Extraction threads PDF — claims non audités sauf indication contraire

---

## Tier 1 — High conviction (architecture décrite, non juste un chiffre)

### @pbot-6 (0x_Punisher)
- **Profil :** https://polymarket.com/@pbot-6
- **Claim :** $100K PnL public
- **Architecture :** 6-layer websocket system décrit en détail → voir [[websocket-6-layer-system]]
- **Spécialité :** BTC 5-min markets, market making
- **Crédibilité :** Architecture cohérente et détaillée, profil public vérifiable

### @rn1 (RN1)
- **Profil :** https://polymarket.com/@rn1
- **Claim :** $8.9M PnL sur $66K en trades — ratio extraordinaire
- **Architecture :** Reverse-engineered par @L1vsun — 5 outils : raw CLOB WS + Claude probability + Kelly + Bayesian update + systemd
- **Spécialité :** Sports quant
- **Note :** Ce wallet est la base de la stratégie "5 tools" de @L1vsun. À étudier en priorité.

### 0xe1d6b51521bd4365769199f392f9818661bd907
- **Profil :** https://polymarket.com/profile/0xe1d6b51521bd4365769199f392f9818661bd907
- **Claim :** $728K en un mois (HFT crypto)
- **Spécialité :** HFT crypto markets
- **Note :** Adresse on-chain directe, vérifiable

---

## Tier 2 — Claims vérifiables, architecture partiellement décrite

### @sharky6999
- **Profil :** https://polymarket.com/@sharky6999
- **Claim :** 99.3% win rate, $840K PnL
- **Architecture :** Bot quant — formules Kelly + Becker calibration mentionnées
- **Note :** Win rate de 99.3% suspect — possible sur marchés near-certain (>95¢). À vérifier.

### @ozpreezy
- **Profil :** https://polymarket.com/@ozpreezy
- **Claim :** $29.3K, 106 trades, $120K positions ouvertes
- **Style :** Conviction plays, MicroStrategy + macro

### @xuanxuan008
- **Profil :** https://polymarket.com/@xuanxuan008
- **Claim :** 10,100 trades, biggest win $669
- **Style :** Volume machine, BTC 5-min markets exclusivement, 24/7 automatisé
- **Note :** Très intéressant — high frequency sur un seul type de marché

### @marketing101
- **Profil :** https://polymarket.com/@marketing101
- **Claim :** 3,777 trades, biggest win $24K (+614% sur un seul BTC entry)
- **Style :** Timing chirurgical sur BTC up/down

---

## Tier 3 — Top BTC 5-min bots (source @0xRicker)

Liste à surveiller pour pattern detection :

1. https://polymarket.com/@0x8dxd
2. https://polymarket.com/profile/0xf705fa045201391d9632b7f3cde06a5e24453ca7
3. https://polymarket.com/@k9q2mx4l8a7zp3r
4. https://polymarket.com/@justdance
5. https://polymarket.com/profile/0x1979ae6b7e6534de9c4539d0c205e582ca637c9d

---

## Aniki (non nommé explicitement)
- **Claim :** $700K+ PnL sur marchés tweets Elon Musk
- **Strategy :** Barbell — market making sur 30 ranges + lottery tickets sur extrêmes
- **Volume :** 1,700–2,900 trades par cycle hebdomadaire
- **Note :** Compte non identifié publiquement dans le thread. À chercher via Data API sur marchés Musk tweets.

---

## Comment monitorer un wallet

```python
# Voir [[api-endpoints-reference]] pour les endpoints complets
import httpx

def get_wallet_stats(address: str) -> dict:
    base_data = "https://data-api.polymarket.com"
    base_lb = "https://lb-api.polymarket.com"
    
    pnl = httpx.get(f"{base_lb}/profit?window=all&address={address}").json()
    positions = httpx.get(f"{base_data}/positions?user={address}&limit=500").json()
    activity = httpx.get(f"{base_data}/activity?user={address}&limit=500").json()
    
    return {"pnl": pnl, "positions": positions, "activity": activity}
```

---

## Red flags à ignorer

- Wallets avec un seul gros win et 80%+ de pertes → Sharpe proche de 0
- Claims sans profil public vérifiable
- "Voir mon channel Telegram pour copier" → promo pure

---

## Liens

- [[api-endpoints-reference]]
- [[becker-calibration-72m-trades]]
- [[quant-formulas-reference]]
