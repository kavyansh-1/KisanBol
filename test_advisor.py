import advisor as a
import i18n
import kisanbol_engine as e


def result(scenario="rainy", lang="en-IN", monkeypatch=None):
    return e.run_pipeline(text="Gehu Khanna mandi 50 quintal", speak=False, weather_scenario=scenario, language=lang)


def test_off_topic_is_refused_in_every_language():
    for lang in i18n.LANGS:
        for q in ("What is the capital of France?", "tell me a joke", "who won the cricket match", "how to train my dog"):
            assert a.reply(q, lang).topic == "refused"
    assert "खेती" in a.reply("tell me a joke", "hi-IN").text


def test_farming_questions_get_guide_answers_in_the_chosen_language():
    cases = [("how to store wheat safely", "storage"), ("keet lage hain kya spray karun", "pest"),
             ("बारिश में कटी फसल कैसे बचाएं", "rain_harvest"), ("ਝੋਨੇ ਨੂੰ ਪਾਣੀ ਕਦੋਂ ਲਾਈਏ", "irrigation"),
             ("kisan credit card kaise milega", "loan"), ("what is MSP", "msp"), ("hail damaged my crop", "insurance")]
    for q, topic in cases:
        r = a.reply(q, "hi-IN")
        assert r.topic == topic and any("ऀ" <= c <= "ॿ" for c in r.text)
    assert a.reply("how to store wheat", "pa-IN").text != a.reply("how to store wheat", "en-IN").text


def test_pest_advice_never_gives_a_dose():
    for lang in i18n.LANGS:
        text = a.reply("which spray for pest on my crop", lang).text
        assert "1800-180-1551" in text and "ml" not in text.lower() and "kg" not in text.lower()


def test_sell_question_uses_live_facts_and_steps():
    r = a.reply("should I sell now", "en-IN", result())
    assert r.topic == "live" and "85" in r.text and "What to do now" in r.text and "1." in r.text
    r = a.reply("अभी बेचूँ या रुकूँ", "hi-IN", result(lang="hi-IN"))
    assert "अभी क्या करें" in r.text


def test_hold_gives_hold_steps():
    r = a.explain(result("clear"), "en-IN")
    assert "raised platform" in r.text


def test_irrigation_adds_forecast_only_when_known():
    assert "rain chance up to 85%" in a.reply("when to irrigate", "en-IN", result()).text
    assert "rain chance" not in a.reply("when to irrigate", "en-IN", None).text


def test_no_result_asks_for_crop_and_mandi():
    assert "mandi" in a.explain(None, "en-IN").text.lower()


def test_unknown_farming_question_points_to_real_help(monkeypatch):
    monkeypatch.setattr(e, "EVON_BASE_URL", "")
    r = a.reply("what is the soil ph of my yield", "en-IN")
    assert r.topic in ("no_match", "seed") or "Kisan Call Centre" in r.text


def test_model_is_used_for_open_questions_but_not_off_topic(monkeypatch):
    res = result()
    monkeypatch.setattr(e, "EVON_BASE_URL", "http://x/v1")
    seen = []
    monkeypatch.setattr(e, "_evon_chat", lambda msgs, max_tokens=300: seen.append(msgs) or "Rotate crops every season.")
    r = a.reply("how should I plan crop rotation on my farm", "en-IN", res)
    assert r.topic == "model" and "Rotate" in r.text
    system = seen[0][0]["content"]
    assert "ONLY farming" in system and "85" in system and "never" in system.lower()
    seen.clear()
    assert a.reply("who is the best cricketer", "en-IN").topic == "refused" and not seen


def test_model_failure_falls_back_to_guide(monkeypatch):
    monkeypatch.setattr(e, "EVON_BASE_URL", "http://x/v1")
    def boom(*args, **kw): raise RuntimeError("down")
    monkeypatch.setattr(e, "_evon_chat", boom)
    assert a.reply("crop rotation plan for my farm", "en-IN").topic == "no_match"


def test_rain_protection_vs_sell_before_rain():
    assert a.reply("how to keep my wheat safe from rain", "en-IN").topic == "rain_harvest"
    assert a.reply("rain is coming, should I sell my wheat", "en-IN", result()).topic == "live"


def test_hindi_pest_question_with_either_nukta_form():
    for q in ("गेहूं में कीड़े लगे हैं, कौन सी दवा डालूं?", "गेहूं में कीड़े लगे हैं, कौन सी दवा डालूं?".replace("ड़", "ड़")):
        assert a.reply(q, "hi-IN").topic == "pest"
