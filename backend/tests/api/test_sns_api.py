"""
Unit and integration tests for SNS API endpoints.

Tests cover:
- POST /api/v1/studio/sns/parse - Parse SNS URLs
- POST /api/v1/studio/sns/download - Download media from SNS URLs
- POST /api/v1/studio/sns/extract-images - Extract images as base64
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


class TestSNSParse:
    """Test SNS URL parsing endpoints."""

    @pytest.mark.asyncio
    async def test_parse_instagram_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with valid Instagram URL."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": "https://www.instagram.com/p/ABC123def456/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "instagram"
        assert data["post_id"] == "ABC123def456"
        assert data["valid"] is True
        assert data["url"] == "https://www.instagram.com/p/ABC123def456/"

    @pytest.mark.asyncio
    async def test_parse_facebook_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with valid Facebook URL."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": "https://www.facebook.com/user/posts/123456789"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "facebook"
        assert data["post_id"] == "123456789"
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_parse_pinterest_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with valid Pinterest URL."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": "https://www.pinterest.com/pin/123456789012345678/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "pinterest"
        assert data["pin_id"] == "123456789012345678"
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_parse_invalid_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with invalid URL."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": "https://example.com/not-a-social-media-url"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "unknown"
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_parse_empty_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with empty URL returns validation error."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_parse_missing_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with missing URL returns validation error."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_parse_instagram_without_www(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/parse with Instagram URL without www."""
        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": "https://instagram.com/p/XYZ789abc123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "instagram"
        assert data["post_id"] == "XYZ789abc123"
        assert data["valid"] is True


