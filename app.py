"""KisanBol: ask by voice, get a clear sell-or-hold answer. Streamlit front end (English, Hindi, Punjabi)."""
import hashlib
import html as _html
import re
import urllib.parse
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

import advisor
import audio_utils
import i18n
import indic
import kisanbol_engine as engine
from ui_style import CSS

st.set_page_config(page_title="KisanBol · किसानबोल", page_icon="🌾", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

CROP_ICON = {"wheat": "🌾", "paddy": "🌾", "rice": "🍚", "maize": "🌽", "mustard": "🌼", "cotton": "☁️",
             "potato": "🥔", "onion": "🧅", "tomato": "🍅"}
VERDICT_KEY = {"SELL NOW": ("v-sell", "verdict.sell"), "HOLD": ("v-hold", "verdict.hold"),
               "NO DATA": ("v-none", "verdict.none")}
SCENARIOS = {"live": None, "rain": "rainy", "clear": "clear"}
INK, AMBER, RED, GREEN = "#14213D", "#FFB703", "#C62828", "#2E7D4F"
for key, default in (("history", []), ("context", None), ("result", None), ("error", None), ("lang", "en-IN"),
                     ("res_lang", None), ("fresh", False), ("chat", []), ("chat_q", "")):
    st.session_state.setdefault(key, default)


def H(markup: str) -> None:
    """Render raw HTML on one line so Markdown never turns indentation into code blocks."""
    st.markdown(re.sub(r"\s*\n\s*", " ", markup.strip()), unsafe_allow_html=True)


def esc(x) -> str:
    return _html.escape(str(x))


# ------------------------------------------------------------------ language switch (top right)
c_brand, c_lang = st.columns([3, 2])
c_brand.markdown("<div class='topbar-brand'>किसानबोल<span>KisanBol</span></div>", unsafe_allow_html=True)
picked = c_lang.segmented_control("Language", list(i18n.LANGS), format_func=i18n.LANGS.get, default=st.session_state["lang"],
                                  key="lang_pick", label_visibility="collapsed")
lang = picked or st.session_state["lang"]
st.session_state["lang"] = lang


def T(key: str, **kw) -> str:
    return i18n.t(lang, key, **kw)


def crop_name(crop: str) -> str:
    return engine.CROP_DISPLAY[lang][crop]


def money(n: int) -> str:
    words = indic.amount_words(n, lang)
    if n >= 100000 and lang == "en-IN":
        return "₹" + words.replace(" rupees", "")
    return words


def run(text=None, audio=None, name="query.wav", speak=None, fresh=True):
    """Run the engine once and keep everything needed to redraw the answer in any language."""
    speak = engine.gnani_configured("tts") if speak is None else speak
    try:
        with st.spinner(T("thinking")):
            res = engine.run_pipeline(audio=audio, text=text, language=lang, filename=name, speak=speak,
                                      weather_scenario=SCENARIOS.get(st.session_state.get("weather_mode", "live")),
                                      context=st.session_state["context"])
    except engine.KisanBolError as exc:
        st.session_state["error"], st.session_state["result"] = exc.localized(lang), None
        return
    st.session_state.update(result=res, error=None, res_lang=lang, fresh=fresh)
    if res.price:
        st.session_state["context"] = res.entities
        st.session_state["history"].insert(0, {"time": datetime.now().strftime("%H:%M"), "q": res.transcript,
                                               "label": res.verdict.label, "crop": res.entities.crop,
                                               "mandi": res.entities.mandi, "price": res.price.modal})


# answer language follows the selected language: redraw the last answer when it changes
prev = st.session_state["result"]
if prev and st.session_state["res_lang"] != lang and prev.transcript:
    run(text=prev.transcript, fresh=False)

# ------------------------------------------------------------------ hero
H(f"""
<div class="hero">
  <div>
    <h1>{esc(T("hero.title"))}</h1>
    <p class="tag">{esc(T("hero.sub"))}</p>
    <div class="feats"><span>{esc(T("feat.price"))}</span><span>{esc(T("feat.rain"))}</span><span>{esc(T("feat.call"))}</span></div>
  </div>
  <div class="quote">
    <p class="qh">{esc(T("hero.example"))}</p>
    <p class="q">“{esc(T("sample.4.q"))}”</p>
    <p class="cap">{esc(T("hero.example_cap"))}</p>
  </div>
</div>
""")

# ------------------------------------------------------------------ ask panel
request = None
with st.container(key="askpanel"):
    H(f'<p class="panel-title">{esc(T("ask.title"))}</p><p class="panel-sub">{esc(T("ask.hint"))}</p>')

    ctx = st.session_state["context"]
    if ctx and ctx.crop and ctx.mandi:
        k1, k2 = st.columns([4, 1])
        k1.markdown(f"<span class='ctx'>{esc(T('ctx.follow', crop=crop_name(ctx.crop), mandi=engine.mandi_name(ctx.mandi, lang)))}</span>",
                    unsafe_allow_html=True)
        if k2.button(T("ctx.new"), use_container_width=True, key="newtopic"):
            st.session_state["context"] = None
            st.rerun()

    st.caption(T("examples"))
    chip_cols = st.columns(4)
    for i, col in enumerate(chip_cols, start=1):
        if col.button(T(f"sample.{i}"), use_container_width=True, key=f"sample{i}"):
            request = {"text": T(f"sample.{i}.q")}

    t_speak, t_upload, t_type = st.tabs([T("tab.speak"), T("tab.upload"), T("tab.type")])
    with t_speak:
        if not engine.voice_ready():
            st.warning(T("voice.off"))
        rec = st.audio_input(T("rec.label"), key="rec")
        if rec is not None:
            data = rec.getvalue()
            sig = hashlib.md5(data).hexdigest()
            if sig != st.session_state.get("done_rec"):
                st.session_state["done_rec"] = sig
                request = {"audio": data, "name": "recording.wav"}
    with t_upload:
        up = st.file_uploader(T("up.label"), type=audio_utils.AUDIO_TYPES, key="upload")
        st.caption(T("up.hint"))
        if up is not None:
            data = up.getvalue()
            (st.video if audio_utils.is_video(up.name) else st.audio)(data)
            sig = hashlib.md5(data).hexdigest()
            if sig != st.session_state.get("done_up"):
                st.session_state["done_up"] = sig
                request = {"audio": data, "name": up.name}
    with t_type:
        with st.form("typeform", border=False):
            typed = st.text_input(T("type.label"), key="typed", placeholder=T("sample.4.q"))
            if st.form_submit_button(T("go"), type="primary", use_container_width=True):
                request = {"text": typed}

    with st.expander(T("demo.title")):
        st.radio(T("demo.weather"), list(SCENARIOS), horizontal=True, key="weather_mode",
                 format_func=lambda k: T({"live": "demo.live", "rain": "demo.rain", "clear": "demo.clear"}[k]))

if request:
    run(text=request.get("text"), audio=request.get("audio"), name=request.get("name", "query.wav"))

if st.session_state["error"]:
    st.error(st.session_state["error"])

# ------------------------------------------------------------------ answer
res = st.session_state["result"]
if res:
    cls, vkey = VERDICT_KEY[res.verdict.label]
    v = res.verdict
    reason = T("reason." + v.code, rain=v.rain, thr=v.threshold)
    chips = ""
    for sg in res.insights.signals:
        params = dict(sg["params"])
        if "alt" in params:
            params["alt"] = engine.mandi_name(params["alt"], lang)
        chips += f'<span class="chip c-{sg["tone"]}">{esc(T("sig." + sg["key"], **params))}</span>'
    conf = f'<div class="conf">{esc(T("conf.label", c=T("conf." + v.confidence)))}</div>' if v.confidence != "n/a" else ""
    verdict_html = (f'<div class="verdict {cls}"><div class="stamp"><div class="en">{esc(T(vkey))}</div></div>'
                    f'<div class="v-body"><p>{esc(reason)}</p><div class="chips">{chips}</div>{conf}</div></div>')

    if res.price:
        e, p = res.entities, res.price
        state = i18n.state_name(engine.MANDIS.get(e.mandi, ("",))[0], lang)
        src = T("price.live") if p.source == "agmarknet" else T("price.demo")
        if res.insights.revenue:
            qty = engine._fmt_qty(res.insights.quantity)
            val = f'<div class="val"><span>{esc(T("kpi.your_qty", q=qty))}</span><b>{esc(money(res.insights.revenue))}</b></div>'
        else:
            val = f'<div class="hint">{esc(T("kpi.qty_hint"))}</div>'
        mandi_txt = engine.mandi_name(e.mandi, lang) + (f", {state}" if state else "")
        board = (f'<div class="board"><div class="row"><span>{esc(T("kpi.crop"))}</span><b>{CROP_ICON[e.crop]} {esc(crop_name(e.crop))}</b></div>'
                 f'<div class="row"><span>{esc(T("kpi.mandi"))}</span><b>{esc(mandi_txt)}</b></div>'
                 f'<div class="price">₹{indic.indian_group(p.modal)}<small>{esc(T("kpi.per_q"))}</small></div>'
                 f'<div class="src">{esc(src)} · {esc(p.date)}</div>{val}</div>')
    else:
        board = (f'<div class="board"><div class="row"><span>{esc(T("kpi.crop"))}</span><b>–</b></div>'
                 f'<div class="row"><span>{esc(T("kpi.mandi"))}</span><b>–</b></div>'
                 f'<div class="hint">{esc(T("kpi.missing"))}</div></div>')
    H(f'<div class="vgrid">{verdict_html}{board}</div>')

    H(f'<div class="convo"><div class="bub you"><small>{esc(T("you"))}</small>{esc(res.transcript)}</div>'
      f'<div class="bub bot"><small>{esc(T("bot"))}</small>{esc(res.advice_text)}</div></div>')
    if res.audio:
        st.audio(res.audio, format="audio/wav", autoplay=bool(st.session_state["fresh"]))
    if res.used_context:
        what = T("and").join(T("w." + w) for w in res.used_context)
        st.caption(T("filled", what=what))

    if res.price and res.weather:
        ins = res.insights
        share = T("wa.text", crop=crop_name(res.entities.crop), mandi=engine.mandi_name(res.entities.mandi, lang),
                  price=indic.indian_group(res.price.modal), verdict=T(vkey), reason=reason)
        a1, a2, _ = st.columns([1.3, 1.3, 3])
        a1.markdown(f'<a class="btn-wa" href="https://wa.me/?text={urllib.parse.quote(share)}" target="_blank" rel="noopener">{esc(T("wa"))}</a>',
                    unsafe_allow_html=True)
        a2.download_button(T("save"), data=res.advice_text.encode("utf-8"), file_name="kisanbol-advice.txt", mime="text/plain")

        mandi_local = engine.mandi_name(res.entities.mandi, lang)
        c_left, c_right = st.columns(2)
        axis_font = "Mukta, 'Noto Sans Gurmukhi', sans-serif"
        cfg = dict(grid=True, gridColor="#E6EAF0", domain=False, labelFont=axis_font, labelColor="#566173")

        lo, hi = min(r["price"] for r in ins.trend), max(r["price"] for r in ins.trend)
        pad = max((hi - lo) * 0.35, hi * 0.01)
        with c_left.container(border=True):
            badge = ("b-live", T("badge.live")) if ins.trend_source == "live" else ("b-demo", T("badge.demo"))
            H(f'<h3 style="margin:0">{esc(T("chart.price", n=len(ins.trend)))}<span class="badge {badge[0]}">{esc(badge[1])}</span></h3>'
              f'<p class="sub" style="margin:0">{esc(T("chart.price_sub", mandi=mandi_local))}</p>')
            df = pd.DataFrame(ins.trend)
            df["label"] = [i18n.day_month(datetime.strptime(d, "%Y-%m-%d"), lang) for d in df["date"]]
            base = alt.Chart(df).encode(
                x=alt.X("label:N", sort=None, axis=alt.Axis(title=None, labelAngle=0, labelOverlap="greedy")),
                y=alt.Y("price:Q", scale=alt.Scale(domain=[lo - pad, hi + pad], nice=False), axis=alt.Axis(title=None, format=",d", tickCount=4)))
            chart = (base.mark_line(color=INK, strokeWidth=2.5) + base.mark_point(color=INK, size=40, filled=True)
                     + alt.Chart(df.tail(1)).mark_point(color=AMBER, size=170, filled=True, stroke=INK, strokeWidth=2)
                     .encode(x=alt.X("label:N", sort=None), y="price:Q")).properties(height=210)
            st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(**cfg), use_container_width=True)
        with c_right.container(border=True):
            badge = ("b-sim", T("badge.sim")) if res.weather.source == "scenario" else ("b-live", T("badge.live"))
            H(f'<h3 style="margin:0">{esc(T("chart.rain"))}<span class="badge {badge[0]}">{esc(badge[1])}</span></h3>'
              f'<p class="sub" style="margin:0">{esc(T("chart.rain_sub", thr=engine.RAIN_THRESHOLD))}</p>')
            wd = pd.DataFrame(res.weather.daily)
            wd["day"] = [i18n.weekday_day(datetime.strptime(d, "%Y-%m-%d"), lang) for d in wd["date"]]
            wd["over"] = wd["rain_prob"] > engine.RAIN_THRESHOLD
            bars = alt.Chart(wd).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=46).encode(
                x=alt.X("day:N", sort=None, axis=alt.Axis(title=None, labelAngle=0)),
                y=alt.Y("rain_prob:Q", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(title=None, values=[0, 25, 50, 75, 100])),
                color=alt.condition(alt.datum.over, alt.value(RED), alt.value(GREEN)), tooltip=["day", "rain_prob", "rain_mm"])
            labels = bars.mark_text(dy=-8, fontWeight="bold", color=INK).encode(text=alt.Text("rain_prob:Q", format=".0f"))
            rule = alt.Chart(pd.DataFrame({"y": [engine.RAIN_THRESHOLD]})).mark_rule(color=INK, strokeDash=[5, 4]).encode(y="y:Q")
            st.altair_chart((bars + labels + rule).properties(height=210).configure_view(strokeWidth=0).configure_axis(**cfg),
                            use_container_width=True)

        if ins.nearby:
            nb = ("b-live", T("badge.live")) if ins.nearby_source == "live" else ("b-demo", T("badge.demo"))
            best = max(ins.nearby, key=lambda r: r["price"])
            rows = ""
            for r in ins.nearby:
                if r["selected"]:
                    diff, dist = esc(T("near.this")), esc(T("near.here"))
                else:
                    sign = "+" if r["diff"] > 0 else "−"
                    diff = f'<span class="{"pos" if r["diff"] > 0 else "neg"}">{sign}₹{indic.indian_group(abs(r["diff"]))}</span>'
                    dist = f'{r["distance_km"]} {esc(T("km"))}'
                star = f'<span class="best">{esc(T("near.best"))}</span>' if r["mandi"] == best["mandi"] and len(ins.nearby) > 1 else ""
                rows += (f'<tr class="{"me" if r["selected"] else ""}"><td>{esc(engine.mandi_name(r["mandi"], lang))}{star}</td>'
                         f'<td>₹{indic.indian_group(r["price"])}</td><td>{diff}</td><td>{dist}</td></tr>')
            H(f'<div class="card"><h3>{esc(T("near.title"))}<span class="badge {nb[0]}">{esc(nb[1])}</span></h3>'
              f'<p class="sub">{esc(T("near.sub"))}</p><table class="mt"><tr><th>{esc(T("near.mandi"))}</th><th>{esc(T("near.price"))}</th>'
              f'<th>{esc(T("near.vs"))}</th><th>{esc(T("near.dist"))}</th></tr>{rows}</table></div>')

    notes = []
    for n in res.warnings:
        if n.public and n.text("en-IN") not in notes:
            params = dict(n.params)
            if "crop" in params:
                params["crop"] = crop_name(params["crop"])
            if "mandi" in params:
                params["mandi"] = engine.mandi_name(params["mandi"], lang)
            notes.append(i18n.t(lang, "note." + n.key, **params))
    notes = list(dict.fromkeys(notes))
    if notes:
        with st.expander(T("notes.title", n=len(notes))):
            for line in notes:
                st.write("• " + line)


