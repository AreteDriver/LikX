"""Tests for uploader module."""

import sys
import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.uploader import Uploader


class TestUploaderInit:
    """Test Uploader initialization."""

    def test_uploader_init(self):
        uploader = Uploader()
        assert uploader is not None

    def test_uploader_has_client_id(self):
        uploader = Uploader()
        assert hasattr(uploader, "imgur_client_id")
        assert uploader.imgur_client_id is not None


class TestUploadToImgur:
    """Test Imgur upload functionality."""

    @patch("src.uploader.subprocess.run")
    def test_upload_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": True,
                "data": {"link": "https://i.imgur.com/abc123.png"}
            })
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is True
        assert url == "https://i.imgur.com/abc123.png"
        assert error is None

    @patch("src.uploader.subprocess.run")
    def test_upload_api_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": False,
                "data": {"error": "Rate limit exceeded"}
            })
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is False
        assert url is None
        assert error is not None

    @patch("src.uploader.subprocess.run")
    def test_upload_curl_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Connection refused"
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is False
        assert url is None
        assert error is not None

    def test_upload_file_not_found(self):
        uploader = Uploader()

        # Use actual non-existent path - will trigger FileNotFoundError on open
        success, url, error = uploader.upload_to_imgur(Path("/nonexistent/image.png"))

        assert success is False
        assert error is not None

    @patch("src.uploader.subprocess.run")
    def test_upload_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=30)

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is False
        assert "timed out" in error.lower()

    @patch("src.uploader.subprocess.run")
    def test_upload_curl_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is False
        assert "curl" in error.lower()

    @patch("src.uploader.subprocess.run")
    def test_upload_invalid_json_response(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json"
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"fake_image_data")):
            success, url, error = uploader.upload_to_imgur(Path("/path/to/image.png"))

        assert success is False
        assert error is not None


class TestUploadToFileIo:
    """Test file.io upload functionality."""

    @patch("src.uploader.subprocess.run")
    def test_upload_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": True,
                "link": "https://file.io/abc123"
            })
        )

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is True
        assert url == "https://file.io/abc123"
        assert error is None

    @patch("src.uploader.subprocess.run")
    def test_upload_api_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": False,
                "error": "File too large"
            })
        )

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is False
        assert url is None
        assert error is not None

    @patch("src.uploader.subprocess.run")
    def test_upload_curl_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Connection refused"
        )

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is False
        assert url is None

    @patch("src.uploader.subprocess.run")
    def test_upload_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="curl", timeout=30)

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is False
        assert "timed out" in error.lower()

    @patch("src.uploader.subprocess.run")
    def test_upload_curl_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is False
        assert "curl" in error.lower()

    @patch("src.uploader.subprocess.run")
    def test_upload_exception(self, mock_run):
        mock_run.side_effect = Exception("Unexpected error")

        uploader = Uploader()
        success, url, error = uploader.upload_to_file_io(Path("/path/to/image.png"))

        assert success is False
        assert error is not None


class TestCopyUrlToClipboard:
    """Test clipboard copy functionality."""

    @patch("src.uploader.subprocess.run")
    def test_copy_with_xclip_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        uploader = Uploader()
        result = uploader.copy_url_to_clipboard("https://example.com/image.png")

        assert result is True
        mock_run.assert_called_once()

    @patch("src.uploader.subprocess.run")
    def test_copy_xclip_not_found_falls_back_to_xsel(self, mock_run):
        mock_run.side_effect = [
            FileNotFoundError(),  # xclip not found
            MagicMock(returncode=0),  # xsel succeeds
        ]

        uploader = Uploader()
        result = uploader.copy_url_to_clipboard("https://example.com/image.png")

        assert result is True
        assert mock_run.call_count == 2

    @patch("src.uploader.subprocess.run")
    def test_copy_both_fail(self, mock_run):
        mock_run.side_effect = [
            FileNotFoundError(),  # xclip not found
            FileNotFoundError(),  # xsel not found
        ]

        uploader = Uploader()
        result = uploader.copy_url_to_clipboard("https://example.com/image.png")

        assert result is False

    @patch("src.uploader.subprocess.run")
    def test_copy_xclip_error(self, mock_run):
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "xclip"),
            FileNotFoundError(),  # xsel not found
        ]

        uploader = Uploader()
        result = uploader.copy_url_to_clipboard("https://example.com/image.png")

        assert result is False

    @patch("src.uploader.subprocess.run")
    def test_copy_xsel_error(self, mock_run):
        mock_run.side_effect = [
            FileNotFoundError(),  # xclip not found
            subprocess.CalledProcessError(1, "xsel"),  # xsel fails
        ]

        uploader = Uploader()
        result = uploader.copy_url_to_clipboard("https://example.com/image.png")

        assert result is False


class TestUnifiedUpload:
    """Test unified upload() method routing."""

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_routes_to_imgur(self, mock_run, mock_config):
        mock_config.return_value = {"upload_service": "imgur"}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": True,
                "data": {"link": "https://i.imgur.com/abc.png"}
            })
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"data")):
            success, url, error = uploader.upload(Path("/path/to/image.png"))

        assert success is True
        assert "imgur" in url

    @patch("src.uploader.config.load_config")
    def test_upload_disabled(self, mock_config):
        mock_config.return_value = {"upload_service": "none"}

        uploader = Uploader()
        success, url, error = uploader.upload(Path("/path/to/image.png"))

        assert success is False
        assert "disabled" in error.lower()

    @patch("src.uploader.config.load_config")
    def test_upload_unknown_service(self, mock_config):
        mock_config.return_value = {"upload_service": "unknown_provider"}

        uploader = Uploader()
        success, url, error = uploader.upload(Path("/path/to/image.png"))

        assert success is False
        assert "unknown" in error.lower()


