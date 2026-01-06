"""Tests for OCR module."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ocr import OCREngine


class TestOCREngineInit:
    """Test OCREngine initialization."""

    @patch("src.ocr.subprocess.run")
    def test_init_with_tesseract_available(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        engine = OCREngine()
        assert engine.available is True

    @patch("src.ocr.subprocess.run")
    def test_init_with_tesseract_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        engine = OCREngine()
        assert engine.available is False

    @patch("src.ocr.subprocess.run")
    def test_init_with_tesseract_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="tesseract", timeout=2)
        engine = OCREngine()
        assert engine.available is False

    @patch("src.ocr.subprocess.run")
    def test_init_with_tesseract_error(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        engine = OCREngine()
        assert engine.available is False


class TestOCREngineExtractText:
    """Test OCREngine text extraction."""

    @patch("src.ocr.subprocess.run")
    def test_extract_text_not_available(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        engine = OCREngine()

        success, text, error = engine.extract_text(MagicMock())
        assert success is False
        assert text is None
        assert "Tesseract not installed" in error

    @patch("src.ocr.subprocess.run")
    @patch("src.ocr.tempfile.mktemp")
    @patch("src.ocr.Path")
    def test_extract_text_success(self, mock_path, mock_mktemp, mock_run):
        # First call for version check succeeds
        # Second call for OCR returns text
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            MagicMock(returncode=0, stdout="Extracted text here", stderr=""),
        ]
        mock_mktemp.return_value = "/tmp/test.png"
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        engine = OCREngine()
        mock_pixbuf = MagicMock()

        success, text, error = engine.extract_text(mock_pixbuf)
        assert success is True
        assert text == "Extracted text here"
        assert error is None

    @patch("src.ocr.subprocess.run")
    @patch("src.ocr.tempfile.mktemp")
    @patch("src.ocr.Path")
    def test_extract_text_no_text_found(self, mock_path, mock_mktemp, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            MagicMock(returncode=0, stdout="", stderr=""),  # empty result
        ]
        mock_mktemp.return_value = "/tmp/test.png"
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        engine = OCREngine()
        mock_pixbuf = MagicMock()

        success, text, error = engine.extract_text(mock_pixbuf)
        assert success is False
        assert text is None
        assert "No text found" in error

    @patch("src.ocr.subprocess.run")
    @patch("src.ocr.tempfile.mktemp")
    @patch("src.ocr.Path")
    def test_extract_text_ocr_failed(self, mock_path, mock_mktemp, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            MagicMock(returncode=1, stdout="", stderr="Error message"),
        ]
        mock_mktemp.return_value = "/tmp/test.png"
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        engine = OCREngine()
        mock_pixbuf = MagicMock()

        success, text, error = engine.extract_text(mock_pixbuf)
        assert success is False
        assert text is None
        assert "OCR failed" in error

    @patch("src.ocr.subprocess.run")
    @patch("src.ocr.tempfile.mktemp")
    @patch("src.ocr.Path")
    def test_extract_text_timeout(self, mock_path, mock_mktemp, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            subprocess.TimeoutExpired(cmd="tesseract", timeout=30),
        ]
        mock_mktemp.return_value = "/tmp/test.png"
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path.return_value = mock_path_instance

        engine = OCREngine()
        mock_pixbuf = MagicMock()

        success, text, error = engine.extract_text(mock_pixbuf)
        assert success is False
        assert text is None
        assert "timed out" in error

    @patch("src.ocr.subprocess.run")
    @patch("src.ocr.tempfile.mktemp")
    def test_extract_text_exception(self, mock_mktemp, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            Exception("Unexpected error"),
        ]
        mock_mktemp.return_value = "/tmp/test.png"

        engine = OCREngine()
        mock_pixbuf = MagicMock()

        success, text, error = engine.extract_text(mock_pixbuf)
        assert success is False
        assert text is None
        assert "OCR error" in error


class TestOCREngineCopyToClipboard:
    """Test OCREngine clipboard copy."""

    @patch("src.ocr.subprocess.run")
    def test_copy_with_xclip_success(self, mock_run):
        # First for version check, second for xclip
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            MagicMock(returncode=0),  # xclip
        ]

        engine = OCREngine()
        result = engine.copy_text_to_clipboard("test text")
        assert result is True

    @patch("src.ocr.subprocess.run")
    def test_copy_with_xsel_fallback(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            FileNotFoundError(),  # xclip not found
            MagicMock(returncode=0),  # xsel works
        ]

        engine = OCREngine()
        result = engine.copy_text_to_clipboard("test text")
        assert result is True

    @patch("src.ocr.subprocess.run")
    def test_copy_both_fail(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            FileNotFoundError(),  # xclip not found
            FileNotFoundError(),  # xsel not found
        ]

        engine = OCREngine()
        result = engine.copy_text_to_clipboard("test text")
        assert result is False

    @patch("src.ocr.subprocess.run")
    def test_copy_xclip_timeout(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            subprocess.TimeoutExpired(cmd="xclip", timeout=2),
            FileNotFoundError(),  # xsel not found
        ]

        engine = OCREngine()
        result = engine.copy_text_to_clipboard("test text")
        assert result is False

    @patch("src.ocr.subprocess.run")
    def test_copy_xclip_error(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0),  # tesseract --version
            subprocess.CalledProcessError(1, "xclip"),
            FileNotFoundError(),  # xsel not found
        ]

        engine = OCREngine()
        result = engine.copy_text_to_clipboard("test text")
        assert result is False
