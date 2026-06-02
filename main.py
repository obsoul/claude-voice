#!/usr/bin/env python3
"""
claude-voice — Local Whisper voice dictation for Claude Code and any app.

Usage:
  python main.py              Start the system tray app (push-to-talk hotkey)
  python main.py --once       Record once, print transcription, then exit
  python main.py --setup      Create default config and exit
  python main.py --model      Choose Whisper model interactively
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="claude-voice", description="Local Whisper voice dictation")
    parser.add_argument("--once", action="store_true", help="Record once, print text, exit (for Claude Code skill)")
    parser.add_argument("--setup", action="store_true", help="Create default config file")
    parser.add_argument("--model", choices=["tiny", "base", "small", "medium", "large-v3"], help="Override Whisper model")
    parser.add_argument("--language", help="Language code (e.g. en, fr) or 'auto'")
    parser.add_argument("--paste-mode", choices=["auto", "clipboard"], help="Paste mode override")
    args = parser.parse_args()

    from claude_voice import config as cfg_mod

    if args.setup:
        cfg_mod.init_default()
        return

    cfg = cfg_mod.load()
    if args.model:
        cfg["model"] = args.model
    if args.language:
        cfg["language"] = args.language
    if args.paste_mode:
        cfg["paste_mode"] = args.paste_mode

    if args.once:
        _run_once(cfg)
    else:
        _run_tray(cfg)


def _run_once(cfg: dict) -> None:
    from claude_voice.recorder import Recorder
    from claude_voice import transcriber

    print("Recording… press Enter to stop.", flush=True)
    recorder = Recorder(sample_rate=cfg["sample_rate"], channels=cfg["channels"])
    recorder.start()
    try:
        input()
    except (KeyboardInterrupt, EOFError):
        pass
    wav = recorder.stop()

    print("Transcribing…", flush=True)
    text = transcriber.transcribe(wav, model_name=cfg["model"], language=cfg["language"], device=cfg["device"])
    print(text)


def _run_tray(cfg: dict) -> None:
    try:
        from claude_voice.tray import VoiceTray
    except ImportError as e:
        print(f"Tray dependencies missing: {e}")
        print("Install with: pip install claude-voice[tray]")
        sys.exit(1)

    tray = VoiceTray()
    tray.cfg = cfg
    tray.run()


if __name__ == "__main__":
    main()
