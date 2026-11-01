"""Usage: python check_locale.py ta   -> checks locales/ta.py is complete and consistent with locales/bn.py (the reference)."""
import string, sys
from importlib import import_module

def fields(s): return sorted(f for _, f, _, _ in string.Formatter().parse(s) if f)

def check(code):
    m, ref = import_module(f"locales.{code}"), import_module("locales.bn")
    errs = []
    for name in ("CODE", "NAME", "VOICE"):
        if not getattr(m, name, ""): errs.append(f"missing {name}")
    def same_keys(a, b, label):
        for k in set(b) - set(a): errs.append(f"{label}: missing key {k}")
        for k in set(a) - set(b): errs.append(f"{label}: extra key {k}")
    for label in ("UI", "TEMPLATES", "CROPS", "CROP_ALIASES", "MANDIS", "STATES"):
        same_keys(getattr(m, label), getattr(ref, label), label)
    for label in ("UI", "TEMPLATES"):
        for k, v in getattr(m, label).items():
            if k in getattr(ref, label) and fields(v) != fields(getattr(ref, label)[k]):
                errs.append(f"{label}[{k}]: placeholders {fields(v)} != {fields(getattr(ref, label)[k])}")
            if not str(v).strip(): errs.append(f"{label}[{k}] is empty")
    for label, n in (("WEEKDAYS", 7), ("MONTHS", 12), ("UNITS", 3)):
        if len(getattr(m, label)) != n: errs.append(f"{label} must have {n} items")
    for label in ("SELL_WORDS", "HOLD_WORDS", "FORECAST_WORDS", "DAY_WORDS", "WEEK_WORDS", "QTY_WORDS", "TON_WORDS"):
        if not getattr(m, label): errs.append(f"{label} empty")
    A, R = m.ADVISOR, ref.ADVISOR
    same_keys(A, R, "ADVISOR")
    for sub in ("keywords", "guide", "steps"):
        same_keys(A[sub], R[sub], f"ADVISOR.{sub}")
    for k in R["steps"]:
        if len(A["steps"][k]) != 3: errs.append(f"ADVISOR.steps[{k}] needs 3 items")
        for a, b in zip(A["steps"][k], R["steps"][k]):
            if fields(a) != fields(b): errs.append(f"ADVISOR.steps[{k}] placeholder mismatch")
    for k in ("rain_line",):
        if fields(A[k]) != fields(R[k]): errs.append(f"ADVISOR.{k} placeholders")
    # the helplines must survive translation
    for k in ("pest", "insurance"):
        need = "1800-180-1551" if k == "pest" else "14447"
        if need not in A["guide"][k]: errs.append(f"ADVISOR.guide[{k}] must mention {need}")
    return errs

if __name__ == "__main__":
    e = check(sys.argv[1])
    print("OK" if not e else "\n".join(e)); sys.exit(1 if e else 0)
