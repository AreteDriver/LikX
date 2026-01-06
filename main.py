#!/usr/bin/env python3
"""LikX - Enhanced screenshot capture and annotation tool for Linux.

Usage:
    likx [OPTIONS]

Options:
    --fullscreen    Capture the entire screen
    --region        Capture a selected region
    --window        Capture the active window
    --delay SECS    Wait SECS seconds before capturing
    --output FILE   Save to FILE instead of default location
    --no-edit       Skip the editor and save directly
    --help          Show this help message
    --version       Show version information
"""

import argparse
import sys
from pathlib import Path

from src import __version__
from src.config import load_config, get_save_path
from src.capture import CaptureMode, capture, save_capture
from src.notification import show_screenshot_saved, show_notification


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="likx",
        description="LikX - A screenshot capture and annotation tool with Wayland support"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"LikX {__version__}"
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--fullscreen", "-f",
        action="store_true",
        help="Capture the entire screen"
    )
    mode_group.add_argument(
        "--region", "-r",
        action="store_true",
        help="Capture a selected region"
    )
    mode_group.add_argument(
        "--window", "-w",
        action="store_true",
        help="Capture the active window"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=int,
        default=0,
        metavar="SECS",
        help="Wait SECS seconds before capturing"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="FILE",
        help="Save to FILE instead of default location"
    )
    
    parser.add_argument(
        "--no-edit",
        action="store_true",
        help="Skip the editor and save directly"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for LikX."""
    args = parse_args()
    
    # If no capture mode specified, launch GUI
    if not (args.fullscreen or args.region or args.window):
        try:
            from src.ui import run_app
            run_app()
        except Exception as e:
            print(f"Error launching GUI: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Determine capture mode
    if args.fullscreen:
        mode = CaptureMode.FULLSCREEN
    elif args.region:
        mode = CaptureMode.REGION
    elif args.window:
        mode = CaptureMode.WINDOW
    else:
        mode = CaptureMode.FULLSCREEN
    
    # Handle region capture
    if mode == CaptureMode.REGION:
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            
            from src.ui import RegionSelector
            
            region_result = [None]
            
            def on_region_selected(x, y, width, height):
                region_result[0] = (x, y, width, height)
                Gtk.main_quit()
            
            RegionSelector(on_region_selected)
            Gtk.main()
            
            if region_result[0] is None:
                print("Region selection cancelled", file=sys.stderr)
                sys.exit(1)
            
            result = capture(mode, delay=args.delay, region=region_result[0])
        except Exception as e:
            print(f"Error during region capture: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fullscreen or window capture
        result = capture(mode, delay=args.delay)
    
    if not result.success:
        print(f"Capture failed: {result.error}", file=sys.stderr)
        show_notification("Capture Failed", result.error, icon="dialog-error")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_save_path()
    
    # Either save directly or open editor
    if args.no_edit:
        result = save_capture(result, output_path)
        if result.success:
            print(f"Screenshot saved to: {result.filepath}")
            cfg = load_config()
            if cfg.get("show_notification", True):
                show_screenshot_saved(str(result.filepath))
        else:
            print(f"Failed to save: {result.error}", file=sys.stderr)
            sys.exit(1)
    else:
        # Open editor
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            
            from src.ui import EditorWindow
            
            EditorWindow(result)
            Gtk.main()
        except Exception as e:
            # If editor fails, save directly
            print(f"Editor failed: {e}", file=sys.stderr)
            result = save_capture(result, output_path)
            if result.success:
                print(f"Screenshot saved to: {result.filepath}")
                cfg = load_config()
                if cfg.get("show_notification", True):
                    show_screenshot_saved(str(result.filepath))
            else:
                print(f"Failed to save: {result.error}", file=sys.stderr)
                sys.exit(1)


if __name__ == "__main__":
    main()
