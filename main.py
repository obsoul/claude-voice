#!/usr/bin/env python3
"""
claude-voice — Local Whisper voice dictation for Claude Code and any app.

Usage:
  python main.py serve              Start the background daemon (keeps model loaded)
  python main.py trigger            Record via the running daemon (fast path)
  python main.py trigger --dur 8    Record for 8 seconds
  python main.py stop               Stop the daemon
  python main.py once               Standalone one-shot (no daemon, slower)
  python main.py tray               System tray app with push-to-talk hotkey
  python main.py setup              Create default config
"""

import argparse
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(prog="claude-voice")
    sub = parser.add_subparsers(dest="cmd")

    # serve
    sub.add_parser("serve", help="Start the background daemon")

    # trigger
    tr = sub.add_parser("trigger", help="Record via running daemon (fast)")
    tr.add_argument("--dur", type=float, default=8, metavar="SECONDS")
    tr.add_argument("--target", choices=["claude", "auto", "clipboard"], default="claude")
    tr.add_argument("--model", choices=["tiny", "base", "small", "medium", "large-v3"])
    tr.add_argument("--language")
    tr.add_argument("--autostart", action="store_true",
                    help="Start daemon automatically if not running")

    # stop
    sub.add_parser("stop", help="Stop the daemon")

    # once (fallback, no daemon)
    on = sub.add_parser("once", help="Standalone record+transcribe (slower, no daemon)")
    on.add_argument("--dur", type=float, default=8)
    on.add_argument("--target", choices=["claude", "auto", "clipboard"], default="claude")
    on.add_argument("--model", choices=["tiny", "base", "small", "medium", "large-v3"])
    on.add_argument("--language")

    # tray
    sub.add_parser("tray", help="System tray push-to-talk app")

    # setup
    sub.add_parser("setup", help="Create default config")

    # legacy --once shim so old skill invocations still work
    parser.add_argument("--once", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--duration", type=float, help=argparse.SUPPRESS)

    args = parser.parse_args()

    from claude_voice import config as cfg_mod
    cfg = cfg_mod.load()

    # Legacy shim
    if args.once or (args.cmd is None and args.duration):
        _cmd_once(cfg, dur=args.duration or 8, target="claude",
                  model=None, language=None)
        return

    if args.cmd == "serve" or args.cmd is None:
        _cmd_serve(cfg)
    elif args.cmd == "trigger":
        _cmd_trigger(cfg, args)
    elif args.cmd == "stop":
        _cmd_stop()
    elif args.cmd == "once":
        _cmd_once(cfg, dur=args.dur, target=args.target,
                  model=args.model, language=args.language)
    elif args.cmd == "tray":
        _cmd_tray(cfg)
    elif args.cmd == "setup":
        cfg_mod.init_default()


# ---------------------------------------------------------------------------

def _cmd_serve(cfg: dict) -> None:
    from claude_voice.daemon import start
    start(cfg)


def _cmd_trigger(cfg: dict, args) -> None:
    from claude_voice import client

    model    = args.model    or cfg.get("model", "tiny")
    language = args.language or cfg.get("language", "auto")

    if not client.is_running():
        if args.autostart:
            print("[claude-voice] Starting daemon...", flush=True)
            subprocess.Popen(
                [sys.executable, __file__, "serve"],
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            # Wait for daemon to be ready (model load)
            for _ in range(30):
                time.sleep(0.5)
                if client.is_running():
                    break
            else:
                print("[claude-voice] Daemon did not start in time.", flush=True)
                sys.exit(1)
        else:
            print("[claude-voice] Daemon not running. Start it with: python main.py serve", flush=True)
            sys.exit(1)

    print(f"[MIC] Recording {args.dur:.0f}s — speak now...", flush=True)
    t0 = time.time()
    text = client.trigger(duration=args.dur, target=args.target, model=model, language=language)
    elapsed = time.time() - t0

    if text:
        print(f"\nTranscription ({elapsed:.1f}s total):\n{text}\n", flush=True)
    else:
        print("(no speech detected)", flush=True)


def _cmd_stop() -> None:
    from claude_voice import client
    client.stop()
    print("[claude-voice] Daemon stopped.", flush=True)


def _cmd_once(cfg: dict, dur: float, target: str, model: str | None, language: str | None) -> None:
    import time
    from claude_voice.recorder import Recorder
    from claude_voice import transcriber
    from claude_voice.paster import paste_to_target

    model    = model    or cfg.get("model", "tiny")
    language = language or cfg.get("language", "auto")

    recorder = Recorder(sample_rate=cfg["sample_rate"], channels=cfg["channels"])
    recorder.start()
    _countdown(dur)
    wav = recorder.stop()

    print("[...] Transcribing...", flush=True)
    text = transcriber.transcribe(wav, model_name=model, language=language, device=cfg["device"])

    if text:
        print(f"\nTranscription:\n{text}\n", flush=True)
        paste_to_target(text, target=target)
    else:
        print("(no speech detected)", flush=True)


def _cmd_tray(cfg: dict) -> None:
    try:
        from claude_voice.tray import VoiceTray
    except ImportError as e:
        print(f"Tray dependencies missing: {e}")
        sys.exit(1)
    tray = VoiceTray()
    tray.cfg = cfg
    tray.run()


def _countdown(duration: float) -> None:
    import time
    total = int(duration)
    for remaining in range(total, 0, -1):
        filled = total - remaining
        bar = "#" * filled + "." * remaining
        _write(f"\r[MIC] Recording  [{bar}]  {remaining}s left  ")
        time.sleep(1)
    _write(f"\r[MIC] Recording  [{'#' * total}]  done!        \n")


def _write(text: str) -> None:
    if hasattr(sys.stdout, "buffer"):
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.flush()
    else:
        sys.stdout.write(text)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
