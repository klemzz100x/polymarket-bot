#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SC-010 — Weather Market Scanner.

Discovers active temperature markets on Polymarket using the slug pattern
described in @AlterEgo_eth's thread:

  slug: highest-temperature-in-{city}-on-{month}-{day}-{year}
  API:  GET https://gamma-api.polymarket.com/events?slug={slug}

Then cross-references current temperature forecasts against market prices
to find mispricings. Uses Open-Meteo API (free, no auth required).

Usage:
    PYTHONPATH=src python scripts/scan_weather_markets.py
    PYTHONPATH=src python scripts/scan_weather_markets.py --days 3 --cities all
    PYTHONPATH=src python scripts/scan_weather_markets.py --obsidian
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import httpx

from polybot.core.config import get_settings
from polybot.research.sizing import quarter_kelly_size

# Cities tracked by Polymarket (common ones)
# Source: discovered from Polymarket event slugs
CITIES: dict[str, dict] = {
    "Seoul": {"lat": 37.5665, "lon": 126.9780, "slug_name": "seoul"},
    "London": {"lat": 51.5074, "lon": -0.1278, "slug_name": "london"},
    "New York": {"lat": 40.7128, "lon": -74.0060, "slug_name": "new-york"},
    "Los Angeles": {"lat": 34.0522, "lon": -118.2437, "slug_name": "los-angeles"},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "slug_name": "tokyo"},
    "Paris": {"lat": 48.8566, "lon": 2.3522, "slug_name": "paris"},
    "Berlin": {"lat": 52.5200, "lon": 13.4050, "slug_name": "berlin"},
    "Sydney": {"lat": -33.8688, "lon": 151.2093, "slug_name": "sydney"},
    "Miami": {"lat": 25.7617, "lon": -80.1918, "slug_name": "miami"},
    "Chicago": {"lat": 41.8781, "lon": -87.6298, "slug_name": "chicago"},
}

GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def build_slug(city_slug: str, target_date: date) -> str:
    """Build Polymarket event slug for a temperature market."""
    month = target_date.strftime("%B").lower()  # "may", "june", etc.
    day = target_date.day
    year = target_date.year
    return f"highest-temperature-in-{city_slug}-on-{month}-{day}-{year}"


def parse_temperature_range(question_text: str) -> tuple[float, float]:
    """Extract temperature range from question text. Returns (lower, upper) in °C."""
    import re
    text = question_text.lower()

    # Pattern: "between X-Y°C" or "X to Y"
    range_match = re.search(r'between\s+(-?\d+(?:\.\d+)?)[–\-](-?\d+(?:\.\d+)?)', text)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    # Pattern: "X°C or higher" / "X or higher"
    higher_match = re.search(r'(-?\d+(?:\.\d+)?)\s*°?[cf]?\s+or\s+higher', text)
    if higher_match:
        return float(higher_match.group(1)), 999.0

    # Pattern: "X°C or lower" / "X or below"
    lower_match = re.search(r'(-?\d+(?:\.\d+)?)\s*°?[cf]?\s+or\s+(?:lower|below)', text)
    if lower_match:
        return -999.0, float(lower_match.group(1))

    # Pattern: "below X°C"
    below_match = re.search(r'below\s+(-?\d+(?:\.\d+)?)', text)
    if below_match:
        return -999.0, float(below_match.group(1))

    # Pattern: "above X°C"
    above_match = re.search(r'above\s+(-?\d+(?:\.\d+)?)', text)
    if above_match:
        return float(above_match.group(1)), 999.0

    # Fallback: single number in °C
    single = re.search(r'(-?\d+(?:\.\d+)?)\s*°c', text)
    if single:
        val = float(single.group(1))
        return val, val + 1.0

    return -999.0, 999.0  # Unknown range


async def fetch_event_markets(client: httpx.AsyncClient, slug: str) -> list[dict]:
    """Fetch markets for a temperature event by slug."""
    try:
        r = await client.get(GAMMA_EVENTS_URL, params={"slug": slug})
        if r.status_code != 200:
            return []
        data = r.json()
        if not data or not isinstance(data, list):
            return []
        event = data[0]
        return event.get("markets", [])
    except Exception:
        return []


async def fetch_forecast(client: httpx.AsyncClient, lat: float, lon: float, target_date: date) -> float | None:
    """Fetch max temperature forecast from Open-Meteo for a given date."""
    try:
        r = await client.get(
            OPEN_METEO_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max",
                "timezone": "auto",
                "forecast_days": 7,
            },
        )
        if r.status_code != 200:
            return None
        data = r.json()
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temps = daily.get("temperature_2m_max", [])
        target_str = target_date.isoformat()
        for d, t in zip(dates, temps):
            if d == target_str and t is not None:
                return float(t)
        return None
    except Exception:
        return None


