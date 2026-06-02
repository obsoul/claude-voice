import io
import tempfile
import os
import wave
import numpy as np
from faster_whisper import WhisperModel

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
_model_cache: dict[str, WhisperModel] = {}


def get_model(name: str, device: str = "cpu") -> WhisperModel:
    key = f"{name}:{device}"
    if key not in _model_cache:
        print(f"Loading Whisper model '{name}' on {device}...")
        _model_cache[key] = WhisperModel(name, device=device, compute_type="int8")
    return _model_cache[key]


def _normalize_wav(wav_bytes: bytes, target_peak: float = 0.5) -> bytes:
    """Denoise + normalize audio so Whisper can handle quiet microphones."""
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    # Noise reduction: estimate noise from first 0.3s (assumed silence before speaking)
    try:
        import noisereduce as nr
        noise_sample = audio[: int(sr * 0.3)]
        audio = nr.reduce_noise(y=audio, sr=sr, y_noise=noise_sample, stationary=False).astype(np.float32)
    except Exception:
        pass  # noisereduce not available, skip

    # Normalize to target peak
    peak = np.abs(audio).max()
    if peak > 0.001:
        audio = audio * min(target_peak / peak, 30.0)
        audio = np.clip(audio, -1.0, 1.0)

    pcm = (audio * 32767).astype(np.int16)
    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return out.getvalue()


def transcribe(wav_bytes: bytes, model_name: str = "base", language: str = "auto", device: str = "cpu") -> str:
    model = get_model(model_name, device)
    lang = None if language == "auto" else language

    wav_bytes = _normalize_wav(wav_bytes)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name

    try:
        segments, info = model.transcribe(tmp_path, language=lang, vad_filter=False, no_speech_threshold=1.0)
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        os.unlink(tmp_path)

    return text
