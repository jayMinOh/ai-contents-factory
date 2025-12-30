"""
Tencent COS Cloud Storage Service

Handles file uploads to Tencent Cloud Object Storage.
Falls back to local storage if COS is not configured.
"""

import os
import logging
from typing import Optional
from qcloud_cos import CosConfig, CosS3Client

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudStorageService:
    """Service for uploading files to Tencent COS or local storage."""

    def __init__(self):
        self._cos_client: Optional[CosS3Client] = None
        self._bucket: Optional[str] = None
        self._region: Optional[str] = None
        self._initialized = False

    def _init_cos(self) -> bool:
        """Initialize COS client if credentials are available."""
        if self._initialized:
            return self._cos_client is not None

        self._initialized = True

        if not all([
            settings.TENCENT_SECRET_ID,
            settings.TENCENT_SECRET_KEY,
            settings.TENCENT_COS_BUCKET,
            settings.TENCENT_COS_REGION,
        ]):
            logger.warning("Tencent COS not configured, using local storage")
            return False

        try:
            config = CosConfig(
                Region=settings.TENCENT_COS_REGION,
                SecretId=settings.TENCENT_SECRET_ID,
                SecretKey=settings.TENCENT_SECRET_KEY,
                Scheme="https",
            )
            self._cos_client = CosS3Client(config)
            self._bucket = settings.TENCENT_COS_BUCKET
            self._region = settings.TENCENT_COS_REGION
            logger.info(f"Tencent COS initialized: bucket={self._bucket}, region={self._region}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Tencent COS: {e}")
            return False

    def _get_cos_url(self, key: str) -> str:
        """Get the public URL for a COS object."""
        return f"https://{self._bucket}.cos.{self._region}.myqcloud.com/{key}"

    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        folder: str = "temp",
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload bytes to cloud storage or local storage.

        Args:
            data: File content as bytes
            filename: Name of the file
            folder: Folder/prefix for the file (e.g., "temp", "products", "references")
            content_type: MIME type of the file

        Returns:
            URL to access the file (COS URL or local /static/ path)
        """
        if self._init_cos():
            return self._upload_to_cos(data, filename, folder, content_type)
        else:
            return self._save_locally(data, filename, folder)

    def _upload_to_cos(
        self,
        data: bytes,
        filename: str,
        folder: str,
        content_type: str,
    ) -> str:
        """Upload to Tencent COS."""
        key = f"{folder}/{filename}"

        try:
            from io import BytesIO
            file_obj = BytesIO(data)

            response = self._cos_client.put_object(
                Bucket=self._bucket,
                Body=file_obj,
                Key=key,
                ContentType=content_type,
            )

            url = self._get_cos_url(key)
            logger.info(f"Uploaded to COS: {key} -> {url}")
            return url

        except Exception as e:
            logger.error(f"Failed to upload to COS: {e}")
            return self._save_locally(data, filename, folder)

    def _save_locally(self, data: bytes, filename: str, folder: str) -> str:
        """Fallback: save to local storage."""
        local_dir = os.path.join(settings.TEMP_DIR, folder)
        os.makedirs(local_dir, exist_ok=True)

        local_path = os.path.join(local_dir, filename)
        with open(local_path, "wb") as f:
            f.write(data)

        url = f"/static/{folder}/{filename}"
        logger.info(f"Saved locally: {local_path} -> {url}")
        return url

    def upload_file(
        self,
        file_path: str,
        filename: str,
        folder: str = "temp",
        content_type: str = "image/jpeg",
    ) -> str:
        """
        Upload a file from disk to cloud storage.

        Args:
            file_path: Path to the file on disk
            filename: Name to use in storage
            folder: Folder/prefix for the file
            content_type: MIME type of the file

        Returns:
            URL to access the file
        """
        with open(file_path, "rb") as f:
            data = f.read()
        return self.upload_bytes(data, filename, folder, content_type)

    def is_cloud_storage_enabled(self) -> bool:
        """Check if cloud storage is configured and available."""
        return self._init_cos()


# Singleton instance
cloud_storage = CloudStorageService()
