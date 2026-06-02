import io
import tempfile
import os
from pathlib import Path
from faster_whisper import WhisperModel

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
_model_cache: dict[str, WhisperModel] = {}


def get_model(name: str, device: str = "cpu") -> WhisperModel:
    key = f"{name}:{device}"
    if key not in _model_cache:
        print(f"Loading Whisper model '{name}' on {device}...")
        _model_cache[key] = WhisperModel(name, device=device, compute_type="int8")
    return _model_cache[key]


def transcribe(wav_bytes: bytes, model_name: str = "base", language: str = "auto", device: str = "cpu") -> str:
    model = get_model(model_name, device)

    lang = None if language == "auto" else language

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp_path = f.name

    try:
        segments, info = model.transcribe(tmp_path, language=lang, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        os.unlink(tmp_path)

    return text
