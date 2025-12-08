"""Global keyboard shortcuts for Linux SnipTool."""

import subprocess
import os
from typing import Callable, Dict, Optional

class HotkeyManager:
    """Manages global keyboard shortcuts."""
    
    def __init__(self):
        self.hotkeys: Dict[str, Callable] = {}
        self.desktop_env = self._detect_desktop_environment()
    
    def _detect_desktop_environment(self) -> str:
        """Detect the current desktop environment."""
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'gnome' in desktop:
            return 'gnome'
        elif 'kde' in desktop or 'plasma' in desktop:
            return 'kde'
        elif 'xfce' in desktop:
            return 'xfce'
        elif 'mate' in desktop:
            return 'mate'
        else:
            return 'unknown'
    
    def register_hotkey(self, key_combo: str, callback: Callable, command: str) -> bool:
        """Register a global hotkey.
        
        Args:
            key_combo: Key combination (e.g., '<Control><Shift>F')
            callback: Function to call when hotkey is pressed
            command: Command to execute
            
        Returns:
            True if registration successful
        """
        self.hotkeys[key_combo] = callback
        
        if self.desktop_env == 'gnome':
            return self._register_gnome_hotkey(key_combo, command)
        elif self.desktop_env == 'kde':
            return self._register_kde_hotkey(key_combo, command)
        
        return False
    
    def _register_gnome_hotkey(self, key_combo: str, command: str) -> bool:
        """Register hotkey in GNOME."""
        try:
            # Create custom keybinding
            schema = 'org.gnome.settings-daemon.plugins.media-keys'
            custom_path = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/sniptool/'
            
            # Get current custom keybindings
            result = subprocess.run(
                ['gsettings', 'get', schema, 'custom-keybindings'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                current = result.stdout.strip()
                if custom_path not in current:
                    # Add our custom path
                    if current == '@as []':
                        new_value = f"['{custom_path}']"
                    else:
                        # Parse existing and add
                        new_value = current.rstrip(']') + f", '{custom_path}']"
                    
                    subprocess.run([
                        'gsettings', 'set', schema, 'custom-keybindings', new_value
                    ])
                
                # Set the binding
                subprocess.run([
                    'gsettings', 'set',
                    f'{schema}.custom-keybinding:{custom_path}',
                    'name', 'Linux SnipTool'
                ])
                subprocess.run([
                    'gsettings', 'set',
                    f'{schema}.custom-keybinding:{custom_path}',
                    'command', command
                ])
                subprocess.run([
                    'gsettings', 'set',
                    f'{schema}.custom-keybinding:{custom_path}',
                    'binding', key_combo
                ])
                
                return True
        except Exception as e:
            print(f"Failed to register GNOME hotkey: {e}")
        
        return False
    
    def _register_kde_hotkey(self, key_combo: str, command: str) -> bool:
        """Register hotkey in KDE."""
        # KDE uses kglobalaccel, more complex to implement
        # Would require D-Bus integration
        return False
    
    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        if self.desktop_env == 'gnome':
            try:
                schema = 'org.gnome.settings-daemon.plugins.media-keys'
                custom_path = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/sniptool/'
                
                # Remove from custom keybindings list
                result = subprocess.run(
                    ['gsettings', 'get', schema, 'custom-keybindings'],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    current = result.stdout.strip()
                    if custom_path in current:
                        # Remove our path
                        new_value = current.replace(f"'{custom_path}', ", "").replace(f", '{custom_path}'", "")
                        subprocess.run([
                            'gsettings', 'set', schema, 'custom-keybindings', new_value
                        ])
            except Exception as e:
                print(f"Failed to unregister hotkeys: {e}")
