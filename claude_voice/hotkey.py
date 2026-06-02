"""
Push-to-talk hotkey listener.

Hold the configured hotkey → recording starts.
Release → recording stops, audio sent to daemon for transcription, result pasted.
"""

import threading
import time
import keyboard

from .recorder import Recorder
from .paster import paste_to_target


class PushToTalk:
    MIN_DURATION = 0.3  # seconds — ignore accidental taps shorter than this

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.hotkey: str = cfg.get("hotkey", "ctrl+shift+space")
        self.target: str = cfg.get("paste_mode", "claude")
        self._recorder: Recorder | None = None
        self._press_time: float = 0.0
        self._recording = False
        self._lock = threading.Lock()

    def run(self) -> None:
        """Block forever, listening for the hotkey."""
        # Parse hotkey — register the trigger key, check modifiers manually
        parts = [p.strip() for p in self.hotkey.split("+")]
        self._trigger_key = parts[-1]
        self._modifiers = parts[:-1]

        keyboard.on_press_key(self._trigger_key, self._on_press, suppress=True)
        keyboard.on_release_key(self._trigger_key, self._on_release, suppress=True)

        print(f"[claude-voice] Push-to-talk ready. Hold [{self.hotkey}] to record.", flush=True)
        print( "[claude-voice] Press Ctrl+C to stop.", flush=True)
        keyboard.wait()  # blocks until Ctrl+C or keyboard.unhook_all()

    def stop(self) -> None:
        keyboard.unhook_all()

    # ------------------------------------------------------------------

    def _modifiers_held(self) -> bool:
        if not self._modifiers:
            return True
        return all(keyboard.is_pressed(m) for m in self._modifiers)

    def _on_press(self, event) -> None:
        if not self._modifiers_held():
            return
        with self._lock:
            if self._recording:
                return
            self._recording = True
            self._press_time = time.monotonic()

        self._recorder = Recorder(
            sample_rate=self.cfg.get("sample_rate", 16000),
            channels=self.cfg.get("channels", 1),
        )
        self._recorder.start()
        self._show("Recording...")

    def _on_release(self, event) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
            duration = time.monotonic() - self._press_time

        if duration < self.MIN_DURATION:
            # Accidental tap — discard
            self._recorder.stop()
            self._recorder = None
            self._show("(tap too short, ignored)")
            return

        recorder = self._recorder
        self._recorder = None
        threading.Thread(target=self._finish, args=(recorder,), daemon=True).start()

    def _finish(self, recorder: Recorder) -> None:
        self._show("Transcribing...")
        wav = recorder.stop()

        text = self._transcribe(wav)

        if text:
            self._show(f"-> {text}")
            paste_to_target(text, target=self.target)
        else:
            self._show("(no speech detected)")

    def _transcribe(self, wav: bytes) -> str:
        """Try daemon first (fast), fall back to local transcription."""
        model_name = self.cfg.get("model", "base")
        language   = self.cfg.get("language", "auto")
        device     = self.cfg.get("device", "cpu")

        # Try daemon
        try:
            from .client import transcribe_wav
            text = transcribe_wav(wav, model=model_name, language=language)
            if text is not None:
                return text
        except Exception:
            pass

        # Fall back to local (model loaded fresh — slower first time)
        from . import transcriber
        return transcriber.transcribe(wav, model_name=model_name, language=language, device=device)

    @staticmethod
    def _show(msg: str) -> None:
        print(f"\r[claude-voice] {msg}                    ", flush=True)
