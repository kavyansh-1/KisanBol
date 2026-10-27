"""KisanBol core engine (channel-agnostic: used by the Streamlit app and the REST API).

Pipeline:  audio -> Prisma STT -> Evon entity extraction (rule-based fallback)
           -> tools: Agmarknet prices + Open-Meteo weather
           -> market intelligence: 7-day trend, nearby mandis, crop value
           -> SELL NOW / HOLD decision -> advice text -> Timbre TTS audio

Every external call degrades gracefully and records a warning, so the system keeps working
(and says what it fell back to) when a service is slow, unconfigured or down."""
from __future__ import annotations

import base64
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

import audio_utils
import i18n
import indic
import market_intel as mi

load_dotenv()

# --------------------------------------------------------------------------
# Configuration (all overridable from .env)
# --------------------------------------------------------------------------
GNANI_BASE_URL = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai")
STT_PATH, TTS_PATH = "/stt/v3", "/api/v1/tts/inference"
TTS_MODEL = os.getenv("TTS_MODEL", "timbre-v2.5")
TTS_VOICE = os.getenv("TTS_VOICE", "Nalini")
TTS_SAMPLE_RATE = int(os.getenv("TTS_SAMPLE_RATE", "22050"))
ENABLE_TTS_TAGS = os.getenv("ENABLE_TTS_TAGS", "false").lower() == "true"

EVON_BASE_URL = os.getenv("EVON_BASE_URL", "").rstrip("/")
EVON_MODEL = os.getenv("EVON_MODEL", "gnani/gnani-evon-v3.3-30B-A3B")
EVON_API_KEY = os.getenv("EVON_API_KEY", "EMPTY")

AGMARKNET_API_KEY = os.getenv("DATA_GOV_IN_API_KEY", "")
AGMARKNET_RESOURCE_ID = os.getenv("AGMARKNET_RESOURCE_ID", "9ef84268-d588-465a-a308-a864a43d0070")

RAIN_THRESHOLD = int(os.getenv("RAIN_THRESHOLD", "70"))
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "600"))

LANGUAGES = {"auto": "Auto-detect", "hi-IN": "Hindi", "pa-IN": "Punjabi", "en-IN": "English"}


class KisanBolError(Exception):
    """An error with a translation key (see i18n.py, `err.<key>`) so the UI can show it in the farmer's language.
    `detail` carries technical information for logs and is never shown in the UI."""

    def __init__(self, key: str, detail: str = "", **params):
        self.key, self.detail, self.params = key, detail, params
        super().__init__(i18n.t("en-IN", "err." + key, **params) + (f" ({detail})" if detail else ""))

    def localized(self, lang: str) -> str:
        return i18n.t(lang, "err." + self.key, **self.params)


@dataclass
class Note:
    """A data note. Public keys (i18n.PUBLIC_NOTES) are shown to the farmer, `dev_*` keys are for developers."""
    key: str
    params: dict = field(default_factory=dict)

    @property
    def public(self) -> bool:
        return self.key in i18n.PUBLIC_NOTES

    def text(self, lang: str = "en-IN") -> str:
        return i18n.t(lang, ("note." if self.public else "") + self.key, **self.params)

    def __str__(self) -> str:
        return self.text()


# --------------------------------------------------------------------------
# Data classes
# --------------------------------------------------------------------------
@dataclass
class Entities:
    crop: str | None = None
    mandi: str | None = None
    intent: str = "sell_or_hold"
    quantity: float | None = None  # quintals


@dataclass
class MarketPrice:
    crop: str
    mandi: str
    modal: int
    min: int | None
    max: int | None
    date: str
    source: str  # "agmarknet" or "demo"


@dataclass
class Weather:
    daily: list[dict]  # [{"date", "rain_prob", "rain_mm", "tmax"}]
    max_rain_prob: int
    source: str = "open-meteo"  # or "scenario"


@dataclass
class Verdict:
    label: str  # "SELL NOW", "HOLD", "NO DATA"
    reason: str  # English text; the UI re-renders it from `code` in the chosen language
    confidence: str = "n/a"  # High / Medium / Low
    code: str = "no_entities"  # sell | hold | no_weather | no_entities
    rain: int = 0
    threshold: int = 70


@dataclass
class Insights:
    trend: list[dict] = field(default_factory=list)
    trend_source: str = "demo"
    trend_pct: float | None = None
    trend_direction: str | None = None
    nearby: list[dict] = field(default_factory=list)
    nearby_source: str = "demo"
    best_alt: dict | None = None
    quantity: float | None = None
    revenue: int | None = None
    signals: list[dict] = field(default_factory=list)  # [{"tone": "red|green|amber|grey", "text": ...}]


@dataclass
class KisanBolResult:
    transcript: str
    entities: Entities
    price: MarketPrice | None
    weather: Weather | None
    verdict: Verdict
    insights: Insights
    advice_text: str
    audio: bytes | None
    language: str  # reply language actually used
    needs_clarification: bool = False
    used_context: list[str] = field(default_factory=list)
    warnings: list = field(default_factory=list)
    timings: dict = field(default_factory=dict)

    def to_dict(self, include_audio: bool = True) -> dict:
        d = {"transcript": self.transcript, "entities": self.entities.__dict__,
             "price": self.price.__dict__ if self.price else None,
             "weather": {"daily": self.weather.daily, "max_rain_prob": self.weather.max_rain_prob,
                         "source": self.weather.source} if self.weather else None,
             "verdict": self.verdict.__dict__, "insights": self.insights.__dict__,
             "advice_text": self.advice_text, "language": self.language,
             "needs_clarification": self.needs_clarification, "used_context": self.used_context,
             "warnings": [str(w) for w in self.warnings], "timings": self.timings}
        if include_audio and self.audio:
            d["audio_base64"] = base64.b64encode(self.audio).decode()
        return d


