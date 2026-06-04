import os
import yaml
from pathlib import Path

DEFAULTS = {
    "model": "tiny",
    "language": "auto",
    "hotkey": "ctrl+shift+space",
    "device": "auto",           # auto | cpu | cuda
    "compute_type": "auto",     # auto | int8 (cpu) | float16 (gpu) | float32
    "paste_mode": "auto",
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

    # Resolve "auto" device at runtime
    if cfg.get("device") == "auto":
        from .transcriber import detect_device
        device, compute_type = detect_device()
        cfg["device"] = device
        if cfg.get("compute_type") == "auto":
            cfg["compute_type"] = compute_type
    elif cfg.get("compute_type") == "auto":
        from .transcriber import best_compute_type
        cfg["compute_type"] = best_compute_type(cfg["device"])

    return cfg


def save(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def init_default() -> None:
    if not CONFIG_PATH.exists():
        save(DEFAULTS)
        print(f"Config created at {CONFIG_PATH}")
