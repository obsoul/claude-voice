import io
import tempfile
import os
import wave
import numpy as np
from faster_whisper import WhisperModel

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
_model_cache: dict[str, WhisperModel] = {}


def detect_device() -> tuple[str, str]:
    """
    Auto-detect the best available device and compute type.
    Returns (device, compute_type).
    """
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass

    # faster-whisper can also check without torch
    try:
        import ctranslate2
        if "cuda" in ctranslate2.get_supported_compute_types("cuda"):
            return "cuda", "float16"
    except Exception:
        pass

    return "cpu", "int8"


def best_compute_type(device: str) -> str:
    """Return the optimal compute type for the given device."""
    if device == "cuda":
        return "float16"   # GPU — float16 is fastest, fully accurate
    if device == "cpu":
        return "int8"      # CPU — int8 quantization, fast with minimal accuracy loss
    return "int8"


def get_model(name: str, device: str = "cpu", compute_type: str | None = None) -> WhisperModel:
    ct = compute_type or best_compute_type(device)
    key = f"{name}:{device}:{ct}"
    if key not in _model_cache:
        print(f"[claude-voice] Loading Whisper '{name}' on {device} ({ct})...", flush=True)
        _model_cache[key] = WhisperModel(name, device=device, compute_type=ct)
        print(f"[claude-voice] Model ready.", flush=True)
    return _model_cache[key]


def _normalize_wav(wav_bytes: bytes, target_peak: float = 0.5) -> bytes:
    """Boost quiet audio to a consistent peak level."""
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sr, ch = wf.getframerate(), wf.getnchannels()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    peak = np.abs(audio).max()
    if peak > 0.001:
        audio = np.clip(audio * min(target_peak / peak, 30.0), -1.0, 1.0)

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(ch); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    return out.getvalue()


def transcribe(
    wav_bytes: bytes,
    model_name: str = "tiny",
    language: str = "auto",
    device: str = "cpu",
    compute_type: str | None = None,
    beam_size: int = 1,
) -> str:
    model = get_model(model_name, device, compute_type)
    lang = None if language == "auto" else language
    wav_bytes = _normalize_wav(wav_bytes)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name

    try:
        segments, _ = model.transcribe(
            tmp_path,
            language=lang,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters={"threshold": 0.3, "min_speech_duration_ms": 100},
            no_speech_threshold=0.8,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        os.unlink(tmp_path)

    return text
