"""Indian-language helpers: script detection, quantity parsing, lakh/crore formatting."""
from __future__ import annotations

import re

from locales import REGISTRY as _LOCALES

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_GURMUKHI = re.compile(r"[਀-੿]")
_SCRIPTS = {"gu-IN": re.compile(r"[઀-૿]"), "bn-IN": re.compile(r"[ঀ-৿]"),
            "ta-IN": re.compile(r"[஀-௿]"), "te-IN": re.compile(r"[ఀ-౿]")}
_PUNJABI_ROMAN = {"tusi", "tuhada", "tuhade", "kinna", "kithe", "dasso", "vech", "hanji", "mainu",
                  "sanu", "menu", "kiven", "hunn", "ethe", "othe"}
_HINGLISH = {"ka", "ki", "ke", "ko", "hai", "hain", "mein", "kya", "kitna", "kitne", "bech", "becho",
             "rakh", "bhav", "bhaav", "abhi", "aur", "chal", "raha", "karun", "doon", "gehu", "chawal",
             "dhan", "sarson", "lun", "bataiye", "batao", "kab", "nahi"}


def detect_language(text: str) -> str:
    """Return hi-IN, pa-IN or en-IN for the *reply*, from script first, then romanised hints."""
    for code, rng in _SCRIPTS.items():
        if len(rng.findall(text)) > 0:
            return code
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
    units = {"en-IN": ("Crore", "Lakh", "rupees"), "hi-IN": ("करोड़", "लाख", "रुपये"), "pa-IN": ("ਕਰੋੜ", "ਲੱਖ", "ਰੁਪਏ")}
    units.update({code: m.UNITS for code, m in _LOCALES.items()})
    unit = units.get(lang, ("Crore", "Lakh", "rupees"))
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
_QTY_EXTRA = [w for m in _LOCALES.values() for w in m.QTY_WORDS]
_TON_EXTRA = [w for m in _LOCALES.values() for w in m.TON_WORDS]
_UNIT = (r"(quintals?|quintl|kwintal|qtl|क्विंटल|क्वंटल|कुंतल|ਕੁਇੰਟਲ|tons?|tonnes?|टन|ਟਨ"
         + "".join("|" + re.escape(w) for w in sorted(_QTY_EXTRA + _TON_EXTRA, key=len, reverse=True)) + ")")
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
    if unit.startswith(("ton", "टन", "ਟਨ", *_TON_EXTRA)):
        value *= 10
    return float(value) if value > 0 else None


_DAY_NUMS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
             "ten": 10, "twelve": 12, "fifteen": 15, "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5,
             "panch": 5, "chhe": 6, "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "barah": 12, "pandrah": 15,
             "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8, "नौ": 9,
             "दस": 10, "बारह": 12, "पंद्रह": 15, "ਇੱਕ": 1, "ਦੋ": 2, "ਤਿੰਨ": 3, "ਚਾਰ": 4, "ਪੰਜ": 5, "ਛੇ": 6, "ਸੱਤ": 7,
             "ਅੱਠ": 8, "ਨੌਂ": 9, "ਦਸ": 10}
# "day" in the languages we support (extended by the locale modules)
DAY_WORDS: list[str] = ["days", "day", "din", "dino", "दिन", "दिनों", "ਦਿਨ", "ਦਿਨਾਂ"]
WEEK_WORDS: list[str] = ["week", "weeks", "hafta", "hafte", "हफ्ता", "हफ्ते", "सप्ताह", "ਹਫ਼ਤਾ", "ਹਫ਼ਤੇ"]
for _m in _LOCALES.values():
    DAY_WORDS.extend(_m.DAY_WORDS)
    WEEK_WORDS.extend(_m.WEEK_WORDS)


def parse_days(text: str) -> int | None:
    """'in five days' / '12 din' / 'next week' -> 5 / 12 / 7. None when no horizon is mentioned."""
    low = text.lower()
    nums = "|".join(sorted(map(re.escape, _DAY_NUMS), key=len, reverse=True))
    unit = "|".join(sorted(map(re.escape, DAY_WORDS), key=len, reverse=True))
    m = re.search(rf"(\d+|{nums})\s*[-\s]?\s*(?:{unit})", low)
    if m:
        raw = m.group(1)
        value = int(raw) if raw.isdigit() else _DAY_NUMS.get(raw)
        if value and 1 <= value <= 90:
            return value
    if any(re.search(rf"(?:^|\W){re.escape(w)}(?:\W|$)", low) if w.isascii() else w in low for w in WEEK_WORDS):
        m2 = re.search(rf"(\d+|{nums})\s*[-\s]?\s*(?:{'|'.join(map(re.escape, WEEK_WORDS))})", low)
        if m2:
            raw = m2.group(1)
            v = int(raw) if raw.isdigit() else _DAY_NUMS.get(raw, 1)
            return min(7 * v, 90)
        return 7
    return None
