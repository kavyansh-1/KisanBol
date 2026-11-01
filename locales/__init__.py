"""Extra regional languages. Each module describes one language completely:

  UI         every on-screen string (same keys as i18n.py)
  TEMPLATES  the spoken/written advice sentences
  CROPS / CROP_ALIASES / MANDIS / MANDI_ALIASES / STATES   names, and the words a farmer might say or type
  SELL_WORDS / HOLD_WORDS / FORECAST_WORDS / DAY_WORDS / WEEK_WORDS / QTY_WORDS / TON_WORDS
  WEEKDAYS / MONTHS / UNITS (crore, lakh, rupees)
  VOICE      default text-to-speech voice for the language
  ADVISOR    farm-assistant texts and keywords

To add a language: copy one module, translate it, add its code to CODES. Missing UI keys fall back to English."""
from importlib import import_module

CODES = ["mr-IN", "gu-IN", "bn-IN", "ta-IN", "te-IN", "kn-IN", "ml-IN"]
REGISTRY = {code: import_module(f"locales.{code[:2]}") for code in CODES}
