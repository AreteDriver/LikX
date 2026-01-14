"""Command palette UI for LikX - searchable command interface."""

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("Gdk", "3.0")
    from gi.repository import Gdk, Gtk

    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from typing import List, Optional

from .commands import Command


class CommandPalette(Gtk.Window):
    """Searchable command palette overlay."""

    def __init__(self, commands: List[Command], parent: Optional[Gtk.Window] = None):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available")

        super().__init__(type=Gtk.WindowType.POPUP)

        self.commands = commands
        self.filtered_commands = commands.copy()
        self.selected_index = 0
        self.parent_window = parent

        self._setup_window()
        self._build_ui()
        self._apply_css()
        self._connect_signals()

    def _setup_window(self):
        """Configure window properties."""
        self.set_decorated(False)
        self.set_modal(True)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)
        self.set_default_size(500, 400)

        if self.parent_window:
            self.set_transient_for(self.parent_window)

    def _build_ui(self):
        """Build the palette UI."""
        # Main container with border
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        self.add(frame)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame.add(vbox)

        # Search entry with icon
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_box.set_margin_top(12)
        search_box.set_margin_bottom(8)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)

        prompt_label = Gtk.Label(label=">")
        prompt_label.get_style_context().add_class("prompt")
        search_box.pack_start(prompt_label, False, False, 0)

        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Type to search commands...")
        self.search_entry.set_has_frame(False)
        search_box.pack_start(self.search_entry, True, True, 0)

        vbox.pack_start(search_box, False, False, 0)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, False, False, 0)

        # Results list in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        scrolled.add(self.listbox)

        vbox.pack_start(scrolled, True, True, 0)

        # Footer with hints
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        footer.set_margin_top(8)
        footer.set_margin_bottom(8)
        footer.set_margin_start(12)
        footer.set_margin_end(12)

        hints = [("↑↓", "Navigate"), ("Enter", "Execute"), ("Esc", "Close")]
        for key, action in hints:
            hint_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
            key_label = Gtk.Label(label=key)
            key_label.get_style_context().add_class("keyhint")
            action_label = Gtk.Label(label=action)
            action_label.get_style_context().add_class("hint")
            hint_box.pack_start(key_label, False, False, 0)
            hint_box.pack_start(action_label, False, False, 0)
            footer.pack_start(hint_box, False, False, 0)

        vbox.pack_start(footer, False, False, 0)

        # Populate initial list
        self._populate_list()

    def _apply_css(self):
        """Apply dark theme CSS styling."""
        css = b"""
        window {
            background-color: #1e1e1e;
            border: 1px solid #3c3c3c;
            border-radius: 8px;
        }
        frame {
            background-color: #1e1e1e;
            border-radius: 8px;
        }
        entry {
            background-color: transparent;
            color: #ffffff;
            font-size: 16px;
            border: none;
            box-shadow: none;
        }
        entry:focus {
            box-shadow: none;
            border: none;
        }
        .prompt {
            color: #569cd6;
            font-size: 18px;
            font-weight: bold;
        }
        separator {
            background-color: #3c3c3c;
            min-height: 1px;
        }
        list {
            background-color: #1e1e1e;
        }
        row {
            padding: 8px 12px;
            background-color: #1e1e1e;
        }
        row:selected {
            background-color: #094771;
        }
        row:hover {
            background-color: #2d2d2d;
        }
        .command-icon {
            font-size: 16px;
            min-width: 24px;
        }
        .command-name {
            color: #ffffff;
            font-size: 14px;
        }
        .command-shortcut {
            color: #808080;
            font-size: 12px;
        }
        .keyhint {
            background-color: #3c3c3c;
            color: #cccccc;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
        }
        .hint {
            color: #808080;
            font-size: 11px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _connect_signals(self):
        """Connect event handlers."""
        self.search_entry.connect("changed", self._on_search_changed)
        self.search_entry.connect("key-press-event", self._on_key_press)
        self.listbox.connect("row-activated", self._on_row_activated)
        self.connect("focus-out-event", self._on_focus_out)

    def _populate_list(self):
        """Populate listbox with filtered commands."""
        # Clear existing rows
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        # Add filtered commands
        for cmd in self.filtered_commands:
            row = self._create_command_row(cmd)
            self.listbox.add(row)

        self.listbox.show_all()

        # Select first item
        if self.filtered_commands:
            first_row = self.listbox.get_row_at_index(0)
            if first_row:
                self.listbox.select_row(first_row)
            self.selected_index = 0

    def _create_command_row(self, cmd: Command) -> Gtk.ListBoxRow:
        """Create a row widget for a command."""
        row = Gtk.ListBoxRow()
        row.command = cmd  # Store reference

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_top(4)
        hbox.set_margin_bottom(4)

        # Icon
        icon_label = Gtk.Label(label=cmd.icon if cmd.icon else "  ")
        icon_label.get_style_context().add_class("command-icon")
        hbox.pack_start(icon_label, False, False, 0)

        # Name
        name_label = Gtk.Label(label=cmd.name)
        name_label.get_style_context().add_class("command-name")
        name_label.set_xalign(0)
        hbox.pack_start(name_label, True, True, 0)

        # Shortcut hint
        if cmd.shortcut:
            shortcut_label = Gtk.Label(label=cmd.shortcut)
            shortcut_label.get_style_context().add_class("command-shortcut")
            hbox.pack_end(shortcut_label, False, False, 0)

        row.add(hbox)
        return row

    def _on_search_changed(self, entry):
        """Filter commands based on search text."""
        query = entry.get_text()

        self.filtered_commands = [cmd for cmd in self.commands if cmd.matches(query)]
        self._populate_list()

    def _on_key_press(self, widget, event):
        """Handle keyboard navigation."""
        keyval = event.keyval

        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True

        elif keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
            self._execute_selected()
            return True

        elif keyval == Gdk.KEY_Up:
            self._move_selection(-1)
            return True

        elif keyval == Gdk.KEY_Down:
            self._move_selection(1)
            return True

        elif keyval == Gdk.KEY_Tab:
            # Tab also moves down
            self._move_selection(1)
            return True

        return False

    def _move_selection(self, delta: int):
        """Move selection up or down."""
        if not self.filtered_commands:
            return

        self.selected_index = (self.selected_index + delta) % len(
            self.filtered_commands
        )
        row = self.listbox.get_row_at_index(self.selected_index)
        if row:
            self.listbox.select_row(row)
            # Scroll to make visible
            row.grab_focus()
            self.search_entry.grab_focus()  # Keep focus on entry

    def _execute_selected(self):
        """Execute the currently selected command."""
        row = self.listbox.get_selected_row()
        if row and hasattr(row, "command"):
            cmd = row.command
            self.hide()
            if cmd.callback:
                cmd.callback()

    def _on_row_activated(self, listbox, row):
        """Handle row click/activation."""
        if row and hasattr(row, "command"):
            cmd = row.command
            self.hide()
            if cmd.callback:
                cmd.callback()

    def _on_focus_out(self, widget, event):
        """Hide when focus is lost."""
        # Small delay to allow click handling
        from gi.repository import GLib

        GLib.timeout_add(100, self._check_focus)
        return False

    def _check_focus(self):
        """Check if we should hide due to focus loss."""
        if not self.has_toplevel_focus():
            self.hide()
        return False

    def show_centered(self, parent: Gtk.Window):
        """Show the palette centered on parent window."""
        self.parent_window = parent
        self.set_transient_for(parent)

        # Get parent geometry
        parent_win = parent.get_window()
        if parent_win:
            _, px, py = parent_win.get_origin()
            pw = parent.get_allocated_width()
            ph = parent.get_allocated_height()

            # Calculate centered position
            w, h = 500, 400
            x = px + (pw - w) // 2
            y = py + (ph - h) // 3  # Slightly above center

            self.move(x, y)

        # Reset state
        self.search_entry.set_text("")
        self.filtered_commands = self.commands.copy()
        self._populate_list()

        self.show_all()
        self.search_entry.grab_focus()
