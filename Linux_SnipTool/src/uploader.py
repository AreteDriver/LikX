"""Cloud upload functionality for Linux SnipTool."""

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

class Uploader:
    """Handles uploading screenshots to cloud services."""
    
    def __init__(self):
        self.imgur_client_id = "546c25a59c58ad7"  # Anonymous Imgur uploads
    
    def upload_to_imgur(self, filepath: Path) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image to Imgur.
        
        Args:
            filepath: Path to image file
            
        Returns:
            Tuple of (success, url, error_message)
        """
        try:
            import base64
            
            # Read image and encode
            with open(filepath, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Use curl to upload
            result = subprocess.run([
                'curl', '-X', 'POST',
                '-H', f'Authorization: Client-ID {self.imgur_client_id}',
                '-F', f'image={image_data}',
                'https://api.imgur.com/3/image'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get('success'):
                    url = response['data']['link']
                    return True, url, None
                else:
                    return False, None, "Imgur API returned error"
            else:
                return False, None, "Upload request failed"
                
        except subprocess.TimeoutExpired:
            return False, None, "Upload timed out"
        except FileNotFoundError:
            return False, None, "curl not installed"
        except Exception as e:
            return False, None, str(e)
    
    def upload_to_file_io(self, filepath: Path) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload to file.io (temporary file sharing).
        
        Args:
            filepath: Path to image file
            
        Returns:
            Tuple of (success, url, error_message)
        """
        try:
            result = subprocess.run([
                'curl', '-F', f'file=@{filepath}',
                'https://file.io'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get('success'):
                    url = response['link']
                    return True, url, None
                else:
                    return False, None, "file.io returned error"
            else:
                return False, None, "Upload failed"
                
        except subprocess.TimeoutExpired:
            return False, None, "Upload timed out"
        except FileNotFoundError:
            return False, None, "curl not installed"
        except Exception as e:
            return False, None, str(e)
    
    def copy_url_to_clipboard(self, url: str) -> bool:
        """Copy URL to clipboard.
        
        Args:
            url: URL to copy
            
        Returns:
            True if successful
        """
        try:
            # Try xclip first
            subprocess.run(['xclip', '-selection', 'clipboard'],
                          input=url.encode(), check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        try:
            # Try xsel
            subprocess.run(['xsel', '--clipboard', '--input'],
                          input=url.encode(), check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
        
        return False
