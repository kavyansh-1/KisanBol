"""Keep tests offline and independent of any real keys in .env."""
import os

for _k in ("GNANI_API_KEY", "GNANI_STT_KEY", "GNANI_TTS_KEY", "DATA_GOV_IN_API_KEY", "EVON_BASE_URL"):
    os.environ[_k] = ""
