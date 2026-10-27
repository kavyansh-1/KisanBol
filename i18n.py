"""Every word the farmer can see, in English, Hindi and Punjabi.

Each entry is (English, Hindi, Punjabi). Keys starting with `dev_` are developer notes (English only)."""
from __future__ import annotations

LANGS = {"en-IN": "English", "hi-IN": "हिन्दी", "pa-IN": "ਪੰਜਾਬੀ"}
_ORDER = ("en-IN", "hi-IN", "pa-IN")

_ENTRIES: dict[str, tuple[str, str, str]] = {
    # ---- hero
    "hero.title": ("Sell your crop today, or wait?", "आज फसल बेचें या रुकें?", "ਅੱਜ ਫ਼ਸਲ ਵੇਚੀਏ ਜਾਂ ਰੁਕੀਏ?"),
    "hero.sub": (
        "Ask in your own words. Get today's mandi price, a 3-day rain warning and one clear answer: sell now or hold.",
        "अपनी भाषा में पूछिए। आज का मंडी भाव, 3 दिन की बारिश की चेतावनी और एक साफ़ जवाब पाइए: अभी बेचें या रुकें।",
        "ਆਪਣੀ ਬੋਲੀ ਵਿੱਚ ਪੁੱਛੋ। ਅੱਜ ਦਾ ਮੰਡੀ ਭਾਅ, 3 ਦਿਨ ਦੇ ਮੀਂਹ ਦੀ ਚੇਤਾਵਨੀ ਅਤੇ ਇੱਕ ਸਾਫ਼ ਜਵਾਬ ਲਓ: ਹੁਣੇ ਵੇਚੋ ਜਾਂ ਰੁਕੋ।"),
    "feat.price": ("Today's mandi price", "आज का मंडी भाव", "ਅੱਜ ਦਾ ਮੰਡੀ ਭਾਅ"),
    "feat.rain": ("3-day rain warning", "3 दिन की बारिश की चेतावनी", "3 ਦਿਨ ਦੇ ਮੀਂਹ ਦੀ ਚੇਤਾਵਨੀ"),
    "feat.call": ("Sell or hold", "बेचें या रुकें", "ਵੇਚੋ ਜਾਂ ਰੁਕੋ"),
    "hero.example": ("You can ask like this", "आप ऐसे पूछ सकते हैं", "ਤੁਸੀਂ ਇਸ ਤਰ੍ਹਾਂ ਪੁੱਛ ਸਕਦੇ ਹੋ"),
    "hero.example_cap": (
        "Speak the way you talk. Hindi, Punjabi and English mixed together is fine.",
        "जैसे बोलते हैं वैसे ही बोलिए। हिंदी, पंजाबी और अंग्रेज़ी मिलाकर बोलना भी ठीक है।",
        "ਜਿਵੇਂ ਬੋਲਦੇ ਹੋ ਉਂਝ ਹੀ ਬੋਲੋ। ਹਿੰਦੀ, ਪੰਜਾਬੀ ਤੇ ਅੰਗਰੇਜ਼ੀ ਰਲਾ ਕੇ ਬੋਲਣਾ ਵੀ ਠੀਕ ਹੈ।"),
    # ---- ask panel
    "ask.title": ("What do you want to know?", "आप क्या जानना चाहते हैं?", "ਤੁਸੀਂ ਕੀ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ?"),
    "ask.hint": (
        "Say the crop and the mandi. Add how much you have, like “50 quintal”, to see what it is worth.",
        "फसल और मंडी का नाम बोलिए। कितनी है यह भी बताइए, जैसे “50 क्विंटल”, ताकि कीमत दिखे।",
        "ਫ਼ਸਲ ਅਤੇ ਮੰਡੀ ਦਾ ਨਾਮ ਦੱਸੋ। ਕਿੰਨੀ ਹੈ ਇਹ ਵੀ ਦੱਸੋ, ਜਿਵੇਂ “50 ਕੁਇੰਟਲ”, ਤਾਂ ਜੋ ਕੀਮਤ ਦਿਖੇ।"),
    "tab.speak": ("Speak", "बोलकर", "ਬੋਲ ਕੇ"),
    "tab.upload": ("Upload audio or video", "ऑडियो या वीडियो डालें", "ਆਡੀਓ ਜਾਂ ਵੀਡੀਓ ਪਾਓ"),
    "tab.type": ("Type", "लिखकर", "ਲਿਖ ਕੇ"),
    "rec.label": ("Tap the mic, speak, then tap again to stop",
                  "माइक दबाइए, बोलिए, फिर रोकने के लिए दोबारा दबाइए",
                  "ਮਾਈਕ ਦਬਾਓ, ਬੋਲੋ, ਫਿਰ ਰੋਕਣ ਲਈ ਦੁਬਾਰਾ ਦਬਾਓ"),
    "up.label": ("Choose an audio or video file", "ऑडियो या वीडियो फ़ाइल चुनिए", "ਆਡੀਓ ਜਾਂ ਵੀਡੀਓ ਫ਼ਾਈਲ ਚੁਣੋ"),
    "up.hint": ("WAV, MP3, M4A, MP4, WebM, OGG and more. The first 60 seconds are used.",
                "WAV, MP3, M4A, MP4, WebM, OGG आदि। पहले 60 सेकंड इस्तेमाल होंगे।",
                "WAV, MP3, M4A, MP4, WebM, OGG ਆਦਿ। ਪਹਿਲੇ 60 ਸਕਿੰਟ ਵਰਤੇ ਜਾਣਗੇ।"),
    "type.label": ("Type your question", "अपना सवाल लिखिए", "ਆਪਣਾ ਸਵਾਲ ਲਿਖੋ"),
    "chat.title": ("Ask the farm assistant", "खेती सहायक से पूछिए", "ਖੇਤੀ ਸਹਾਇਕ ਤੋਂ ਪੁੱਛੋ"),
    "chat.sub": ("Questions about farming only: selling, storage, rain, seeds, fertiliser, pests, loans, insurance.",
                 "सिर्फ़ खेती के सवाल: बेचना, भंडारण, बारिश, बीज, खाद, कीट, कर्ज़, बीमा।",
                 "ਸਿਰਫ਼ ਖੇਤੀ ਦੇ ਸਵਾਲ: ਵੇਚਣਾ, ਭੰਡਾਰ, ਮੀਂਹ, ਬੀਜ, ਖਾਦ, ਕੀੜੇ, ਕਰਜ਼ਾ, ਬੀਮਾ।"),
    "chat.explain": ("Explain everything simply", "सब कुछ आसान शब्दों में समझाइए", "ਸਭ ਕੁਝ ਸੌਖੇ ਸ਼ਬਦਾਂ ਵਿੱਚ ਸਮਝਾਓ"),
    "chat.placeholder": ("For example: How do I keep wheat safe from rain?", "जैसे: बारिश से गेहूं को कैसे बचाएँ?",
                         "ਜਿਵੇਂ: ਕਣਕ ਨੂੰ ਮੀਂਹ ਤੋਂ ਕਿਵੇਂ ਬਚਾਈਏ?"),
    "chat.send": ("Ask", "पूछिए", "ਪੁੱਛੋ"),
    "chat.clear": ("Clear chat", "बातचीत साफ़ करें", "ਗੱਲਬਾਤ ਮਿਟਾਓ"),
    "chat.hint": ("Try one", "इनमें से कोई आज़माइए", "ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਅਜ਼ਮਾਓ"),
    "chat.q1": ("How do I keep wheat safe from rain?", "बारिश से गेहूं को कैसे बचाएँ?", "ਕਣਕ ਨੂੰ ਮੀਂਹ ਤੋਂ ਕਿਵੇਂ ਬਚਾਈਏ?"),
    "chat.q2": ("Is it worth taking my crop to another mandi?", "क्या दूसरी मंडी में माल ले जाना फ़ायदे का है?",
                "ਕੀ ਦੂਜੀ ਮੰਡੀ ਵਿੱਚ ਮਾਲ ਲਿਜਾਣਾ ਫ਼ਾਇਦੇ ਦਾ ਹੈ?"),
    "chat.q3": ("What should I do if hail damages my crop?", "ओले से फसल ख़राब हो जाए तो क्या करें?",
                "ਗੜਿਆਂ ਨਾਲ ਫ਼ਸਲ ਖ਼ਰਾਬ ਹੋ ਜਾਵੇ ਤਾਂ ਕੀ ਕਰੀਏ?"),
    "go": ("Get advice", "सलाह लीजिए", "ਸਲਾਹ ਲਓ"),
    "examples": ("Try an example", "उदाहरण आज़माइए", "ਇੱਕ ਮਿਸਾਲ ਅਜ਼ਮਾਓ"),
    "thinking": ("Listening, checking price and weather…", "सुन रहा हूँ, भाव और मौसम देख रहा हूँ…",
                 "ਸੁਣ ਰਿਹਾ ਹਾਂ, ਭਾਅ ਤੇ ਮੌਸਮ ਵੇਖ ਰਿਹਾ ਹਾਂ…"),
    "demo.title": ("Demo options", "डेमो विकल्प", "ਡੈਮੋ ਵਿਕਲਪ"),
    "demo.weather": ("Weather", "मौसम", "ਮੌਸਮ"),
    "demo.live": ("Live forecast", "असली पूर्वानुमान", "ਅਸਲੀ ਅਨੁਮਾਨ"),
    "demo.rain": ("Show heavy rain (demo)", "भारी बारिश दिखाएँ (डेमो)", "ਭਾਰੀ ਮੀਂਹ ਦਿਖਾਓ (ਡੈਮੋ)"),
    "demo.clear": ("Show clear skies (demo)", "साफ़ मौसम दिखाएँ (डेमो)", "ਸਾਫ਼ ਮੌਸਮ ਦਿਖਾਓ (ਡੈਮੋ)"),
    "ctx.follow": ("Following up on {crop} · {mandi}. Say only what changes, for example “aur Karnal mein?”",
                   "{crop} · {mandi} पर बात जारी है। सिर्फ़ जो बदले वह बोलिए, जैसे “और करनाल में?”",
                   "{crop} · {mandi} ਬਾਰੇ ਗੱਲ ਜਾਰੀ ਹੈ। ਸਿਰਫ਼ ਜੋ ਬਦਲੇ ਉਹ ਬੋਲੋ, ਜਿਵੇਂ “ਹੋਰ ਕਰਨਾਲ ਵਿੱਚ?”"),
    "ctx.new": ("New question", "नया सवाल", "ਨਵਾਂ ਸਵਾਲ"),
    "voice.off": (
        "Voice recognition is not set up on this computer yet, so recordings cannot be understood. Typing and the examples work now.",
        "इस कंप्यूटर पर आवाज़ पहचान अभी चालू नहीं है, इसलिए रिकॉर्डिंग समझी नहीं जाएगी। लिखकर या उदाहरण दबाकर काम चल जाएगा।",
        "ਇਸ ਕੰਪਿਊਟਰ 'ਤੇ ਆਵਾਜ਼ ਦੀ ਪਛਾਣ ਅਜੇ ਚਾਲੂ ਨਹੀਂ, ਇਸ ਲਈ ਰਿਕਾਰਡਿੰਗ ਸਮਝੀ ਨਹੀਂ ਜਾਵੇਗੀ। ਲਿਖ ਕੇ ਜਾਂ ਮਿਸਾਲ ਦਬਾ ਕੇ ਕੰਮ ਚੱਲ ਜਾਵੇਗਾ।"),
    "sample.1": ("Wheat · Khanna", "गेहूं · खन्ना", "ਕਣਕ · ਖੰਨਾ"),
    "sample.1.q": ("What is the wheat price in Khanna mandi, should I sell or hold?",
                   "खन्ना मंडी में गेहूं का भाव क्या है, बेचूं या रुकूं?",
                   "ਖੰਨਾ ਮੰਡੀ ਵਿੱਚ ਕਣਕ ਦਾ ਭਾਅ ਕੀ ਹੈ, ਵੇਚਾਂ ਜਾਂ ਰੁਕਾਂ?"),
    "sample.2": ("Rice · Karnal · 80 quintal", "चावल · करनाल · 80 क्विंटल", "ਚੌਲ · ਕਰਨਾਲ · 80 ਕੁਇੰਟਲ"),
    "sample.2.q": ("Rice price in Karnal mandi? I have 80 quintal, should I sell now?",
                   "करनाल मंडी में चावल का भाव क्या है, मेरे पास 80 क्विंटल है, अभी बेच दूँ?",
                   "ਕਰਨਾਲ ਮੰਡੀ ਵਿੱਚ ਚੌਲ ਦਾ ਭਾਅ ਕੀ ਹੈ, ਮੇਰੇ ਕੋਲ 80 ਕੁਇੰਟਲ ਹੈ, ਹੁਣੇ ਵੇਚ ਦਿਆਂ?"),
    "sample.3": ("Mustard · Hisar", "सरसों · हिसार", "ਸਰ੍ਹੋਂ · ਹਿਸਾਰ"),
    "sample.3.q": ("Mustard price in Hisar mandi, should I keep it or sell?",
                   "हिसार मंडी में सरसों का भाव क्या चल रहा है, रख लूँ या बेच दूँ?",
                   "ਹਿਸਾਰ ਮੰਡੀ ਵਿੱਚ ਸਰ੍ਹੋਂ ਦਾ ਭਾਅ ਕੀ ਚੱਲ ਰਿਹਾ ਹੈ, ਰੱਖ ਲਵਾਂ ਜਾਂ ਵੇਚ ਦਿਆਂ?"),
    "sample.4": ("Mixed language", "मिली-जुली भाषा", "ਰਲੀ-ਮਿਲੀ ਬੋਲੀ"),
    "sample.4.q": ("Gehu ka rate kya chal raha hai Khanna mandi mein, hold karun ya bech doon?",) * 3,
    # ---- verdict
    "verdict.sell": ("SELL NOW", "अभी बेचिए", "ਹੁਣੇ ਵੇਚੋ"),
    "verdict.hold": ("HOLD", "रुकिए", "ਰੁਕੋ"),
    "verdict.none": ("NEED MORE INFO", "और जानकारी चाहिए", "ਹੋਰ ਜਾਣਕਾਰੀ ਚਾਹੀਦੀ"),
    "reason.sell": (
        "Rain chance is up to {rain}% in the next 3 days (above {thr}%). Rain can damage stored grain.",
        "अगले 3 दिनों में बारिश की संभावना {rain}% तक है ({thr}% से ज़्यादा)। बारिश से रखा अनाज भीग सकता है।",
        "ਅਗਲੇ 3 ਦਿਨਾਂ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {rain}% ਤੱਕ ਹੈ ({thr}% ਤੋਂ ਵੱਧ)। ਮੀਂਹ ਨਾਲ ਰੱਖਿਆ ਅਨਾਜ ਭਿੱਜ ਸਕਦਾ ਹੈ।"),
    "reason.hold": (
        "Rain chance is at most {rain}% in the next 3 days (not above {thr}%), so waiting is low risk.",
        "अगले 3 दिनों में बारिश की संभावना अधिकतम {rain}% है ({thr}% से ज़्यादा नहीं), इसलिए रुकना कम जोखिम वाला है।",
        "ਅਗਲੇ 3 ਦਿਨਾਂ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ ਵੱਧ ਤੋਂ ਵੱਧ {rain}% ਹੈ ({thr}% ਤੋਂ ਵੱਧ ਨਹੀਂ), ਇਸ ਲਈ ਰੁਕਣਾ ਘੱਟ ਜੋਖ਼ਮ ਵਾਲਾ ਹੈ।"),
    "reason.no_weather": (
        "The weather forecast is not available, so no sell or hold advice is given.",
        "मौसम का पूर्वानुमान नहीं मिल पाया, इसलिए बेचने या रुकने की सलाह नहीं दी गई।",
        "ਮੌਸਮ ਦਾ ਅਨੁਮਾਨ ਨਹੀਂ ਮਿਲ ਸਕਿਆ, ਇਸ ਲਈ ਵੇਚਣ ਜਾਂ ਰੁਕਣ ਦੀ ਸਲਾਹ ਨਹੀਂ ਦਿੱਤੀ ਗਈ।"),
    "reason.no_entities": (
        "Tell me the crop and the mandi, for example “wheat, Khanna mandi”.",
        "फसल और मंडी का नाम बताइए, जैसे “गेहूं, खन्ना मंडी”।",
        "ਫ਼ਸਲ ਅਤੇ ਮੰਡੀ ਦਾ ਨਾਮ ਦੱਸੋ, ਜਿਵੇਂ “ਕਣਕ, ਖੰਨਾ ਮੰਡੀ”।"),
    "conf.label": ("How sure: {c}", "भरोसा: {c}", "ਭਰੋਸਾ: {c}"),
    "conf.High": ("High", "ऊँचा", "ਉੱਚਾ"),
    "conf.Medium": ("Medium", "मध्यम", "ਦਰਮਿਆਨਾ"),
    "conf.Low": ("Low", "कम", "ਘੱਟ"),
    # ---- price board
    "kpi.crop": ("Crop", "फसल", "ਫ਼ਸਲ"),
    "kpi.mandi": ("Mandi", "मंडी", "ਮੰਡੀ"),
    "kpi.per_q": ("per quintal", "प्रति क्विंटल", "ਪ੍ਰਤੀ ਕੁਇੰਟਲ"),
    "kpi.your_qty": ("Your {q} quintals", "आपके {q} क्विंटल", "ਤੁਹਾਡੇ {q} ਕੁਇੰਟਲ"),
    "kpi.qty_hint": ("Say how much you have, like “50 quintal”, to see its value.",
                     "कितना माल है यह बोलिए, जैसे “50 क्विंटल”, तो कीमत दिखेगी।",
                     "ਕਿੰਨਾ ਮਾਲ ਹੈ ਇਹ ਬੋਲੋ, ਜਿਵੇਂ “50 ਕੁਇੰਟਲ”, ਤਾਂ ਕੀਮਤ ਦਿਖੇਗੀ।"),
    "kpi.missing": ("Tell me a crop and a mandi, for example “wheat, Khanna mandi”.",
                    "फसल और मंडी बताइए, जैसे “गेहूं, खन्ना मंडी”।", "ਫ਼ਸਲ ਅਤੇ ਮੰਡੀ ਦੱਸੋ, ਜਿਵੇਂ “ਕਣਕ, ਖੰਨਾ ਮੰਡੀ”।"),
    "badge.live": ("Live", "ताज़ा", "ਤਾਜ਼ਾ"),
    "badge.demo": ("Demo data", "डेमो डेटा", "ਡੈਮੋ ਡਾਟਾ"),
    "badge.sim": ("Demo weather", "डेमो मौसम", "ਡੈਮੋ ਮੌਸਮ"),
    "price.live": ("Live price", "ताज़ा भाव", "ਤਾਜ਼ਾ ਭਾਅ"),
    "price.demo": ("Demo price", "डेमो भाव", "ਡੈਮੋ ਭਾਅ"),
    # ---- answer
    "you": ("You said", "आपने कहा", "ਤੁਸੀਂ ਕਿਹਾ"),
    "bot": ("KisanBol says", "किसानबोल कहता है", "ਕਿਸਾਨਬੋਲ ਕਹਿੰਦਾ ਹੈ"),
    "wa": ("Share on WhatsApp", "WhatsApp पर भेजें", "WhatsApp 'ਤੇ ਭੇਜੋ"),
    "wa.text": ("KisanBol: {crop} in {mandi} is ₹{price} per quintal. {verdict}. {reason}",
                "किसानबोल: {mandi} में {crop} का भाव ₹{price} प्रति क्विंटल है। {verdict}। {reason}",
                "ਕਿਸਾਨਬੋਲ: {mandi} ਵਿੱਚ {crop} ਦਾ ਭਾਅ ₹{price} ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਹੈ। {verdict}। {reason}"),
    "save": ("Save advice", "सलाह सहेजें", "ਸਲਾਹ ਸੰਭਾਲੋ"),
    "chart.price": ("Price, last {n} days", "भाव, पिछले {n} दिन", "ਭਾਅ, ਪਿਛਲੇ {n} ਦਿਨ"),
    "chart.price_sub": ("Rupees per quintal in {mandi}", "{mandi} में रुपये प्रति क्विंटल", "{mandi} ਵਿੱਚ ਰੁਪਏ ਪ੍ਰਤੀ ਕੁਇੰਟਲ"),
    "chart.rain": ("Rain chance, next 3 days", "अगले 3 दिन बारिश की संभावना", "ਅਗਲੇ 3 ਦਿਨ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ"),
    "chart.rain_sub": ("Dashed line is {thr}%. Above it means sell now.",
                       "बिंदीदार रेखा {thr}% है। इससे ऊपर यानी अभी बेचिए।",
                       "ਬਿੰਦੀਆਂ ਵਾਲੀ ਲਕੀਰ {thr}% ਹੈ। ਇਸ ਤੋਂ ਉੱਪਰ ਮਤਲਬ ਹੁਣੇ ਵੇਚੋ।"),
    "near.title": ("Nearby mandis", "आस-पास की मंडियाँ", "ਨੇੜਲੀਆਂ ਮੰਡੀਆਂ"),
    "near.sub": ("Same crop within 250 km. A better price may be worth the trip.",
                 "250 किमी के अंदर वही फसल। बेहतर भाव के लिए जाना फ़ायदे का हो सकता है।",
                 "250 ਕਿਮੀ ਦੇ ਅੰਦਰ ਉਹੀ ਫ਼ਸਲ। ਬਿਹਤਰ ਭਾਅ ਲਈ ਜਾਣਾ ਫ਼ਾਇਦੇ ਦਾ ਹੋ ਸਕਦਾ ਹੈ।"),
    "near.mandi": ("Mandi", "मंडी", "ਮੰਡੀ"),
    "near.price": ("Price per quintal", "प्रति क्विंटल भाव", "ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਭਾਅ"),
    "near.vs": ("Compared with here", "यहाँ से तुलना", "ਇੱਥੋਂ ਨਾਲ ਤੁਲਨਾ"),
    "near.dist": ("Distance", "दूरी", "ਦੂਰੀ"),
    "near.this": ("this mandi", "यही मंडी", "ਇਹੀ ਮੰਡੀ"),
    "near.here": ("here", "यहीं", "ਇੱਥੇ"),
    "near.best": ("Best price", "सबसे अच्छा भाव", "ਸਭ ਤੋਂ ਵਧੀਆ ਭਾਅ"),
    "km": ("km", "किमी", "ਕਿਮੀ"),
    "hist.title": ("Recent questions ({n})", "हाल के सवाल ({n})", "ਹਾਲੀਆ ਸਵਾਲ ({n})"),
    "notes.title": ("About this data ({n})", "इस जानकारी के बारे में ({n})", "ਇਸ ਜਾਣਕਾਰੀ ਬਾਰੇ ({n})"),
    "filled": ("Used the {what} from your previous question.", "पिछले सवाल से {what} लिया गया।",
               "ਪਿਛਲੇ ਸਵਾਲ ਤੋਂ {what} ਲਿਆ ਗਿਆ।"),
    "w.crop": ("crop", "फसल", "ਫ਼ਸਲ"), "w.mandi": ("mandi", "मंडी", "ਮੰਡੀ"),
    "w.quantity": ("quantity", "मात्रा", "ਮਾਤਰਾ"), "and": (" and ", " और ", " ਅਤੇ "),
    "disclaimer": ("Decision support, not financial advice. Prices and forecasts can change.",
                   "यह सिर्फ़ मदद के लिए है, वित्तीय सलाह नहीं। भाव और मौसम बदल सकते हैं।",
                   "ਇਹ ਸਿਰਫ਼ ਮਦਦ ਲਈ ਹੈ, ਵਿੱਤੀ ਸਲਾਹ ਨਹੀਂ। ਭਾਅ ਅਤੇ ਮੌਸਮ ਬਦਲ ਸਕਦੇ ਹਨ।"),
    "privacy": ("Your recordings are not stored.", "आपकी रिकॉर्डिंग सहेजी नहीं जाती।", "ਤੁਹਾਡੀ ਰਿਕਾਰਡਿੰਗ ਸੰਭਾਲੀ ਨਹੀਂ ਜਾਂਦੀ।"),
    # ---- signals (chips)
    "sig.rain": ("Rain chance up to {rain}% in 3 days", "3 दिन में बारिश की संभावना {rain}% तक",
                 "3 ਦਿਨਾਂ ਵਿੱਚ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {rain}% ਤੱਕ"),
    "sig.up": ("Price rising ({pct}% in {n} days)", "भाव बढ़ रहा है ({n} दिन में {pct}%)",
               "ਭਾਅ ਵਧ ਰਿਹਾ ਹੈ ({n} ਦਿਨਾਂ ਵਿੱਚ {pct}%)"),
    "sig.down": ("Price falling ({pct}% in {n} days)", "भाव गिर रहा है ({n} दिन में {pct}%)",
                 "ਭਾਅ ਘਟ ਰਿਹਾ ਹੈ ({n} ਦਿਨਾਂ ਵਿੱਚ {pct}%)"),
    "sig.flat": ("Price steady over {n} days", "{n} दिन में भाव स्थिर है", "{n} ਦਿਨਾਂ ਵਿੱਚ ਭਾਅ ਸਥਿਰ ਹੈ"),
    "sig.better": ("{alt} pays ₹{diff} more, {km} km away", "{alt} में ₹{diff} ज़्यादा मिल रहा है, {km} किमी दूर",
                   "{alt} ਵਿੱਚ ₹{diff} ਵੱਧ ਮਿਲ ਰਿਹਾ ਹੈ, {km} ਕਿਮੀ ਦੂਰ"),
    "sig.soft": ("Prices are softening: consider selling part of the stock",
                 "भाव नरम पड़ रहे हैं: कुछ माल बेचने पर विचार करें",
                 "ਭਾਅ ਨਰਮ ਪੈ ਰਹੇ ਹਨ: ਕੁਝ ਮਾਲ ਵੇਚਣ ਬਾਰੇ ਸੋਚੋ"),
    # ---- errors
    "err.no_input": ("Record, upload or type a question first.", "पहले सवाल बोलिए, फ़ाइल डालिए या लिखिए।",
                     "ਪਹਿਲਾਂ ਸਵਾਲ ਬੋਲੋ, ਫ਼ਾਈਲ ਪਾਓ ਜਾਂ ਲਿਖੋ।"),
    "err.no_key": ("Voice is not set up yet. Please type your question.", "आवाज़ की सुविधा अभी चालू नहीं है। कृपया सवाल लिखिए।",
                   "ਆਵਾਜ਼ ਦੀ ਸਹੂਲਤ ਅਜੇ ਚਾਲੂ ਨਹੀਂ। ਕਿਰਪਾ ਕਰਕੇ ਸਵਾਲ ਲਿਖੋ।"),
    "err.no_stt": ("Voice recognition is not set up on this computer. Please type your question.",
                   "इस कंप्यूटर पर आवाज़ पहचान चालू नहीं है। कृपया सवाल लिखिए।",
                   "ਇਸ ਕੰਪਿਊਟਰ 'ਤੇ ਆਵਾਜ਼ ਦੀ ਪਛਾਣ ਚਾਲੂ ਨਹੀਂ। ਕਿਰਪਾ ਕਰਕੇ ਸਵਾਲ ਲਿਖੋ।"),
    "err.stt_empty": ("Could not hear a question. Speak a little louder or longer, or type it.",
                      "सवाल सुनाई नहीं दिया। थोड़ा ज़ोर से या ज़्यादा देर बोलिए, या लिखिए।",
                      "ਸਵਾਲ ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤਾ। ਥੋੜ੍ਹਾ ਉੱਚਾ ਜਾਂ ਵੱਧ ਦੇਰ ਬੋਲੋ, ਜਾਂ ਲਿਖੋ।"),
    "err.stt_service": ("The voice service could not be reached. Try again, or type your question.",
                        "आवाज़ सेवा से संपर्क नहीं हो पाया। दोबारा कोशिश कीजिए, या सवाल लिखिए।",
                        "ਆਵਾਜ਼ ਸੇਵਾ ਨਾਲ ਸੰਪਰਕ ਨਹੀਂ ਹੋ ਸਕਿਆ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ, ਜਾਂ ਸਵਾਲ ਲਿਖੋ।"),
    "err.stt_local": ("The offline voice model could not start (it needs a one-time download). Please type your question.",
                      "ऑफ़लाइन आवाज़ मॉडल शुरू नहीं हो पाया (इसे एक बार डाउनलोड करना पड़ता है)। कृपया सवाल लिखिए।",
                      "ਆਫ਼ਲਾਈਨ ਆਵਾਜ਼ ਮਾਡਲ ਸ਼ੁਰੂ ਨਹੀਂ ਹੋ ਸਕਿਆ (ਇਸਨੂੰ ਇੱਕ ਵਾਰ ਡਾਊਨਲੋਡ ਕਰਨਾ ਪੈਂਦਾ ਹੈ)। ਕਿਰਪਾ ਕਰਕੇ ਸਵਾਲ ਲਿਖੋ।"),
    "err.tts_service": ("The spoken reply is not available right now.", "बोलकर जवाब अभी उपलब्ध नहीं है।",
                        "ਬੋਲ ਕੇ ਜਵਾਬ ਹੁਣੇ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।"),
    "err.bad_audio": ("This file could not be read as audio. Try a WAV, MP3, M4A, MP4 or WebM file.",
                      "यह फ़ाइल ऑडियो के रूप में नहीं पढ़ी जा सकी। WAV, MP3, M4A, MP4 या WebM फ़ाइल आज़माइए।",
                      "ਇਹ ਫ਼ਾਈਲ ਆਡੀਓ ਵਜੋਂ ਨਹੀਂ ਪੜ੍ਹੀ ਜਾ ਸਕੀ। WAV, MP3, M4A, MP4 ਜਾਂ WebM ਫ਼ਾਈਲ ਅਜ਼ਮਾਓ।"),
    "err.too_big": ("This file is too large. The limit is {mb} MB.", "यह फ़ाइल बहुत बड़ी है। सीमा {mb} MB है।",
                    "ਇਹ ਫ਼ਾਈਲ ਬਹੁਤ ਵੱਡੀ ਹੈ। ਹੱਦ {mb} MB ਹੈ।"),
    "err.no_ffmpeg": ("This file type needs the audio converter. Run: pip install imageio-ffmpeg",
                      "इस फ़ाइल के लिए ऑडियो कन्वर्टर चाहिए। चलाइए: pip install imageio-ffmpeg",
                      "ਇਸ ਫ਼ਾਈਲ ਲਈ ਆਡੀਓ ਕਨਵਰਟਰ ਚਾਹੀਦਾ ਹੈ। ਚਲਾਓ: pip install imageio-ffmpeg"),
    "err.generic": ("Something went wrong. Please try again.", "कुछ गड़बड़ हो गई। कृपया दोबारा कोशिश कीजिए।",
                    "ਕੁਝ ਗੜਬੜ ਹੋ ਗਈ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।"),
    # ---- data notes shown to the farmer
    "note.demo_price": ("This price is demo data, not live.", "यह भाव डेमो है, ताज़ा नहीं।", "ਇਹ ਭਾਅ ਡੈਮੋ ਹੈ, ਤਾਜ਼ਾ ਨਹੀਂ।"),
    "note.no_live_record": ("No live price was found for {crop} at {mandi}, so a demo price is shown.",
                            "{mandi} में {crop} का ताज़ा भाव नहीं मिला, इसलिए डेमो भाव दिखाया गया है।",
                            "{mandi} ਵਿੱਚ {crop} ਦਾ ਤਾਜ਼ਾ ਭਾਅ ਨਹੀਂ ਮਿਲਿਆ, ਇਸ ਲਈ ਡੈਮੋ ਭਾਅ ਦਿਖਾਇਆ ਗਿਆ ਹੈ।"),
    "note.agmark_unavailable": ("The price service could not be reached, so a demo price is shown.",
                                "भाव सेवा से संपर्क नहीं हो पाया, इसलिए डेमो भाव दिखाया गया है।",
                                "ਭਾਅ ਸੇਵਾ ਨਾਲ ਸੰਪਰਕ ਨਹੀਂ ਹੋ ਸਕਿਆ, ਇਸ ਲਈ ਡੈਮੋ ਭਾਅ ਦਿਖਾਇਆ ਗਿਆ ਹੈ।"),
    "note.weather_unavailable": ("The weather service could not be reached.", "मौसम सेवा से संपर्क नहीं हो पाया।",
                                 "ਮੌਸਮ ਸੇਵਾ ਨਾਲ ਸੰਪਰਕ ਨਹੀਂ ਹੋ ਸਕਿਆ।"),
    "note.weather_unlocated": ("Could not find {mandi} for the forecast.", "पूर्वानुमान के लिए {mandi} नहीं मिली।",
                               "ਅਨੁਮਾਨ ਲਈ {mandi} ਨਹੀਂ ਮਿਲੀ।"),
    "note.scenario": ("The weather shown is a demo, not the real forecast.", "दिखाया गया मौसम डेमो है, असली पूर्वानुमान नहीं।",
                      "ਦਿਖਾਇਆ ਮੌਸਮ ਡੈਮੋ ਹੈ, ਅਸਲੀ ਅਨੁਮਾਨ ਨਹੀਂ।"),
    "note.tts_unavailable": ("The spoken reply is not available right now.", "बोलकर जवाब अभी उपलब्ध नहीं है।",
                             "ਬੋਲ ਕੇ ਜਵਾਬ ਹੁਣੇ ਉਪਲਬਧ ਨਹੀਂ ਹੈ।"),
}

