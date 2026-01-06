"""Screenshot history manager - browse and manage past captures."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkPixbuf', '2.0')
    from gi.repository import Gtk, GdkPixbuf
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

from . import config


class HistoryEntry:
    """Represents a screenshot in history."""
    
    def __init__(self, filepath: Path, timestamp: datetime, mode: str = "unknown"):
        self.filepath = filepath
        self.timestamp = timestamp
        self.mode = mode
        self.thumbnail = None
    
    def to_dict(self) -> Dict:
        return {
            'filepath': str(self.filepath),
            'timestamp': self.timestamp.isoformat(),
            'mode': self.mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HistoryEntry':
        return cls(
            Path(data['filepath']),
            datetime.fromisoformat(data['timestamp']),
            data.get('mode', 'unknown')
        )


class HistoryManager:
    """Manages screenshot history."""
    
    def __init__(self):
        self.history_file = config.get_config_dir() / "history.json"
        self.entries: List[HistoryEntry] = []
        self.load()
    
    def load(self) -> None:
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [HistoryEntry.from_dict(e) for e in data]
                    # Filter out deleted files
                    self.entries = [e for e in self.entries if e.filepath.exists()]
            except (json.JSONDecodeError, KeyError):
                self.entries = []
    
    def save(self) -> None:
        """Save history to file."""
        config.ensure_config_dir()
        try:
            with open(self.history_file, 'w') as f:
                json.dump([e.to_dict() for e in self.entries], f, indent=2)
        except IOError:
            pass
    
    def add(self, filepath: Path, mode: str = "unknown") -> None:
        """Add a screenshot to history."""
        entry = HistoryEntry(filepath, datetime.now(), mode)
        self.entries.insert(0, entry)  # Most recent first
        
        # Keep only last 100 entries
        self.entries = self.entries[:100]
        self.save()
    
    def remove(self, entry: HistoryEntry) -> None:
        """Remove entry from history."""
        if entry in self.entries:
            self.entries.remove(entry)
            self.save()
    
    def clear(self) -> None:
        """Clear all history."""
        self.entries.clear()
        self.save()
    
    def get_recent(self, limit: int = 20) -> List[HistoryEntry]:
        """Get recent entries."""
        return self.entries[:limit]


class HistoryWindow:
    """Window to browse screenshot history."""
    
    def __init__(self, parent=None):
        if not GTK_AVAILABLE:
            raise RuntimeError("GTK not available - install python3-gi")
        
        self.manager = HistoryManager()
        
        self.window = Gtk.Window(title="Screenshot History")
        self.window.set_default_size(800, 600)
        if parent:
            self.window.set_transient_for(parent)
        
        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(vbox)
        
        # Toolbar
        toolbar = self._create_toolbar()
        vbox.pack_start(toolbar, False, False, 0)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Icon view for thumbnails
        self.store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, object)
        self.icon_view = Gtk.IconView(model=self.store)
        self.icon_view.set_pixbuf_column(0)
        self.icon_view.set_text_column(1)
        self.icon_view.set_item_width(150)
        self.icon_view.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.icon_view.connect("item-activated", self._on_item_activated)
        
        scrolled.add(self.icon_view)
        vbox.pack_start(scrolled, True, True, 0)
        
        # Status bar
        self.statusbar = Gtk.Statusbar()
        vbox.pack_start(self.statusbar, False, False, 0)
        
        self.window.show_all()
        self._load_history()
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = Gtk.Toolbar()
        
        refresh = Gtk.ToolButton(label="🔄 Refresh")
        refresh.connect("clicked", lambda b: self._load_history())
        toolbar.insert(refresh, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        delete = Gtk.ToolButton(label="🗑️ Delete Selected")
        delete.connect("clicked", self._on_delete)
        toolbar.insert(delete, -1)
        
        clear = Gtk.ToolButton(label="🧹 Clear All")
        clear.connect("clicked", self._on_clear_all)
        toolbar.insert(clear, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        folder = Gtk.ToolButton(label="📁 Open Folder")
        folder.connect("clicked", self._on_open_folder)
        toolbar.insert(folder, -1)
        
        return toolbar
    
    def _load_history(self) -> None:
        """Load history into icon view."""
        self.store.clear()
        self.manager.load()
        
        for entry in self.manager.get_recent():
            if entry.filepath.exists():
                try:
                    # Load thumbnail
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(entry.filepath), 128, 128, True
                    )
                    
                    # Format info
                    time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M")
                    info = f"{time_str}\n{entry.mode}"
                    
                    self.store.append([pixbuf, info, str(entry.filepath), entry])
                except Exception:
                    pass
        
        count = len(self.store)
        self.statusbar.push(0, f"{count} screenshots")
    
    def _on_item_activated(self, icon_view, path):
        """Open selected screenshot."""
        model = icon_view.get_model()
        iter = model.get_iter(path)
        filepath = model.get_value(iter, 2)
        
        import subprocess
        try:
            subprocess.Popen(['xdg-open', filepath])
        except Exception as e:
            print(f"Failed to open: {e}")
    
    def _on_delete(self, button):
        """Delete selected screenshot."""
        selected = self.icon_view.get_selected_items()
        if not selected:
            return
        
        path = selected[0]
        iter = self.store.get_iter(path)
        entry = self.store.get_value(iter, 3)
        
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Delete this screenshot?"
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            # Delete file
            if entry.filepath.exists():
                entry.filepath.unlink()
            # Remove from history
            self.manager.remove(entry)
            # Reload
            self._load_history()
    
    def _on_clear_all(self, button):
        """Clear all history."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Clear all screenshot history?",
            secondary_text="This will not delete the files, only the history records."
        )
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self.manager.clear()
            self._load_history()
    
    def _on_open_folder(self, button):
        """Open screenshots folder."""
        cfg = config.load_config()
        folder = Path(cfg.get('save_directory', '~/Pictures/Screenshots')).expanduser()
        
        import subprocess
        try:
            subprocess.Popen(['xdg-open', str(folder)])
        except Exception as e:
            print(f"Failed to open folder: {e}")
