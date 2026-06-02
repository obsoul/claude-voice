import time
import pyperclip


def paste_to_target(text: str, target: str = "claude") -> None:
    """
    Send transcribed text to the right place:
      claude    — find the Claude Code window, focus it, paste into the chat input
      auto      — paste into whatever window is currently focused
      clipboard — copy to clipboard only, no auto-paste
    """
    pyperclip.copy(text)

    if target == "clipboard":
        print("[OK] Copied to clipboard.", flush=True)
        return

    if target == "claude":
        if _focus_claude_code():
            _send_paste()
            print("[OK] Pasted into Claude Code.", flush=True)
            return
        print("[!] Claude Code window not found. Text is on your clipboard -- paste with Ctrl+V.", flush=True)
        return

    # target == "auto": paste into whatever is focused right now
    _send_paste()
    print("[OK] Pasted into active window.", flush=True)


def _focus_claude_code() -> bool:
    """Find and focus the Claude Code window. Returns True on success."""
    try:
        import pygetwindow as gw
        # Claude Code's window title contains "Claude" on Windows
        matches = [w for w in gw.getAllWindows()
                   if "claude" in w.title.lower() and w.title.strip()]
        if not matches:
            return False
        win = matches[0]
        win.activate()
        time.sleep(0.3)  # let the window actually come to front
        return True
    except Exception:
        return False


def _send_paste() -> None:
    try:
        import pyautogui
        time.sleep(0.15)
        pyautogui.hotkey("ctrl", "v")
    except Exception:
        pass
