"""Indian-language helpers: script detection, quantity parsing, lakh/crore formatting."""
from __future__ import annotations

import re

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_GURMUKHI = re.compile(r"[਀-੿]")
_PUNJABI_ROMAN = {"tusi", "tuhada", "tuhade", "kinna", "kithe", "dasso", "vech", "hanji", "mainu",
                  "sanu", "menu", "kiven", "hunn", "ethe", "othe"}
_HINGLISH = {"ka", "ki", "ke", "ko", "hai", "hain", "mein", "kya", "kitna", "kitne", "bech", "becho",
             "rakh", "bhav", "bhaav", "abhi", "aur", "chal", "raha", "karun", "doon", "gehu", "chawal",
             "dhan", "sarson", "lun", "bataiye", "batao", "kab", "nahi"}


def detect_language(text: str) -> str:
    """Return hi-IN, pa-IN or en-IN for the *reply*, from script first, then romanised hints."""
    g, d = len(_GURMUKHI.findall(text)), len(_DEVANAGARI.findall(text))
    if g > d and g > 0:
        return "pa-IN"
    if d > 0:
        return "hi-IN"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & _PUNJABI_ROMAN:
        return "pa-IN"
    if words & _HINGLISH:
        return "hi-IN"
    return "en-IN"


def indian_group(n: int) -> str:
    """2275 -> '2,275'; 227500 -> '2,27,500'."""
    s, neg = str(abs(int(n))), n < 0
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return ("-" if neg else "") + s


def _trim(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def amount_words(amount: int, lang: str = "en-IN") -> str:
    """Speakable rupee amount: 120000 -> '1.2 Lakh rupees' / '1.2 लाख रुपये'."""
    unit = {"en-IN": ("Crore", "Lakh", "rupees"), "hi-IN": ("करोड़", "लाख", "रुपये"),
            "pa-IN": ("ਕਰੋੜ", "ਲੱਖ", "ਰੁਪਏ")}.get(lang, ("Crore", "Lakh", "rupees"))
    if amount >= 10_000_000:
        return f"{_trim(amount / 10_000_000)} {unit[0]} {unit[2]}"
    if amount >= 100_000:
        return f"{_trim(amount / 100_000)} {unit[1]} {unit[2]}"
    return f"₹{indian_group(amount)}"


_NUM_WORDS = {"ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5, "das": 10, "bees": 20,
              "tees": 30, "chalis": 40, "pachas": 50, "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
              "sau": 100, "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "दस": 10, "बीस": 20,
              "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
              "सौ": 100}
_UNIT = r"(quintals?|quintl|kwintal|qtl|क्विंटल|क्वंटल|कुंतल|ਕੁਇੰਟਲ|tons?|tonnes?|टन|ਟਨ)"
_QTY = re.compile(r"(\d[\d,]*(?:\.\d+)?|" + "|".join(sorted(map(re.escape, _NUM_WORDS), key=len, reverse=True))
                  + r")\s*" + _UNIT, re.I)


def parse_quantity(text: str) -> float | None:
    """Quantity in quintals from phrases like '50 quintal', 'pachas quintal', '2 ton'."""
    m = _QTY.search(text.lower())
    if not m:
        return None
    raw, unit = m.group(1), m.group(2)
    value = _NUM_WORDS.get(raw)
    if value is None:
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            return None
    if unit.startswith(("ton", "टन", "ਟਨ")):
        value *= 10
    return float(value) if value > 0 else None
