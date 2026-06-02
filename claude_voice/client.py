"""
Thin client that talks to the running daemon.
"""

import json
import socket
import urllib.request
import urllib.error
from .daemon import PORT


def is_running() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=0.5)
        return True
    except Exception:
        return False


def trigger(duration: float, target: str, model: str, language: str) -> str | None:
    url = (
        f"http://127.0.0.1:{PORT}/record"
        f"?duration={duration}&target={target}&model={model}&language={language}"
    )
    try:
        with urllib.request.urlopen(url, timeout=duration + 15) as resp:
            data = json.loads(resp.read())
            return data.get("text", "")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[claude-voice] Daemon error {e.code}: {body}", flush=True)
        return None
    except urllib.error.URLError as e:
        print(f"[claude-voice] Could not reach daemon: {e.reason}", flush=True)
        return None


def transcribe_wav(wav_bytes: bytes, model: str = "base", language: str = "auto") -> str | None:
    """Send recorded WAV bytes to the daemon for transcription. Returns text or None if daemon unreachable."""
    url = f"http://127.0.0.1:{PORT}/transcribe?model={model}&language={language}"
    req = urllib.request.Request(url, data=wav_bytes, method="POST")
    req.add_header("Content-Type", "audio/wav")
    req.add_header("Content-Length", len(wav_bytes))
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data.get("text", "")
    except Exception:
        return None


def stop() -> None:
    try:
        urllib.request.urlopen(
            urllib.request.Request(f"http://127.0.0.1:{PORT}/stop", method="POST"),
            timeout=2,
        )
    except Exception:
        pass