# ---------------------------------------------------------------- farm assistant
def _spoken(text: str) -> str:
    return re.sub(r"[*#]|^\d+\.\s*", "", text, flags=re.M)


def _turn_reply(turn: dict, cl: str, history: list) -> "advisor.Reply":
    """The assistant's answer for one turn in language `cl`. Cached per language, so switching language redraws the chat."""
    res = st.session_state.get("result")
    key = (cl, id(res))
    if key not in turn["replies"]:
        flat = []
        for prev in history:  # earlier turns as plain messages, for follow-up questions and the optional model
            r_ = prev["replies"].get(key) or next(iter(prev["replies"].values()), None)
            flat.append({"role": "user", "text": prev["q"] or T("chat.explain")})
            if r_:
                flat.append({"role": "bot", "text": r_.text, "topic": r_.topic})
        turn["replies"][key] = (advisor.explain(res, cl) if turn["explain"]
                                else advisor.reply(turn["q"], cl, res, flat))
    return turn["replies"][key]


def chat_ask(question: str | None = None, explain: bool = False) -> None:
    """Callback: add one question (or an 'explain everything' request) to the conversation."""
    cl = st.session_state["lang"]
    q = (question if question is not None else st.session_state.get("chat_q", "")).strip()
    if not q and not explain:
        return
    chat = st.session_state["chat"]
    for t_ in chat:
        t_["audio"] = None  # only the newest answer keeps its audio
    turn = {"q": q, "explain": explain, "replies": {}, "audio": None}
    rep = _turn_reply(turn, cl, chat)
    if engine.gnani_configured("tts") and rep.topic != "refused":
        try:
            turn["audio"] = engine.synthesize(_spoken(rep.text)[:900], cl)
        except Exception:
            pass
    chat.append(turn)
    st.session_state["chat_q"] = ""


