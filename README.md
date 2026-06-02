# claude-voice 🎙

**Talk to Claude instead of typing.** Hold a hotkey, say what you want, let go — your words appear instantly.

Works in Claude Code and any Windows app. Runs 100% on your computer. No internet, no API keys, no subscriptions.

---

## What it does

- **Hold a hotkey → speak → release** — text is typed wherever your cursor is
- Works inside **Claude Code** as a `/voice` command
- Transcribes your voice using [Whisper AI](https://github.com/openai/whisper), running locally on your CPU
- Under **0.5 seconds** from when you stop talking to when text appears

---

## Before you start — what you need

You only need three things:

### 1. Python 3.10 or newer
If you're not sure whether you have it, open PowerShell and type:
```
python --version
```
If you see `Python 3.10` or higher, you're good. If not, download it free from **[python.org](https://python.org)** — make sure to check the box that says **"Add Python to PATH"** during installation.

### 2. A microphone
Any microphone works — your laptop's built-in mic, a webcam mic, a USB mic, or a headset. If your computer can make video calls, it will work.

### 3. Claude Code
You're probably already here if you're reading this! Claude Code is Anthropic's AI coding assistant. Get it at **[claude.ai/code](https://claude.ai/code)**.

---

## Installation — 3 steps

> **Windows or Mac?** The steps are almost identical — just pick the right installer in Step 2.

### Step 1 — Download the project

**Windows** — open PowerShell (search "PowerShell" in your Start menu):
```powershell
git clone https://github.com/obsoul/claude-voice.git
cd claude-voice
```

**Mac** — open Terminal (search "Terminal" in Spotlight):
```bash
git clone https://github.com/obsoul/claude-voice.git
cd claude-voice
```

> Don't have `git`? **Windows:** download from [git-scm.com](https://git-scm.com). **Mac:** run `xcode-select --install` in Terminal.

### Step 2 — Run the installer

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Mac:**
```bash
bash install.sh
```

This will:
- Install all required Python packages (~2 minutes on first run)
- Download the Whisper AI model to your computer (~75 MB, one time only)
- Set up the `/voice` command in Claude Code
- Create a config file at `C:\Users\YourName\.claude-voice\config.yaml`

### Step 3 — Start the background service

The background service keeps the AI model loaded in memory so transcription is fast:

```powershell
python main.py serve
```

Keep this window open. You can minimize it — it runs quietly in the background.

**That's it. You're ready.**

---

## How to use it

### Option A — Inside Claude Code (the `/voice` command)

Open Claude Code, type `/voice`, and press Enter. Claude will tell you to speak, then automatically paste your words into the chat.

```
/voice
```

Want more time to speak?
```
/voice --dur 15
```

### Option B — Global hotkey (works in any app)

Open a new PowerShell window and run:

```powershell
python main.py hotkey
```

Now you can dictate **anywhere on your computer**:

1. Click into any text field (Claude Code, Notepad, Word, browser, anything)
2. Hold **Ctrl + Shift + Space**
3. Speak
4. Release — your words appear

> **Note:** The global hotkey requires running PowerShell as Administrator, or enabling Windows Developer Mode. See the [Troubleshooting](#troubleshooting) section if this doesn't work.

### Option C — Quick one-time recording

Don't want the background service? Use this for a single recording:

```powershell
python main.py once --dur 8
```

---

## The two pieces explained

claude-voice has two parts that work together:

| Part | What it does | How to start it |
|------|-------------|-----------------|
| **Background service** (daemon) | Keeps the AI model loaded so transcription is instant | `python main.py serve` |
| **Hotkey listener** | Detects when you hold/release the hotkey | `python main.py hotkey` |

You start both once, minimize the windows, and forget about them. They keep running until you close the windows or restart your computer.

**To start both automatically together**, you can run:
```powershell
python main.py serve
# In a second PowerShell window:
python main.py hotkey --autostart
```

---

## Customizing your settings

Your settings live at `C:\Users\YourName\.claude-voice\config.yaml`. Open it with any text editor (Notepad works fine).

```yaml
# How accurate vs how fast:
#   tiny   = fastest (~0.5s), still very accurate for most speech
#   base   = a bit slower (~2s), slightly more accurate
#   small  = slower (~4s), more accurate
model: tiny

# Language — "auto" detects it automatically, or set e.g. "en", "fr", "es"
language: auto

# The hotkey to hold while speaking
hotkey: ctrl+shift+space

# Where the text goes after transcription:
#   claude    = paste into Claude Code
#   auto      = paste into whatever app you're typing in
#   clipboard = just copy to clipboard (you paste with Ctrl+V)
paste_mode: auto
```

After changing settings, restart the background service for them to take effect.

---

## Troubleshooting

### "The hotkey isn't working" (Windows)
The `keyboard` library needs elevated permissions to intercept global key presses. Try one of these:

**Option 1** — Run PowerShell as Administrator:
Right-click PowerShell in the Start menu → "Run as administrator" → run `python main.py hotkey`

**Option 2** — Enable Windows Developer Mode:
Settings → System → For Developers → turn on "Developer Mode" → restart and try again

### "The hotkey isn't working" (Mac)
Mac requires Accessibility permission for the hotkey listener. Here's how to grant it:

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button
3. Add your Terminal app (Terminal, iTerm2, or whichever you use)
4. Restart the hotkey listener: `python3 main.py hotkey`

> If you're running from a virtual environment, you may need to add the Python binary itself instead of Terminal.

### "It's not picking up my voice"
- Check that your microphone is set as the default in Windows: right-click the speaker icon in the taskbar → Sound settings → Input → make sure your mic is selected
- Try speaking louder or closer to the mic
- Run `python main.py once --dur 5` and speak clearly — if it works, the hotkey listener just needs to be restarted

### "It says 'no speech detected'"
- Make sure you're speaking **during** the countdown, not after
- Check that your mic volume is turned up in Windows Sound settings (right-click speaker icon → Sound settings → Input volume)

### "I get an error about Python not being found"
You need to reinstall Python and make sure to check **"Add Python to PATH"** during installation.

### "The installer failed"
Run PowerShell as Administrator (right-click → Run as administrator) and try the installer again.

### "I want to stop everything"
- Stop the background service: `python main.py stop`
- Close the hotkey listener window (or press Ctrl+C in it)

---

## Frequently asked questions

**Does my voice get sent to the internet?**
No. Everything runs on your computer. The Whisper model is downloaded once during install, then runs locally forever.

**Does it work on Mac?**
Yes! Full Mac support is included. Run `bash install.sh` to get started. Linux support is planned — contributions welcome!

**What permissions does Mac need?**
Just one: Accessibility access for the hotkey listener (so it can detect global key presses). The installer will remind you how to enable it. No root or admin password required.

**How accurate is it?**
Very accurate for clear speech in English. It handles accents well. Background noise can reduce accuracy — a quiet room or a headset microphone helps.

**Can I use a different language?**
Yes — set `language: fr` (or any language code) in your config file, or pass `--language fr` when using `/voice`.

**Can I make it more accurate (and don't mind it being slower)?**
Change `model: tiny` to `model: base` or `model: small` in your config file, then restart the background service.

**What's the difference between the `/voice` skill and the hotkey?**
- `/voice` works only inside Claude Code and is triggered by typing a command
- The hotkey works **everywhere** on your computer and is triggered by holding a key combination

---

## Commands reference

```powershell
# Start the background service (keep this running)
python main.py serve

# Start the global push-to-talk hotkey
python main.py hotkey

# Start hotkey and auto-launch the background service if needed
python main.py hotkey --autostart

# Record once for 8 seconds (no hotkey needed)
python main.py trigger --dur 8

# Stop the background service
python main.py stop

# Create a fresh config file
python main.py setup
```

---

## Project layout

```
claude-voice/
├── main.py               ← Start here — all commands go through this
├── SKILL.md              ← The /voice Claude Code skill definition
├── install.ps1           ← Windows one-click installer
├── config.yaml           ← Default settings (copy to ~/.claude-voice/)
├── requirements.txt      ← Python packages needed
└── claude_voice/
    ├── daemon.py         ← Background service (keeps AI model loaded)
    ├── hotkey.py         ← Push-to-talk hotkey listener
    ├── recorder.py       ← Microphone recording
    ├── transcriber.py    ← Whisper AI transcription
    ├── paster.py         ← Pastes text into the right window
    ├── client.py         ← Talks to the background service
    └── config.py         ← Loads and saves settings
```

---

## Contributing

Pull requests are welcome! If you run into a bug or want to suggest a feature, please [open an issue](https://github.com/obsoul/claude-voice/issues).

Ideas for future versions:
- Mac and Linux support
- Wake word activation ("Hey Claude...")
- Real-time streaming transcription (words appear as you speak)
- GPU acceleration for even faster transcription

---

## License

MIT — free to use, modify, and distribute.
