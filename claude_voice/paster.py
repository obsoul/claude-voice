import time
import pyperclip


def paste_text(text: str, mode: str = "auto") -> None:
    """Copy text to clipboard and optionally auto-paste into the focused window."""
    pyperclip.copy(text)

    if mode == "auto":
        _auto_paste()


def _auto_paste() -> None:
    try:
        import pyautogui
        time.sleep(0.1)  # brief pause so the hotkey key-up is fully processed
        pyautogui.hotkey("ctrl", "v")
    except Exception:
        # Fall back silently — text is still on clipboard
        pass
