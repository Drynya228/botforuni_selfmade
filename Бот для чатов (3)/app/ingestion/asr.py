import subprocess
import tempfile
from app.core.config import cfg

try:
    from faster_whisper import WhisperModel
    _whisper = WhisperModel("medium", compute_type="int8") if cfg.ASR_ENABLED else None
except Exception:  # noqa: BLE001
    _whisper = None


def _extract_wav(src_path: str) -> str:
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = ["ffmpeg", "-y", "-i", src_path, "-vn", "-ac", "1", "-ar", "16000", out]
    subprocess.run(cmd, check=True)
    return out

async def transcribe_message(src_path: str) -> str:
    if not cfg.ASR_ENABLED or _whisper is None:
        return ""  # мягкий фолбэк
    wav = _extract_wav(src_path)
    segments, _ = _whisper.transcribe(wav, language="ru", vad_filter=True, beam_size=5)
    text = " ".join(s.text for s in segments).strip()
    return text