"""Cloud upload functionality for LikX."""

import json
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from . import config


class Uploader:
    """Handles uploading screenshots to cloud services."""

    def __init__(self):
        self.imgur_client_id = "546c25a59c58ad7"  # Anonymous Imgur uploads

    def upload(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image using configured service.

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        cfg = config.load_config()
        service = cfg.get("upload_service", "imgur")

        if service == "imgur":
            return self.upload_to_imgur(filepath)
        elif service == "fileio":
            return self.upload_to_file_io(filepath)
        elif service == "s3":
            return self.upload_to_s3(filepath)
        elif service == "dropbox":
            return self.upload_to_dropbox(filepath)
        elif service == "gdrive":
            return self.upload_to_gdrive(filepath)
        elif service == "none":
            return False, None, "Upload disabled"
        else:
            return False, None, f"Unknown upload service: {service}"

    def upload_to_imgur(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image to Imgur.

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        try:
            import base64

            # Read image and encode
            with open(filepath, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Use curl to upload
            result = subprocess.run(
                [
                    "curl",
                    "-X",
                    "POST",
                    "-H",
                    f"Authorization: Client-ID {self.imgur_client_id}",
                    "-F",
                    f"image={image_data}",
                    "https://api.imgur.com/3/image",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get("success"):
                    url = response["data"]["link"]
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

    def upload_to_file_io(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload to file.io (temporary file sharing).

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        try:
            result = subprocess.run(
                ["curl", "-F", f"file=@{filepath}", "https://file.io"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                response = json.loads(result.stdout)
                if response.get("success"):
                    url = response["link"]
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

    def upload_to_s3(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image to AWS S3.

        Requires AWS CLI configured or environment variables:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - S3 bucket configured in LikX settings

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        cfg = config.load_config()
        bucket = cfg.get("s3_bucket", "")
        region = cfg.get("s3_region", "us-east-1")
        make_public = cfg.get("s3_public", True)

        if not bucket:
            return False, None, "S3 bucket not configured in settings"

        try:
            # Build S3 key (filename in bucket)
            s3_key = f"screenshots/{filepath.name}"

            # Build aws s3 cp command
            cmd = [
                "aws", "s3", "cp",
                str(filepath),
                f"s3://{bucket}/{s3_key}",
                "--region", region,
            ]

            if make_public:
                cmd.extend(["--acl", "public-read"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Construct public URL
                if make_public:
                    url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
                else:
                    url = f"s3://{bucket}/{s3_key}"
                return True, url, None
            else:
                error = result.stderr.strip() or "Upload failed"
                return False, None, error

        except subprocess.TimeoutExpired:
            return False, None, "Upload timed out"
        except FileNotFoundError:
            return False, None, "AWS CLI not installed. Install with: pip install awscli"
        except Exception as e:
            return False, None, str(e)

    def upload_to_dropbox(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image to Dropbox.

        Requires Dropbox access token configured in LikX settings.
        Get token from: https://www.dropbox.com/developers/apps

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        cfg = config.load_config()
        access_token = cfg.get("dropbox_token", "")

        if not access_token:
            return (
                False,
                None,
                "Dropbox access token not configured. "
                "Get one from https://www.dropbox.com/developers/apps",
            )

        try:
            dropbox_path = f"/Screenshots/{filepath.name}"

            # Upload file using Dropbox API
            result = subprocess.run(
                [
                    "curl", "-X", "POST",
                    "https://content.dropboxapi.com/2/files/upload",
                    "-H", f"Authorization: Bearer {access_token}",
                    "-H", "Content-Type: application/octet-stream",
                    "-H", f'Dropbox-API-Arg: {{"path": "{dropbox_path}", "mode": "add"}}',
                    "--data-binary", f"@{filepath}",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return False, None, "Dropbox upload request failed"

            response = json.loads(result.stdout)

            if "error" in response:
                error_msg = response.get("error_summary", "Upload failed")
                return False, None, error_msg

            # Create shared link
            share_result = subprocess.run(
                [
                    "curl", "-X", "POST",
                    "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
                    "-H", f"Authorization: Bearer {access_token}",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps({"path": dropbox_path}),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if share_result.returncode == 0:
                share_response = json.loads(share_result.stdout)
                if "url" in share_response:
                    # Convert to direct link
                    url = share_response["url"].replace("dl=0", "dl=1")
                    return True, url, None
                elif "error" in share_response:
                    # Link may already exist, try to get existing
                    if "shared_link_already_exists" in str(share_response):
                        existing = share_response.get("error", {}).get(
                            "shared_link_already_exists", {}
                        ).get("metadata", {}).get("url", "")
                        if existing:
                            return True, existing.replace("dl=0", "dl=1"), None

            # Fallback: file uploaded but couldn't create share link
            return True, f"Uploaded to Dropbox: {dropbox_path}", None

        except subprocess.TimeoutExpired:
            return False, None, "Upload timed out"
        except FileNotFoundError:
            return False, None, "curl not installed"
        except json.JSONDecodeError:
            return False, None, "Invalid response from Dropbox"
        except Exception as e:
            return False, None, str(e)

    def upload_to_gdrive(
        self, filepath: Path
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload image to Google Drive.

        Requires gdrive CLI tool or rclone configured.
        Install gdrive: https://github.com/glotlabs/gdrive

        Args:
            filepath: Path to image file

        Returns:
            Tuple of (success, url, error_message)
        """
        cfg = config.load_config()
        folder_id = cfg.get("gdrive_folder_id", "")

        # Try gdrive CLI first
        try:
            cmd = ["gdrive", "files", "upload", str(filepath)]
            if folder_id:
                cmd.extend(["--parent", folder_id])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Parse output for file ID
                # gdrive output: "Uploaded <filename> with id <id>"
                output = result.stdout
                if "id" in output.lower():
                    # Extract file ID from output
                    parts = output.split()
                    for i, part in enumerate(parts):
                        if part.lower() == "id" and i + 1 < len(parts):
                            file_id = parts[i + 1].strip()
                            url = f"https://drive.google.com/file/d/{file_id}/view"
                            return True, url, None

                # Fallback if can't parse ID
                return True, "Uploaded to Google Drive", None
            else:
                error = result.stderr.strip() or "Upload failed"
                if "not found" in error.lower() or result.returncode == 127:
                    raise FileNotFoundError("gdrive not found")
                return False, None, error

        except FileNotFoundError:
            pass  # Try rclone next

        # Try rclone as fallback
        try:
            remote = cfg.get("gdrive_rclone_remote", "gdrive")
            remote_path = f"{remote}:Screenshots/{filepath.name}"

            result = subprocess.run(
                ["rclone", "copyto", str(filepath), remote_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Get shareable link
                link_result = subprocess.run(
                    ["rclone", "link", remote_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if link_result.returncode == 0 and link_result.stdout.strip():
                    return True, link_result.stdout.strip(), None
                return True, f"Uploaded to {remote_path}", None
            else:
                error = result.stderr.strip() or "Upload failed"
                return False, None, error

        except FileNotFoundError:
            return (
                False,
                None,
                "Google Drive upload requires gdrive or rclone. "
                "Install gdrive: https://github.com/glotlabs/gdrive",
            )
        except subprocess.TimeoutExpired:
            return False, None, "Upload timed out"
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
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=url.encode(), check=True
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        try:
            # Try xsel
            subprocess.run(
                ["xsel", "--clipboard", "--input"], input=url.encode(), check=True
            )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        return False
