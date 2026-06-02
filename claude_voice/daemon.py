"""
claude-voice daemon — keeps Whisper loaded in memory between recordings.

Runs a local HTTP server on 127.0.0.1:45678.
  GET  /health          -> {"status":"ready","model":"..."}
  POST /record          -> records + transcribes + pastes, returns {"text":"..."}
       ?duration=8      seconds to record
       ?target=claude   where to paste (claude | auto | clipboard)
  POST /test-mic        -> records and returns peak amplitude (diagnostics)
  POST /stop            -> shutdown daemon
"""

import json
import traceback
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 45678
_model_ref: dict = {}


def _get_model(name: str, device: str):
    if _model_ref.get("name") != name or _model_ref.get("device") != device:
        from faster_whisper import WhisperModel
        print(f"[daemon] Loading Whisper '{name}' on {device}...", flush=True)
        _model_ref["model"] = WhisperModel(name, device=device, compute_type="int8")
        _model_ref["name"] = name
        _model_ref["device"] = device
        print("[daemon] Model ready.", flush=True)
    return _model_ref["model"]


def _record_wav(duration: float, sample_rate: int = 16000):
    import numpy as np
    import sounddevice as sd
    import io, wave

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    peak = float(np.abs(audio).max())
    rms  = float(np.sqrt(np.mean(audio**2)))
    print(f"[daemon] peak={peak:.4f} rms={rms:.4f}", flush=True)

    pcm = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue(), peak


def _record_and_transcribe(duration: float, model_name: str, language: str, device: str, target: str) -> str:
    import tempfile, os
    from claude_voice.transcriber import _normalize_wav
    from claude_voice.paster import paste_to_target

    print(f"[daemon] Recording {duration}s...", flush=True)
    wav_bytes, peak = _record_wav(duration)
    wav_bytes = _normalize_wav(wav_bytes)

    print(f"[daemon] Transcribing with model={model_name} lang={language}...", flush=True)
    model = _get_model(model_name, device)
    lang = None if language == "auto" else language

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp = f.name
    try:
        segments, info = model.transcribe(
            tmp, language=lang,
            beam_size=1,
            vad_filter=True,
            vad_parameters={"threshold": 0.3, "min_speech_duration_ms": 100},
            no_speech_threshold=0.8,
        )
        text = " ".join(s.text.strip() for s in segments).strip()
    finally:
        os.unlink(tmp)

    print(f"[daemon] Result: {text!r}", flush=True)
    if text:
        paste_to_target(text, target=target)
    return text


class _Handler(BaseHTTPRequestHandler):
    cfg: dict = {}

    def log_message(self, *_):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/health":
            self._json({"status": "ready", "model": _model_ref.get("name", "not loaded")})
        elif parsed.path in ("/record",):
            # Client sends GET with query params
            try:
                self._dispatch(parsed.path, qs)
            except Exception as e:
                tb = traceback.format_exc()
                print(f"[daemon] ERROR:\n{tb}", flush=True)
                self._json({"error": str(e)}, 500)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        try:
            self._dispatch(parsed.path, qs)
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[daemon] ERROR in {parsed.path}:\n{tb}", flush=True)
            self._json({"error": str(e), "traceback": tb}, 500)

    def _dispatch(self, path: str, qs: dict):
        if path == "/transcribe":
            # Accept raw WAV bytes in request body, return transcribed text
            length = int(self.headers.get("Content-Length", 0))
            wav_bytes = self.rfile.read(length) if length else b""
            model_name = qs.get("model",    [self.cfg.get("model", "base")])[0]
            language   = qs.get("language", [self.cfg.get("language", "auto")])[0]
            device     = self.cfg.get("device", "cpu")

            from claude_voice.transcriber import _normalize_wav
            import tempfile, os

            wav_bytes = _normalize_wav(wav_bytes)
            model = _get_model(model_name, device)
            lang = None if language == "auto" else language

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(wav_bytes); tmp = f.name
            try:
                segments, _ = model.transcribe(
                    tmp, language=lang,
                    beam_size=1,
                    vad_filter=True,
                    vad_parameters={"threshold": 0.3, "min_speech_duration_ms": 100},
                    no_speech_threshold=0.8,
                )
                text = " ".join(s.text.strip() for s in segments).strip()
            finally:
                os.unlink(tmp)

            print(f"[daemon] /transcribe -> {text!r}", flush=True)
            self._json({"text": text})

        elif path == "/record":
            duration   = float(qs.get("duration",  [8])[0])
            target     = qs.get("target",   [self.cfg.get("paste_mode", "claude")])[0]
            model_name = qs.get("model",    [self.cfg.get("model", "base")])[0]
            language   = qs.get("language", [self.cfg.get("language", "auto")])[0]
            device     = self.cfg.get("device", "cpu")
            text = _record_and_transcribe(duration, model_name, language, device, target)
            self._json({"text": text, "pasted": bool(text)})

        elif path == "/test-mic":
            import sounddevice as sd, numpy as np
            dur   = float(qs.get("duration", [3])[0])
            audio_raw, peak = _record_wav(dur)
            devices = sd.query_devices(kind="input")
            self._json({"peak": peak, "device": devices["name"]})

        elif path == "/stop":
            self._json({"status": "stopping"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        else:
            self._json({"error": "not found"}, 404)

    def _json(self, data: dict, code: int = 200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


def start(cfg: dict) -> None:
    _Handler.cfg = cfg
    _get_model(cfg.get("model", "base"), cfg.get("device", "cpu"))
    server = HTTPServer(("127.0.0.1", PORT), _Handler)
    print(f"[daemon] Listening on 127.0.0.1:{PORT}", flush=True)
    server.serve_forever()
