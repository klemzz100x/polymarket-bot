---
tags: [oracle, becker, claude, signals, 2026-05-21]
date: 2026-05-21
scan_type: becker+claude
markets_scanned: 68
signals_found: 9
actionable: 5
threshold_cl_edge: 3%
---

# Oracle Scan — 2026-05-21

**Méthode** : Becker calibration (72M trades) + Claude oracle (Haiku 4.5)  
**Univers** : 68 outcomes, prix 10–40%, volume >$20k  
**Signaux Becker** : 9 (edge >1%)  
**Signaux actionnables Claude** : 5 (edge >3%, confiance medium+)

---

## Signaux actionnables

### 1. Declan Rice NO — Ballon d'Or 2026
- **Prix marché** : 10.2% | **Side** : NO | **Prix trade** : 89.8¢
- **Claude edge** : +5.08% | **Kelly¼** : 12.44% | **Volume** : $54k
- **Confiance** : medium
- **Raisonnement** : Seulement 2 milieux défensifs ont gagné en 20 ans (Cannavaro 2006, Modric 2018). Rice aurait besoin d'une saison exceptionnelle + victoire en Champions League. Base rate ~3-5%.
- **condition_id** : `0x36d6b5a0d75f0759c747b41afb84d86fff70db2b2eebaeb3bea92fe444de934f`

### 2. Byron Donalds NO — Gouverneur Floride (primaires Rep.)
- **Prix marché** : 12.0% | **Side** : NO | **Prix trade** : 88¢
- **Claude edge** : +4.99% | **Kelly¼** : 10.39% | **Volume** : $120k
- **Confiance** : medium
- **Raisonnement** : Les membres de la Chambre gagnent rarement les primaires gouvernatoriales sans expérience exécutive. La Floride favorise les candidats établis (CFO, gouverneurs). Base rate ~5-12%.
- **condition_id** : `0xd4a3de1964b1f3fa1edeca40dbc3ef6663a56fda84e804066c23096b615904f9`

### 3. Metamask FDV >$2B NO — Jour du lancement
- **Prix marché** : 11.0% | **Side** : NO | **Prix trade** : 89¢
- **Claude edge** : +3.99% | **Kelly¼** : 9.06% | **Volume** : $382k
- **Confiance** : medium
- **Raisonnement** : $2B FDV en 24h est un seuil extrêmement élevé. Les tokens wallet/infrastructure dépassent rarement ce niveau rapidement. Base rate <10%.
- **condition_id** : `0x77399fdf6c5097661705ee1fcf8ad615721ea5dd695871dcae2c9eb192a3d75b`

### 4. Lamine Yamal NO — Ballon d'Or 2026
- **Prix marché** : 10.0% | **Side** : NO | **Prix trade** : 90¢
- **Claude edge** : +3.93% | **Kelly¼** : 9.83% | **Volume** : $81k
- **Confiance** : medium
- **Raisonnement** : À 19 ans en 2026, Yamal serait parmi les plus jeunes jamais vainqueurs. Seul Pelé a gagné à un âge comparable. Les vainqueurs modernes ont 23-29 ans.
- **condition_id** : `0xa34edb6c898232378a9cc08744842df2cd89d278ba45b012bed3ac10c7241c4d`

### 5. Angleterre NO — Coupe du Monde 2026 ⭐ MEILLEURE OPPORTUNITÉ
- **Prix marché** : 11.35% | **Side** : NO | **Prix trade** : 88.65¢
- **Claude edge** : +3.87% | **Kelly¼** : 8.52% | **Volume** : $18.3M 🔥
- **Confiance** : medium
- **Raisonnement** : Aucune victoire en Coupe du Monde depuis 1966. Classement mondial 4-6ème. Historique de défaillances en phases finales. Base rate France/Argentine/Brésil = 12-15% chacun, donc ~40-45% pour le top 3 = England devrait être ~7-9%.
- **condition_id** : `0x375409bc5eeeff961e82b479caeccc20f33d15738e5bce1186d628aa3d9dfb1f`
- **NOTE** : Meilleure opportunité en raison de la liquidité exceptionnelle ($18M). Facile à exécuter en maker.

---

## Signal négatif notable (marché surestimé)

### Hunter Biden Presidential Run YES — HIGH CONFIDENCE AVOID
- **Prix marché** : 11.25% | Claude dit : ~4% vrai
- **Claude edge** : -8.01% (marché très surestimé côté YES)
- **Confiance** : high
- **Raisonnement** : Pas de track record politique, forte exposition légale, base rate <1% pour ce profil.
- Si tu avais déjà une position YES → sortir.

---

## Analyse de l'univers

```
Prix couvert : 10–40%
Seuil Becker : >1% edge
Seuil Claude : >3% edge, confiance medium+

Signaux retenus : 5/68 outcomes = 7.4% taux de signal
Tous les signaux actionnables sont côté NO
Pattern : le marché surévalue systématiquement les YES dans la plage 10-12%
Confirmation de la thèse Becker : YES contracts <50¢ sont structurellement trop chers
```

---

## Notes d'exécution

**Si tu veux agir sur ces signaux en maker :**
1. Poster des ordres NO limit au prix actuel (ou légèrement mieux)
2. Fees = 0% en maker → edge net = edge brut
3. Sizing suggéré : Kelly¼ × bankroll (ex: 1000€ × 8.52% = 85€ sur England NO)
4. Priorité : England NO (liquidité $18M) puis Metamask NO ($382k volume)

**Risques à noter :**
- Confiance = "medium" pour tous les signaux (pas "high") → sizing conservateur recommandé
- La Coupe du Monde 2026 commence en juin → time horizon court
- Metamask launch est un event-driven signal → peut changer rapidement

---

## Raw JSON
→ `tmp/becker_oracle_scan.json`