# --------------------------------------------------------------------------
# Domain tables
# --------------------------------------------------------------------------
CROP_ALIASES = {
    "wheat": ["wheat", "gehu", "gehun", "gehoon", "kanak", "गेहूं", "गेहूँ", "गेहु", "गेंहू", "ਕਣਕ"],
    "paddy": ["paddy", "dhan", "dhaan", "धान", "ਝੋਨਾ"],
    "rice": ["rice", "chawal", "chaawal", "चावल", "ਚੌਲ"],
    "maize": ["maize", "makka", "makki", "corn", "मक्का", "ਮੱਕੀ"],
    "mustard": ["mustard", "sarson", "sarso", "सरसों", "ਸਰ੍ਹੋਂ"],
    "cotton": ["cotton", "kapas", "narma", "कपास", "ਕਪਾਹ"],
    "potato": ["potato", "aloo", "aalu", "आलू", "ਆਲੂ"],
    "onion": ["onion", "pyaz", "pyaaz", "प्याज", "ਪਿਆਜ਼"],
    "tomato": ["tomato", "tamatar", "टमाटर", "ਟਮਾਟਰ"],
}
AGMARKNET_COMMODITY = {"wheat": "Wheat", "paddy": "Paddy(Dhan)(Common)", "rice": "Rice", "maize": "Maize",
                       "mustard": "Mustard", "cotton": "Cotton", "potato": "Potato", "onion": "Onion",
                       "tomato": "Tomato"}
CROP_DISPLAY = {
    "hi-IN": {"wheat": "गेहूं", "paddy": "धान", "rice": "चावल", "maize": "मक्का", "mustard": "सरसों",
              "cotton": "कपास", "potato": "आलू", "onion": "प्याज", "tomato": "टमाटर"},
    "pa-IN": {"wheat": "ਕਣਕ", "paddy": "ਝੋਨਾ", "rice": "ਚੌਲ", "maize": "ਮੱਕੀ", "mustard": "ਸਰ੍ਹੋਂ",
              "cotton": "ਕਪਾਹ", "potato": "ਆਲੂ", "onion": "ਪਿਆਜ਼", "tomato": "ਟਮਾਟਰ"},
    "en-IN": {k: k.capitalize() for k in CROP_ALIASES},
}
# mandi -> (state, lat, lon, aliases)
MANDIS = {
    "Khanna": ("Punjab", 30.6987, 76.2217, ["khanna", "खन्ना", "ਖੰਨਾ"]),
    "Ludhiana": ("Punjab", 30.9010, 75.8573, ["ludhiana", "लुधियाना", "ਲੁਧਿਆਣਾ"]),
    "Amritsar": ("Punjab", 31.6340, 74.8723, ["amritsar", "अमृतसर", "ਅੰਮ੍ਰਿਤਸਰ"]),
    "Patiala": ("Punjab", 30.3398, 76.3869, ["patiala", "पटियाला", "ਪਟਿਆਲਾ"]),
    "Jalandhar": ("Punjab", 31.3260, 75.5762, ["jalandhar", "जालंधर", "ਜਲੰਧਰ"]),
    "Bathinda": ("Punjab", 30.2110, 74.9455, ["bathinda", "बठिंडा", "ਬਠਿੰਡਾ"]),
    "Karnal": ("Haryana", 29.6857, 76.9905, ["karnal", "करनाल", "ਕਰਨਾਲ"]),
    "Ambala": ("Haryana", 30.3782, 76.7767, ["ambala", "अंबाला", "अम्बाला", "ਅੰਬਾਲਾ"]),
    "Hisar": ("Haryana", 29.1492, 75.7217, ["hisar", "हिसार", "ਹਿਸਾਰ"]),
    "Sirsa": ("Haryana", 29.5349, 75.0288, ["sirsa", "सिरसा", "ਸਰਸਾ"]),
    "Kurukshetra": ("Haryana", 29.9695, 76.8783, ["kurukshetra", "कुरुक्षेत्र", "ਕੁਰੂਕਸ਼ੇਤਰ"]),
}
MANDI_DISPLAY = {
    "hi-IN": {"Khanna": "खन्ना", "Ludhiana": "लुधियाना", "Amritsar": "अमृतसर", "Patiala": "पटियाला",
              "Jalandhar": "जालंधर", "Bathinda": "बठिंडा", "Karnal": "करनाल", "Ambala": "अंबाला",
              "Hisar": "हिसार", "Sirsa": "सिरसा", "Kurukshetra": "कुरुक्षेत्र"},
    "pa-IN": {"Khanna": "ਖੰਨਾ", "Ludhiana": "ਲੁਧਿਆਣਾ", "Amritsar": "ਅੰਮ੍ਰਿਤਸਰ", "Patiala": "ਪਟਿਆਲਾ",
              "Jalandhar": "ਜਲੰਧਰ", "Bathinda": "ਬਠਿੰਡਾ", "Karnal": "ਕਰਨਾਲ", "Ambala": "ਅੰਬਾਲਾ",
              "Hisar": "ਹਿਸਾਰ", "Sirsa": "ਸਰਸਾ", "Kurukshetra": "ਕੁਰੂਕਸ਼ੇਤਰ"},
}
MANDI_COORDS = {k: (v[1], v[2]) for k, v in MANDIS.items()}
# Illustrative prices used ONLY when live Agmarknet data is unavailable. Always labelled as demo.
DEMO_PRICES = {"wheat": 2275, "paddy": 2320, "rice": 3400, "maize": 2090, "mustard": 5650,
               "cotton": 7121, "potato": 1450, "onion": 1800, "tomato": 2200}
