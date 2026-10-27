"""Farm assistant: answers farming questions in English, Hindi or Punjabi.

Rules it follows:
  * Farming only. Anything else gets a polite redirect.
  * Numbers (price, rain chance, verdict) always come from the live result, never from guesswork.
  * Works with no AI model: a built-in guide covers common topics.
    If an OpenAI-compatible model is configured (EVON_BASE_URL) it answers open questions, within the same limits.
  * Never invents doses, subsidy amounts or MSP figures; it points to the right office or helpline instead.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import kisanbol_engine as engine

LANG_NAME = {"en-IN": "English", "hi-IN": "Hindi (Devanagari script)", "pa-IN": "Punjabi (Gurmukhi script)"}
_I = {"en-IN": 0, "hi-IN": 1, "pa-IN": 2}

# ---- what counts as farming --------------------------------------------------------------------
AGRI_WORDS = (
    "crop", "farm", "kisan", "kheti", "fasal", "फसल", "खेती", "किसान", "ਫ਼ਸਲ", "ਫਸਲ", "ਖੇਤੀ", "ਕਿਸਾਨ", "ਖੇਤ", "खेत",
    "mandi", "मंडी", "ਮੰਡੀ", "wheat", "gehu", "gehun", "गेहूं", "गेहू", "ਕਣਕ", "kanak", "rice", "chawal", "चावल", "ਚੌਲ",
    "paddy", "dhan", "धान", "ਝੋਨਾ", "jhona", "maize", "makka", "मक्का", "ਮੱਕੀ", "mustard", "sarson", "सरसों", "ਸਰ੍ਹੋਂ",
    "cotton", "kapas", "कपास", "ਕਪਾਹ", "potato", "aloo", "आलू", "ਆਲੂ", "onion", "pyaz", "प्याज", "ਪਿਆਜ਼", "tomato",
    "tamatar", "टमाटर", "ਟਮਾਟਰ", "sugarcane", "ganna", "गन्ना", "ਗੰਨਾ", "seed", "beej", "बीज", "ਬੀਜ", "soil", "mitti",
    "मिट्टी", "ਮਿੱਟੀ", "tractor", "irrigat", "sinchai", "सिंचाई", "ਸਿੰਚਾਈ", "paani", "पानी", "ਪਾਣੀ", "weather", "mausam",
    "मौसम", "ਮੌਸਮ", "rain", "baarish", "barish", "बारिश", "बरसात", "ਮੀਂਹ", "ਬਾਰਿਸ਼", "price", "bhav", "bhaav", "भाव", "ਭਾਅ",
    "rate", "sell", "bech", "बेच", "ਵੇਚ", "hold", "store", "storage", "godown", "भंडार", "ਭੰਡਾਰ", "fertili", "khad", "खाद",
    "ਖਾਦ", "urea", "यूरिया", "ਯੂਰੀਆ", "pest", "insect", "keet", "कीट", "कीड़", "ਕੀੜ", "dawa", "दवा", "दवाई", "ਦਵਾਈ", "medicine", "pesticide", "कीटनाशक", "ਕੀਟਨਾਸ਼ਕ", "spray", "छिड़काव", "ਸਪਰੇਅ", "disease",
    "rog", "रोग", "ਬਿਮਾਰੀ", "harvest", "katai", "कटाई", "ਵਾਢੀ", "msp", "एमएसपी", "ਐੱਮਐੱਸਪੀ", "loan", "kcc", "कर्ज", "ਕਰਜ਼",
    "kisan credit", "किसान क्रेडिट", "insurance", "bima", "बीमा", "ਬੀਮਾ", "subsidy", "सब्सिडी", "quintal", "क्विंटल",
    "ਕੁਇੰਟਲ", "arhtiya", "आढ़ती", "ਆੜ੍ਹਤੀ", "tarpaulin", "तिरपाल", "ਤਰਪਾਲ", "livestock", "dairy", "cattle", "cow", "buffalo",
    "dudh", "दूध", "ਦੁੱਧ", "gai", "गाय", "bhains", "भैंस", "ਮੱਝ", "organic", "jaivik", "जैविक", "ਜੈਵਿਕ", "krishi", "कृषि",
    "ਖੇਤੀਬਾੜੀ", "kvk", "grain", "anaaj", "अनाज", "ਅਨਾਜ", "mandi", "yield", "paidawar", "उपज", "ਜਿਣਸ", "ਝਾੜ",
)

# (topic, keywords, answers en/hi/pa). Order = priority. Keep answers general: no doses, no figures that change.
_GUIDE: list[tuple[str, tuple[str, ...], tuple[str, str, str]]] = [
    ("pest", ("pest", "insect", "keet", "कीट", "कीड़", "ਕੀੜ", "dawa", "दवा", "दवाई", "ਦਵਾਈ", "medicine", "pesticide", "कीटनाशक", "ਕੀਟਨਾਸ਼ਕ", "spray", "छिड़काव", "ਸਪਰੇਅ", "disease", "rog", "रोग", "ਬਿਮਾਰੀ", "fungus", "इल्ली", "sundi", "सुंडी"), (
        "Do not spray in a hurry. First look closely at the leaves and stems, find out what the pest or disease is, and take a leaf or plant sample to your nearest Krishi Vigyan Kendra or agriculture officer. They will tell you the right product and dose for your crop. The Kisan Call Centre (1800-180-1551, toll-free) also gives free advice.",
        "जल्दबाज़ी में छिड़काव न कीजिए। पहले पत्तों और तनों को ध्यान से देखिए, पता कीजिए कि कौन-सा कीट या रोग है, और पौधे या पत्ते का नमूना नज़दीकी कृषि विज्ञान केंद्र या कृषि अधिकारी को दिखाइए। वे आपकी फसल के लिए सही दवा और मात्रा बताएँगे। किसान कॉल सेंटर (1800-180-1551, निःशुल्क) भी मुफ़्त सलाह देता है।",
        "ਕਾਹਲੀ ਵਿੱਚ ਸਪਰੇਅ ਨਾ ਕਰੋ। ਪਹਿਲਾਂ ਪੱਤਿਆਂ ਤੇ ਤਣਿਆਂ ਨੂੰ ਧਿਆਨ ਨਾਲ ਦੇਖੋ, ਪਤਾ ਕਰੋ ਕਿ ਕਿਹੜਾ ਕੀੜਾ ਜਾਂ ਬਿਮਾਰੀ ਹੈ, ਅਤੇ ਬੂਟੇ ਜਾਂ ਪੱਤੇ ਦਾ ਨਮੂਨਾ ਨੇੜਲੇ ਖੇਤੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਜਾਂ ਖੇਤੀਬਾੜੀ ਅਫ਼ਸਰ ਨੂੰ ਦਿਖਾਓ। ਉਹ ਤੁਹਾਡੀ ਫ਼ਸਲ ਲਈ ਸਹੀ ਦਵਾਈ ਤੇ ਮਾਤਰਾ ਦੱਸਣਗੇ। ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ (1800-180-1551, ਮੁਫ਼ਤ) ਵੀ ਮੁਫ਼ਤ ਸਲਾਹ ਦਿੰਦਾ ਹੈ।")),
    ("fertilizer", ("fertili", "khad", "खाद", "ਖਾਦ", "urea", "यूरिया", "ਯੂਰੀਆ", "dap", "manure", "npk", "nutrient"), (
        "Get your soil tested (Soil Health Card or a local lab) and apply fertiliser as the report suggests, not by habit. Too much urea wastes money and can weaken the crop. Split doses are usually better than one heavy dose; your agriculture officer can give the schedule for your crop and soil.",
        "अपनी मिट्टी की जाँच करवाइए (मृदा स्वास्थ्य कार्ड या स्थानीय प्रयोगशाला) और रिपोर्ट के अनुसार खाद डालिए, आदत से नहीं। ज़्यादा यूरिया पैसे बर्बाद करता है और फसल कमज़ोर कर सकता है। एक बार में ज़्यादा डालने से बेहतर है कि कई बार में बाँटकर डालें; आपकी फसल और मिट्टी का कार्यक्रम कृषि अधिकारी बता सकते हैं।",
        "ਆਪਣੀ ਮਿੱਟੀ ਦੀ ਜਾਂਚ ਕਰਵਾਓ (ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ ਜਾਂ ਸਥਾਨਕ ਲੈਬ) ਅਤੇ ਰਿਪੋਰਟ ਮੁਤਾਬਕ ਖਾਦ ਪਾਓ, ਆਦਤ ਨਾਲ ਨਹੀਂ। ਵੱਧ ਯੂਰੀਆ ਪੈਸੇ ਬਰਬਾਦ ਕਰਦਾ ਹੈ ਤੇ ਫ਼ਸਲ ਕਮਜ਼ੋਰ ਕਰ ਸਕਦਾ ਹੈ। ਇੱਕੋ ਵਾਰ ਵੱਧ ਪਾਉਣ ਨਾਲੋਂ ਕਈ ਵਾਰ ਵੰਡ ਕੇ ਪਾਉਣਾ ਚੰਗਾ ਹੈ; ਤੁਹਾਡੀ ਫ਼ਸਲ ਤੇ ਮਿੱਟੀ ਦਾ ਪ੍ਰੋਗਰਾਮ ਖੇਤੀਬਾੜੀ ਅਫ਼ਸਰ ਦੱਸ ਸਕਦੇ ਹਨ।")),
    ("irrigation", ("irrigat", "sinchai", "सिंचाई", "ਸਿੰਚਾਈ", "water my", "पानी लगा", "ਪਾਣੀ ਲਾ", "paani", "पानी", "ਪਾਣੀ"), (
        "Irrigate according to the crop stage and how dry the soil feels, not on a fixed habit. Do not irrigate just before forecast rain: it wastes water and can waterlog the field. Early morning or evening irrigation loses less water.",
        "सिंचाई फसल की अवस्था और मिट्टी की सूखावट देखकर कीजिए, तय आदत से नहीं। बारिश के पूर्वानुमान से ठीक पहले सिंचाई न करें: इससे पानी बर्बाद होता है और खेत में जलभराव हो सकता है। सुबह जल्दी या शाम को सिंचाई में पानी कम उड़ता है।",
        "ਸਿੰਚਾਈ ਫ਼ਸਲ ਦੀ ਅਵਸਥਾ ਤੇ ਮਿੱਟੀ ਦੀ ਖ਼ੁਸ਼ਕੀ ਦੇਖ ਕੇ ਕਰੋ, ਪੱਕੀ ਆਦਤ ਨਾਲ ਨਹੀਂ। ਮੀਂਹ ਦੇ ਅਨੁਮਾਨ ਤੋਂ ਠੀਕ ਪਹਿਲਾਂ ਸਿੰਚਾਈ ਨਾ ਕਰੋ: ਇਸ ਨਾਲ ਪਾਣੀ ਬਰਬਾਦ ਹੁੰਦਾ ਹੈ ਤੇ ਖੇਤ ਵਿੱਚ ਪਾਣੀ ਖੜ੍ਹ ਸਕਦਾ ਹੈ। ਸਵੇਰੇ ਜਲਦੀ ਜਾਂ ਸ਼ਾਮ ਨੂੰ ਸਿੰਚਾਈ ਵਿੱਚ ਪਾਣੀ ਘੱਟ ਉੱਡਦਾ ਹੈ।")),
    ("insurance", ("insurance", "bima", "बीमा", "ਬੀਮਾ", "pmfby", "claim", "compensation", "मुआवज", "ਮੁਆਵਜ਼", "hail", "ओले", "ਗੜ", "flood", "बाढ़", "ਹੜ੍ਹ"), (
        "If rain, hail or flood damages your crop and you are enrolled in the crop insurance scheme (PMFBY), report the loss to your insurer, bank or the helpline 14447 within 72 hours, with photos. If you are not enrolled, ask your bank or agriculture office before the next season's cut-off date.",
        "अगर बारिश, ओले या बाढ़ से फसल को नुकसान हो और आप फसल बीमा योजना (पीएमएफबीवाई) में शामिल हैं, तो 72 घंटे के भीतर फ़ोटो के साथ नुकसान की सूचना बीमा कंपनी, बैंक या हेल्पलाइन 14447 पर दीजिए। शामिल नहीं हैं तो अगले मौसम की अंतिम तारीख़ से पहले अपने बैंक या कृषि कार्यालय से पूछिए।",
        "ਜੇ ਮੀਂਹ, ਗੜੇ ਜਾਂ ਹੜ੍ਹ ਨਾਲ ਫ਼ਸਲ ਦਾ ਨੁਕਸਾਨ ਹੋਵੇ ਅਤੇ ਤੁਸੀਂ ਫ਼ਸਲ ਬੀਮਾ ਯੋਜਨਾ (ਪੀਐੱਮਐੱਫ਼ਬੀਵਾਈ) ਵਿੱਚ ਹੋ, ਤਾਂ 72 ਘੰਟਿਆਂ ਦੇ ਅੰਦਰ ਫ਼ੋਟੋਆਂ ਸਮੇਤ ਨੁਕਸਾਨ ਦੀ ਸੂਚਨਾ ਬੀਮਾ ਕੰਪਨੀ, ਬੈਂਕ ਜਾਂ ਹੈਲਪਲਾਈਨ 14447 'ਤੇ ਦਿਓ। ਸ਼ਾਮਲ ਨਹੀਂ ਹੋ ਤਾਂ ਅਗਲੇ ਮੌਸਮ ਦੀ ਆਖ਼ਰੀ ਤਾਰੀਖ਼ ਤੋਂ ਪਹਿਲਾਂ ਆਪਣੇ ਬੈਂਕ ਜਾਂ ਖੇਤੀਬਾੜੀ ਦਫ਼ਤਰ ਤੋਂ ਪੁੱਛੋ।")),
    ("loan", ("loan", "kcc", "kisan credit", "किसान क्रेडिट", "कर्ज", "क़र्ज", "ਕਰਜ਼", "credit", "subsidy", "सब्सिडी", "ਸਬਸਿਡੀ"), (
        "The Kisan Credit Card (KCC) gives farmers short-term farm credit at a lower interest rate, and prompt repayment can earn extra interest relief. Ask your bank or cooperative society which documents you need; terms change, so confirm the current rate with them.",
        "किसान क्रेडिट कार्ड (केसीसी) किसानों को कम ब्याज पर खेती के लिए अल्पकालिक कर्ज़ देता है, और समय पर चुकाने पर ब्याज में अतिरिक्त राहत मिल सकती है। कौन-से कागज़ चाहिए, यह अपने बैंक या सहकारी समिति से पूछिए; शर्तें बदलती रहती हैं, इसलिए मौजूदा दर वहीं से पक्की कर लीजिए।",
        "ਕਿਸਾਨ ਕ੍ਰੈਡਿਟ ਕਾਰਡ (ਕੇਸੀਸੀ) ਕਿਸਾਨਾਂ ਨੂੰ ਘੱਟ ਵਿਆਜ 'ਤੇ ਖੇਤੀ ਲਈ ਥੋੜ੍ਹੇ ਸਮੇਂ ਦਾ ਕਰਜ਼ਾ ਦਿੰਦਾ ਹੈ, ਅਤੇ ਸਮੇਂ ਸਿਰ ਮੋੜਨ 'ਤੇ ਵਿਆਜ ਵਿੱਚ ਵਾਧੂ ਰਾਹਤ ਮਿਲ ਸਕਦੀ ਹੈ। ਕਿਹੜੇ ਕਾਗਜ਼ ਚਾਹੀਦੇ ਹਨ, ਇਹ ਆਪਣੇ ਬੈਂਕ ਜਾਂ ਸਹਿਕਾਰੀ ਸਭਾ ਤੋਂ ਪੁੱਛੋ; ਸ਼ਰਤਾਂ ਬਦਲਦੀਆਂ ਰਹਿੰਦੀਆਂ ਹਨ, ਇਸ ਲਈ ਮੌਜੂਦਾ ਦਰ ਉੱਥੋਂ ਪੱਕੀ ਕਰ ਲਓ।")),
    ("msp", ("msp", "एमएसपी", "ਐੱਮਐੱਸਪੀ", "support price", "समर्थन मूल्य", "ਸਮਰਥਨ", "procurement", "सरकारी खरीद", "ਸਰਕਾਰੀ ਖ਼ਰੀਦ"), (
        "MSP is the support price the government announces for each crop. If the mandi price is below MSP, ask about government procurement or the nearest purchase centre. Check the officially announced MSP for your crop and season before you sell; I do not quote it from memory because it changes each season.",
        "एमएसपी वह समर्थन मूल्य है जो सरकार हर फसल के लिए घोषित करती है। मंडी भाव एमएसपी से कम हो तो सरकारी ख़रीद या नज़दीकी ख़रीद केंद्र के बारे में पूछिए। बेचने से पहले अपनी फसल और मौसम का सरकारी घोषित एमएसपी देख लीजिए; यह हर मौसम बदलता है, इसलिए मैं याद से आँकड़ा नहीं बताता।",
        "ਐੱਮਐੱਸਪੀ ਉਹ ਸਹਾਇਕ ਭਾਅ ਹੈ ਜੋ ਸਰਕਾਰ ਹਰ ਫ਼ਸਲ ਲਈ ਐਲਾਨਦੀ ਹੈ। ਜੇ ਮੰਡੀ ਦਾ ਭਾਅ ਐੱਮਐੱਸਪੀ ਤੋਂ ਘੱਟ ਹੋਵੇ ਤਾਂ ਸਰਕਾਰੀ ਖ਼ਰੀਦ ਜਾਂ ਨੇੜਲੇ ਖ਼ਰੀਦ ਕੇਂਦਰ ਬਾਰੇ ਪੁੱਛੋ। ਵੇਚਣ ਤੋਂ ਪਹਿਲਾਂ ਆਪਣੀ ਫ਼ਸਲ ਤੇ ਮੌਸਮ ਦਾ ਸਰਕਾਰੀ ਐਲਾਨਿਆ ਐੱਮਐੱਸਪੀ ਦੇਖ ਲਓ; ਇਹ ਹਰ ਮੌਸਮ ਬਦਲਦਾ ਹੈ, ਇਸ ਲਈ ਮੈਂ ਯਾਦ ਤੋਂ ਅੰਕੜਾ ਨਹੀਂ ਦੱਸਦਾ।")),
    ("storage", ("storage", "store", "godown", "भंडार", "भण्डार", "ਭੰਡਾਰ", "stock", "rakh", "रख", "ਰੱਖ", "cold storage", "moisture", "नमी", "ਨਮੀ"), (
        "Store grain only when it is dry. Spread and sun-dry it first, check moisture, then keep it in clean, covered bags on a raised platform away from walls so damp does not reach it. Check the stock every week for insects and wet patches.",
        "अनाज को तभी रखिए जब वह पूरी तरह सूखा हो। पहले धूप में सुखाइए, नमी जाँचिए, फिर साफ़ ढके बोरों में दीवार से हटाकर ऊँचे चबूतरे पर रखिए ताकि सीलन न पहुँचे। हर हफ़्ते कीड़े और गीले हिस्से देखते रहिए।",
        "ਅਨਾਜ ਉਦੋਂ ਹੀ ਰੱਖੋ ਜਦੋਂ ਪੂਰਾ ਸੁੱਕਾ ਹੋਵੇ। ਪਹਿਲਾਂ ਧੁੱਪ ਵਿੱਚ ਸੁਕਾਓ, ਨਮੀ ਜਾਂਚੋ, ਫਿਰ ਸਾਫ਼ ਢਕੀਆਂ ਬੋਰੀਆਂ ਕੰਧ ਤੋਂ ਹਟਾ ਕੇ ਉੱਚੇ ਥੜ੍ਹੇ 'ਤੇ ਰੱਖੋ ਤਾਂ ਜੋ ਸਿੱਲ੍ਹ ਨਾ ਪਹੁੰਚੇ। ਹਰ ਹਫ਼ਤੇ ਕੀੜੇ ਤੇ ਗਿੱਲੇ ਹਿੱਸੇ ਦੇਖਦੇ ਰਹੋ।")),
    ("rain_harvest", ("harvest", "katai", "कटाई", "कटी", "ਵਾਢੀ", "ਵੱਢੀ", "बचा", "ਬਚਾ", "bachao", "bachana", "wet", "भीग", "ਭਿੱਜ", "bheeg", "cover", "tarpaulin", "तिरपाल", "ਤਰਪਾਲ", "damage", "नुकसान", "ਨੁਕਸਾਨ"), (
        "If rain is coming, move harvested crop to a dry, covered place or cover heaps with a tarpaulin, and keep it off the ground. Wet grain fetches a lower price and spoils quickly, so do not leave it open in the mandi overnight. Dry it again before selling if it got wet.",
        "बारिश आने वाली हो तो कटी फसल को सूखी ढकी जगह में रखिए या तिरपाल से ढकिए, और ज़मीन से ऊपर रखिए। गीला अनाज कम दाम पर बिकता है और जल्दी ख़राब होता है, इसलिए रात में मंडी में खुले में न छोड़िए। भीग जाए तो बेचने से पहले दोबारा सुखाइए।",
        "ਜੇ ਮੀਂਹ ਆਉਣ ਵਾਲਾ ਹੋਵੇ ਤਾਂ ਵੱਢੀ ਫ਼ਸਲ ਨੂੰ ਸੁੱਕੀ ਢਕੀ ਥਾਂ ਰੱਖੋ ਜਾਂ ਤਰਪਾਲ ਨਾਲ ਢਕੋ, ਅਤੇ ਜ਼ਮੀਨ ਤੋਂ ਉੱਪਰ ਰੱਖੋ। ਗਿੱਲਾ ਅਨਾਜ ਘੱਟ ਭਾਅ 'ਤੇ ਵਿਕਦਾ ਹੈ ਤੇ ਛੇਤੀ ਖ਼ਰਾਬ ਹੁੰਦਾ ਹੈ, ਇਸ ਲਈ ਰਾਤ ਨੂੰ ਮੰਡੀ ਵਿੱਚ ਖੁੱਲ੍ਹੇ ਵਿੱਚ ਨਾ ਛੱਡੋ। ਭਿੱਜ ਜਾਵੇ ਤਾਂ ਵੇਚਣ ਤੋਂ ਪਹਿਲਾਂ ਦੁਬਾਰਾ ਸੁਕਾਓ।")),
    ("transport", ("transport", "truck", "tempo", "ट्रक", "टेम्पो", "ਟਰੱਕ", "bhada", "भाड़ा", "ਕਿਰਾਇਆ", "other mandi", "दूसरी मंडी", "ਦੂਜੀ ਮੰਡੀ", "nearby", "नज़दीक", "ਨੇੜ", "distance", "दूरी", "ਦੂਰੀ"), (
        "A higher price in another mandi helps only if the extra money is more than the cost of transport, loading and waiting. Subtract the truck or tempo cost and any commission from the extra rupees per quintal, then compare. The nearby-mandi table above shows the gap and distance.",
        "दूसरी मंडी का ज़्यादा भाव तभी फ़ायदे का है जब अतिरिक्त कमाई ढुलाई, लदाई और इंतज़ार के ख़र्च से ज़्यादा हो। प्रति क्विंटल अतिरिक्त रुपयों में से ट्रक या टेम्पो का भाड़ा और कमीशन घटाकर तुलना कीजिए। ऊपर की आस-पास की मंडियों की तालिका में अंतर और दूरी दिखती है।",
        "ਦੂਜੀ ਮੰਡੀ ਦਾ ਵੱਧ ਭਾਅ ਤਾਂ ਹੀ ਫ਼ਾਇਦੇ ਦਾ ਹੈ ਜੇ ਵਾਧੂ ਕਮਾਈ ਢੁਆਈ, ਲੋਡਿੰਗ ਤੇ ਉਡੀਕ ਦੇ ਖ਼ਰਚੇ ਤੋਂ ਵੱਧ ਹੋਵੇ। ਪ੍ਰਤੀ ਕੁਇੰਟਲ ਵਾਧੂ ਰੁਪਇਆਂ ਵਿੱਚੋਂ ਟਰੱਕ ਜਾਂ ਟੈਂਪੂ ਦਾ ਕਿਰਾਇਆ ਤੇ ਕਮਿਸ਼ਨ ਘਟਾ ਕੇ ਤੁਲਨਾ ਕਰੋ। ਉੱਪਰ ਆਸ-ਪਾਸ ਦੀਆਂ ਮੰਡੀਆਂ ਦੀ ਸਾਰਣੀ ਵਿੱਚ ਫ਼ਰਕ ਤੇ ਦੂਰੀ ਦਿਸਦੀ ਹੈ।")),
    ("quality", ("quality", "grade", "grading", "ग्रेड", "ਗ੍ਰੇਡ", "clean", "साफ़", "ਸਾਫ਼", "better price", "अच्छा भाव", "ਚੰਗਾ ਭਾਅ", "sorting", "छँटाई", "ਛਾਂਟੀ"), (
        "Clean, dry, evenly graded produce gets a better price. Remove stones, husk and broken or damaged grain, dry to the moisture level the buyer expects, and use clean bags. Ask the arhtiya or buyer what grade standard they apply before you load.",
        "साफ़, सूखी और एक-सी छँटी उपज का भाव बेहतर मिलता है। कंकड़, भूसी और टूटे या ख़राब दाने निकालिए, ख़रीदार की अपेक्षा के अनुसार नमी तक सुखाइए और साफ़ बोरे इस्तेमाल कीजिए। माल लादने से पहले आढ़ती या ख़रीदार से पूछ लीजिए कि वे कौन-सा ग्रेड मानते हैं।",
        "ਸਾਫ਼, ਸੁੱਕੀ ਤੇ ਇੱਕਸਾਰ ਛਾਂਟੀ ਹੋਈ ਜਿਣਸ ਦਾ ਭਾਅ ਚੰਗਾ ਮਿਲਦਾ ਹੈ। ਕੰਕਰ, ਫੂਸ ਤੇ ਟੁੱਟੇ ਜਾਂ ਖ਼ਰਾਬ ਦਾਣੇ ਕੱਢੋ, ਖ਼ਰੀਦਦਾਰ ਦੀ ਲੋੜ ਮੁਤਾਬਕ ਨਮੀ ਤੱਕ ਸੁਕਾਓ ਅਤੇ ਸਾਫ਼ ਬੋਰੀਆਂ ਵਰਤੋ। ਮਾਲ ਲੱਦਣ ਤੋਂ ਪਹਿਲਾਂ ਆੜ੍ਹਤੀਏ ਜਾਂ ਖ਼ਰੀਦਦਾਰ ਤੋਂ ਪੁੱਛ ਲਓ ਕਿ ਉਹ ਕਿਹੜਾ ਗ੍ਰੇਡ ਮੰਨਦੇ ਹਨ।")),
    ("seed", ("seed", "beej", "बीज", "ਬੀਜ", "sowing", "buwai", "बुवाई", "ਬਿਜਾਈ", "variety", "क़िस्म", "किस्म", "ਕਿਸਮ"), (
        "Use certified seed from a trusted seed store or government centre, keep the bill, and ask for the variety suited to your area and sowing date. Treat seed before sowing as your agriculture officer advises. Saved seed from a diseased crop can carry the disease forward.",
        "भरोसेमंद बीज भंडार या सरकारी केंद्र से प्रमाणित बीज लीजिए, बिल रखिए, और अपने इलाके व बुवाई की तारीख़ के हिसाब से क़िस्म पूछिए। कृषि अधिकारी की सलाह के अनुसार बुवाई से पहले बीज उपचार कीजिए। रोगी फसल का रखा हुआ बीज रोग को आगे ले जा सकता है।",
        "ਭਰੋਸੇਯੋਗ ਬੀਜ ਭੰਡਾਰ ਜਾਂ ਸਰਕਾਰੀ ਕੇਂਦਰ ਤੋਂ ਪ੍ਰਮਾਣਿਤ ਬੀਜ ਲਓ, ਬਿੱਲ ਰੱਖੋ, ਅਤੇ ਆਪਣੇ ਇਲਾਕੇ ਤੇ ਬਿਜਾਈ ਦੀ ਤਾਰੀਖ਼ ਮੁਤਾਬਕ ਕਿਸਮ ਪੁੱਛੋ। ਖੇਤੀਬਾੜੀ ਅਫ਼ਸਰ ਦੀ ਸਲਾਹ ਮੁਤਾਬਕ ਬਿਜਾਈ ਤੋਂ ਪਹਿਲਾਂ ਬੀਜ ਦੀ ਸੋਧ ਕਰੋ। ਬਿਮਾਰ ਫ਼ਸਲ ਦਾ ਰੱਖਿਆ ਬੀਜ ਬਿਮਾਰੀ ਅੱਗੇ ਲਿਜਾ ਸਕਦਾ ਹੈ।")),
]

_SELL_WORDS = ("sell", "hold", "bech", "बेच", "ਵੇਚ", "rok", "रुक", "रोक", "ਰੁਕ", "ਰੋਕ", "wait")

# words meaning "should I sell / what is the price / explain" -> answered from the live result
_PRICE_WORDS = ("sell", "hold", "bech", "बेच", "ਵੇਚ", "rate", "price", "bhav", "bhaav", "भाव", "ਭਾਅ", "rok", "रुक", "रोक", "ਰੁਕ",
                "ਰੋਕ", "explain", "samjha", "समझा", "ਸਮਝਾ", "summary", "सारांश", "ਸਾਰ", "wait", "intezaar", "इंतज़ार", "kab", "कब", "ਕਦੋਂ",
                "profit", "munafa", "मुनाफ़ा", "ਮੁਨਾਫ਼ਾ", "कीमत", "ਕੀਮਤ", "dam", "दाम", "ਦਾਮ")

OFF_TOPIC = (
    "I can only help with farming: crop prices, weather, selling or holding, storage, seeds, fertiliser, pests, loans and insurance. Please ask me something about your farm.",
    "मैं सिर्फ़ खेती में मदद कर सकता हूँ: फसल के भाव, मौसम, बेचना या रुकना, भंडारण, बीज, खाद, कीट, कर्ज़ और बीमा। कृपया अपनी खेती से जुड़ा सवाल पूछिए।",
    "ਮੈਂ ਸਿਰਫ਼ ਖੇਤੀ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ: ਫ਼ਸਲ ਦੇ ਭਾਅ, ਮੌਸਮ, ਵੇਚਣਾ ਜਾਂ ਰੁਕਣਾ, ਭੰਡਾਰ, ਬੀਜ, ਖਾਦ, ਕੀੜੇ, ਕਰਜ਼ਾ ਤੇ ਬੀਮਾ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀ ਖੇਤੀ ਬਾਰੇ ਸਵਾਲ ਪੁੱਛੋ।")

NO_MATCH = (
    "I do not have a ready answer for that. For advice specific to your field, call the Kisan Call Centre (1800-180-1551, free) or visit your nearest Krishi Vigyan Kendra. You can also ask me about storage, rain, irrigation, fertiliser, pests, seeds, MSP, loans, insurance, or whether to sell now.",
    "इसका तैयार जवाब मेरे पास नहीं है। अपने खेत की ख़ास सलाह के लिए किसान कॉल सेंटर (1800-180-1551, निःशुल्क) पर बात कीजिए या नज़दीकी कृषि विज्ञान केंद्र जाइए। आप मुझसे भंडारण, बारिश, सिंचाई, खाद, कीट, बीज, एमएसपी, कर्ज़, बीमा या अभी बेचने के बारे में पूछ सकते हैं।",
    "ਇਸ ਦਾ ਤਿਆਰ ਜਵਾਬ ਮੇਰੇ ਕੋਲ ਨਹੀਂ। ਆਪਣੇ ਖੇਤ ਦੀ ਖ਼ਾਸ ਸਲਾਹ ਲਈ ਕਿਸਾਨ ਕਾਲ ਸੈਂਟਰ (1800-180-1551, ਮੁਫ਼ਤ) 'ਤੇ ਗੱਲ ਕਰੋ ਜਾਂ ਨੇੜਲੇ ਖੇਤੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਜਾਓ। ਤੁਸੀਂ ਮੈਨੂੰ ਭੰਡਾਰ, ਮੀਂਹ, ਸਿੰਚਾਈ, ਖਾਦ, ਕੀੜੇ, ਬੀਜ, ਐੱਮਐੱਸਪੀ, ਕਰਜ਼ਾ, ਬੀਮਾ ਜਾਂ ਹੁਣੇ ਵੇਚਣ ਬਾਰੇ ਪੁੱਛ ਸਕਦੇ ਹੋ।")

NEED_DATA = (
    "Tell me your crop and mandi first, for example “Wheat in Khanna”, and I will check today's price and the rain forecast.",
    "पहले अपनी फसल और मंडी बताइए, जैसे “गेहूं खन्ना”, फिर मैं आज का भाव और बारिश का पूर्वानुमान देखूँगा।",
    "ਪਹਿਲਾਂ ਆਪਣੀ ਫ਼ਸਲ ਤੇ ਮੰਡੀ ਦੱਸੋ, ਜਿਵੇਂ “ਕਣਕ ਖੰਨਾ”, ਫਿਰ ਮੈਂ ਅੱਜ ਦਾ ਭਾਅ ਤੇ ਮੀਂਹ ਦਾ ਅਨੁਮਾਨ ਦੇਖਾਂਗਾ।")

RAIN_LINE = (
    "Your forecast: rain chance up to {rain}% in the next 3 days{demo}.",
    "आपके इलाके का पूर्वानुमान: अगले 3 दिन बारिश की संभावना {rain}% तक{demo}।",
    "ਤੁਹਾਡੇ ਇਲਾਕੇ ਦਾ ਅਨੁਮਾਨ: ਅਗਲੇ 3 ਦਿਨ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {rain}% ਤੱਕ{demo}।")
DEMO_TAG = (" (demo)", " (डेमो)", " (ਡੈਮੋ)")

NEXT_TITLE = ("What to do now", "अभी क्या करें", "ਹੁਣ ਕੀ ਕਰੀਏ")
STEPS = {
    "sell": (
        ("Move the crop to a dry, covered place today and keep it ready to go.",
         "Sell today or tomorrow, before the rain arrives. Do not leave it open overnight.",
         "Ask for the weight slip and the payment date."),
        ("आज ही फसल को सूखी, ढकी जगह पर रखिए और भेजने के लिए तैयार रखिए।",
         "बारिश आने से पहले आज या कल बेच दीजिए। रात को खुले में मत छोड़िए।",
         "तौल की पर्ची और भुगतान की तारीख़ ज़रूर लीजिए।"),
        ("ਅੱਜ ਹੀ ਫ਼ਸਲ ਨੂੰ ਸੁੱਕੀ, ਢਕੀ ਥਾਂ ਰੱਖੋ ਅਤੇ ਭੇਜਣ ਲਈ ਤਿਆਰ ਰੱਖੋ।",
         "ਮੀਂਹ ਆਉਣ ਤੋਂ ਪਹਿਲਾਂ ਅੱਜ ਜਾਂ ਕੱਲ੍ਹ ਵੇਚ ਦਿਓ। ਰਾਤ ਨੂੰ ਖੁੱਲ੍ਹੇ ਵਿੱਚ ਨਾ ਛੱਡੋ।",
         "ਤੋਲ ਦੀ ਪਰਚੀ ਤੇ ਭੁਗਤਾਨ ਦੀ ਤਾਰੀਖ਼ ਜ਼ਰੂਰ ਲਓ।")),
    "hold": (
        ("Keep the crop dry and covered, on a raised platform.",
         "Check the price again in a day or two.",
         "If the rain chance goes above {thr}%, sell before it arrives."),
        ("फसल को सूखा और ढका रखिए, ऊँचे चबूतरे पर।",
         "एक-दो दिन में भाव फिर से देखिए।",
         "अगर बारिश की संभावना {thr}% से ऊपर जाए, तो बारिश से पहले बेच दीजिए।"),
        ("ਫ਼ਸਲ ਨੂੰ ਸੁੱਕੀ ਤੇ ਢਕੀ ਰੱਖੋ, ਉੱਚੇ ਥੜ੍ਹੇ 'ਤੇ।",
         "ਇੱਕ-ਦੋ ਦਿਨਾਂ ਵਿੱਚ ਭਾਅ ਫਿਰ ਦੇਖੋ।",
         "ਜੇ ਮੀਂਹ ਦੀ ਸੰਭਾਵਨਾ {thr}% ਤੋਂ ਉੱਪਰ ਜਾਵੇ, ਤਾਂ ਮੀਂਹ ਤੋਂ ਪਹਿਲਾਂ ਵੇਚ ਦਿਓ।")),
    "no_weather": (
        ("Check the weather forecast yourself before you decide.",
         "Compare the price with a nearby mandi.",
         "Ask me again in a little while."),
        ("फ़ैसला करने से पहले मौसम का पूर्वानुमान ख़ुद देख लीजिए।",
         "भाव की तुलना किसी नज़दीकी मंडी से कीजिए।",
         "थोड़ी देर बाद मुझसे फिर पूछिए।"),
        ("ਫ਼ੈਸਲਾ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ ਮੌਸਮ ਦਾ ਅਨੁਮਾਨ ਆਪ ਦੇਖ ਲਓ।",
         "ਭਾਅ ਦੀ ਤੁਲਨਾ ਕਿਸੇ ਨੇੜਲੀ ਮੰਡੀ ਨਾਲ ਕਰੋ।",
         "ਥੋੜ੍ਹੀ ਦੇਰ ਬਾਅਦ ਮੈਨੂੰ ਫਿਰ ਪੁੱਛੋ।")),
}


@dataclass
class Reply:
    text: str
    topic: str  # a guide topic, "live", "refused", "no_match", "model"


def _pick(table: tuple, lang: str) -> str:
    return table[_I.get(lang, 0)]


def _has_any(text: str, words: tuple[str, ...]) -> bool:
    """Short Latin words must match a whole word ("rain" must not fire on "train"); everything else is a substring."""
    text = unicodedata.normalize("NFC", text)  # "ड़" can be typed as one letter or two; make both match
    tokens = set(re.findall(r"[a-z]+", text))
    tokens |= {t[:-1] for t in tokens if t.endswith("s")}
    for w in words:
        if w.isascii() and len(w) <= 5:
            if w in tokens:
                return True
        elif unicodedata.normalize("NFC", w) in text:
            return True
    return False


def is_farming(question: str) -> bool:
    return _has_any(question.lower(), AGRI_WORDS)


def _rain_line(result, lang: str) -> str:
    if result is None or result.weather is None:
        return ""
    demo = _pick(DEMO_TAG, lang) if result.weather.source == "scenario" else ""
    return _pick(RAIN_LINE, lang).format(rain=result.weather.max_rain_prob, demo=demo)


def explain(result, lang: str) -> Reply:
    """One-shot plain explanation of the current result: the facts, why, and what to do now."""
    if result is None or result.price is None or result.needs_clarification:
        return Reply(_pick(NEED_DATA, lang), "live")
    code = result.verdict.code if result.verdict.code in STEPS else "no_weather"
    steps = [s.format(thr=engine.RAIN_THRESHOLD) for s in STEPS[code][_I.get(lang, 0)]]
    body = engine.strip_tags(result.advice_text)
    lines = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    return Reply(f"{body}\n\n**{_pick(NEXT_TITLE, lang)}**\n{lines}", "live")


def _facts(result) -> dict:
    if result is None or result.price is None:
        return {}
    f = {"crop": result.entities.crop, "mandi": result.entities.mandi, "price_per_quintal_inr": result.price.modal,
         "price_source": result.price.source, "verdict": result.verdict.label}
    if result.weather:
        f["max_rain_chance_next_3_days_percent"] = result.weather.max_rain_prob
        f["rain_threshold_percent"] = engine.RAIN_THRESHOLD
    if result.insights.trend_pct is not None:
        f["price_change_7_days_percent"] = result.insights.trend_pct
    if result.insights.best_alt:
        f["better_nearby_mandi"] = result.insights.best_alt
    return f


def _model_reply(question: str, lang: str, result, history: list[dict]) -> str | None:
    """Optional: answer an open question with a configured model. Returns None when unavailable or unsafe."""
    if not engine.evon_configured():
        return None
    system = (
        "You are KisanBol, a careful assistant for Indian farmers. Answer ONLY farming questions (crops, prices, "
        "weather, storage, seeds, fertiliser, pests, irrigation, loans, insurance, mandi selling). For anything else "
        f"reply with one short sentence saying you only help with farming. Reply in {LANG_NAME.get(lang, 'English')}, "
        "in simple words, at most 5 short sentences. Use ONLY the numbers in FACTS for prices, rain and verdicts; never "
        "invent prices, MSP values, subsidy amounts or pesticide doses. For pest, disease or dose questions, tell the "
        "farmer to consult a Krishi Vigyan Kendra, agriculture officer or Kisan Call Centre 1800-180-1551. "
        f"FACTS: {_facts(result) or 'none yet'}")
    msgs = [{"role": "system", "content": system}]
    for m in history[-6:]:
        msgs.append({"role": "user" if m["role"] == "user" else "assistant", "content": m["text"][:600]})
    msgs.append({"role": "user", "content": question[:600]})
    try:
        out = engine._evon_chat(msgs, max_tokens=320).strip()
    except Exception:
        return None
    return out[:1200] or None


def reply(question: str, lang: str, result=None, history: list[dict] | None = None) -> Reply:
    q = (question or "").strip()
    if not q:
        return Reply(_pick(NO_MATCH, lang), "no_match")
    low = q.lower()
    history = history or []
    follow_up = any(m["role"] == "bot" and m.get("topic") not in ("refused", None) for m in history[-2:])
    if not is_farming(q) and not (follow_up and len(q.split()) <= 4):
        return Reply(_pick(OFF_TOPIC, lang), "refused")

    sell_intent = _has_any(low, _SELL_WORDS)
    rain_words = ("rain", "baarish", "barish", "बारिश", "बरसात", "ਮੀਂਹ", "ਬਾਰਿਸ਼", "ਬਰਸਾਤ")
    for topic, words, answers in _GUIDE:
        hit = _has_any(low, words) or (topic == "rain_harvest" and not sell_intent and _has_any(low, rain_words))
        if hit:
            text = _pick(answers, lang)
            if topic in ("irrigation", "rain_harvest", "storage"):
                extra = _rain_line(result, lang)
                if extra:
                    text = f"{text}\n\n{extra}"
            return Reply(text, topic)

    if _has_any(low, _PRICE_WORDS):
        return explain(result, lang)

    smart = _model_reply(q, lang, result, history)
    if smart:
        return Reply(smart, "model")
    return Reply(_pick(NO_MATCH, lang), "no_match")
