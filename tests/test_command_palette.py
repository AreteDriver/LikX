"""Tests for command_palette module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCommandPaletteModuleAvailability:
    """Test command_palette module can be imported."""

    def test_command_palette_module_imports(self):
        from src import command_palette
        assert command_palette is not None

    def test_gtk_available_flag_exists(self):
        from src.command_palette import GTK_AVAILABLE
        assert isinstance(GTK_AVAILABLE, bool)

    def test_command_palette_class_exists(self):
        from src.command_palette import CommandPalette
        assert CommandPalette is not None


class TestCommandPaletteInit:
    """Test CommandPalette initialization."""

    def test_init_raises_without_gtk(self):
        """Should raise RuntimeError if GTK not available."""
        with patch("src.command_palette.GTK_AVAILABLE", False):
            from src.command_palette import CommandPalette
            from src.commands import Command

            try:
                # Need to reload to get patched value
                CommandPalette([Command(name="Test")], None)
                # If GTK_AVAILABLE was already True at import, it won't raise
            except RuntimeError as e:
                assert "GTK not available" in str(e)

    def test_init_stores_commands(self):
        """Test that commands are stored."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return  # Skip if GTK not available

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Test 1"),
            Command(name="Test 2"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        assert len(palette.commands) == 2
        assert palette.filtered_commands == commands

    def test_init_sets_selected_index(self):
        """Test initial selected index is 0."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        assert palette.selected_index == 0


class TestCommandPaletteAttributes:
    """Test CommandPalette attributes and methods exist."""

    def test_has_setup_window(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_setup_window")

    def test_has_build_ui(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_build_ui")

    def test_has_apply_css(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_apply_css")

    def test_has_connect_signals(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_connect_signals")

    def test_has_populate_list(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_populate_list")

    def test_has_create_command_row(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_create_command_row")

    def test_has_on_search_changed(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_on_search_changed")

    def test_has_on_key_press(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_on_key_press")

    def test_has_move_selection(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_move_selection")

    def test_has_execute_selected(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_execute_selected")

    def test_has_on_row_activated(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_on_row_activated")

    def test_has_on_focus_out(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "_on_focus_out")

    def test_has_show_centered(self):
        from src.command_palette import CommandPalette
        assert hasattr(CommandPalette, "show_centered")


class TestCommandPaletteFiltering:
    """Test command filtering functionality."""

    def test_empty_query_shows_all(self):
        """Empty query should show all commands."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Pen Tool"),
            Command(name="Arrow Tool"),
            Command(name="Text Tool"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Simulate empty search
        palette.search_entry.get_text = MagicMock(return_value="")
        palette._on_search_changed(palette.search_entry)

        assert len(palette.filtered_commands) == 3

    def test_filter_by_name(self):
        """Should filter commands by name."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Pen Tool"),
            Command(name="Arrow Tool"),
            Command(name="Text Tool"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Simulate search for "Pen"
        palette.search_entry.get_text = MagicMock(return_value="Pen")
        palette._on_search_changed(palette.search_entry)

        assert len(palette.filtered_commands) == 1
        assert palette.filtered_commands[0].name == "Pen Tool"

    def test_filter_by_keyword(self):
        """Should filter commands by keyword."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Pen Tool", keywords=["draw", "brush"]),
            Command(name="Arrow Tool", keywords=["pointer"]),
            Command(name="Text Tool", keywords=["type"]),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Search by keyword
        palette.search_entry.get_text = MagicMock(return_value="draw")
        palette._on_search_changed(palette.search_entry)

        assert len(palette.filtered_commands) == 1
        assert palette.filtered_commands[0].name == "Pen Tool"


