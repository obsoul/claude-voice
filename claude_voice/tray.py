import threading
import time
import pystray
import keyboard
from . import config as cfg_mod
from .recorder import Recorder
from . import transcriber
from . import paster
from .icon import make_icon
from pathlib import Path

_ASSETS = Path(__file__).parent.parent / "assets"

def _load_icon(name: str, recording: bool = False) -> "Image":
    from PIL import Image
    path = _ASSETS / name
    if path.exists():
        return Image.open(path)
    return make_icon(recording=recording)


class VoiceTray:
    def __init__(self):
        self.cfg = cfg_mod.load()
        self.recorder = Recorder(
            sample_rate=self.cfg["sample_rate"],
            channels=self.cfg["channels"],
        )
        self._recording = False
        self._lock = threading.Lock()
        self._icon: pystray.Icon | None = None
        self._status = "idle"

    # ------------------------------------------------------------------
    # Tray lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        self._icon = pystray.Icon(
            "claude-voice",
            _load_icon("tray_idle.png", recording=False),
            "Claude Voice — idle",
            menu=self._build_menu(),
        )
        keyboard.add_hotkey(self.cfg["hotkey"], self._on_hotkey_down, suppress=True, trigger_on_release=False)
        keyboard.on_release_key(self.cfg["hotkey"].split("+")[-1], self._on_hotkey_up, suppress=False)
        print(f"Claude Voice running. Hold [{self.cfg['hotkey']}] to record.")
        self._icon.run()

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("Claude Voice", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"Model: {self.cfg['model']}", None, enabled=False),
            pystray.MenuItem(f"Hotkey: {self.cfg['hotkey']}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit),
        )

    def _quit(self) -> None:
        keyboard.unhook_all()
        self._icon.stop()

    # ------------------------------------------------------------------
    # Hotkey handlers
    # ------------------------------------------------------------------

    def _on_hotkey_down(self) -> None:
        with self._lock:
            if self._recording:
                return
            self._recording = True

        self._set_icon(recording=True, label="Claude Voice — recording…")
        self.recorder.start()

    def _on_hotkey_up(self, _event=None) -> None:
        with self._lock:
            if not self._recording:
                return
            self._recording = False

        threading.Thread(target=self._finish, daemon=True).start()

    def _finish(self) -> None:
        self._set_icon(recording=False, label="Claude Voice — transcribing…")
        wav = self.recorder.stop()
        text = transcriber.transcribe(
            wav,
            model_name=self.cfg["model"],
            language=self.cfg["language"],
            device=self.cfg["device"],
        )
        if text:
            paster.paste_text(text, mode=self.cfg["paste_mode"])
            print(f"[claude-voice] {text}")
        self._set_icon(recording=False, label="Claude Voice — idle")

    def _set_icon(self, recording: bool, label: str) -> None:
        if self._icon:
            name = "tray_recording.png" if recording else "tray_idle.png"
            self._icon.icon = _load_icon(name, recording=recording)
            self._icon.title = label
