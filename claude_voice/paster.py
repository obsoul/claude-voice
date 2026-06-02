"""
Cross-platform text pasting.

Windows : pygetwindow to focus + Ctrl+V via pyautogui
macOS   : osascript to focus + Cmd+V via osascript (no extra deps)
"""

import sys
import time
import pyperclip


def paste_to_target(text: str, target: str = "claude") -> None:
    pyperclip.copy(text)

    if target == "clipboard":
        print("[OK] Copied to clipboard.", flush=True)
        return

    if target == "claude":
        if _focus_claude_code():
            _send_paste()
            print("[OK] Pasted into Claude Code.", flush=True)
        else:
            print("[!] Claude Code window not found. Text is on your clipboard -- paste with Ctrl+V / Cmd+V.", flush=True)
        return

    # target == "auto"
    _send_paste()
    print("[OK] Pasted into active window.", flush=True)


# ------------------------------------------------------------------
# Window focus
# ------------------------------------------------------------------

def _focus_claude_code() -> bool:
    if sys.platform == "darwin":
        return _focus_mac()
    if sys.platform == "linux":
        return _focus_linux()
    return _focus_windows()


def _focus_windows() -> bool:
    try:
        import pygetwindow as gw
        matches = [w for w in gw.getAllWindows()
                   if "claude" in w.title.lower() and w.title.strip()]
        if not matches:
            return False
        matches[0].activate()
        time.sleep(0.3)
        return True
    except Exception:
        return False


def _focus_mac() -> bool:
    import subprocess
    # Claude Code on Mac runs as "Claude" or "Claude Code"
    for app_name in ("Claude Code", "Claude"):
        result = subprocess.run(
            ["osascript", "-e", f'tell application "{app_name}" to activate'],
            capture_output=True,
            timeout=3,
        )
        if result.returncode == 0:
            time.sleep(0.3)
            return True
    return False


# ------------------------------------------------------------------
# Paste keypress
# ------------------------------------------------------------------

def _send_paste() -> None:
    time.sleep(0.15)
    if sys.platform == "darwin":
        _paste_mac()
    elif sys.platform == "linux":
        _paste_linux()
    else:
        _paste_windows()


def _paste_windows() -> None:
    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "v")
    except Exception:
        pass


def _focus_linux() -> bool:
    import subprocess
    # Try xdotool to find and raise the Claude Code window
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", "Claude"],
            capture_output=True, text=True, timeout=3,
        )
        wids = result.stdout.strip().split()
        if wids:
            subprocess.run(["xdotool", "windowactivate", "--sync", wids[0]],
                           capture_output=True, timeout=3)
            time.sleep(0.2)
            return True
    except FileNotFoundError:
        print("[!] xdotool not found. Install with: sudo apt install xdotool", flush=True)
    except Exception:
        pass
    return False


def _paste_linux() -> None:
    import subprocess
    try:
        subprocess.run(["xdotool", "key", "ctrl+v"],
                       capture_output=True, timeout=3)
    except FileNotFoundError:
        print("[!] xdotool not found. Install with: sudo apt install xdotool", flush=True)
    except Exception:
        pass


def _paste_mac() -> None:
    import subprocess
    subprocess.run(
        ["osascript", "-e",
         'tell application "System Events" to keystroke "v" using {command down}'],
        capture_output=True,
        timeout=3,
    )
