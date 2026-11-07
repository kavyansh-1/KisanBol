"""GPS-based mandi choice and the 1 / 3 / 7 day windows."""
import io
import wave

import i18n
import kisanbol_engine as e


def run(text, **kw):
    return e.run_pipeline(text=text, speak=False, weather_scenario=kw.pop("scenario", "clear"), language=kw.pop("lang", "en-IN"), **kw)


# ---- location -------------------------------------------------------------------------------
def test_nearest_mandi_is_found_and_distance_is_reported():
    name, km, close = e.nearest_mandi(30.91, 75.85)  # next to Ludhiana
    assert (name, close) == ("Ludhiana", True) and km <= 5
    assert e.nearest_mandi(29.69, 76.99)[0] == "Karnal"


def test_location_fills_the_missing_mandi():
    r = run("what is the wheat price", location=(30.91, 75.85))
    assert r.entities.mandi == "Ludhiana" and r.price.mandi == "Ludhiana"
    assert r.location_info == {"mandi": "Ludhiana", "km": r.location_info["km"], "used": True}
    assert r.to_dict()["location_info"]["used"] is True


def test_a_named_mandi_beats_the_location():
    r = run("wheat price in Karnal", location=(30.91, 75.85))
    assert r.entities.mandi == "Karnal" and r.location_info is None


def test_far_away_location_is_never_guessed():
    r = run("what is the wheat price", location=(19.07, 72.87))  # Mumbai
    assert r.price is None and r.needs_clarification
    assert r.location_info["used"] is False and r.location_info["km"] > e.LOCATION_MAX_KM


def test_location_needs_a_crop_and_is_optional():
    assert run("how much is the price", location=(30.91, 75.85)).entities.mandi is None
    assert run("wheat price in Khanna").location_info is None


def test_location_works_in_every_language():
    for lang in i18n.LANGS:
        r = run("wheat price", lang=lang, location=(29.69, 76.99))
        assert r.price.mandi == "Karnal" and r.language == lang


# ---- day windows ----------------------------------------------------------------------------
def test_view_days_set_price_and_forecast_windows():
    for d, points, rain_days in ((1, 2, 1), (3, 3, 3), (7, 7, 5)):
        r = run("wheat Karnal sell or hold", scenario="rainy", view_days=d)
        assert len(r.insights.trend) == points and r.insights.price_days == d and len(r.weather.daily) == rain_days


def test_default_view_is_unchanged():
    r = run("wheat Karnal sell or hold")
    assert r.verdict.days == 3 and r.insights.price_days == 7 and "seven days" in r.advice_text


def test_question_days_beat_the_selector():
    assert run("wheat Karnal sell or hold in 2 days", scenario="rainy", view_days=1).verdict.days == 2


def test_one_day_grammar():
    assert "next 1 day " in run("wheat Karnal sell or hold", view_days=1).advice_text
    assert "1 days" not in run("wheat Karnal sell or hold", view_days=1).advice_text
    assert i18n.t("en-IN", "chart.rain", n=1) == "Rain chance, next 1 day" and i18n.t("en-IN", "chart.rain", n=3).endswith("3 days")
    assert "1 दिनों" not in i18n.t("hi-IN", "reason.sell", n=1, rain=80, thr=70)
    for lang in i18n.LANGS:  # every language renders the 1-day sentence without errors
        assert run("wheat Karnal sell or hold", lang=lang, view_days=1).advice_text


def test_short_trend_sentence_matches_the_window_in_every_language():
    for lang in i18n.LANGS:
        for d in (1, 3):
            text = run("wheat Karnal sell or hold", lang=lang, view_days=d).advice_text
            assert "seven" not in text.lower()
