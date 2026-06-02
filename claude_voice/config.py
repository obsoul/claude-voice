import os
import yaml
from pathlib import Path

DEFAULTS = {
    "model": "base",
    "language": "auto",
    "hotkey": "ctrl+shift+space",
    "device": "cpu",
    "paste_mode": "auto",       # auto | clipboard
    "sample_rate": 16000,
    "channels": 1,
    "silence_threshold": 0.01,
    "min_record_seconds": 0.5,
}

CONFIG_PATH = Path.home() / ".claude-voice" / "config.yaml"


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            overrides = yaml.safe_load(f) or {}
        cfg.update(overrides)
    return cfg


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def init_default() -> None:
    if not CONFIG_PATH.exists():
        save(DEFAULTS)
        print(f"Config created at {CONFIG_PATH}")
