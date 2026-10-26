"""Tests for audio/video input handling and the translations. Offline: no keys needed."""
import io
import string
import subprocess
import wave

import pytest

import audio_utils as au
import i18n
import kisanbol_engine as e

FFMPEG = au.ffmpeg_path()
needs_ffmpeg = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg not available")


def make_wav(seconds=2, rate=44100, channels=2) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes((b"\x10\x20" * channels) * (rate * seconds))
    return buf.getvalue()


def transcode(src_wav: bytes, ext: str, tmp_path, video=False) -> bytes:
    src, dst = tmp_path / "a.wav", tmp_path / f"out.{ext}"
    src.write_bytes(src_wav)
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(src)]
    if video:
        cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=blue:s=64x64:d=2", "-i", str(src), "-shortest"]
    subprocess.run(cmd + [str(dst)], check=True)
    return dst.read_bytes()


def is_16k_mono(data: bytes) -> bool:
    with wave.open(io.BytesIO(data)) as w:
        return w.getframerate() == 16000 and w.getnchannels() == 1 and w.getsampwidth() == 2


@needs_ffmpeg
@pytest.mark.parametrize("ext", ["mp3", "m4a", "ogg", "webm", "flac", "aac"])
def test_audio_formats_convert_to_16k_mono_wav(ext, tmp_path):
    out = au.to_wav16k(transcode(make_wav(), ext, tmp_path), f"clip.{ext}")
    assert is_16k_mono(out)


@needs_ffmpeg
def test_video_file_audio_is_extracted(tmp_path):
    out = au.to_wav16k(transcode(make_wav(), "mp4", tmp_path, video=True), "voice.mp4")
    assert is_16k_mono(out) and au.is_video("voice.mp4") and not au.is_video("a.mp3")


@needs_ffmpeg
def test_long_audio_is_cut_to_60_seconds():
    out = au.to_wav16k(make_wav(seconds=75, rate=8000, channels=1), "long.wav")
    with wave.open(io.BytesIO(out)) as w:
        assert w.getnframes() / w.getframerate() <= 60.5


def test_ready_wav_passes_through_untouched():
    ready = make_wav(seconds=1, rate=16000, channels=1)
    assert au.to_wav16k(ready, "q.wav") == ready


def test_bad_and_oversized_files_give_translatable_errors():
    with pytest.raises(au.AudioError) as ex:
        au.to_wav16k(b"this is not audio at all" * 50, "x.mp3")
    assert ex.value.key in ("bad_audio", "no_ffmpeg")
    with pytest.raises(au.AudioError) as ex:
        au.to_wav16k(b"0" * (au.MAX_BYTES + 1), "big.wav")
    assert ex.value.key == "too_big"


# ---- speech recognition routing ----------------------------------------
def test_hosted_recognition_receives_converted_wav(monkeypatch):
    monkeypatch.setenv("GNANI_API_KEY", "test-key")
    seen = {}

    class Resp:
        ok = True
        status_code = 200
        text = ""
        def json(self): return {"transcript": "gehu ka rate khanna mandi mein"}

    def fake_post(url, headers=None, data=None, files=None, timeout=None):
        seen.update(url=url, headers=headers, data=data, wav=files["audio_file"][1])
        return Resp()

    monkeypatch.setattr(e.requests, "post", fake_post)
    text = e.transcribe(make_wav(seconds=1, rate=22050, channels=2), "clip.wav", "hi-IN")
    assert text == "gehu ka rate khanna mandi mein"
    assert seen["headers"] == {"X-API-Key-ID": "test-key"} and seen["data"]["language_code"] == "hi-IN"
    assert is_16k_mono(seen["wav"])


def test_without_key_or_offline_recognizer_error_is_friendly(monkeypatch):
    monkeypatch.delenv("GNANI_API_KEY", raising=False)
    monkeypatch.setattr(au, "local_stt_available", lambda: False)
    with pytest.raises(e.KisanBolError) as ex:
        e.transcribe(make_wav(seconds=1, rate=16000, channels=1), "q.wav")
    assert ex.value.key == "no_stt" and "पहचान" in ex.value.localized("hi-IN")
    assert not e.voice_ready()


def test_offline_recognizer_is_used_when_no_key(monkeypatch):
    monkeypatch.delenv("GNANI_API_KEY", raising=False)
    monkeypatch.setattr(au, "local_stt_available", lambda: True)
    monkeypatch.setattr(au, "local_transcribe", lambda wav, lang: "sarson hisar mandi")
    assert e.transcribe(make_wav(seconds=1, rate=16000, channels=1), "q.wav", "hi-IN") == "sarson hisar mandi"
    assert e.voice_ready()


# ---- translations --------------------------------------------------------
def _fields(s):
    return sorted(f for _, f, _, _ in string.Formatter().parse(s) if f)


def test_every_key_exists_in_all_three_languages_with_same_placeholders():
    en = i18n.TEXT["en-IN"]
    for lang in ("hi-IN", "pa-IN"):
        assert set(en) == set(i18n.TEXT[lang])
        for key, text in en.items():
            assert _fields(text) == _fields(i18n.TEXT[lang][key]), (lang, key)


def test_translation_helpers():
    assert i18n.t("hi-IN", "verdict.sell") == "अभी बेचिए"
    assert "85" in i18n.t("pa-IN", "reason.sell", rain=85, thr=70)
    assert i18n.t("xx-XX", "go") == "Get advice" and i18n.t("en-IN", "no.such.key") == "no.such.key"


def test_every_sample_question_is_understood_in_every_language():
    expected = [("wheat", "Khanna", None), ("rice", "Karnal", 80.0), ("mustard", "Hisar", None)]
    for lang in ("en-IN", "hi-IN", "pa-IN"):
        for i, (crop, mandi, qty) in enumerate(expected, start=1):
            ent = e.extract_entities_rules(i18n.t(lang, f"sample.{i}.q"))
            assert (ent.crop, ent.mandi, ent.quantity) == (crop, mandi, qty), (lang, i)


def test_notes_and_verdicts_render_in_each_language(monkeypatch):
    monkeypatch.setattr(e, "AGMARKNET_API_KEY", "")
    r = e.run_pipeline(text="Gehu Khanna mandi 50 quintal", speak=False, weather_scenario="rainy", language="pa-IN")
    assert r.verdict.code == "sell" and r.language == "pa-IN"
    public = [n for n in r.warnings if n.public]
    assert public and all(n.text("hi-IN") != n.text("en-IN") for n in public)
    assert not any(n.public for n in r.warnings if n.key.startswith("dev_"))
    assert any(sg["key"] == "rain" for sg in r.insights.signals)
