# app/ingestion/asr.py
import os, subprocess, tempfile

ASR_ENABLED = (os.getenv("ASR_ENABLED", "true").lower() == "true")

try:
    if ASR_ENABLED:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("base", compute_type="int8")
    else:
        _whisper = None
except Exception:
    _whisper = None

def _to_wav16k(src: str) -> str:
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    subprocess.run(["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", out], check=True)
    return out

async def transcribe(path: str) -> str:
    if not _whisper:
        return ""
    wav = _to_wav16k(path)
    segments, _ = _whisper.transcribe(wav, language="ru", vad_filter=True, beam_size=5)
    return " ".join(s.text for s in segments).strip()