# developer-only notes (English only, never shown to the farmer)
_DEV = {
    "dev_evon_extract": "Evon extraction failed ({exc}); used rule-based extraction.",
    "dev_evon_phrase": "Evon phrasing failed; used the standard advice template.",
    "dev_evon_dropped": "Evon's rephrasing dropped a fact; used the standard advice template.",
    "dev_no_agmarknet_key": "DATA_GOV_IN_API_KEY not set; showing demo prices, not live Agmarknet data.",
}

TEXT: dict[str, dict[str, str]] = {lang: {} for lang in _ORDER}
for _k, _v in _ENTRIES.items():
    for _lang, _s in zip(_ORDER, _v):
        TEXT[_lang][_k] = _s
for _k, _s in _DEV.items():
    for _lang in _ORDER:
        TEXT[_lang][_k] = _s

PUBLIC_NOTES = ("demo_price", "no_live_record", "agmark_unavailable", "weather_unavailable",
                "weather_unlocated", "scenario", "tts_unavailable")

STATE_NAMES = {"hi-IN": {"Punjab": "पंजाब", "Haryana": "हरियाणा"}, "pa-IN": {"Punjab": "ਪੰਜਾਬ", "Haryana": "ਹਰਿਆਣਾ"}}
_WEEKDAYS = {"en-IN": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
             "hi-IN": ["सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "रवि"],
             "pa-IN": ["ਸੋਮ", "ਮੰਗਲ", "ਬੁੱਧ", "ਵੀਰ", "ਸ਼ੁੱਕਰ", "ਸ਼ਨਿੱਚਰ", "ਐਤ"]}
_MONTHS = {"en-IN": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
           "hi-IN": ["जन", "फ़र", "मार्च", "अप्रै", "मई", "जून", "जुला", "अग", "सित", "अक्टू", "नव", "दिस"],
           "pa-IN": ["ਜਨ", "ਫ਼ਰ", "ਮਾਰਚ", "ਅਪ੍ਰੈ", "ਮਈ", "ਜੂਨ", "ਜੁਲਾ", "ਅਗ", "ਸਤੰ", "ਅਕਤੂ", "ਨਵੰ", "ਦਸੰ"]}


def t(lang: str, key: str, **kw) -> str:
    """Translate `key` into `lang`, falling back to English, then to the key itself."""
    s = TEXT.get(lang, TEXT["en-IN"]).get(key) or TEXT["en-IN"].get(key) or key
    try:
        return s.format(**kw) if kw else s
    except (KeyError, IndexError):
        return s


def state_name(state: str, lang: str) -> str:
    return STATE_NAMES.get(lang, {}).get(state, state)


def weekday_day(d, lang: str) -> str:
    """'Sun 25' / 'रवि 25' for a date."""
    return f"{_WEEKDAYS.get(lang, _WEEKDAYS['en-IN'])[d.weekday()]} {d.day}"


def day_month(d, lang: str) -> str:
    """'25 Oct' / '25 अक्टू'."""
    return f"{d.day} {_MONTHS.get(lang, _MONTHS['en-IN'])[d.month - 1]}"