def find_best_bucket(markets: list[dict], forecast_temp: float) -> dict | None:
    """Find the market bucket that matches the forecast temperature."""
    buckets = []
    for m in markets:
        question = str(m.get("question") or "")
        try:
            prices = json.loads(m.get("outcomePrices") or "[0.5, 0.5]")
            yes_price = float(prices[0])
        except Exception:
            continue
        lo, hi = parse_temperature_range(question)
        # Check if forecast falls in this bucket
        in_bucket = lo <= forecast_temp <= hi
        buckets.append({
            "question": question[:70],
            "condition_id": str(m.get("conditionId") or ""),
            "yes_price": round(yes_price, 4),
            "lower_bound": lo,
            "upper_bound": hi,
            "in_bucket": in_bucket,
            "edge": round((1.0 - yes_price) if in_bucket else 0.0, 4),  # YES should be ~1.0 if in bucket
        })
    buckets.sort(key=lambda x: x["lower_bound"])
    return buckets


async def run() -> int:
    parser = argparse.ArgumentParser(description="SC-010 Weather market scanner")
    parser.add_argument("--days", type=int, default=3, help="Days ahead to scan (today + N days)")
    parser.add_argument("--cities", type=str, default="all", help="Comma-separated city names, or 'all'")
    parser.add_argument("--min-edge", type=float, default=0.05, help="Min edge to report (default 5%%)")
    parser.add_argument("--bankroll", type=float, default=20.0, help="Total bankroll in USD for Kelly sizing")
    parser.add_argument("--obsidian", action="store_true")
    parser.add_argument("--json-out", type=Path, default=Path("tmp/weather_market_scan.json"))
    args = parser.parse_args()

    settings = get_settings()
    today = date.today()
    today_str = today.isoformat()

    print(f"\n{'='*70}")
    print(f"SC-010 WEATHER MARKET SCANNER — {today_str}")
    print(f"Days ahead: {args.days} | Min edge: {args.min_edge:.0%}")
    print(f"{'='*70}")

    # Select cities
    if args.cities.lower() == "all":
        cities = CITIES
    else:
        city_names = [c.strip() for c in args.cities.split(",")]
        cities = {k: v for k, v in CITIES.items() if k in city_names}

    scan_dates = [today + timedelta(days=i) for i in range(args.days + 1)]

    results: list[dict] = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for target_date in scan_dates:
            print(f"\n  Scanning {target_date.isoformat()}...")
            for city_name, city_info in cities.items():
                slug = build_slug(city_info["slug_name"], target_date)

                # Fetch markets by slug
                markets = await fetch_event_markets(client, slug)
                if not markets:
                    continue

                # Fetch forecast
                forecast = await fetch_forecast(client, city_info["lat"], city_info["lon"], target_date)

                print(f"    {city_name}: {len(markets)} buckets | forecast={forecast}°C" if forecast else f"    {city_name}: {len(markets)} buckets | forecast=N/A")

                if not markets:
                    continue

                # Analyze all buckets
                buckets = find_best_bucket(markets, forecast or -999.0)

                for b in buckets:
                    if b["in_bucket"] and forecast is not None:
                        # We have a forecast AND it matches this bucket
                        # Edge: YES should be close to 1.0 if our forecast is right
                        edge = 1.0 - b["yes_price"]  # potential gain if YES wins
                        if edge >= args.min_edge:
                            results.append({
                                "city": city_name,
                                "target_date": target_date.isoformat(),
                                "slug": slug,
                                "question": b["question"],
                                "condition_id": b["condition_id"],
                                "yes_price": b["yes_price"],
                                "forecast_temp": round(forecast, 1),
                                "bucket_low": b["lower_bound"],
                                "bucket_high": b["upper_bound"],
                                "edge": round(edge, 4),
                                "edge_pct": round(edge * 100, 2),
                                "signal": "BUY_YES",
                                "rationale": f"Forecast {forecast:.1f}°C falls in [{b['lower_bound']},{b['upper_bound']}] bucket. Market YES only at {b['yes_price']:.3f}.",
                            })
                    elif not b["in_bucket"] and b["yes_price"] > (1.0 - args.min_edge) and forecast is not None:
                        # Market overprices a bucket our forecast says is wrong
                        edge = b["yes_price"]  # potential gain if NO wins (bucket wrong)
                        results.append({
                            "city": city_name,
                            "target_date": target_date.isoformat(),
                            "slug": slug,
                            "question": b["question"],
                            "condition_id": b["condition_id"],
                            "yes_price": b["yes_price"],
                            "forecast_temp": round(forecast, 1),
                            "bucket_low": b["lower_bound"],
                            "bucket_high": b["upper_bound"],
                            "edge": round(edge, 4),
                            "edge_pct": round(edge * 100, 2),
                            "signal": "BUY_NO",
                            "rationale": f"Forecast {forecast:.1f}°C outside [{b['lower_bound']},{b['upper_bound']}]. Market YES at {b['yes_price']:.3f} — fade it.",
                        })

    results.sort(key=lambda x: x["edge"], reverse=True)

    # Compute Kelly sizing for each signal
    for r in results:
        edge_dec = r["edge"]  # already decimal (e.g., 0.85 for BUY_NO where yes_price=0.145)
        signal_price = r["yes_price"] if r["signal"] == "BUY_YES" else (1.0 - r["yes_price"])
        sz = quarter_kelly_size(edge_decimal=max(0.0, edge_dec), signal_price=signal_price, bankroll=args.bankroll)
        r["size_usd"] = sz.size_usd
        r["kelly_full_pct"] = sz.kelly_full_pct

    print(f"\n{'='*110}")
    print(f"{'#':<3} {'City':<12} {'Date':<12} {'Signal':>6} {'Price':>6} {'Edge%':>6} {'Size$':>6} {'Forecast':>9} {'Bucket':<25}")
    print(f"{'='*110}")

    for i, r in enumerate(results[:20], 1):
        bucket_str = f"[{r['bucket_low']:.0f}–{r['bucket_high']:.0f}]" if r["bucket_high"] < 900 else f"[{r['bucket_low']:.0f}+]"
        size_str = f"${r['size_usd']:.2f}" if r["size_usd"] > 0 else "  skip"
        print(
            f"{i:<3} {r['city']:<12} {r['target_date']:<12} "
            f"{r['signal']:>6} "
            f"{r['yes_price']:>6.3f} "
            f"{r['edge_pct']:>+5.2f}% "
            f"{size_str:>6} "
            f"{r['forecast_temp']:>7.1f}°C "
            f"{bucket_str:<25}"
        )

    if not results:
        print("No weather market opportunities found.")
        print("  Markets may not be active for these dates, or forecasts are aligned with market prices.")
        print("  Try: --days 5 --min-edge 0.02")
    else:
        best = results[0]
        print(f"\n⭐ BEST: [{best['signal']}] {best['city']} {best['target_date']}")
        print(f"   {best['rationale']}")
        print(f"   Size: ${best['size_usd']:.2f} | Kelly full: {best['kelly_full_pct']:.1f}% | Bankroll: ${args.bankroll:.0f}")

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON → {args.json_out}")

    if args.obsidian and results:
        from polybot.knowledge.obsidian import ObsidianVault
        vault = ObsidianVault(settings.obsidian_vault_dir)
        vault.ensure_structure()

        lines = [
            f"---",
            f"tags: [sc-010, weather, temperature, {today_str}]",
            f"date: {today_str}",
            f"opportunities: {len(results)}",
            f"cities_scanned: {len(cities)}",
            f"---",
            f"",
            f"# SC-010 Weather Markets — {today_str}",
            f"",
            f"**Villes** : {len(cities)} | **Jours** : {args.days} | **Opportunités** : {len(results)}",
            f"**Source forecasts** : Open-Meteo (température max journalière)",
            f"",
            f"## Technique (@AlterEgo_eth)",
            f"",
            f"Slug : `highest-temperature-in-{{city}}-on-{{month}}-{{day}}-{{year}}`",
            f"API : `GET gamma-api.polymarket.com/events?slug={{slug}}`",
            f"→ récupère tous les buckets de température avec leurs prix YES/NO",
            f"→ compare forecast Open-Meteo avec les buckets → edge si désalignement",
            f"",
        ]

        if results:
            lines += [
                f"## Opportunités",
                f"",
                f"| # | Ville | Date | Signal | Prix | Edge% | Forecast | Bucket |",
                f"|---|-------|------|--------|------|-------|----------|--------|",
            ]
            for i, r in enumerate(results[:20], 1):
                bucket_str = f"[{r['bucket_low']:.0f}–{r['bucket_high']:.0f}]" if r["bucket_high"] < 900 else f"[{r['bucket_low']:.0f}+]"
                lines.append(
                    f"| {i} | {r['city']} | {r['target_date']} | {r['signal']} | "
                    f"{r['yes_price']:.3f} | {r['edge_pct']:+.2f}% | {r['forecast_temp']:.1f}°C | {bucket_str} |"
                )
            best = results[0]
            lines += [
                f"",
                f"## Meilleure opportunité",
                f"",
                f"**[{best['signal']}] {best['city']} {best['target_date']}**",
                f"- {best['rationale']}",
                f"- Condition ID : `{best['condition_id']}`",
            ]
        else:
            lines.append("Aucune opportunité trouvée. Marchés weather peut-être non actifs pour ces dates.")

        lines.append(f"\n→ `{args.json_out}`")
        note_path = vault.write_note(
            "Research/Edge-Research",
            f"SC-010 Weather Markets {today_str}",
            "\n".join(lines),
            overwrite=True,
        )
        print(f"Obsidian → {note_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
