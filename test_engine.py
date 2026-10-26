"""Offline tests: no network or API keys needed. Run with: python -m pytest -q"""
import kisanbol_engine as e
import indic
import market_intel as mi


# ---- entity extraction -------------------------------------------------
def test_example_query_hinglish():
    ent = e.extract_entities_rules("Gehu ka rate kya chal raha hai Khanna mandi mein, hold karun ya bech doon?")
    assert ent.crop == "wheat" and ent.mandi == "Khanna" and ent.intent == "sell_or_hold"


def test_devanagari_and_gurmukhi_queries():
    assert e.extract_entities_rules("खन्ना मंडी में गेहूं का भाव क्या है").mandi == "Khanna"
    ent = e.extract_entities_rules("ਖੰਨਾ ਮੰਡੀ ਵਿੱਚ ਕਣਕ ਦਾ ਭਾਅ ਕੀ ਹੈ")
    assert ent.crop == "wheat" and ent.mandi == "Khanna"


def test_paddy_beats_rice_and_unknown_mandi():
    ent = e.extract_entities_rules("Paddy ka bhaav Rajpura mandi mein kya hai")
    assert ent.crop == "paddy" and ent.mandi == "Rajpura"


def test_quantity_is_extracted():
    assert e.extract_entities_rules("Gehu Khanna mandi, 50 quintal hai").quantity == 50


# ---- indic helpers -----------------------------------------------------
def test_indian_grouping_and_lakh_words():
    assert indic.indian_group(227500) == "2,27,500" and indic.indian_group(2275) == "2,275"
    assert indic.amount_words(120000, "en-IN") == "1.2 Lakh rupees"
    assert indic.amount_words(120000, "hi-IN") == "1.2 लाख रुपये"
    assert indic.amount_words(87500) == "₹87,500"


def test_quantity_parsing():
    assert indic.parse_quantity("pachas quintal") == 50
    assert indic.parse_quantity("2 ton") == 20
    assert indic.parse_quantity("1,200 qtl") == 1200
    assert indic.parse_quantity("kuch nahi") is None


def test_language_detection():
    assert indic.detect_language("Gehu ka rate") == "hi-IN"
    assert indic.detect_language("what is the wheat price") == "en-IN"
    assert indic.detect_language("ਕਣਕ ਦਾ ਭਾਅ") == "pa-IN"
    assert indic.detect_language("गेहूं का भाव") == "hi-IN"


# ---- market intelligence ----------------------------------------------
def test_demo_series_is_deterministic_and_ends_at_price():
    a, b = mi.demo_series("wheat", "Khanna", 2275), mi.demo_series("wheat", "Khanna", 2275)
    assert a == b and a[-1]["price"] == 2275 and len(a) == 7


def test_compare_mandis_and_best_alternative():
    coords = {"A": (30.0, 76.0), "B": (30.2, 76.0), "C": (35.0, 76.0)}
    rows = mi.compare_mandis("A", {"A": 2000, "B": 2100, "C": 2500}, coords)
    assert [r["mandi"] for r in rows] == ["B", "A"]  # C is too far
    assert mi.best_alternative(rows)["mandi"] == "B"
    assert mi.best_alternative(mi.compare_mandis("A", {"A": 2000, "B": 2010}, coords)) is None


# ---- decision ----------------------------------------------------------
def test_decision_threshold_is_strictly_above_70():
    mk = lambda p: e.Weather(daily=[{"date": "2026-10-23", "rain_prob": p}], max_rain_prob=p)
    assert e.decide(mk(71)).label == "SELL NOW"
    assert e.decide(mk(70)).label == "HOLD"
    assert e.decide(mk(10)).label == "HOLD"
    assert e.decide(None).label == "NO DATA"
    assert e.decide(mk(95)).confidence == "High" and e.decide(mk(75)).confidence == "Low"