class TestSNSDownload:
    """Test SNS media download endpoints."""

    @pytest.mark.asyncio
    async def test_download_invalid_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/download with invalid URL."""
        response = await client.post(
            "/api/v1/studio/sns/download",
            json={"url": "https://example.com/not-supported"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["images"] == []
        assert "Invalid or unsupported" in data["error_message"]

    @pytest.mark.asyncio
    async def test_download_empty_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/download with empty URL returns validation error."""
        response = await client.post(
            "/api/v1/studio/sns/download",
            json={"url": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.download")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_metadata")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.is_valid_url")
    async def test_download_success_mock(
        self,
        mock_is_valid: MagicMock,
        mock_extract_metadata: AsyncMock,
        mock_download: AsyncMock,
        client: AsyncClient,
    ):
        """Test POST /api/v1/studio/sns/download with mocked successful download."""
        # Setup mocks
        mock_is_valid.return_value = True
        mock_extract_metadata.return_value = {"platform": "instagram"}
        mock_download.return_value = {
            "platform": "instagram",
            "url": "https://www.instagram.com/p/ABC123/",
            "images": [],  # Empty list since temp files won't exist
            "success": True,
        }

        response = await client.post(
            "/api/v1/studio/sns/download",
            json={"url": "https://www.instagram.com/p/ABC123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["platform"] == "instagram"
        assert data["success"] is True

    @pytest.mark.asyncio
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_metadata")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.is_valid_url")
    async def test_download_metadata_error(
        self,
        mock_is_valid: MagicMock,
        mock_extract_metadata: AsyncMock,
        client: AsyncClient,
    ):
        """Test POST /api/v1/studio/sns/download when metadata extraction fails."""
        from app.services.sns_media_downloader import SNSMediaDownloadError

        mock_is_valid.return_value = True
        mock_extract_metadata.side_effect = SNSMediaDownloadError("Failed to extract metadata")

        response = await client.post(
            "/api/v1/studio/sns/download",
            json={"url": "https://www.instagram.com/p/ABC123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "Failed to extract metadata" in data["error_message"]


class TestSNSExtractImages:
    """Test SNS image extraction endpoints."""

    @pytest.mark.asyncio
    async def test_extract_images_invalid_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/extract-images with invalid URL."""
        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": "https://example.com/not-supported"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["count"] == 0
        assert data["images"] == []
        assert "Invalid or unsupported" in data["error_message"]

    @pytest.mark.asyncio
    async def test_extract_images_empty_url(self, client: AsyncClient):
        """Test POST /api/v1/studio/sns/extract-images with empty URL returns validation error."""
        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_images_from_post")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_metadata")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.is_valid_url")
    async def test_extract_images_success_mock(
        self,
        mock_is_valid: MagicMock,
        mock_extract_metadata: AsyncMock,
        mock_extract_images: AsyncMock,
        client: AsyncClient,
    ):
        """Test POST /api/v1/studio/sns/extract-images with mocked successful extraction."""
        import base64

        # Create sample image bytes (minimal valid PNG)
        sample_image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

        mock_is_valid.return_value = True
        mock_extract_metadata.return_value = {"platform": "instagram"}
        mock_extract_images.return_value = [sample_image_bytes]

        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": "https://www.instagram.com/p/ABC123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert len(data["images"]) == 1
        assert data["platform"] == "instagram"

        # Verify base64 encoding
        decoded = base64.b64decode(data["images"][0])
        assert decoded == sample_image_bytes

    @pytest.mark.asyncio
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_images_from_post")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_metadata")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.is_valid_url")
    async def test_extract_multiple_images(
        self,
        mock_is_valid: MagicMock,
        mock_extract_metadata: AsyncMock,
        mock_extract_images: AsyncMock,
        client: AsyncClient,
    ):
        """Test POST /api/v1/studio/sns/extract-images with multiple images."""
        sample_images = [
            b"\x89PNG\r\n\x1a\n" + b"\x01" * 50,
            b"\x89PNG\r\n\x1a\n" + b"\x02" * 50,
            b"\x89PNG\r\n\x1a\n" + b"\x03" * 50,
        ]

        mock_is_valid.return_value = True
        mock_extract_metadata.return_value = {"platform": "instagram"}
        mock_extract_images.return_value = sample_images

        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": "https://www.instagram.com/p/MultiImage123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 3
        assert len(data["images"]) == 3

    @pytest.mark.asyncio
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.extract_metadata")
    @patch("app.services.sns_media_downloader.SNSMediaDownloader.is_valid_url")
    async def test_extract_images_download_error(
        self,
        mock_is_valid: MagicMock,
        mock_extract_metadata: AsyncMock,
        client: AsyncClient,
    ):
        """Test POST /api/v1/studio/sns/extract-images when download fails."""
        from app.services.sns_media_downloader import SNSMediaDownloadError

        mock_is_valid.return_value = True
        mock_extract_metadata.side_effect = SNSMediaDownloadError("Download failed")

        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": "https://www.instagram.com/p/ABC123/"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert data["count"] == 0
        assert "Download failed" in data["error_message"]


class TestSNSSchemaValidation:
    """Test request/response schema validation."""

    @pytest.mark.asyncio
    async def test_parse_url_too_long(self, client: AsyncClient):
        """Test that URLs over 2048 characters are rejected."""
        long_url = "https://www.instagram.com/p/" + "a" * 2500

        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": long_url},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_parse_url_too_short(self, client: AsyncClient):
        """Test that URLs under 10 characters are rejected."""
        short_url = "http://a"

        response = await client.post(
            "/api/v1/studio/sns/parse",
            json={"url": short_url},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_download_response_structure(self, client: AsyncClient):
        """Test that download response has correct structure."""
        response = await client.post(
            "/api/v1/studio/sns/download",
            json={"url": "https://example.com/invalid"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "platform" in data
        assert "images" in data
        assert "success" in data
        assert isinstance(data["images"], list)
        assert isinstance(data["success"], bool)

    @pytest.mark.asyncio
    async def test_extract_images_response_structure(self, client: AsyncClient):
        """Test that extract-images response has correct structure."""
        response = await client.post(
            "/api/v1/studio/sns/extract-images",
            json={"url": "https://example.com/invalid"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "images" in data
        assert "count" in data
        assert "success" in data
        assert isinstance(data["images"], list)
        assert isinstance(data["count"], int)
        assert isinstance(data["success"], bool)


class TestSNSPlatformDetection:
    """Test platform detection for various URL formats."""

    @pytest.mark.asyncio
    async def test_instagram_post_formats(self, client: AsyncClient):
        """Test various Instagram URL formats."""
        urls = [
            "https://www.instagram.com/p/ABC123/",
            "https://instagram.com/p/ABC123/",
            "http://www.instagram.com/p/ABC123/",
            "https://www.instagram.com/p/ABC123",
        ]

        for url in urls:
            response = await client.post(
                "/api/v1/studio/sns/parse",
                json={"url": url},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["platform"] == "instagram", f"Failed for URL: {url}"
            assert data["valid"] is True, f"Failed for URL: {url}"

    @pytest.mark.asyncio
    async def test_facebook_post_formats(self, client: AsyncClient):
        """Test various Facebook URL formats."""
        urls = [
            "https://www.facebook.com/user/posts/123456789",
            "https://facebook.com/user/posts/123456789",
        ]

        for url in urls:
            response = await client.post(
                "/api/v1/studio/sns/parse",
                json={"url": url},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["platform"] == "facebook", f"Failed for URL: {url}"
            assert data["valid"] is True, f"Failed for URL: {url}"

    @pytest.mark.asyncio
    async def test_pinterest_pin_formats(self, client: AsyncClient):
        """Test various Pinterest URL formats."""
        urls = [
            "https://www.pinterest.com/pin/123456789/",
            "https://pinterest.com/pin/123456789/",
        ]

        for url in urls:
            response = await client.post(
                "/api/v1/studio/sns/parse",
                json={"url": url},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["platform"] == "pinterest", f"Failed for URL: {url}"
            assert data["valid"] is True, f"Failed for URL: {url}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
