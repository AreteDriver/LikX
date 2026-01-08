"""Tests for commands module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCommandsModuleAvailability:
    """Test commands module can be imported."""

    def test_commands_module_imports(self):
        from src import commands
        assert commands is not None

    def test_command_class_exists(self):
        from src.commands import Command
        assert Command is not None

    def test_build_command_registry_exists(self):
        from src.commands import build_command_registry
        assert callable(build_command_registry)


class TestCommandDataclass:
    """Test Command dataclass."""

    def test_create_command_basic(self):
        from src.commands import Command

        cmd = Command(name="Test Command")
        assert cmd.name == "Test Command"
        assert cmd.keywords == []
        assert cmd.callback is None
        assert cmd.icon == ""
        assert cmd.shortcut == ""

    def test_create_command_with_all_fields(self):
        from src.commands import Command

        callback = lambda: None
        cmd = Command(
            name="Full Command",
            keywords=["test", "example"],
            callback=callback,
            icon="📝",
            shortcut="Ctrl+T"
        )

        assert cmd.name == "Full Command"
        assert cmd.keywords == ["test", "example"]
        assert cmd.callback is callback
        assert cmd.icon == "📝"
        assert cmd.shortcut == "Ctrl+T"

    def test_command_with_keywords(self):
        from src.commands import Command

        cmd = Command(
            name="Pen Tool",
            keywords=["draw", "pen", "brush"]
        )

        assert len(cmd.keywords) == 3
        assert "draw" in cmd.keywords


class TestCommandMatches:
    """Test Command.matches() method."""

    def test_matches_empty_query(self):
        from src.commands import Command

        cmd = Command(name="Test Command")
        assert cmd.matches("") is True

    def test_matches_whitespace_query(self):
        from src.commands import Command

        cmd = Command(name="Test Command")
        assert cmd.matches("   ") is True

    def test_matches_name_exact(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool")
        assert cmd.matches("Pen Tool") is True

    def test_matches_name_case_insensitive(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool")
        assert cmd.matches("pen tool") is True
        assert cmd.matches("PEN TOOL") is True

    def test_matches_name_partial(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool")
        assert cmd.matches("Pen") is True
        assert cmd.matches("Tool") is True
        assert cmd.matches("en") is True

    def test_matches_keyword_exact(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool", keywords=["draw", "brush"])
        assert cmd.matches("draw") is True
        assert cmd.matches("brush") is True

    def test_matches_keyword_case_insensitive(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool", keywords=["draw", "brush"])
        assert cmd.matches("DRAW") is True
        assert cmd.matches("Brush") is True

    def test_matches_keyword_partial(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool", keywords=["draw", "brush"])
        assert cmd.matches("dra") is True
        assert cmd.matches("rus") is True

    def test_no_match(self):
        from src.commands import Command

        cmd = Command(name="Pen Tool", keywords=["draw", "brush"])
        assert cmd.matches("eraser") is False
        assert cmd.matches("xyz") is False

    def test_matches_with_no_keywords(self):
        from src.commands import Command

        cmd = Command(name="Test")
        assert cmd.matches("Test") is True
        assert cmd.matches("other") is False


class TestBuildCommandRegistry:
    """Test build_command_registry function."""

    def test_returns_list(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        assert isinstance(commands, list)

    def test_returns_command_objects(self):
        from src.commands import build_command_registry, Command

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        for cmd in commands:
            assert isinstance(cmd, Command)

    def test_contains_tool_commands(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        names = [cmd.name for cmd in commands]
        assert "Pen Tool" in names
        assert "Arrow Tool" in names
        assert "Text Tool" in names
        assert "Blur Tool" in names

    def test_contains_action_commands(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        names = [cmd.name for cmd in commands]
        assert "Save" in names
        assert "Copy to Clipboard" in names
        assert "Undo" in names
        assert "Redo" in names

    def test_contains_effect_commands(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        names = [cmd.name for cmd in commands]
        assert "Add Shadow" in names
        assert "Add Border" in names
        assert "Round Corners" in names

    def test_contains_premium_commands(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        names = [cmd.name for cmd in commands]
        assert "OCR - Extract Text" in names
        assert "Pin to Desktop" in names

    def test_commands_have_callbacks(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        # Most commands should have callbacks
        for cmd in commands:
            if cmd.name not in ["Clear All Annotations"]:
                assert cmd.callback is not None or cmd.name in ["Eraser"]

    def test_commands_have_icons(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        # Most commands should have icons
        icons_found = sum(1 for cmd in commands if cmd.icon)
        assert icons_found > 20  # Most commands have icons

    def test_commands_have_shortcuts(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        # Some commands should have shortcuts
        shortcuts_found = sum(1 for cmd in commands if cmd.shortcut)
        assert shortcuts_found > 10


class TestCommandCallbacks:
    """Test that command callbacks work correctly."""

    def test_tool_command_callback_sets_tool(self):
        from src.commands import build_command_registry
        from src.editor import ToolType

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        # Find Pen Tool command
        pen_cmd = next((c for c in commands if c.name == "Pen Tool"), None)
        assert pen_cmd is not None

        # Execute callback
        pen_cmd.callback()

        # Should have called _set_tool with ToolType.PEN
        mock_editor._set_tool.assert_called_once_with(ToolType.PEN)

    def test_action_command_callback(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        # Find Save command
        save_cmd = next((c for c in commands if c.name == "Save"), None)
        assert save_cmd is not None

        # Execute callback
        save_cmd.callback()

        # Should have called _save
        mock_editor._save.assert_called_once()

    def test_undo_command_callback(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        undo_cmd = next((c for c in commands if c.name == "Undo"), None)
        assert undo_cmd is not None

        undo_cmd.callback()
        mock_editor._undo.assert_called_once()

    def test_redo_command_callback(self):
        from src.commands import build_command_registry

        mock_editor = MagicMock()
        commands = build_command_registry(mock_editor)

        redo_cmd = next((c for c in commands if c.name == "Redo"), None)
        assert redo_cmd is not None

        redo_cmd.callback()
        mock_editor._redo.assert_called_once()


class TestCommandEdgeCases:
    """Test edge cases for Command class."""

    def test_command_with_empty_name(self):
        from src.commands import Command

        cmd = Command(name="")
        assert cmd.name == ""
        assert cmd.matches("") is True

    def test_command_matches_with_special_characters(self):
        from src.commands import Command

        cmd = Command(name="OCR - Extract Text", keywords=["ocr", "text"])
        assert cmd.matches("OCR") is True
        assert cmd.matches("-") is True
        assert cmd.matches("Extract") is True

    def test_command_with_unicode_icon(self):
        from src.commands import Command

        cmd = Command(name="Test", icon="📝")
        assert cmd.icon == "📝"

    def test_command_with_complex_shortcut(self):
        from src.commands import Command

        cmd = Command(name="Test", shortcut="Ctrl+Shift+P")
        assert cmd.shortcut == "Ctrl+Shift+P"
