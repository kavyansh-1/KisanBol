"""Market intelligence: price trend, nearby-mandi comparison, demo data generators.

Demo generators are deterministic (seeded by crop, mandi and date) so a demo is repeatable,
and every consumer labels the result as demo data."""
from __future__ import annotations

import hashlib
import math
import random
from datetime import datetime, timedelta


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (la1, lo1), (la2, lo2) = a, b
    p1, p2 = math.radians(la1), math.radians(la2)
    dp, dl = p2 - p1, math.radians(lo2 - lo1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _rng(*parts) -> random.Random:
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return random.Random(int(digest[:12], 16))


def demo_series(crop: str, mandi: str, current: int, days: int = 7, today: datetime | None = None) -> list[dict]:
    """A plausible 7-day price walk that ends exactly at `current`."""
    today = today or datetime.now()
    r = _rng("series", crop, mandi, today.date())
    prices = [float(current)]
    for _ in range(days - 1):
        prices.append(prices[-1] / (1 + r.uniform(-0.012, 0.014)))
    prices = [round(p) for p in reversed(prices)]
    prices[-1] = current
    return [{"date": (today - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d"), "price": p}
            for i, p in enumerate(prices)]


def trend_stats(series: list[dict]) -> dict | None:
    if len(series) < 2 or not series[0]["price"]:
        return None
    first, last = series[0]["price"], series[-1]["price"]
    pct = (last - first) / first * 100
    return {"pct": round(pct, 1), "direction": "up" if pct > 1 else "down" if pct < -1 else "flat",
            "days": len(series)}


def demo_mandi_prices(crop: str, base: int, mandis, selected: str, today: datetime | None = None) -> dict[str, int]:
    today = today or datetime.now()
    out = {}
    for name in mandis:
        off = 0.0 if name == selected else _rng("mandi", crop, name, today.date()).uniform(-0.035, 0.04)
        out[name] = round(base * (1 + off))
    return out


def compare_mandis(selected: str, prices: dict[str, int], coords: dict[str, tuple[float, float]],
                   radius_km: float = 250, limit: int = 6) -> list[dict]:
    """Rows for the selected mandi and its neighbours, best price first."""
    if selected not in prices or selected not in coords:
        return []
    base = prices[selected]
    rows = []
    for name, price in prices.items():
        if name not in coords:
            continue
        dist = 0.0 if name == selected else haversine_km(coords[selected], coords[name])
        if dist > radius_km:
            continue
        rows.append({"mandi": name, "price": price, "distance_km": round(dist), "diff": price - base,
                     "diff_pct": round((price - base) / base * 100, 1), "selected": name == selected})
    rows.sort(key=lambda r: -r["price"])
    chosen = [r for r in rows if r["selected"]]
    chosen += [r for r in rows if not r["selected"]][: limit - 1]
    return sorted(chosen, key=lambda r: -r["price"])


def best_alternative(rows: list[dict], min_gain_pct: float = 2.0, max_km: float = 120) -> dict | None:
    cands = [r for r in rows if not r["selected"] and r["diff_pct"] >= min_gain_pct and r["distance_km"] <= max_km]
    return max(cands, key=lambda r: r["diff"]) if cands else None