def chat_clear() -> None:
    st.session_state["chat"] = []


with st.container(border=True, key="assistant"):
    H(f'<h3 style="margin:0">{esc(T("chat.title"))}</h3><p class="sub" style="margin:0 0 .5rem">{esc(T("chat.sub"))}</p>')
    st.button("💡 " + T("chat.explain"), key="chat_explain", on_click=chat_ask, kwargs={"explain": True}, use_container_width=True)
    H(f'<p class="sub" style="margin:.4rem 0 .2rem">{esc(T("chat.hint"))}</p>')
    cc = st.columns(3)
    for i, col in enumerate(cc, start=1):
        col.button(T(f"chat.q{i}"), key=f"chat_q_btn{i}", on_click=chat_ask, kwargs={"question": T(f"chat.q{i}")}, use_container_width=True)
    for n, turn in enumerate(st.session_state["chat"]):
        rep = _turn_reply(turn, lang, st.session_state["chat"][:n])
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(T("chat.explain") if turn["explain"] else turn["q"])
        with st.chat_message("assistant", avatar="🌾"):
            st.markdown(rep.text)
            if turn.get("audio") and n == len(st.session_state["chat"]) - 1 and turn["replies"].get((lang, id(st.session_state.get("result")))):
                st.audio(turn["audio"], format="audio/wav")
    with st.form("chat_form", clear_on_submit=False, border=False):
        st.text_input(T("chat.send"), key="chat_q", placeholder=T("chat.placeholder"), label_visibility="collapsed")
        f1, f2 = st.columns([3, 1])
        f1.form_submit_button(T("chat.send"), on_click=chat_ask, use_container_width=True, type="primary")
        f2.form_submit_button(T("chat.clear"), on_click=chat_clear, use_container_width=True)

if st.session_state["history"]:
    with st.expander(T("hist.title", n=len(st.session_state["history"]))):
        for h in st.session_state["history"][:8]:
            icon = {"SELL NOW": "🔴", "HOLD": "🟢"}.get(h["label"], "⚪")
            st.write(f"{icon} **{h['time']}** · {crop_name(h['crop'])}, {engine.mandi_name(h['mandi'], lang)}, "
                     f"₹{indic.indian_group(h['price'])} · {T(VERDICT_KEY[h['label']][1])}")

H(f'<p class="foot">{esc(T("disclaimer"))} {esc(T("privacy"))}</p>')
