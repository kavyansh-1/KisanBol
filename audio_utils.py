"""Audio input handling: accept almost any audio or video file and turn it into what speech recognition needs
(16 kHz, mono, 16-bit WAV, at most 60 seconds).

Browsers record WebM/Opus, phones record M4A/3GP/AMR, WhatsApp voice notes are Opus/OGG, and people upload MP4
videos. Speech services generally want plain WAV, so everything goes through ffmpeg first.
ffmpeg comes from the system if installed, otherwise from the `imageio-ffmpeg` pip package (bundled binary)."""
from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import tempfile
import wave

MAX_BYTES = 25 * 1024 * 1024
MAX_SECONDS = 60
AUDIO_TYPES = ["wav", "mp3", "m4a", "mp4", "webm", "ogg", "opus", "aac", "flac", "3gp", "amr", "wma", "mov", "mkv", "mpeg", "mpga"]
VIDEO_EXT = {"mp4", "webm", "mov", "mkv", "3gp"}


class AudioError(Exception):
    """Carries a translation key (see i18n.py) plus parameters."""

    def __init__(self, key: str, **params):
        super().__init__(key)
        self.key, self.params = key, params


def ffmpeg_path() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def is_video(filename: str) -> bool:
    return filename.lower().rsplit(".", 1)[-1] in VIDEO_EXT


def _is_ready_wav(data: bytes) -> bool:
    try:
        with wave.open(io.BytesIO(data)) as w:
            return (w.getnchannels() == 1 and w.getframerate() == 16000 and w.getsampwidth() == 2
                    and w.getnframes() / 16000 <= MAX_SECONDS)
    except (wave.Error, EOFError):
        return False


def to_wav16k(data: bytes, filename: str = "") -> bytes:
    """Return 16 kHz mono WAV bytes (first 60 s) for any audio/video input."""
    if not data:
        raise AudioError("no_input")
    if len(data) > MAX_BYTES:
        raise AudioError("too_big", mb=MAX_BYTES // (1024 * 1024))
    if _is_ready_wav(data):
        return data
    exe = ffmpeg_path()
    if not exe:
        raise AudioError("no_ffmpeg")
    ext = re.sub(r"[^a-z0-9]", "", filename.lower().rsplit(".", 1)[-1])[:5] if "." in filename else ""
    with tempfile.TemporaryDirectory() as d:
        src, dst = os.path.join(d, "in." + (ext or "bin")), os.path.join(d, "out.wav")
        with open(src, "wb") as f:
            f.write(data)
        cmd = [exe, "-nostdin", "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
               "-sample_fmt", "s16", "-t", str(MAX_SECONDS), "-f", "wav", dst]
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=90)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise AudioError("bad_audio") from exc
        if proc.returncode != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 100:
            raise AudioError("bad_audio")
        with open(dst, "rb") as f:
            return f.read()


# ------------------------------------------------------------------ optional offline recognition
_MODEL = None


def local_stt_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def local_transcribe(wav: bytes, language: str = "hi-IN") -> str:
    """Offline speech recognition with faster-whisper (optional install). The model downloads on first use."""
    global _MODEL
    from faster_whisper import WhisperModel
    if _MODEL is None:
        _MODEL = WhisperModel(os.getenv("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "q.wav")
        with open(path, "wb") as f:
            f.write(wav)
        segments, _ = _MODEL.transcribe(path, language=language.split("-")[0], vad_filter=True, beam_size=5)
        return " ".join(s.text.strip() for s in segments).strip()
