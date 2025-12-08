"""Desktop notification support for Linux SnipTool."""

import subprocess

def show_notification(title: str, message: str, icon: str = "camera-photo", 
                     urgency: str = "normal", timeout: int = 5000) -> bool:
    """Show a desktop notification.
    
    Args:
        title: Notification title
        message: Notification message
        icon: Icon name or path
        urgency: Urgency level (low, normal, critical)
        timeout: Timeout in milliseconds
        
    Returns:
        True if notification was shown successfully
    """
    try:
        # Try using GI Notify first (native)
        import gi
        gi.require_version('Notify', '0.7')
        from gi.repository import Notify
        
        Notify.init("Linux SnipTool")
        notification = Notify.Notification.new(title, message, icon)
        notification.set_timeout(timeout)
        notification.show()
        return True
    except:
        pass
    
    # Fallback to notify-send
    try:
        subprocess.run([
            'notify-send',
            '-u', urgency,
            '-i', icon,
            '-t', str(timeout),
            title,
            message
        ], check=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    
    return False


def show_screenshot_saved(filepath: str) -> None:
    """Show notification that screenshot was saved."""
    show_notification(
        "Screenshot Saved",
        f"Saved to {filepath}",
        icon="document-save"
    )


def show_screenshot_copied() -> None:
    """Show notification that screenshot was copied to clipboard."""
    show_notification(
        "Screenshot Copied",
        "Screenshot copied to clipboard",
        icon="edit-copy"
    )


def show_upload_success(url: str) -> None:
    """Show notification that upload succeeded."""
    show_notification(
        "Upload Successful",
        f"URL copied to clipboard: {url}",
        icon="emblem-web",
        timeout=10000
    )


def show_upload_error(error: str) -> None:
    """Show notification that upload failed."""
    show_notification(
        "Upload Failed",
        error,
        icon="dialog-error",
        urgency="critical"
    )
