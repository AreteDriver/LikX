"""Tests for config module."""

from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    DEFAULT_CONFIG,
    load_config,
    get_setting,
    validate_format,
    get_save_path,
)


class TestDefaultConfig:
    """Test default configuration values."""

    def test_default_config_has_required_keys(self):
        required_keys = [
            "save_directory",
            "default_format",
            "supported_formats",
            "copy_to_clipboard",
            "show_notification",
        ]
        for key in required_keys:
            assert key in DEFAULT_CONFIG

    def test_default_format_is_png(self):
        assert DEFAULT_CONFIG["default_format"] == "png"

    def test_supported_formats_includes_common_types(self):
        formats = DEFAULT_CONFIG["supported_formats"]
        assert "png" in formats
        assert "jpg" in formats


class TestLoadConfig:
    """Test config loading."""

    def test_load_config_returns_dict(self):
        config = load_config()
        assert isinstance(config, dict)

    def test_load_config_has_default_values(self):
        config = load_config()
        assert "default_format" in config
        assert "save_directory" in config

    @patch("src.config.CONFIG_FILE")
    def test_load_config_with_missing_file(self, mock_file):
        mock_file.exists.return_value = False
        config = load_config()
        assert config == DEFAULT_CONFIG


class TestValidateFormat:
    """Test format validation."""

    def test_validate_png(self):
        assert validate_format("png") is True

    def test_validate_jpg(self):
        assert validate_format("jpg") is True

    def test_validate_jpeg(self):
        assert validate_format("jpeg") is True

    def test_validate_invalid_format(self):
        assert validate_format("xyz") is False

    def test_validate_case_insensitive(self):
        assert validate_format("PNG") is True
        assert validate_format("Png") is True


class TestGetSavePath:
    """Test save path generation."""

    def test_get_save_path_returns_path(self):
        path = get_save_path()
        assert isinstance(path, Path)

    def test_get_save_path_has_correct_extension(self):
        path = get_save_path(format_str="png")
        assert path.suffix == ".png"

    def test_get_save_path_with_custom_filename(self):
        path = get_save_path(filename="test_image", format_str="png")
        assert path.name == "test_image.png"

    def test_get_save_path_with_jpg_format(self):
        path = get_save_path(format_str="jpg")
        assert path.suffix == ".jpg"


class TestGetSetting:
    """Test getting individual settings."""

    def test_get_existing_setting(self):
        value = get_setting("default_format")
        assert value is not None

    def test_get_missing_setting_returns_default(self):
        value = get_setting("nonexistent_key", default="fallback")
        assert value == "fallback"

    def test_get_missing_setting_without_default(self):
        value = get_setting("nonexistent_key")
        assert value is None
