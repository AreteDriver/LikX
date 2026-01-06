"""Command registry for LikX command palette."""

from dataclasses import dataclass, field
from typing import Callable, List

from .editor import ToolType


@dataclass
class Command:
    """A command that can be executed from the command palette."""

    name: str  # Display name
    keywords: List[str] = field(default_factory=list)  # Search keywords
    callback: Callable = None  # Action to execute
    icon: str = ""  # Optional icon/emoji
    shortcut: str = ""  # Display shortcut hint

    def matches(self, query: str) -> bool:
        """Check if command matches search query (case-insensitive)."""
        query = query.lower().strip()
        if not query:
            return True

        # Check name
        if query in self.name.lower():
            return True

        # Check keywords
        for keyword in self.keywords:
            if query in keyword.lower():
                return True

        return False


def build_command_registry(editor_window) -> List[Command]:
    """Build list of all available commands for the palette."""
    commands = []

    # === TOOLS ===
    commands.extend(
        [
            Command(
                "Pen Tool",
                ["draw", "pen", "brush", "freehand"],
                lambda: editor_window._set_tool(ToolType.PEN),
                "✏️",
                "P",
            ),
            Command(
                "Highlighter",
                ["highlight", "marker", "emphasis"],
                lambda: editor_window._set_tool(ToolType.HIGHLIGHTER),
                "🖍️",
                "H",
            ),
            Command(
                "Arrow Tool",
                ["arrow", "pointer", "direction"],
                lambda: editor_window._set_tool(ToolType.ARROW),
                "➡️",
                "A",
            ),
            Command(
                "Text Tool",
                ["text", "type", "label", "annotation"],
                lambda: editor_window._set_tool(ToolType.TEXT),
                "📝",
                "T",
            ),
            Command(
                "Blur Tool",
                ["blur", "privacy", "hide", "obscure"],
                lambda: editor_window._set_tool(ToolType.BLUR),
                "🔍",
                "B",
            ),
            Command(
                "Pixelate Tool",
                ["pixelate", "censor", "redact", "mosaic"],
                lambda: editor_window._set_tool(ToolType.PIXELATE),
                "◼️",
                "X",
            ),
            Command(
                "Rectangle",
                ["rectangle", "box", "shape", "square"],
                lambda: editor_window._set_tool(ToolType.RECTANGLE),
                "⬜",
                "R",
            ),
            Command(
                "Ellipse",
                ["ellipse", "circle", "oval", "round"],
                lambda: editor_window._set_tool(ToolType.ELLIPSE),
                "⭕",
                "E",
            ),
            Command(
                "Line Tool",
                ["line", "straight", "segment"],
                lambda: editor_window._set_tool(ToolType.LINE),
                "📏",
                "L",
            ),
            Command(
                "Crop Tool",
                ["crop", "trim", "cut", "resize"],
                lambda: editor_window._set_tool(ToolType.CROP),
                "✂️",
                "C",
            ),
            Command(
                "Eraser",
                ["eraser", "delete", "remove", "undo drawing"],
                lambda: editor_window._set_tool(ToolType.ERASER),
                "🧹",
                "",
            ),
            Command(
                "Number Marker",
                ["number", "marker", "step", "sequence", "counter"],
                lambda: editor_window._set_tool(ToolType.NUMBER),
                "①",
                "N",
            ),
        ]
    )

    # === ACTIONS ===
    commands.extend(
        [
            Command(
                "Save",
                ["save", "export", "file", "disk"],
                editor_window._save,
                "💾",
                "Ctrl+S",
            ),
            Command(
                "Copy to Clipboard",
                ["copy", "clipboard", "paste"],
                editor_window._copy_to_clipboard,
                "📋",
                "Ctrl+C",
            ),
            Command(
                "Upload to Imgur",
                ["upload", "share", "imgur", "cloud", "link"],
                editor_window._upload,
                "☁️",
                "",
            ),
            Command(
                "Undo",
                ["undo", "back", "revert", "mistake"],
                editor_window._undo,
                "↩️",
                "Ctrl+Z",
            ),
            Command(
                "Redo",
                ["redo", "forward", "repeat"],
                editor_window._redo,
                "↪️",
                "Ctrl+Y",
            ),
            Command(
                "Clear All Annotations",
                ["clear", "reset", "delete all", "clean"],
                editor_window._clear,
                "🗑️",
                "",
            ),
        ]
    )

    # === EFFECTS ===
    commands.extend(
        [
            Command(
                "Add Shadow",
                ["shadow", "effect", "drop shadow"],
                editor_window._apply_shadow,
                "🌑",
                "",
            ),
            Command(
                "Add Border",
                ["border", "frame", "outline"],
                editor_window._apply_border,
                "🔲",
                "",
            ),
            Command(
                "Round Corners",
                ["round", "corners", "radius", "curved"],
                editor_window._apply_round_corners,
                "⬜",
                "",
            ),
        ]
    )

    # === PREMIUM FEATURES ===
    commands.extend(
        [
            Command(
                "OCR - Extract Text",
                ["ocr", "text", "extract", "read", "recognize"],
                editor_window._extract_text,
                "📖",
                "",
            ),
            Command(
                "Pin to Desktop",
                ["pin", "float", "always on top", "sticky"],
                editor_window._pin_to_desktop,
                "📌",
                "",
            ),
        ]
    )

    return commands
