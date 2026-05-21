# Claude comme Oracle de Probabilité — Prompt Template

**Source :** @LunarResearcher (thread le plus complet sur le sujet)  
**Validation :** Architecture utilisée par @L1vsun (@rn1 reverse-engineer) — 87% de l'edge vient de ce seul call  
**Coût :** ~$0.003 par call, 50 marchés toutes les 90 secondes

---

## Prompt System (ne jamais modifier)

```
You are a prediction market calibration engine.
Your ONLY output is a JSON object. No explanation. No caveats.
```

## Prompt Template

```python
prompt = f"""
Analyze this Polymarket question:
"{market_question}"

Current market price: {market_price}
Category: {category}
Resolution date: {resolution_date}
Context: {news_context}

Return JSON:
{{
  "true_probability": <float 0-1, your calibrated estimate>,
  "confidence": <"low"|"medium"|"high">,
  "key_factors": [<top 3 factors affecting outcome>],
  "bias_flags": [<any detected narrative bias in market pricing>],
  "edge_direction": <"YES"|"NO"|"NONE">
}}

Calibration rules:
- Never output >0.97 or <0.03
- Apply reference class forecasting
- Weight base rates over narrative
- Flag if market price deviates >15% from your estimate
"""
```

## Code complet d'intégration

```python
import anthropic
import json

client = anthropic.Anthropic()

def get_claude_probability(
    market_question: str,
    market_price: float,
    category: str,
    resolution_date: str,
    news_context: str = ""
) -> dict:
    response = client.messages.create(
        model="claude-opus-4-5",  # Utiliser Opus pour la calibration
        max_tokens=1024,
        system="You are a prediction market calibration engine. Output ONLY valid JSON.",
        messages=[{"role": "user", "content": prompt}]
    )
    result = json.loads(response.content[0].text)
    # Appliquer correction Becker APRÈS l'estimation Claude — deux opérations distinctes
    result["corrected_probability"] = apply_longshot_correction(result["true_probability"])
    result["kelly_recommendation"] = kelly_size(
        p_model=result["true_probability"],
        market_price=market_price,
        bankroll=1000  # normaliser à $1000
    )
    return result
```

---

## Architecture 3 couches (ne pas fusionner)

```
Layer 1 : Market price → consensus du marché, biaisé
Layer 2 : Claude probability → prior calibré, indépendant des news
Layer 3 : Corrected probability → ajusté pour biais Becker

Trade le gap entre Layer 1 et Layer 3.
Si |Layer3 - Layer1| > 8% → signal actionnable.
```

---

## Filtre d'entrée scanner complet

```python
def run_polymarket_scanner(markets, bankroll, min_edge=0.08, min_volume=50_000):
    signals = []
    for market in markets:
        # Filtres durs
        if market["volume"] < min_volume:
            continue
        if not (0.10 <= market["price"] <= 0.40):  # Zone longshot bias maximale
            continue
        
        claude_result = get_claude_probability(
            market_question=market["question"],
            market_price=market["price"],
            category=market["category"],
            resolution_date=market["end_date"],
        )
        
        if claude_result["confidence"] == "low":
            continue
        
        corrected = apply_longshot_correction(claude_result["true_probability"])
        edge = corrected - market["price"]
        
        if abs(edge) < min_edge:
            continue
        
        # ... Kelly sizing + append signal
```

---

## Notes importantes

- **Ne pas fusionner** `apply_longshot_correction` avec le prompt Claude : deux opérations indépendantes
- Modèle recommandé : `claude-opus-4-5` pour la calibration (meilleure précision des priors)
- Appeler toutes les 90 secondes sur 50 marchés → $0.003 × 50 × 40 calls/heure = $6/heure max
- Si confidence = "low" → skip obligatoire, ne pas forcer

---

## Liens

- [[becker-calibration-72m-trades]]
- [[quant-formulas-reference]]