SELL_WORDS = ["bech", "beche", "becho", "sell", "बेच", "ਵੇਚ", "vech"]
HOLD_WORDS = ["hold", "rakh", "rok", "ruk", "रख", "रुक", "रोक", "ਰੱਖ", "ਰੋਕ", "ਰੁਕ"]


def mandi_name(mandi: str, lang: str) -> str:
    return MANDI_DISPLAY.get(lang, {}).get(mandi, mandi)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
_CACHE: dict = {}


def _cached(key, fn, ttl: int = CACHE_TTL):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    value = fn()
    _CACHE[key] = (time.time(), value)
    return value


def _has(alias: str, text: str) -> bool:
    if alias.isascii():
        return re.search(rf"\b{re.escape(alias)}\b", text) is not None
    return alias in text


def _key_for(service: str) -> str:
    """service: 'stt' or 'tts'. A dedicated key wins; GNANI_API_KEY works for both."""
    return os.getenv(f"GNANI_{service.upper()}_KEY", "") or os.getenv("GNANI_API_KEY", "")


def _auth_headers(service: str = "stt") -> dict:
    key = _key_for(service)
    if not key:
        raise KisanBolError("no_key")
    return {"X-API-Key-ID": key}


def gnani_configured(service: str = "stt") -> bool:
    return bool(_key_for(service))


def voice_ready() -> bool:
    """True when a recording can be turned into text: hosted speech service, or the optional offline recognizer."""
    return gnani_configured("stt") or audio_utils.local_stt_available()


def evon_configured() -> bool:
    return bool(EVON_BASE_URL)


# --------------------------------------------------------------------------
# 1. Speech-to-text: Gnani Prisma v2.5
# --------------------------------------------------------------------------
def _extract_transcript(data) -> str | None:
    if isinstance(data, str):
        return data.strip() or None
    if isinstance(data, dict):
        for key in ("transcript", "text", "transcription"):
            if isinstance(data.get(key), str):
                return data[key].strip()
        for key in ("data", "result", "output"):
            if key in data:
                found = _extract_transcript(data[key])
                if found:
                    return found
    return None