class TestUploadToS3:
    """Test S3 upload functionality."""

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_success(self, mock_run, mock_config):
        mock_config.return_value = {
            "s3_bucket": "my-bucket",
            "s3_region": "us-west-2",
            "s3_public": True
        }
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        uploader = Uploader()
        success, url, error = uploader.upload_to_s3(Path("/path/to/image.png"))

        assert success is True
        assert "my-bucket" in url
        assert "us-west-2" in url
        assert "image.png" in url

    @patch("src.uploader.config.load_config")
    def test_upload_no_bucket_configured(self, mock_config):
        mock_config.return_value = {"s3_bucket": "", "s3_region": "us-east-1"}

        uploader = Uploader()
        success, url, error = uploader.upload_to_s3(Path("/path/to/image.png"))

        assert success is False
        assert "bucket" in error.lower()

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_aws_cli_not_found(self, mock_run, mock_config):
        mock_config.return_value = {
            "s3_bucket": "my-bucket",
            "s3_region": "us-east-1",
            "s3_public": True
        }
        mock_run.side_effect = FileNotFoundError()

        uploader = Uploader()
        success, url, error = uploader.upload_to_s3(Path("/path/to/image.png"))

        assert success is False
        assert "aws" in error.lower()

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_failure(self, mock_run, mock_config):
        mock_config.return_value = {
            "s3_bucket": "my-bucket",
            "s3_region": "us-east-1",
            "s3_public": True
        }
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Access Denied"
        )

        uploader = Uploader()
        success, url, error = uploader.upload_to_s3(Path("/path/to/image.png"))

        assert success is False
        assert "Access Denied" in error


class TestUploadToDropbox:
    """Test Dropbox upload functionality."""

    @patch("src.uploader.config.load_config")
    def test_upload_no_token(self, mock_config):
        mock_config.return_value = {"dropbox_token": ""}

        uploader = Uploader()
        success, url, error = uploader.upload_to_dropbox(Path("/path/to/image.png"))

        assert success is False
        assert "token" in error.lower()

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_success_with_share_link(self, mock_run, mock_config):
        mock_config.return_value = {"dropbox_token": "sl.test-token"}

        # First call: upload, Second call: create share link
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout=json.dumps({"path_display": "/Screenshots/image.png"})),
            MagicMock(returncode=0, stdout=json.dumps({"url": "https://www.dropbox.com/s/abc/image.png?dl=0"}))
        ]

        uploader = Uploader()
        success, url, error = uploader.upload_to_dropbox(Path("/path/to/image.png"))

        assert success is True
        assert "dropbox" in url.lower()
        assert "dl=1" in url  # Should be direct download link

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_curl_not_found(self, mock_run, mock_config):
        mock_config.return_value = {"dropbox_token": "sl.test-token"}
        mock_run.side_effect = FileNotFoundError()

        uploader = Uploader()
        success, url, error = uploader.upload_to_dropbox(Path("/path/to/image.png"))

        assert success is False
        assert "curl" in error.lower()


class TestUploadToGdrive:
    """Test Google Drive upload functionality."""

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_with_gdrive_success(self, mock_run, mock_config):
        mock_config.return_value = {"gdrive_folder_id": ""}
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Uploaded image.png with id abc123xyz"
        )

        uploader = Uploader()
        success, url, error = uploader.upload_to_gdrive(Path("/path/to/image.png"))

        assert success is True
        assert "abc123xyz" in url or "Google Drive" in url

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_gdrive_not_found_tries_rclone(self, mock_run, mock_config):
        mock_config.return_value = {"gdrive_folder_id": "", "gdrive_rclone_remote": "gdrive"}

        # First call: gdrive not found, Second call: rclone succeeds
        mock_run.side_effect = [
            FileNotFoundError(),  # gdrive not found
            MagicMock(returncode=0, stdout=""),  # rclone copy
            MagicMock(returncode=0, stdout="https://drive.google.com/file/d/xyz")  # rclone link
        ]

        uploader = Uploader()
        success, url, error = uploader.upload_to_gdrive(Path("/path/to/image.png"))

        assert success is True

    @patch("src.uploader.config.load_config")
    @patch("src.uploader.subprocess.run")
    def test_upload_all_tools_not_found(self, mock_run, mock_config):
        mock_config.return_value = {"gdrive_folder_id": "", "gdrive_rclone_remote": "gdrive"}

        mock_run.side_effect = FileNotFoundError()

        uploader = Uploader()
        success, url, error = uploader.upload_to_gdrive(Path("/path/to/image.png"))

        assert success is False
        assert "gdrive" in error.lower() or "rclone" in error.lower()


class TestUploaderEdgeCases:
    """Test edge cases and error handling."""

    @patch("src.uploader.subprocess.run")
    def test_upload_special_characters_in_path(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "success": True,
                "data": {"link": "https://i.imgur.com/abc.png"}
            })
        )

        uploader = Uploader()
        with patch("builtins.open", mock_open(read_data=b"data")):
            success, url, error = uploader.upload_to_imgur(
                Path("/path with spaces/image.png")
            )

        # Should handle spaces in path
        assert mock_run.called

    @patch("src.uploader.subprocess.run")
    def test_clipboard_with_long_url(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        uploader = Uploader()
        long_url = "https://example.com/" + "a" * 1000
        result = uploader.copy_url_to_clipboard(long_url)

        assert result is True
