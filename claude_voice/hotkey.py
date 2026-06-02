"""
Push-to-talk hotkey listener — cross-platform.

Windows : uses `keyboard` library (raw hook, no suppression)
macOS   : uses `pynput` (Accessibility API, no root needed)

Hold the configured hotkey → recording starts.
Release → recording stops, audio sent to daemon for transcription, result pasted.
"""

import sys
import threading
import time

from .recorder import Recorder
from .paster import paste_to_target


class PushToTalk:
    MIN_DURATION = 0.3  # seconds — ignore accidental taps

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.hotkey: str = cfg.get("hotkey", "ctrl+shift+space")
        self.target: str = cfg.get("paste_mode", "claude")
        self._recorder: Recorder | None = None
        self._press_time: float = 0.0
        self._recording = False
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        print(f"[claude-voice] Push-to-talk ready. Hold [{self.hotkey}] to record.", flush=True)
        print("[claude-voice] Press Ctrl+C to stop.", flush=True)

        if sys.platform in ("darwin", "linux"):
            self._run_pynput()
        else:
            self._run_windows()

    def stop(self) -> None:
        if sys.platform in ("darwin", "linux"):
            pass  # pynput listener stopped by KeyboardInterrupt
        else:
            try:
                import keyboard
                keyboard.unhook_all()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Windows — keyboard library
    # ------------------------------------------------------------------

    def _run_windows(self) -> None:
        import keyboard

        parts = [p.strip() for p in self.hotkey.split("+")]
        self._trigger_key = parts[-1]
        self._modifiers = parts[:-1]

        keyboard.hook(self._windows_hook, suppress=False)
        keyboard.wait()

    def _windows_hook(self, event) -> None:
        import keyboard
        if event.name != self._trigger_key:
            return
        if event.event_type == keyboard.KEY_DOWN and self._windows_modifiers_held():
            self._on_press()
        elif event.event_type == keyboard.KEY_UP and self._recording:
            self._on_release()

    def _windows_modifiers_held(self) -> bool:
        import keyboard
        return all(keyboard.is_pressed(m) for m in self._modifiers)

    # ------------------------------------------------------------------
    # macOS + Linux — pynput library
    # ------------------------------------------------------------------

    def _run_pynput(self) -> None:
        from pynput import keyboard as pynput_kb

        self._mac_pressed: set = set()
        self._mac_hotkeys = _parse_pynput_hotkey(self.hotkey)

        def on_press(key):
            self._mac_pressed.add(_normalize_pynput_key(key))
            if self._mac_hotkeys.issubset(self._mac_pressed):
                self._on_press()

        def on_release(key):
            normalized = _normalize_pynput_key(key)
            was_active = self._mac_hotkeys.issubset(self._mac_pressed)
            self._mac_pressed.discard(normalized)
            if was_active and self._recording:
                self._on_release()

        with pynput_kb.Listener(on_press=on_press, on_release=on_release) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                pass

    # ------------------------------------------------------------------
    # Shared press/release logic
    # ------------------------------------------------------------------

    def _on_press(self) -> None:
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

    def _on_release(self) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False
            duration = time.monotonic() - self._press_time

        if duration < self.MIN_DURATION:
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
        model_name = self.cfg.get("model", "tiny")
        language   = self.cfg.get("language", "auto")
        device     = self.cfg.get("device", "cpu")
        try:
            from .client import transcribe_wav
            text = transcribe_wav(wav, model=model_name, language=language)
            if text is not None:
                return text
        except Exception:
            pass
        from . import transcriber
        return transcriber.transcribe(wav, model_name=model_name, language=language, device=device)

    @staticmethod
    def _show(msg: str) -> None:
        print(f"\r[claude-voice] {msg}                    ", flush=True)


# ------------------------------------------------------------------
# pynput helpers
# ------------------------------------------------------------------

def _normalize_pynput_key(key):
    """Collapse left/right modifier variants to a single canonical key."""
    try:
        from pynput.keyboard import Key
        variants = {
            Key.ctrl_l: Key.ctrl, Key.ctrl_r: Key.ctrl,
            Key.shift_l: Key.shift, Key.shift_r: Key.shift,
            Key.alt_l: Key.alt, Key.alt_r: Key.alt,
            Key.cmd_l: Key.cmd, Key.cmd_r: Key.cmd,
        }
        return variants.get(key, key)
    except Exception:
        return key


def _parse_pynput_hotkey(hotkey_str: str) -> set:
    """Convert a hotkey string like 'ctrl+shift+space' into a set of pynput keys."""
    from pynput.keyboard import Key, KeyCode

    mapping = {
        "ctrl":    Key.ctrl,
        "shift":   Key.shift,
        "alt":     Key.alt,
        "cmd":     Key.cmd,
        "command": Key.cmd,
        "space":   Key.space,
        "enter":   Key.enter,
        "tab":     Key.tab,
        "esc":     Key.esc,
    }

    result = set()
    for part in hotkey_str.lower().split("+"):
        part = part.strip()
        if part in mapping:
            result.add(mapping[part])
        elif len(part) == 1:
            result.add(KeyCode.from_char(part))
    return result