def transcribe(audio: bytes, filename: str = "query.wav", language: str = "hi-IN") -> str:
    """Any audio/video file -> 16 kHz mono WAV -> transcript (hosted service, else optional offline recognizer)."""
    try:
        wav = audio_utils.to_wav16k(audio, filename)
    except audio_utils.AudioError as exc:
        raise KisanBolError(exc.key, **exc.params) from exc
    if not gnani_configured("stt"):
        if not audio_utils.local_stt_available():
            raise KisanBolError("no_stt")
        try:
            transcript = audio_utils.local_transcribe(wav, language)
        except Exception as exc:
            raise KisanBolError("stt_local", detail=type(exc).__name__) from exc
        if not transcript:
            raise KisanBolError("stt_empty")
        return transcript
    form = {"language_code": language, "preferred_language": language,
            "format": "transcribe", "itn_native_numerals": "false"}
    try:
        resp = requests.post(GNANI_BASE_URL + STT_PATH, headers=_auth_headers("stt"), data=form,
                             files={"audio_file": ("query.wav", wav, "audio/wav")}, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise KisanBolError("stt_service", detail=str(exc)[:120]) from exc
    if not resp.ok:
        raise KisanBolError("stt_service", detail=f"HTTP {resp.status_code}: {resp.text[:160]}")
    try:
        data = resp.json()
    except ValueError:
        data = resp.text
    transcript = _extract_transcript(data)
    if not transcript:
        raise KisanBolError("stt_empty")
    return transcript


# --------------------------------------------------------------------------
# 2. Reasoning: Evon v3.3 entity extraction, with rule-based fallback
# --------------------------------------------------------------------------
def extract_entities_rules(transcript: str) -> Entities:
    text = transcript.lower()
    crop = None
    pairs = [(a, k) for k, aliases in CROP_ALIASES.items() for a in aliases]
    for alias, key in sorted(pairs, key=lambda p: -len(p[0])):
        if _has(alias, text):
            crop = key
            break
    mandi = None
    for name, (_, _, _, aliases) in MANDIS.items():
        if any(_has(a, text) for a in aliases):
            mandi = name
            break
    if mandi is None:
        m = re.search(r"([^\W\d_]+)\s+(?:mandi|मंडी|मण्डी|ਮੰਡੀ)", text)
        if m and m.group(1) not in {"ki", "ka", "ke", "is", "us", "yeh", "woh", "kaun", "si", "ਦੀ", "की", "का", "के"}:
            mandi = m.group(1).title()
    sell = any(_has(w, text) for w in SELL_WORDS)
    hold = any(_has(w, text) for w in HOLD_WORDS)
    return Entities(crop=crop, mandi=mandi, intent="sell_or_hold" if (sell or hold) else "price_check",
                    quantity=indic.parse_quantity(transcript))


def _evon_chat(messages: list[dict], max_tokens: int = 300) -> str:
    resp = requests.post(f"{EVON_BASE_URL}/chat/completions",
                         headers={"Authorization": f"Bearer {EVON_API_KEY}"},
                         json={"model": EVON_MODEL, "messages": messages, "temperature": 0, "max_tokens": max_tokens},
                         timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_entities_evon(transcript: str) -> Entities:
    system = ("You extract entities from an Indian farmer's spoken query (Hindi/Punjabi/English mix, possibly in "
              "Devanagari or Gurmukhi). Reply with ONLY a JSON object: {\"crop\": one of "
              + json.dumps(list(CROP_ALIASES)) + " or null, \"mandi\": market name in English letters or null, "
              "\"intent\": \"sell_or_hold\" or \"price_check\", \"quantity_quintals\": number or null}.")
    raw = _evon_chat([{"role": "system", "content": system}, {"role": "user", "content": transcript}])
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("Evon returned no JSON")
    data = json.loads(match.group(0))
    crop = data.get("crop") if data.get("crop") in CROP_ALIASES else None
    mandi = data.get("mandi").strip().title() if isinstance(data.get("mandi"), str) and data["mandi"].strip() else None
    intent = data.get("intent") if data.get("intent") in ("sell_or_hold", "price_check") else "sell_or_hold"
    q = data.get("quantity_quintals")
    return Entities(crop=crop, mandi=mandi, intent=intent, quantity=float(q) if isinstance(q, (int, float)) and q > 0 else None)


def extract_entities(transcript: str, warnings: list) -> Entities:
    rules = extract_entities_rules(transcript)
    if not evon_configured():
        return rules
    try:
        evon = extract_entities_evon(transcript)
    except Exception as exc:
        warnings.append(Note("dev_evon_extract", {"exc": type(exc).__name__}))
        return rules
    return Entities(crop=evon.crop or rules.crop, mandi=evon.mandi or rules.mandi, intent=evon.intent,
                    quantity=evon.quantity or rules.quantity)


# --------------------------------------------------------------------------
# 3. Tools: market snapshot (Agmarknet) and weather (Open-Meteo)
# --------------------------------------------------------------------------
def _to_int(value) -> int | None:
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def _parse_date(s: str) -> datetime:
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except (TypeError, ValueError):
            continue
    return datetime.min


def parse_agmarknet_records(records: list[dict], crop: str, mandi: str) -> MarketPrice | None:
    rows = [r for r in records if _to_int(r.get("modal_price"))]
    if not rows:
        return None
    latest = max(rows, key=lambda r: _parse_date(r.get("arrival_date", "")))
    return MarketPrice(crop=crop, mandi=mandi, modal=_to_int(latest["modal_price"]),
                       min=_to_int(latest.get("min_price")), max=_to_int(latest.get("max_price")),
                       date=latest.get("arrival_date", ""), source="agmarknet")


def parse_market_snapshot(records: list[dict], crop: str, mandi: str) -> dict | None:
    """Turn raw Agmarknet rows (many markets, many dates) into price, neighbours and a series."""
    by_market: dict[str, dict[str, list[int]]] = {}
    for r in records:
        modal = _to_int(r.get("modal_price"))
        if not modal:
            continue
        by_market.setdefault(str(r.get("market", "")).strip(), {}).setdefault(r.get("arrival_date", ""), []).append(modal)

    def canon(name: str) -> str | None:
        return next((k for k in MANDIS if k.lower() in name.lower() or name.lower() in k.lower()), None)

    sel_key = next((k for k in by_market if mandi.lower() in k.lower()), None)
    if sel_key is None:
        return None
    sel_rows = [r for r in records if str(r.get("market", "")).strip() == sel_key]
    selected = parse_agmarknet_records(sel_rows, crop, mandi)
    if selected is None:
        return None
    prices = {}
    for name, dates in by_market.items():
        c = canon(name)
        if c:
            latest = max(dates, key=_parse_date)
            prices[c] = round(sum(dates[latest]) / len(dates[latest]))
    dates = by_market[sel_key]
    series = None
    if len(dates) >= 3:
        series = [{"date": _parse_date(d).strftime("%Y-%m-%d"), "price": round(sum(v) / len(v))}
                  for d, v in sorted(dates.items(), key=lambda kv: _parse_date(kv[0]))][-7:]
    return {"selected": selected, "prices": prices, "series": series, "source": "agmarknet"}


def _live_snapshot(crop: str, mandi: str, state: str | None) -> dict | None:
    params = {"api-key": AGMARKNET_API_KEY, "format": "json", "limit": 500,
              "filters[commodity]": AGMARKNET_COMMODITY[crop]}
    if state:
        params["filters[state]"] = state

    def call():
        resp = requests.get(f"https://api.data.gov.in/resource/{AGMARKNET_RESOURCE_ID}", params=params,
                            timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("records", [])

    return parse_market_snapshot(_cached(("agmarknet", crop, state), call), crop, mandi)


def _demo_snapshot(crop: str, mandi: str) -> dict:
    base = DEMO_PRICES[crop]
    names = list(MANDIS) if mandi in MANDIS else [mandi]
    prices = mi.demo_mandi_prices(crop, base, names, mandi)
    selected = MarketPrice(crop=crop, mandi=mandi, modal=base, min=None, max=None,
                           date=datetime.now().strftime("%d/%m/%Y"), source="demo")
    return {"selected": selected, "prices": prices, "series": None, "source": "demo"}


def fetch_market_snapshot(crop: str, mandi: str, warnings: list) -> dict:
    state = MANDIS.get(mandi, (None,))[0]
    if AGMARKNET_API_KEY:
        try:
            live = _live_snapshot(crop, mandi, state)
            if live:
                return live
            warnings.append(Note("no_live_record", {"crop": crop, "mandi": mandi}))
        except (requests.RequestException, ValueError) as exc:
            warnings.append(Note("agmark_unavailable"))
    else:
        warnings.append(Note("dev_no_agmarknet_key"))
        warnings.append(Note("demo_price"))
    return _demo_snapshot(crop, mandi)


def fetch_price(crop: str, mandi: str, warnings: list) -> MarketPrice:
    return fetch_market_snapshot(crop, mandi, warnings)["selected"]


def _coordinates(mandi: str) -> tuple[float, float] | None:
    if mandi in MANDI_COORDS:
        return MANDI_COORDS[mandi]
    try:
        resp = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                            params={"name": mandi, "count": 1, "country_code": "IN"}, timeout=15)
        results = resp.json().get("results") or []
        if results:
            return results[0]["latitude"], results[0]["longitude"]
    except (requests.RequestException, ValueError):
        pass
    return None


def fetch_weather(mandi: str, warnings: list) -> Weather | None:
    coords = _coordinates(mandi)
    if not coords:
        warnings.append(Note("weather_unlocated", {"mandi": mandi}))
        return None

    def call():
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": coords[0], "longitude": coords[1], "forecast_days": 3, "timezone": "Asia/Kolkata",
            "daily": "precipitation_probability_max,precipitation_sum,temperature_2m_max"}, timeout=15)
        resp.raise_for_status()
        return resp.json()["daily"]

    try:
        d = _cached(("weather", coords), call)
        days = [{"date": t, "rain_prob": int(p or 0), "rain_mm": float(mm or 0), "tmax": float(tx) if tx is not None else None}
                for t, p, mm, tx in zip(d["time"], d["precipitation_probability_max"],
                                        d["precipitation_sum"], d["temperature_2m_max"])]
    except (requests.RequestException, KeyError, ValueError) as exc:
        warnings.append(Note("weather_unavailable"))
        return None
    return Weather(daily=days, max_rain_prob=max(x["rain_prob"] for x in days))


