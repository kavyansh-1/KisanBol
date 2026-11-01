"""Different questions must give different answers; the forecast horizon follows the question."""
import kisanbol_engine as e
import indic


def run(text, scenario="clear", lang="en-IN"):
    return e.run_pipeline(text=text, speak=False, weather_scenario=scenario, language=lang)


def test_five_and_twelve_days_give_different_answers():
    five = run("kindly brief me about the price of wheat in five days in karnal")
    twelve = run("kindly brief me about the price of wheat in 12 days in karnal")
    assert five.verdict.days == 5 and len(five.weather.daily) == 5
    assert "next 5 days" in five.advice_text and "only 5 days" not in five.advice_text
    assert twelve.insights.days_requested == 12 and "only 5 days, not 12" in twelve.advice_text
    assert five.advice_text != twelve.advice_text
    assert "cannot predict" in five.advice_text


def test_default_horizon_is_three_days():
    r = run("wheat price in Karnal, sell or hold?")
    assert r.verdict.days == 3 and "next 3 days" in r.advice_text and "cannot predict" not in r.advice_text


def test_decision_uses_only_the_asked_days():
    # rainy scenario peaks on day 2 (85%); a 1-day question sees only day 1 (45%)
    assert run("wheat Karnal sell or hold in 1 day", "rainy").verdict.code == "hold"
    assert run("wheat Karnal sell or hold in 2 days", "rainy").verdict.code == "sell"


def test_weather_question_is_a_forecast_not_the_same_template():
    r = run("will it rain in Karnal for my wheat")
    assert r.entities.intent == "forecast" and "Day by day" in r.advice_text


def test_non_price_questions_are_answered_not_forced_into_price_template():
    r = run("how to store wheat safely")
    assert r.general and r.general["topic"] == "storage" and r.price is None and not r.needs_clarification
    r = run("who won the cricket match")
    assert r.general["topic"] == "refused"
    r = run("how do I protect my wheat in Karnal from pests")
    assert r.general["topic"] == "pest" and r.price is None


def test_partial_price_question_still_asks_what_is_missing():
    r = run("wheat price today")
    assert r.needs_clarification and r.general is None


def test_follow_up_still_works():
    first = run("wheat price in Khanna, sell or hold?")
    follow = e.run_pipeline(text="and in Karnal?", speak=False, weather_scenario="clear", context=first.entities)
    assert follow.price and follow.entities.mandi == "Karnal" and not follow.general


def test_accuweather_is_used_when_key_is_set(monkeypatch):
    monkeypatch.setattr(e, "ACCUWEATHER_API_KEY", "k")
    e._CACHE.clear()
    calls = []

    class R:
        def __init__(self, data): self.data = data
        def raise_for_status(self): pass
        def json(self): return self.data

    def fake_get(url, params=None, timeout=None):
        calls.append(url)
        if "geoposition" in url:
            assert params["apikey"] == "k" and "," in params["q"]
            return R({"Key": "206985"})
        assert url.endswith("/forecasts/v1/daily/5day/206985") and params["metric"] == "true"
        return R({"DailyForecasts": [
            {"Date": f"2026-10-{27 + i}T07:00:00+05:30", "Temperature": {"Maximum": {"Value": 30.5}},
             "Day": {"RainProbability": p, "Rain": {"Value": 1.5}}, "Night": {"RainProbability": 10, "Rain": {"Value": 0.5}}}
            for i, p in enumerate([20, 75, 40, 10, 5])]})

    monkeypatch.setattr(e.requests, "get", fake_get)
    w = e.fetch_weather("Karnal", [])
    assert w.source == "accuweather" and [d["rain_prob"] for d in w.daily] == [20, 75, 40, 10, 10]
    assert w.daily[0]["rain_mm"] == 2.0 and w.daily[0]["date"] == "2026-10-27" and w.daily[0]["tmax"] == 30.5


def test_accuweather_failure_falls_back_to_open_meteo(monkeypatch):
    monkeypatch.setattr(e, "ACCUWEATHER_API_KEY", "bad")
    e._CACHE.clear()
    notes = []

    def fake_get(url, params=None, timeout=None):
        if "accuweather" in url:
            raise e.requests.ConnectionError("blocked")
        class R:
            def raise_for_status(self): pass
            def json(self):
                return {"daily": {"time": ["2026-10-27", "2026-10-28"], "precipitation_probability_max": [10, 20],
                                  "precipitation_sum": [0, 0], "temperature_2m_max": [30, 31]}}
        return R()

    monkeypatch.setattr(e.requests, "get", fake_get)
    w = e.fetch_weather("Karnal", notes)
    assert w.source == "open-meteo" and any(n.key == "dev_accu_failed" for n in notes)


def test_voice_follows_language(monkeypatch):
    seen = []
    class R:
        ok = True; content = b"RIFF...."; headers = {"content-type": "audio/wav"}
    monkeypatch.setattr(e.requests, "post", lambda url, headers=None, json=None, timeout=None: seen.append(json) or R())
    monkeypatch.setenv("GNANI_TTS_KEY", "k")
    e.synthesize("ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "pa-IN"); e.synthesize("नमस्ते", "hi-IN")
    assert [b["voice"] for b in seen] == ["Mehuli", "Nalini"] and [b["language"] for b in seen] == ["pa-IN", "hi-IN"]


def test_parse_days():
    assert [indic.parse_days(x) for x in ("in five days", "12 din", "next week", "ਤਿੰਨ ਦਿਨ", "price today")] == [5, 12, 7, 3, None]
