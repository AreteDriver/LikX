"""Global keyboard shortcuts for LikX."""

import os
import subprocess
from typing import Callable, Dict, List, Tuple


class HotkeyManager:
    """Manages global keyboard shortcuts."""

    # Base path for LikX custom keybindings
    GNOME_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
    GNOME_BASE_PATH = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"

    def __init__(self):
        # key_id -> (callback, command)
        self.hotkeys: Dict[str, Tuple[Callable, str]] = {}
        self.desktop_env = self._detect_desktop_environment()
        self._registered_paths: List[str] = []

    def _detect_desktop_environment(self) -> str:
        """Detect the current desktop environment."""
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

        if "gnome" in desktop:
            return "gnome"
        elif "kde" in desktop or "plasma" in desktop:
            return "kde"
        elif "xfce" in desktop:
            return "xfce"
        elif "mate" in desktop:
            return "mate"
        else:
            return "unknown"

    def register_hotkey(
        self, key_combo: str, callback: Callable, command: str, hotkey_id: str = ""
    ) -> bool:
        """Register a global hotkey.

        Args:
            key_combo: Key combination (e.g., '<Control><Shift>F')
            callback: Function to call when hotkey is pressed
            command: Command to execute
            hotkey_id: Unique identifier for this hotkey (e.g., 'fullscreen', 'region')

        Returns:
            True if registration successful
        """
        # Generate ID from command if not provided
        if not hotkey_id:
            if "--" in command:
                hotkey_id = command.split("--")[-1].split()[0]
            else:
                hotkey_id = "default"

        self.hotkeys[hotkey_id] = (callback, command)

        if self.desktop_env == "gnome":
            return self._register_gnome_hotkey(key_combo, command, hotkey_id)
        elif self.desktop_env == "kde":
            return self._register_kde_hotkey(key_combo, command, hotkey_id)

        return False

    def _register_gnome_hotkey(
        self, key_combo: str, command: str, hotkey_id: str
    ) -> bool:
        """Register hotkey in GNOME with unique path per hotkey."""
        try:
            # Create unique path for this hotkey
            custom_path = f"{self.GNOME_BASE_PATH}/likx-{hotkey_id}/"

            # Get current custom keybindings
            result = subprocess.run(
                ["gsettings", "get", self.GNOME_SCHEMA, "custom-keybindings"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                current = result.stdout.strip()
                if custom_path not in current:
                    # Add our custom path
                    if current == "@as []":
                        new_value = f"['{custom_path}']"
                    else:
                        # Parse existing and add
                        new_value = current.rstrip("]") + f", '{custom_path}']"

                    subprocess.run([
                        "gsettings", "set", self.GNOME_SCHEMA,
                        "custom-keybindings", new_value
                    ])

                # Set the binding properties
                binding_schema = f"{self.GNOME_SCHEMA}.custom-keybinding:{custom_path}"
                name = f"LikX {hotkey_id.replace('-', ' ').title()}"

                subprocess.run(
                    ["gsettings", "set", binding_schema, "name", name]
                )
                subprocess.run(
                    ["gsettings", "set", binding_schema, "command", command]
                )
                subprocess.run(
                    ["gsettings", "set", binding_schema, "binding", key_combo]
                )

                if custom_path not in self._registered_paths:
                    self._registered_paths.append(custom_path)

                return True
        except Exception as e:
            print(f"Failed to register GNOME hotkey '{hotkey_id}': {e}")

        return False

    def _register_kde_hotkey(
        self, key_combo: str, command: str, hotkey_id: str
    ) -> bool:
        """Register hotkey in KDE."""
        # KDE uses kglobalaccel, more complex to implement
        # Would require D-Bus integration
        return False

    def update_hotkey(self, hotkey_id: str, key_combo: str) -> bool:
        """Update an existing hotkey binding without re-registering command.

        Args:
            hotkey_id: The hotkey identifier (e.g., 'fullscreen', 'region')
            key_combo: New key combination

        Returns:
            True if update successful
        """
        if self.desktop_env == "gnome":
            try:
                custom_path = f"{self.GNOME_BASE_PATH}/likx-{hotkey_id}/"
                binding_schema = f"{self.GNOME_SCHEMA}.custom-keybinding:{custom_path}"

                result = subprocess.run(
                    ["gsettings", "set", binding_schema, "binding", key_combo],
                    capture_output=True,
                )
                return result.returncode == 0
            except Exception as e:
                print(f"Failed to update hotkey '{hotkey_id}': {e}")
                return False
        return False

    def unregister_all(self) -> None:
        """Unregister all LikX hotkeys."""
        if self.desktop_env == "gnome":
            try:
                # Get current custom keybindings
                result = subprocess.run(
                    ["gsettings", "get", self.GNOME_SCHEMA, "custom-keybindings"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    current = result.stdout.strip()

                    # Remove all likx- paths
                    for path in self._registered_paths:
                        current = current.replace(f"'{path}', ", "")
                        current = current.replace(f", '{path}'", "")
                        current = current.replace(f"'{path}'", "")

                    # Clean up empty array or malformed result
                    if current in ("[]", "[@as ]", ""):
                        current = "@as []"

                    subprocess.run([
                        "gsettings", "set", self.GNOME_SCHEMA,
                        "custom-keybindings", current
                    ])

                self._registered_paths.clear()
                self.hotkeys.clear()

            except Exception as e:
                print(f"Failed to unregister hotkeys: {e}")