def scenario_weather(kind: str) -> Weather:
    """Fixed forecasts for demos: 'rainy' (SELL NOW) or 'clear' (HOLD). Labelled in the UI."""
    rows = {"rainy": [(45, 6.0, 29), (85, 22.0, 27), (60, 11.0, 28)],
            "clear": [(10, 0.0, 33), (20, 0.4, 34), (15, 0.0, 33)]}[kind]
    today = datetime.now()
    days = [{"date": (today + timedelta(days=i)).strftime("%Y-%m-%d"), "rain_prob": p, "rain_mm": mm, "tmax": t}
            for i, (p, mm, t) in enumerate(rows)]
    return Weather(daily=days, max_rain_prob=max(r[0] for r in rows), source="scenario")


# --------------------------------------------------------------------------
# 4. Decision logic + market intelligence
# --------------------------------------------------------------------------
def decide(weather: Weather | None, threshold: int = RAIN_THRESHOLD) -> Verdict:
    if weather is None:
        return Verdict("NO DATA", i18n.t("en-IN", "reason.no_weather"), "n/a", "no_weather", 0, threshold)
    rain = weather.max_rain_prob
    margin = abs(rain - threshold)
    conf = "High" if margin >= 20 else "Medium" if margin >= 10 else "Low"
    if rain > threshold:
        return Verdict("SELL NOW", i18n.t("en-IN", "reason.sell", rain=rain, thr=threshold), conf, "sell", rain, threshold)
    return Verdict("HOLD", i18n.t("en-IN", "reason.hold", rain=rain, thr=threshold), conf, "hold", rain, threshold)


