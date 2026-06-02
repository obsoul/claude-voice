# /voice — Claude Code Voice Dictation Skill

When the user invokes `/voice`, execute the following steps:

## What this skill does

Records audio from the microphone using local Whisper (faster-whisper), transcribes it offline, and returns the text into the Claude Code session. No audio leaves the machine.

## Steps

1. **Check for Python and faster-whisper**
   - Run: `python -c "import faster_whisper; print('ok')"` 
   - If it fails, tell the user to run `pip install faster-whisper sounddevice` and stop.

2. **Run the one-shot recorder**
   - Run: `python "<path-to-claude-voice>/main.py" --once`
   - Replace `<path-to-claude-voice>` with the actual installation path.
   - The script will print "Recording… press Enter to stop."
   - Inform the user: "Speak now — press Enter in the terminal when done."
   - After the script exits, it prints the transcribed text to stdout.

3. **Capture and display the result**
   - Show the user the transcribed text.
   - Ask: "Would you like me to use this as your message, or use it as context?"

## Installation path resolution

Check these locations in order:
1. `CLAUDE_VOICE_PATH` environment variable
2. `~/.claude-voice/` (if `main.py` exists there)
3. `~/claude-voice/main.py`
4. Anywhere on PATH: `claude-voice --once`

## Tips

- Model and language are read from `~/.claude-voice/config.yaml`
- Override per-invocation: `/voice --model small --language en`
- Run the tray app separately for system-wide hotkey: `python main.py`

## Args passthrough

If the user types `/voice --model small` or `/voice --language fr`, pass those flags through to `main.py --once`.
