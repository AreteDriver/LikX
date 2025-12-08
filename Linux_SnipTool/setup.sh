#!/bin/bash
# Linux SnipTool 2.0 - Enhanced Setup Script
# Supports X11 and Wayland installations

set -e

echo "======================================"
echo "  Linux SnipTool 2.0 - Setup Script"
echo "======================================"
echo

# Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

# Detect display server
detect_display_server() {
    if [ -n "$WAYLAND_DISPLAY" ]; then
        echo "wayland"
    elif [ -n "$DISPLAY" ]; then
        echo "x11"
    else
        echo "unknown"
    fi
}

PKG_MANAGER=$(detect_package_manager)
DISPLAY_SERVER=$(detect_display_server)

echo "Detected package manager: $PKG_MANAGER"
echo "Detected display server: $DISPLAY_SERVER"
echo

# Install dependencies
install_dependencies() {
    case $PKG_MANAGER in
        apt)
            echo "Installing dependencies using apt..."
            sudo apt-get update
            
            # Core dependencies
            sudo apt-get install -y \
                python3 \
                python3-pip \
                python3-gi \
                python3-gi-cairo \
                gir1.2-gtk-3.0 \
                gir1.2-gdk-3.0 \
                gir1.2-gdkpixbuf-2.0 \
                gir1.2-notify-0.7 \
                libcairo2-dev \
                libgirepository1.0-dev \
                curl
            
            # X11 specific
            if [ "$DISPLAY_SERVER" = "x11" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo apt-get install -y xdotool xclip
            fi
            
            # Wayland specific
            if [ "$DISPLAY_SERVER" = "wayland" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo apt-get install -y gnome-screenshot
                # Try to install grim if available (for wlroots)
                sudo apt-get install -y grim 2>/dev/null || true
            fi
            ;;
            
        dnf|yum)
            echo "Installing dependencies using $PKG_MANAGER..."
            
            sudo $PKG_MANAGER install -y \
                python3 \
                python3-pip \
                python3-gobject \
                gtk3 \
                cairo-gobject \
                gobject-introspection \
                libnotify \
                curl
            
            if [ "$DISPLAY_SERVER" = "x11" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo $PKG_MANAGER install -y xdotool xclip
            fi
            
            if [ "$DISPLAY_SERVER" = "wayland" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo $PKG_MANAGER install -y gnome-screenshot grim
            fi
            ;;
            
        pacman)
            echo "Installing dependencies using pacman..."
            
            sudo pacman -Syu --noconfirm \
                python \
                python-pip \
                python-gobject \
                gtk3 \
                cairo \
                gobject-introspection \
                libnotify \
                curl
            
            if [ "$DISPLAY_SERVER" = "x11" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo pacman -S --noconfirm xdotool xclip
            fi
            
            if [ "$DISPLAY_SERVER" = "wayland" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo pacman -S --noconfirm gnome-screenshot grim
            fi
            ;;
            
        zypper)
            echo "Installing dependencies using zypper..."
            
            sudo zypper install -y \
                python3 \
                python3-pip \
                python3-gobject \
                python3-gobject-Gdk \
                gtk3 \
                cairo \
                typelib-1_0-Gtk-3_0 \
                libnotify \
                curl
            
            if [ "$DISPLAY_SERVER" = "x11" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo zypper install -y xdotool xclip
            fi
            
            if [ "$DISPLAY_SERVER" = "wayland" ] || [ "$DISPLAY_SERVER" = "unknown" ]; then
                sudo zypper install -y gnome-screenshot
            fi
            ;;
            
        *)
            echo "Error: Unknown package manager."
            echo "Please install dependencies manually."
            echo
            echo "Required:"
            echo "  - Python 3.8+"
            echo "  - PyGObject (python3-gi)"
            echo "  - GTK 3.0"
            echo "  - Cairo"
            echo "  - libnotify"
            echo "  - curl"
            echo
            echo "For X11:"
            echo "  - xdotool"
            echo "  - xclip"
            echo
            echo "For Wayland:"
            echo "  - gnome-screenshot or grim"
            exit 1
            ;;
    esac
}

# Install Python dependencies
install_python_deps() {
    echo
    echo "Installing Python dependencies..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        echo "Warning: pip not found. Skipping Python package installation."
        return
    fi
    
    # Install pycairo if needed
    if ! python3 -c "import cairo" 2>/dev/null; then
        $PIP_CMD install --user pycairo
    fi
}

# Setup configuration
setup_config() {
    echo
    echo "Setting up configuration directory..."
    
    CONFIG_DIR="$HOME/.config/linux-sniptool"
    mkdir -p "$CONFIG_DIR"
    
    SCREENSHOTS_DIR="$HOME/Pictures/Screenshots"
    mkdir -p "$SCREENSHOTS_DIR"
    
    echo "Configuration directory: $CONFIG_DIR"
    echo "Screenshots directory: $SCREENSHOTS_DIR"
}

# Create desktop entry
create_desktop_entry() {
    echo
    echo "Creating desktop entry..."
    
    DESKTOP_DIR="$HOME/.local/share/applications"
    mkdir -p "$DESKTOP_DIR"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ICON_PATH="$SCRIPT_DIR/resources/icons/app_icon.svg"
    
    cat > "$DESKTOP_DIR/linux-sniptool.desktop" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Linux SnipTool
GenericName=Screenshot Tool
Comment=Capture and annotate screenshots with Wayland support
Exec=python3 $SCRIPT_DIR/main.py
Icon=$ICON_PATH
Terminal=false
Categories=Graphics;Utility;
Keywords=screenshot;capture;snip;screen;annotation;wayland;
StartupNotify=true

Actions=fullscreen;region;window;

[Desktop Action fullscreen]
Name=Capture Fullscreen
Exec=python3 $SCRIPT_DIR/main.py --fullscreen

[Desktop Action region]
Name=Capture Region
Exec=python3 $SCRIPT_DIR/main.py --region

[Desktop Action window]
Name=Capture Window
Exec=python3 $SCRIPT_DIR/main.py --window
DESKTOP_EOF
    
    chmod +x "$DESKTOP_DIR/linux-sniptool.desktop"
    echo "Desktop entry created at: $DESKTOP_DIR/linux-sniptool.desktop"
}

# Make scripts executable
make_executable() {
    echo
    echo "Making scripts executable..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    chmod +x "$SCRIPT_DIR/main.py"
}

# Main installation
main() {
    echo "This script will install Linux SnipTool 2.0 and its dependencies."
    echo
    
    if [ "$EUID" -eq 0 ]; then
        echo "Warning: Running as root. Some user-specific configurations"
        echo "may not be set up correctly."
        echo
    fi
    
    # Install system dependencies
    install_dependencies
    
    # Install Python dependencies
    install_python_deps
    
    # Setup configuration
    setup_config
    
    # Create desktop entry
    create_desktop_entry
    
    # Make scripts executable
    make_executable
    
    echo
    echo "======================================"
    echo "  Installation Complete!"
    echo "======================================"
    echo
    echo "You can now run Linux SnipTool:"
    echo "  1. From terminal: python3 $(dirname "$0")/main.py"
    echo "  2. From application menu: Search for 'Linux SnipTool'"
    echo
    echo "Global keyboard shortcuts (GNOME):"
    echo "  Ctrl+Shift+F - Fullscreen capture"
    echo "  Ctrl+Shift+R - Region capture"
    echo "  Ctrl+Shift+W - Window capture"
    echo
    echo "Display server: $DISPLAY_SERVER"
    
    if [ "$DISPLAY_SERVER" = "wayland" ]; then
        echo
        echo "Note: Running on Wayland. Some features require:"
        echo "  - gnome-screenshot (for window capture)"
        echo "  - grim (for wlroots compositors)"
    fi
    
    echo
    echo "For more information, see README.md"
    echo
}

main
