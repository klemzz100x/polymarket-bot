"""Becker calibration + Claude probability oracle signal detector.

Based on: Jonathan Becker's 72M trade dataset (Polymarket + Kalshi)
Structural insight: YES contracts <50¢ are systematically overpriced.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Empirical win rates from Becker's 72M trade dataset
# Key: market price (float), Value: actual resolution rate
BECKER_TABLE: dict[float, float] = {
    0.01: 0.0043,
    0.05: 0.0418,
    0.10: 0.0890,
    0.20: 0.1940,
    0.30: 0.2950,
    0.50: 0.4980,
    0.70: 0.7050,
    0.80: 0.8140,
    0.90: 0.9120,
    0.95: 0.9610,
}

_PRICES = np.array(sorted(BECKER_TABLE.keys()))
_RATES = np.array([BECKER_TABLE[p] for p in _PRICES])


def becker_correction(market_price: float) -> float:
    """Return the empirically calibrated true win rate for a given market price."""
    return float(np.interp(market_price, _PRICES, _RATES))


def becker_edge(market_price: float, side: str = "YES") -> float:
    """Compute EV-based edge after Becker correction.

    Positive = trade has structural edge. Negative = avoid.
    """
    true_rate = becker_correction(market_price)
    if side == "YES":
        return true_rate - market_price
    else:  # NO
        return (1 - true_rate) - (1 - market_price)


@dataclass
class OracleSignal:
    condition_id: str
    question: str
    outcome: str
    market_price: float
    volume_usd: float
    becker_true_rate: float
    becker_edge: float
    recommended_side: str
    claude_prob: float | None = None
    claude_corrected_prob: float | None = None
    claude_edge: float | None = None
    claude_confidence: str | None = None
    claude_key_factors: list[str] | None = None
    combined_edge: float | None = None  # max(becker, claude) when both available

    @property
    def final_edge(self) -> float:
        if self.claude_edge is not None:
            return self.claude_edge
        return self.becker_edge

    @property
    def kelly_quarter(self) -> float:
        """Quarter-Kelly bet fraction."""
        if self.recommended_side not in ("YES", "NO"):
            return 0.0
        yes_true_rate = self.claude_corrected_prob if self.claude_corrected_prob is not None else self.becker_true_rate
        if self.recommended_side == "YES":
            p = yes_true_rate
            price = self.market_price
        else:
            p = 1.0 - yes_true_rate  # NO win probability
            price = 1.0 - self.market_price
        b = (1 - price) / price if price > 0 else 0
        q = 1 - p
        f_full = (p * b - q) / b if b > 0 else 0
        return max(0.0, f_full * 0.25)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "question": self.question[:80],
            "outcome": self.outcome,
            "market_price": round(self.market_price, 4),
            "volume_usd": round(self.volume_usd, 0),
            "becker_true_rate": round(self.becker_true_rate, 4),
            "becker_edge": round(self.becker_edge, 4),
            "recommended_side": self.recommended_side,
            "claude_prob": round(self.claude_prob, 4) if self.claude_prob is not None else None,
            "claude_corrected_prob": round(self.claude_corrected_prob, 4) if self.claude_corrected_prob is not None else None,
            "claude_edge": round(self.claude_edge, 4) if self.claude_edge is not None else None,
            "claude_confidence": self.claude_confidence,
            "claude_key_factors": self.claude_key_factors,
            "final_edge": round(self.final_edge, 4),
            "kelly_quarter": round(self.kelly_quarter, 4),
        }


def scan_becker(
    markets: list[dict[str, Any]],
    min_volume: float = 50_000,
    price_low: float = 0.10,
    price_high: float = 0.40,
    min_becker_edge: float = 0.01,
) -> list[OracleSignal]:
    """Apply Becker correction to a list of market dicts and return ranked signals.

    Each market dict must have: condition_id, question, outcome, price, volume.
    """
    signals: list[OracleSignal] = []

    for m in markets:
        price = float(m["price"])
        volume = float(m.get("volume", 0))

        if volume < min_volume:
            continue
        if not (price_low <= price <= price_high):
            continue

        true_rate = becker_correction(price)
        yes_edge = becker_edge(price, "YES")
        no_edge = becker_edge(price, "NO")

        # Structural bias: YES is overpriced below 50¢ → NO has positive edge
        best_side = "NO" if no_edge > yes_edge else "YES"
        best_edge = max(yes_edge, no_edge)

        if best_edge < min_becker_edge:
            continue

        signals.append(OracleSignal(
            condition_id=m["condition_id"],
            question=m["question"],
            outcome=m.get("outcome", ""),
            market_price=price,
            volume_usd=volume,
            becker_true_rate=true_rate,
            becker_edge=best_edge,
            recommended_side=best_side,
        ))

    return sorted(signals, key=lambda s: s.becker_edge, reverse=True)


def enrich_with_claude(
    signals: list[OracleSignal],
    api_key: str,
    model: str = "claude-haiku-4-5-20251001",
    resolution_date: str = "",
) -> list[OracleSignal]:
    """Call Claude oracle for each signal and enrich with per-market probability."""
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed")
        return signals

    client = anthropic.Anthropic(api_key=api_key)
    enriched: list[OracleSignal] = []

    for sig in signals:
        try:
            prompt = f"""Analyze this Polymarket question:
"{sig.question}"

Current market price: {sig.market_price:.2%}
Outcome being evaluated: {sig.outcome}
Resolution date: {resolution_date or "unknown"}

Return JSON only:
{{
  "true_probability": <float 0-1, your calibrated estimate>,
  "confidence": <"low"|"medium"|"high">,
  "key_factors": [<top 3 factors, strings>],
  "bias_flags": [<detected narrative biases>],
  "edge_direction": <"YES"|"NO"|"NONE">
}}

Rules:
- Never output >0.97 or <0.03
- Apply reference class forecasting
- Weight base rates over narrative
- Flag if market price deviates >15% from your estimate"""

            response = client.messages.create(
                model=model,
                max_tokens=512,
                temperature=0.1,  # low temp for reproducible probability estimates
                system="You are a prediction market calibration engine. Output ONLY valid JSON. No explanation. No markdown.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text.strip()
            # strip markdown code fences if model wraps JSON
            json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            result = json.loads(json_match.group(0) if json_match else raw_text)
            raw_prob = float(result.get("true_probability", sig.market_price))
            corrected = becker_correction(raw_prob)  # calibrated YES probability
            edge_direction = result.get("edge_direction", sig.recommended_side)

            if edge_direction == "YES":
                claude_edge_val = corrected - sig.market_price
            elif edge_direction == "NO":
                claude_edge_val = (1.0 - corrected) - (1.0 - sig.market_price)
            else:  # NONE — Claude sees no edge
                claude_edge_val = 0.0

            enriched.append(OracleSignal(
                condition_id=sig.condition_id,
                question=sig.question,
                outcome=sig.outcome,
                market_price=sig.market_price,
                volume_usd=sig.volume_usd,
                becker_true_rate=sig.becker_true_rate,
                becker_edge=sig.becker_edge,
                recommended_side=edge_direction,
                claude_prob=raw_prob,
                claude_corrected_prob=corrected,
                claude_edge=claude_edge_val,
                claude_confidence=result.get("confidence"),
                claude_key_factors=result.get("key_factors", []),
            ))
            logger.info("oracle_enriched q=%s edge=%.4f", sig.question[:60], claude_edge_val)

        except Exception as exc:
            logger.warning("oracle_error q=%s err=%s", sig.question[:60], str(exc))
            enriched.append(sig)

    return sorted(enriched, key=lambda s: s.final_edge, reverse=True)
