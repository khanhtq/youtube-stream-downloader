"""
Configuration management for YouTube Stream Downloader
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "output_dir": str(Path.home() / "Downloads"),
    "format": "mkv",
    "quality": "best",
    "concurrent_fragments": 16,
    "default_cutoff_minutes": 45,
    "theme_mode": "dark"
}

CONFIG_FILE_NAME = "config.json"


def get_config_path() -> Path:
    """Returns the path to the config file."""
    return Path(__file__).resolve().parent.parent / CONFIG_FILE_NAME


def load_config() -> Dict[str, Any]:
    """Loads configuration from JSON file or returns defaults."""
    config = DEFAULT_CONFIG.copy()
    cfg_path = get_config_path()
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                config.update(data)
        except Exception:
            pass
            
    # Ensure output_dir exists or fallback
    out_dir = config.get("output_dir", "")
    if not out_dir or not os.path.exists(out_dir):
        default_dl = Path.home() / "Downloads"
        if default_dl.exists():
            config["output_dir"] = str(default_dl)
        else:
            config["output_dir"] = str(Path(__file__).resolve().parent.parent)

    return config


def save_config(config_data: Dict[str, Any]) -> bool:
    """Saves configuration to JSON file."""
    cfg_path = get_config_path()
    try:
        current = load_config()
        current.update(config_data)
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False