# ---- agmarknet parsing -------------------------------------------------
def test_agmarknet_picks_latest_row():
    rows = [{"arrival_date": "20/10/2026", "modal_price": "2200"},
            {"arrival_date": "22/10/2026", "modal_price": "2275", "min_price": "2200", "max_price": "2300"},
            {"arrival_date": "23/10/2026", "modal_price": ""}]
    p = e.parse_agmarknet_records(rows, "wheat", "Khanna")
    assert p.modal == 2275 and p.date == "22/10/2026"


def test_market_snapshot_builds_neighbours_and_series():
    rec = lambda m, d, p: {"market": m, "arrival_date": d, "modal_price": str(p), "min_price": str(p - 50), "max_price": str(p + 50)}
    rows = [rec("Khanna", f"{d}/10/2026", 2200 + d) for d in (20, 21, 22)] + [rec("Ludhiana", "22/10/2026", 2300)]
    snap = e.parse_market_snapshot(rows, "wheat", "Khanna")
    assert snap["selected"].modal == 2222 and snap["prices"]["Ludhiana"] == 2300
    assert [x["price"] for x in snap["series"]] == [2220, 2221, 2222]
    assert e.parse_market_snapshot(rows, "wheat", "Karnal") is None


def test_transcript_parsing_variants():
    assert e._extract_transcript({"transcript": " hello "}) == "hello"
    assert e._extract_transcript({"data": {"text": "namaste"}}) == "namaste"
    assert e._extract_transcript({"foo": 1}) is None


# ---- full pipeline (offline) -------------------------------------------
def _offline(monkeypatch):
    monkeypatch.setattr(e, "AGMARKNET_API_KEY", "")


def test_advice_has_facts_value_and_lakh(monkeypatch):
    _offline(monkeypatch)
    r = e.run_pipeline(text="Gehu ka rate Khanna mandi mein, 50 quintal hai, bech doon?", speak=False,
                       weather_scenario="rainy")
    assert r.verdict.label == "SELL NOW" and r.language == "hi-IN"
    assert "₹2,275" in r.advice_text and "85" in r.advice_text and "लाख रुपये" in r.advice_text
    assert r.insights.revenue == 113750 and "<" not in r.advice_text


def test_both_scenarios_and_demo_labels(monkeypatch):
    _offline(monkeypatch)
    q = "Gehu ka rate Khanna mandi mein, bech doon?"
    assert e.run_pipeline(text=q, speak=False, weather_scenario="rainy").verdict.label == "SELL NOW"
    r = e.run_pipeline(text=q, speak=False, weather_scenario="clear")
    assert r.verdict.label == "HOLD" and r.price.source == "demo" and r.audio is None
    assert any(n.key == "scenario" for n in r.warnings) and any(n.key == "demo_price" for n in r.warnings)


def test_follow_up_uses_context(monkeypatch):
    _offline(monkeypatch)
    ctx = e.Entities("wheat", "Khanna", quantity=40)
    r = e.run_pipeline(text="aur Karnal mein?", speak=False, weather_scenario="clear", context=ctx)
    assert r.entities.crop == "wheat" and r.entities.mandi == "Karnal" and r.entities.quantity == 40
    assert r.used_context == ["crop", "quantity"]


def test_missing_entities_ask_a_question_in_the_right_language(monkeypatch):
    _offline(monkeypatch)
    r = e.run_pipeline(text="Gehu ka rate kya hai", speak=False)
    assert r.needs_clarification and r.verdict.label == "NO DATA" and "मंडी" in r.advice_text
    r = e.run_pipeline(text="what is the price in Khanna mandi", speak=False)
    assert r.language == "en-IN" and "Which crop" in r.advice_text


def test_result_serialises_for_the_api(monkeypatch):
    _offline(monkeypatch)
    d = e.run_pipeline(text="Gehu Khanna mandi bech doon", speak=False, weather_scenario="clear").to_dict()
    assert d["verdict"]["label"] == "HOLD" and d["insights"]["nearby"]