def build_insights(entities: Entities, snapshot: dict, weather: Weather | None, verdict: Verdict) -> Insights:
    sel: MarketPrice = snapshot["selected"]
    ins = Insights(quantity=entities.quantity)
    series = snapshot.get("series")
    ins.trend_source = "live" if series else "demo"
    ins.trend = series or mi.demo_series(sel.crop, sel.mandi, sel.modal)
    stats = mi.trend_stats(ins.trend)
    if stats:
        ins.trend_pct, ins.trend_direction = stats["pct"], stats["direction"]
    ins.nearby_source = "live" if snapshot["source"] == "agmarknet" else "demo"
    prices = dict(snapshot["prices"])
    prices[sel.mandi] = sel.modal
    ins.nearby = mi.compare_mandis(sel.mandi, prices, MANDI_COORDS)
    ins.best_alt = mi.best_alternative(ins.nearby)
    if entities.quantity:
        ins.revenue = round(entities.quantity * sel.modal)

    def sig(tone, key, **params):
        ins.signals.append({"tone": tone, "key": key, "params": params, "text": i18n.t("en-IN", "sig." + key, **params)})

    if weather:
        sig("red" if verdict.label == "SELL NOW" else "green", "rain", rain=weather.max_rain_prob)
    if ins.trend_direction:
        sig({"up": "green", "down": "amber", "flat": "grey"}[ins.trend_direction], ins.trend_direction,
            pct=f"{abs(ins.trend_pct):g}", n=len(ins.trend))
    if ins.best_alt:
        sig("amber", "better", alt=ins.best_alt["mandi"], diff=indic.indian_group(ins.best_alt["diff"]),
            km=ins.best_alt["distance_km"])
    if verdict.label == "HOLD" and ins.trend_direction == "down":
        sig("amber", "soft")
    return ins


# --------------------------------------------------------------------------
# 5. Advice text (Hindi, Punjabi, English)
# --------------------------------------------------------------------------
TEMPLATES = {
    "hi-IN": {
        "intro": "<reassuring> नमस्ते किसान भाई। <pause> {mandi} मंडी में {crop} का भाव आज ₹{price} प्रति क्विंटल है। <pause> ",
        "SELL NOW": "अगले तीन दिनों में बारिश की संभावना {rain} प्रतिशत तक है। फसल भीगने का खतरा है, इसलिए मेरी सलाह है कि अभी बेच दीजिए।",
        "HOLD": "अगले तीन दिनों में बारिश की संभावना सिर्फ {rain} प्रतिशत है, इसलिए घबराने की ज़रूरत नहीं। अभी रुकिए और अच्छे भाव का इंतज़ार कीजिए।",
        "NO DATA": "मौसम की जानकारी अभी नहीं मिल पाई, इसलिए बेचने या रुकने की सलाह नहीं दे सकता। कृपया थोड़ी देर बाद फिर कोशिश करें।",
        "trend_up": "पिछले सात दिनों में भाव लगभग {pct} प्रतिशत बढ़ा है।",
        "trend_down": "पिछले सात दिनों में भाव लगभग {pct} प्रतिशत गिरा है।",
        "trend_flat": "पिछले सात दिनों में भाव लगभग स्थिर रहा है।",
        "revenue": "आपके {qty} क्विंटल {crop} की कीमत लगभग {amount} बनती है।",
        "better": "एक बात और: {alt} मंडी सिर्फ़ {km} किलोमीटर दूर है और वहाँ भाव ₹{diff} प्रति क्विंटल ज़्यादा है।",
        "ask_both": "मुझे फसल या मंडी का नाम समझ नहीं आया। कृपया फिर से बोलिए, जैसे: खन्ना मंडी में गेहूं का भाव क्या है?",
        "ask_crop": "कौन सी फसल का भाव जानना चाहते हैं? जैसे गेहूं, धान या सरसों।",
        "ask_mandi": "किस मंडी का भाव चाहिए? जैसे खन्ना या करनाल।",
    },
    "pa-IN": {
        "intro": "<reassuring> ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਕਿਸਾਨ ਵੀਰ ਜੀ। <pause> {mandi} ਮੰਡੀ ਵਿੱਚ {crop} ਦਾ ਭਾਅ ਅੱਜ ₹{price} ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਹੈ। <pause> ",
        "SELL NOW": "ਅਗਲੇ ਤਿੰਨ ਦਿਨਾਂ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {rain} ਪ੍ਰਤੀਸ਼ਤ ਤੱਕ ਹੈ। ਫ਼ਸਲ ਭਿੱਜਣ ਦਾ ਖ਼ਤਰਾ ਹੈ, ਇਸ ਲਈ ਮੇਰੀ ਸਲਾਹ ਹੈ ਕਿ ਹੁਣੇ ਵੇਚ ਦਿਓ।",
        "HOLD": "ਅਗਲੇ ਤਿੰਨ ਦਿਨਾਂ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਸਿਰਫ਼ {rain} ਪ੍ਰਤੀਸ਼ਤ ਹੈ, ਇਸ ਲਈ ਫ਼ਿਕਰ ਨਾ ਕਰੋ। ਹਾਲੇ ਰੁਕੋ ਅਤੇ ਚੰਗੇ ਭਾਅ ਦੀ ਉਡੀਕ ਕਰੋ।",
        "NO DATA": "ਮੌਸਮ ਦੀ ਜਾਣਕਾਰੀ ਹੁਣੇ ਨਹੀਂ ਮਿਲ ਸਕੀ, ਇਸ ਲਈ ਵੇਚਣ ਜਾਂ ਰੁਕਣ ਦੀ ਸਲਾਹ ਨਹੀਂ ਦੇ ਸਕਦਾ। ਕਿਰਪਾ ਕਰਕੇ ਥੋੜ੍ਹੀ ਦੇਰ ਬਾਅਦ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
        "trend_up": "ਪਿਛਲੇ ਸੱਤ ਦਿਨਾਂ ਵਿੱਚ ਭਾਅ ਲਗਭਗ {pct} ਪ੍ਰਤੀਸ਼ਤ ਵਧਿਆ ਹੈ।",
        "trend_down": "ਪਿਛਲੇ ਸੱਤ ਦਿਨਾਂ ਵਿੱਚ ਭਾਅ ਲਗਭਗ {pct} ਪ੍ਰਤੀਸ਼ਤ ਘਟਿਆ ਹੈ।",
        "trend_flat": "ਪਿਛਲੇ ਸੱਤ ਦਿਨਾਂ ਵਿੱਚ ਭਾਅ ਲਗਭਗ ਸਥਿਰ ਰਿਹਾ ਹੈ।",
        "revenue": "ਤੁਹਾਡੇ {qty} ਕੁਇੰਟਲ {crop} ਦੀ ਕੀਮਤ ਲਗਭਗ {amount} ਬਣਦੀ ਹੈ।",
        "better": "ਇੱਕ ਗੱਲ ਹੋਰ: {alt} ਮੰਡੀ ਸਿਰਫ਼ {km} ਕਿਲੋਮੀਟਰ ਦੂਰ ਹੈ ਅਤੇ ਉੱਥੇ ਭਾਅ ₹{diff} ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਵੱਧ ਹੈ।",
        "ask_both": "ਮੈਨੂੰ ਫ਼ਸਲ ਜਾਂ ਮੰਡੀ ਦਾ ਨਾਮ ਸਮਝ ਨਹੀਂ ਆਇਆ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਬੋਲੋ।",
        "ask_crop": "ਕਿਹੜੀ ਫ਼ਸਲ ਦਾ ਭਾਅ ਜਾਣਨਾ ਹੈ? ਜਿਵੇਂ ਕਣਕ, ਝੋਨਾ ਜਾਂ ਸਰ੍ਹੋਂ।",
        "ask_mandi": "ਕਿਹੜੀ ਮੰਡੀ ਦਾ ਭਾਅ ਚਾਹੀਦਾ ਹੈ? ਜਿਵੇਂ ਖੰਨਾ ਜਾਂ ਕਰਨਾਲ।",
    },
    "en-IN": {
        "intro": "<reassuring> Hello. <pause> The price of {crop} in {mandi} mandi today is ₹{price} per quintal. <pause> ",
        "SELL NOW": "There is up to a {rain} percent chance of rain in the next three days, which can damage your crop. My advice is to sell now.",
        "HOLD": "The chance of rain in the next three days is only {rain} percent, so there is no need to worry. Hold for now and wait for a better price.",
        "NO DATA": "I could not get the weather forecast right now, so I cannot advise on selling or holding. Please try again shortly.",
        "trend_up": "Over the last seven days the price has risen about {pct} percent.",
        "trend_down": "Over the last seven days the price has fallen about {pct} percent.",
        "trend_flat": "Over the last seven days the price has stayed about the same.",
        "revenue": "Your {qty} quintals of {crop} are worth about {amount}.",
        "better": "One more thing: {alt} mandi is only {km} kilometres away and pays ₹{diff} more per quintal.",
        "ask_both": "I could not understand the crop or the mandi. Please say it again, for example: wheat price in Khanna mandi?",
        "ask_crop": "Which crop's price do you want? For example wheat, paddy or mustard.",
        "ask_mandi": "Which mandi's price do you want? For example Khanna or Karnal.",
    },
}
_TAG_RE = re.compile(r"</?(?:reassuring|pause)\s*/?>\s*", re.I)


