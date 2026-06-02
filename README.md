# claude-voice

> Local Whisper voice dictation for Claude Code and any Windows app — push-to-talk, auto-paste, fully offline.

Inspired by [WhisprFlow](https://whisprflow.app) and [OpenWhisper](https://github.com/openai/whisper). No cloud. No API keys. Your audio never leaves your machine.

---

## Features

- **Push-to-talk hotkey** — hold `Ctrl+Shift+Space` (configurable), speak, release — text appears instantly
- **Auto-paste** — transcribed text is typed into whatever app you're focused on
- **Claude Code `/voice` skill** — speak directly into any Claude Code session
- **Multiple model sizes** — `tiny` to `large-v3`, trading speed for accuracy
- **Language auto-detect** — or pin to a specific language
- **System tray app** — lives quietly in your taskbar
- **100% offline** — powered by [faster-whisper](https://github.com/guillaumekynast/faster-whisper) running locally on CPU (or CUDA)

---

## Requirements

- Windows 10/11
- Python 3.10+
- A microphone

---

## Quick Start

```powershell
# Clone the repo
git clone https://github.com/yourusername/claude-voice.git
cd claude-voice

# Run the installer (installs deps, config, and Claude Code skill)
powershell -ExecutionPolicy Bypass -File install.ps1

# Start the tray app
python main.py
```

Hold `Ctrl+Shift+Space` anywhere — speak — release. Done.

---

## Claude Code Skill

After running the installer, type `/voice` in any Claude Code session:

```
/voice
```

Claude will record your voice, transcribe it locally, and use it as your message. You can also pass flags:

```
/voice --model small --language en
```

---

## Configuration

Config lives at `~/.claude-voice/config.yaml`:

```yaml
model: base          # tiny | base | small | medium | large-v3
language: auto       # auto-detect, or e.g. "en", "fr", "es"
hotkey: ctrl+shift+space
device: cpu          # cpu | cuda
paste_mode: auto     # auto (pastes) | clipboard (copy only)
```

### Model comparison

| Model | Size | Speed (CPU) | Accuracy |
|-------|------|-------------|----------|
| tiny | 39 MB | ~0.5s | Basic |
| base | 74 MB | ~1s | Good (default) |
| small | 244 MB | ~2-3s | Better |
| medium | 769 MB | ~5-8s | High |
| large-v3 | 1.5 GB | ~15s+ | Best |

---

## Manual Install

```powershell
# Core only (Claude Code skill + one-shot mode)
pip install faster-whisper sounddevice numpy scipy PyYAML pyperclip

# Full tray app
pip install pystray Pillow keyboard pyautogui
```

---

## Usage

```powershell
# System tray app (push-to-talk hotkey, runs in background)
python main.py

# One-shot: record once, print transcription, exit
python main.py --once

# Override model or language for one session
python main.py --once --model small --language en

# Create default config file
python main.py --setup
```

---

## How It Works

```
Hotkey held down
    └─ sounddevice records mic → float32 PCM frames
Hotkey released
    └─ frames → WAV bytes → faster-whisper transcribes locally
        └─ text → pyperclip (clipboard) + pyautogui Ctrl+V (auto-paste)
```

Whisper models are downloaded from HuggingFace on first use (~seconds) and cached locally.

---

## Project Structure

```
claude-voice/
├── main.py                  Entry point (tray + one-shot modes)
├── SKILL.md                 Claude Code /voice skill definition
├── config.yaml              Default configuration
├── install.ps1              Windows installer
├── requirements.txt
├── pyproject.toml
└── claude_voice/
    ├── config.py            Config loader
    ├── recorder.py          Microphone recording (sounddevice)
    ├── transcriber.py       Whisper transcription (faster-whisper)
    ├── paster.py            Clipboard + auto-paste
    ├── tray.py              System tray app (pystray + keyboard)
    └── icon.py              Programmatic tray icon (Pillow)
```

---

## Troubleshooting

**No audio / silent transcription**
- Check your default microphone in Windows Sound settings
- Run `python -c "import sounddevice; print(sounddevice.query_devices())"` to list devices

**Hotkey not working**
- Run as Administrator (some apps block global hotkeys)
- Change the hotkey in `~/.claude-voice/config.yaml`

**Slow transcription**
- Switch to `model: tiny` in config for near-instant results
- If you have an NVIDIA GPU: set `device: cuda`

**`keyboard` module requires admin**
- Right-click the terminal → Run as Administrator, or use `paste_mode: clipboard` and paste manually

---

## Contributing

PRs welcome. Please open an issue first for large changes.

Ideas for future versions:
- macOS support (CoreAudio + pynput)
- Linux support (PulseAudio)
- Whisper.cpp backend option
- Custom vocabulary / prompt injection
- Wake word activation

---

## License

MIT © 2026
