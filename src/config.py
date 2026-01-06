"""Configuration module for LikX."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "save_directory": str(Path.home() / "Pictures" / "Screenshots"),
    "default_format": "png",
    "supported_formats": ["png", "jpg", "jpeg", "bmp", "gif"],
    "hotkey_fullscreen": "<Control><Shift>F",
    "hotkey_region": "<Control><Shift>R",
    "hotkey_window": "<Control><Shift>W",
    "auto_save": False,
    "copy_to_clipboard": True,
    "show_notification": True,
    "include_cursor": False,
    "delay_seconds": 0,
    "editor_enabled": True,
    "theme": "system",
    "upload_service": "imgur",  # imgur, fileio, none
    "auto_upload": False,
}

# Configuration file path
CONFIG_DIR = Path.home() / ".config" / "likx"
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return CONFIG_DIR


def get_config_file() -> Path:
    """Get the configuration file path."""
    return CONFIG_FILE


def ensure_config_dir() -> bool:
    """Ensure the configuration directory exists."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except OSError:
        return False


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    config = DEFAULT_CONFIG.copy()
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
        except (json.JSONDecodeError, IOError):
            pass
    
    return config


def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file."""
    if not ensure_config_dir():
        return False
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except IOError:
        return False


def get_setting(key: str, default: Optional[Any] = None) -> Any:
    """Get a specific configuration setting."""
    config = load_config()
    return config.get(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set a specific configuration setting."""
    config = load_config()
    config[key] = value
    return save_config(config)


def reset_config() -> bool:
    """Reset configuration to defaults."""
    return save_config(DEFAULT_CONFIG.copy())


def validate_format(format_str: str) -> bool:
    """Validate if a format string is supported."""
    config = load_config()
    supported = config.get("supported_formats", DEFAULT_CONFIG["supported_formats"])
    return format_str.lower() in [fmt.lower() for fmt in supported]


def get_save_path(filename: Optional[str] = None, format_str: Optional[str] = None) -> Path:
    """Generate a save path for a screenshot."""
    config = load_config()
    save_dir = Path(config.get("save_directory", DEFAULT_CONFIG["save_directory"]))
    
    save_dir = Path(save_dir).expanduser()
    save_dir.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}"
    
    if format_str is None:
        format_str = config.get("default_format", DEFAULT_CONFIG["default_format"])
    
    return save_dir / f"{filename}.{format_str}"
