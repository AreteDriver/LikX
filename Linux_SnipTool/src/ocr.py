"""OCR (Optical Character Recognition) module for Linux SnipTool."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

class OCREngine:
    """Handles text extraction from screenshots using Tesseract."""
    
    def __init__(self):
        self.available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is installed."""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def extract_text(self, pixbuf) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract text from a pixbuf.
        
        Args:
            pixbuf: GdkPixbuf containing the image
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        if not self.available:
            return False, None, "Tesseract not installed. Install with: sudo apt install tesseract-ocr"
        
        try:
            # Save pixbuf to temporary file
            temp_file = Path(tempfile.mktemp(suffix='.png'))
            pixbuf.savev(str(temp_file), 'png', [], [])
            
            # Run Tesseract
            result = subprocess.run(
                ['tesseract', str(temp_file), 'stdout'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
            
            if result.returncode == 0:
                text = result.stdout.strip()
                if text:
                    return True, text, None
                else:
                    return False, None, "No text found in image"
            else:
                return False, None, f"OCR failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, None, "OCR timed out"
        except Exception as e:
            return False, None, f"OCR error: {str(e)}"
    
    def copy_text_to_clipboard(self, text: str) -> bool:
        """Copy extracted text to clipboard."""
        try:
            subprocess.run(['xclip', '-selection', 'clipboard'],
                          input=text.encode(), check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        try:
            subprocess.run(['xsel', '--clipboard', '--input'],
                          input=text.encode(), check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        return False