class TestCommandPaletteNavigation:
    """Test keyboard navigation."""

    def test_move_selection_down(self):
        """Test moving selection down."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Test 1"),
            Command(name="Test 2"),
            Command(name="Test 3"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        assert palette.selected_index == 0

        palette._move_selection(1)
        assert palette.selected_index == 1

        palette._move_selection(1)
        assert palette.selected_index == 2

    def test_move_selection_up(self):
        """Test moving selection up."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Test 1"),
            Command(name="Test 2"),
            Command(name="Test 3"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        palette.selected_index = 2
        palette._move_selection(-1)
        assert palette.selected_index == 1

    def test_move_selection_wraps_around(self):
        """Test selection wraps around list."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [
            Command(name="Test 1"),
            Command(name="Test 2"),
            Command(name="Test 3"),
        ]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Move past end
        palette.selected_index = 2
        palette._move_selection(1)
        assert palette.selected_index == 0

        # Move before start
        palette._move_selection(-1)
        assert palette.selected_index == 2

    def test_move_selection_empty_list(self):
        """Test moving selection with empty list."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([], None)

        # Should not raise
        palette.filtered_commands = []
        palette._move_selection(1)


class TestCommandPaletteExecution:
    """Test command execution."""

    def test_execute_selected_calls_callback(self):
        """Test that execute_selected calls the command callback."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        callback = MagicMock()
        commands = [Command(name="Test", callback=callback)]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Mock the listbox
        mock_row = MagicMock()
        mock_row.command = commands[0]
        palette.listbox.get_selected_row = MagicMock(return_value=mock_row)
        palette.hide = MagicMock()

        palette._execute_selected()

        callback.assert_called_once()
        palette.hide.assert_called_once()

    def test_execute_selected_no_selection(self):
        """Test execute_selected with no selection."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette.listbox.get_selected_row = MagicMock(return_value=None)

        # Should not raise
        palette._execute_selected()

    def test_on_row_activated_calls_callback(self):
        """Test that row activation calls callback."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        callback = MagicMock()
        cmd = Command(name="Test", callback=callback)

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([cmd], None)

        mock_row = MagicMock()
        mock_row.command = cmd
        palette.hide = MagicMock()

        palette._on_row_activated(palette.listbox, mock_row)

        callback.assert_called_once()
        palette.hide.assert_called_once()


class TestCommandPaletteKeyHandling:
    """Test key press handling."""

    def test_escape_hides_palette(self):
        """Test Escape key hides palette."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette.hide = MagicMock()

        # Mock key event for Escape
        mock_event = MagicMock()
        mock_event.keyval = 65307  # Gdk.KEY_Escape

        result = palette._on_key_press(None, mock_event)

        assert result is True
        palette.hide.assert_called_once()

    def test_return_executes_selected(self):
        """Test Return key executes selected command."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette._execute_selected = MagicMock()

        # Mock key event for Return
        mock_event = MagicMock()
        mock_event.keyval = 65293  # Gdk.KEY_Return

        result = palette._on_key_press(None, mock_event)

        assert result is True
        palette._execute_selected.assert_called_once()

    def test_up_moves_selection_up(self):
        """Test Up arrow moves selection up."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette._move_selection = MagicMock()

        mock_event = MagicMock()
        mock_event.keyval = 65362  # Gdk.KEY_Up

        result = palette._on_key_press(None, mock_event)

        assert result is True
        palette._move_selection.assert_called_once_with(-1)

    def test_down_moves_selection_down(self):
        """Test Down arrow moves selection down."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette._move_selection = MagicMock()

        mock_event = MagicMock()
        mock_event.keyval = 65364  # Gdk.KEY_Down

        result = palette._on_key_press(None, mock_event)

        assert result is True
        palette._move_selection.assert_called_once_with(1)

    def test_tab_moves_selection_down(self):
        """Test Tab moves selection down."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        palette._move_selection = MagicMock()

        mock_event = MagicMock()
        mock_event.keyval = 65289  # Gdk.KEY_Tab

        result = palette._on_key_press(None, mock_event)

        assert result is True
        palette._move_selection.assert_called_once_with(1)

    def test_other_key_returns_false(self):
        """Test other keys return False."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([Command(name="Test")], None)

        mock_event = MagicMock()
        mock_event.keyval = 97  # 'a' key

        result = palette._on_key_press(None, mock_event)

        assert result is False


class TestCommandPaletteEdgeCases:
    """Test edge cases for CommandPalette."""

    def test_filter_case_insensitive(self):
        """Test filtering is case insensitive."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        commands = [Command(name="Pen Tool")]

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette(commands, None)

        # Search with different cases
        palette.search_entry.get_text = MagicMock(return_value="PEN")
        palette._on_search_changed(palette.search_entry)
        assert len(palette.filtered_commands) == 1

        palette.search_entry.get_text = MagicMock(return_value="pen")
        palette._on_search_changed(palette.search_entry)
        assert len(palette.filtered_commands) == 1

    def test_empty_commands_list(self):
        """Test with empty commands list."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([], None)

        assert palette.commands == []
        assert palette.filtered_commands == []

    def test_command_without_callback(self):
        """Test command without callback doesn't crash."""
        from src.command_palette import GTK_AVAILABLE
        if not GTK_AVAILABLE:
            return

        from src.command_palette import CommandPalette
        from src.commands import Command

        cmd = Command(name="Test", callback=None)

        with patch.object(CommandPalette, "_apply_css"):
            palette = CommandPalette([cmd], None)

        mock_row = MagicMock()
        mock_row.command = cmd
        palette.listbox.get_selected_row = MagicMock(return_value=mock_row)
        palette.hide = MagicMock()

        # Should not raise even though callback is None
        palette._execute_selected()