def strip_tags(text: str) -> str:
    return re.sub(r"\s{2,}", " ", _TAG_RE.sub("", text)).strip()


def _fmt_qty(q: float) -> str:
    return str(int(q)) if float(q).is_integer() else f"{q:g}"


def clarification(language: str, entities: Entities) -> str:
    t = TEMPLATES[language]
    if not entities.crop and not entities.mandi:
        return t["ask_both"]
    return t["ask_crop"] if not entities.crop else t["ask_mandi"]


def compose_advice(language: str, entities: Entities, price: MarketPrice | None, weather: Weather | None,
                   verdict: Verdict, insights: Insights | None = None) -> str:
    t = TEMPLATES.get(language, TEMPLATES["hi-IN"])
    if price is None:
        return clarification(language, entities)
    crop = CROP_DISPLAY[language][price.crop]
    text = t["intro"].format(mandi=mandi_name(price.mandi, language), crop=crop, price=indic.indian_group(price.modal))
    text += t[verdict.label].format(rain=weather.max_rain_prob if weather else 0)
    if insights:
        if insights.trend_direction:
            text += " " + t["trend_" + insights.trend_direction].format(pct=f"{abs(insights.trend_pct):g}")
        if insights.revenue and insights.quantity:
            text += " <pause> " + t["revenue"].format(qty=_fmt_qty(insights.quantity), crop=crop,
                                                      amount=indic.amount_words(insights.revenue, language))
        if insights.best_alt:
            a = insights.best_alt
            text += " <pause> " + t["better"].format(alt=mandi_name(a["mandi"], language), km=a["distance_km"],
                                                     diff=indic.indian_group(a["diff"]))
    return text


def polish_with_evon(text: str, language: str, price: MarketPrice, rain: int, warnings: list) -> str:
    """Optionally let Evon rephrase the advice more naturally; verified facts must survive."""
    if not evon_configured():
        return text
    system = ("Rewrite this advice for a farmer as warm, simple spoken " + {"hi-IN": "Hindi", "pa-IN": "Punjabi",
              "en-IN": "English"}.get(language, "Hindi") + ". Keep every number and the SELL/HOLD decision exactly. "
              "Keep the tags <reassuring> and <pause>. Reply with only the rewritten text, at most 6 sentences.")
    try:
        out = _evon_chat([{"role": "system", "content": system}, {"role": "user", "content": text}], 500).strip()
    except Exception:
        warnings.append(Note("dev_evon_phrase"))
        return text
    if indic.indian_group(price.modal) in out and str(rain) in out:
        return out
    warnings.append(Note("dev_evon_dropped"))
    return text


# --------------------------------------------------------------------------
# 6. Text-to-speech: Gnani Timbre
# --------------------------------------------------------------------------
def synthesize(text: str, language: str = "hi-IN") -> bytes:
    spoken = text if ENABLE_TTS_TAGS else strip_tags(text)
    body = {"model": TTS_MODEL, "voice": TTS_VOICE, "language": language, "text": spoken,
            "sample_rate": TTS_SAMPLE_RATE, "container": "wav", "encoding": "linear_pcm"}
    try:
        resp = requests.post(GNANI_BASE_URL + TTS_PATH, headers={**_auth_headers("tts"), "Content-Type": "application/json"},
                             json=body, timeout=HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise KisanBolError("tts_service", detail=str(exc)[:120]) from exc
    if not resp.ok:
        raise KisanBolError("tts_service", detail=f"HTTP {resp.status_code}: {resp.text[:160]}")
    if resp.headers.get("content-type", "").startswith("audio") or resp.content[:4] == b"RIFF" or resp.content[:3] == b"ID3":
        return resp.content
    try:
        data = resp.json()
        for key in ("audio", "audio_content", "audio_base64"):
            if isinstance(data.get(key), str):
                return base64.b64decode(data[key])
    except ValueError:
        pass
    raise KisanBolError("tts_service", detail="unexpected response format")


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def run_pipeline(audio: bytes | None = None, text: str | None = None, language: str = "auto",
                 filename: str = "query.wav", speak: bool = True, weather_scenario: str | None = None,
                 context: Entities | None = None) -> KisanBolResult:
    """Run the full loop. `audio` = real flow, `text` = skip STT. `context` = previous turn's entities,
    used to fill gaps in follow-ups such as 'aur Karnal mein?'."""
    warnings: list = []
    timings: dict[str, float] = {}
    stt_lang = "hi-IN" if language == "auto" else language

    t0 = time.perf_counter()
    if audio is not None:
        transcript = transcribe(audio, filename, stt_lang)
    elif text and text.strip():
        transcript = text.strip()
    else:
        raise KisanBolError("no_input")
    timings["stt"] = time.perf_counter() - t0
    reply_lang = indic.detect_language(transcript) if language == "auto" else language

    t0 = time.perf_counter()
    entities = extract_entities(transcript, warnings)
    used_context: list[str] = []
    if context:
        if not entities.crop and context.crop and entities.mandi:
            entities.crop = context.crop
            used_context.append("crop")
        if not entities.mandi and context.mandi and entities.crop:
            entities.mandi = context.mandi
            used_context.append("mandi")
        if used_context and not entities.quantity and context.quantity:
            entities.quantity = context.quantity
            used_context.append("quantity")
    timings["reasoning"] = time.perf_counter() - t0

    price = weather = None
    insights = Insights(quantity=entities.quantity)
    needs_clarification = not (entities.crop and entities.mandi)
    if not needs_clarification:
        t0 = time.perf_counter()
        snapshot = fetch_market_snapshot(entities.crop, entities.mandi, warnings)
        price = snapshot["selected"]
        if weather_scenario in ("rainy", "clear"):
            weather = scenario_weather(weather_scenario)
            warnings.append(Note("scenario"))
        else:
            weather = fetch_weather(entities.mandi, warnings)
        timings["tools"] = time.perf_counter() - t0
        verdict = decide(weather)
        insights = build_insights(entities, snapshot, weather, verdict)
    else:
        verdict = Verdict("NO DATA", i18n.t("en-IN", "reason.no_entities"), "n/a", "no_entities")

    advice = compose_advice(reply_lang, entities, price, weather, verdict, insights)
    if price and weather:
        advice = polish_with_evon(advice, reply_lang, price, weather.max_rain_prob, warnings)

    audio_out = None
    if speak:
        t0 = time.perf_counter()
        try:
            audio_out = synthesize(advice, reply_lang)
        except KisanBolError as exc:
            warnings.append(Note("tts_unavailable"))
        timings["tts"] = time.perf_counter() - t0

    return KisanBolResult(transcript=transcript, entities=entities, price=price, weather=weather, verdict=verdict,
                          insights=insights, advice_text=strip_tags(advice), audio=audio_out, language=reply_lang,
                          needs_clarification=needs_clarification, used_context=used_context,
                          warnings=warnings, timings=timings)
