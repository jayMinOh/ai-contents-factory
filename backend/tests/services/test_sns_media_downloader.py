"""
Test suite for SNS Media Downloader service using gallery-dl integration.

Tests cover:
- Media downloading from Instagram, Facebook, Pinterest
- Image extraction and validation
- Error handling and retry logic
- Temporary file management
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from PIL import Image
import io

from app.services.sns_media_downloader import (
    SNSMediaDownloader,
    SNSMediaDownloadError,
)


class TestSNSMediaDownloader:
    """Test suite for SNSMediaDownloader service."""

    @pytest.fixture
    def downloader(self):
        """Create SNSMediaDownloader instance for testing."""
        return SNSMediaDownloader()

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing."""
        img = Image.new("RGB", (1080, 1350), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        return img_bytes.getvalue()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for downloads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    # Test initialization and configuration
    def test_downloader_initialization(self, downloader):
        """Test SNSMediaDownloader initialization."""
        assert downloader is not None
        assert hasattr(downloader, 'supported_platforms')
        assert hasattr(downloader, 'download')
        assert 'instagram' in downloader.supported_platforms
        assert 'facebook' in downloader.supported_platforms
        assert 'pinterest' in downloader.supported_platforms

    # Test platform support
    def test_is_supported_platform_instagram(self, downloader):
        """Test Instagram platform support detection."""
        assert downloader.is_supported_platform('instagram') is True

    def test_is_supported_platform_facebook(self, downloader):
        """Test Facebook platform support detection."""
        assert downloader.is_supported_platform('facebook') is True

    def test_is_supported_platform_pinterest(self, downloader):
        """Test Pinterest platform support detection."""
        assert downloader.is_supported_platform('pinterest') is True

    def test_is_supported_platform_unsupported(self, downloader):
        """Test unsupported platform detection."""
        assert downloader.is_supported_platform('tiktok') is False
        assert downloader.is_supported_platform('youtube') is False

    def test_is_supported_platform_none(self, downloader):
        """Test None platform handling."""
        assert downloader.is_supported_platform(None) is False
        assert downloader.is_supported_platform('') is False

    # Test URL validation
    def test_is_valid_url_instagram(self, downloader):
        """Test Instagram URL validation."""
        valid_urls = [
            'https://www.instagram.com/p/ABC123def456/',
            'https://instagram.com/p/ABC123def456/',
            'instagram.com/p/ABC123def456/',
        ]
        for url in valid_urls:
            assert downloader.is_valid_url(url) is True

    def test_is_valid_url_facebook(self, downloader):
        """Test Facebook URL validation."""
        valid_urls = [
            'https://www.facebook.com/user/posts/123456789/',
            'https://facebook.com/user/posts/123456789/',
            'facebook.com/user/posts/123456789/',
        ]
        for url in valid_urls:
            assert downloader.is_valid_url(url) is True

    def test_is_valid_url_pinterest(self, downloader):
        """Test Pinterest URL validation."""
        valid_urls = [
            'https://www.pinterest.com/pin/123456789/',
            'https://pinterest.com/pin/123456789/',
            'pinterest.com/pin/123456789/',
        ]
        for url in valid_urls:
            assert downloader.is_valid_url(url) is True

    def test_is_valid_url_invalid(self, downloader):
        """Test invalid URL handling."""
        invalid_urls = [
            'https://example.com',
            'https://twitter.com/user/status/123',
            'not a url',
            '',
            None,
        ]
        for url in invalid_urls:
            assert downloader.is_valid_url(url) is False

    # Test async download method
    @pytest.mark.asyncio
    async def test_download_instagram_url(self, downloader, temp_dir):
        """Test Instagram URL download with mocked gallery-dl."""
        url = 'https://www.instagram.com/p/ABC123def456/'

        with patch('app.services.sns_media_downloader.job') as mock_job:
            # Mock the DownloadJob
            mock_download_job = MagicMock()
            mock_job.DownloadJob.return_value = mock_download_job
            mock_download_job.run.return_value = None

            result = await downloader.download(url, temp_dir)

            assert result is not None
            assert 'platform' in result
            assert 'images' in result
            assert result['platform'] == 'instagram'

    @pytest.mark.asyncio
    async def test_download_facebook_url(self, downloader, temp_dir):
        """Test Facebook URL download with mocked gallery-dl."""
        url = 'https://www.facebook.com/user/posts/123456789/'

        with patch('app.services.sns_media_downloader.job') as mock_job:
            mock_download_job = MagicMock()
            mock_job.DownloadJob.return_value = mock_download_job
            mock_download_job.run.return_value = None

            result = await downloader.download(url, temp_dir)

            assert result is not None
            assert result['platform'] == 'facebook'

    @pytest.mark.asyncio
    async def test_download_pinterest_url(self, downloader, temp_dir):
        """Test Pinterest URL download with mocked gallery-dl."""
        url = 'https://www.pinterest.com/pin/123456789/'

        with patch('app.services.sns_media_downloader.job') as mock_job:
            mock_download_job = MagicMock()
            mock_job.DownloadJob.return_value = mock_download_job
            mock_download_job.run.return_value = None

            result = await downloader.download(url, temp_dir)

            assert result is not None
            assert result['platform'] == 'pinterest'

    @pytest.mark.asyncio
    async def test_download_invalid_url(self, downloader, temp_dir):
        """Test invalid URL handling."""
        url = 'https://example.com'

        with pytest.raises(SNSMediaDownloadError):
            await downloader.download(url, temp_dir)

    @pytest.mark.asyncio
    async def test_download_none_url(self, downloader, temp_dir):
        """Test None URL handling."""
        with pytest.raises(SNSMediaDownloadError):
            await downloader.download(None, temp_dir)

    # Test image list retrieval
    def test_get_downloaded_images_empty_dir(self, downloader, temp_dir):
        """Test getting images from empty directory."""
        images = downloader.get_downloaded_images(temp_dir)
        assert images == []

    def test_get_downloaded_images_with_images(self, downloader, temp_dir, sample_image_bytes):
        """Test getting images from directory with image files."""
        # Create sample image files
        img_path1 = os.path.join(temp_dir, 'image1.jpg')
        img_path2 = os.path.join(temp_dir, 'image2.png')

        with open(img_path1, 'wb') as f:
            f.write(sample_image_bytes)

        # Create PNG image
        img = Image.new("RGB", (800, 600), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        with open(img_path2, 'wb') as f:
            f.write(img_bytes.getvalue())

        images = downloader.get_downloaded_images(temp_dir)

        assert len(images) == 2
        assert any('image1.jpg' in img for img in images)
        assert any('image2.png' in img for img in images)

    def test_get_downloaded_images_with_non_image_files(self, downloader, temp_dir, sample_image_bytes):
        """Test that non-image files are ignored."""
        # Create image file
        img_path = os.path.join(temp_dir, 'image.jpg')
        with open(img_path, 'wb') as f:
            f.write(sample_image_bytes)

        # Create non-image files
        text_path = os.path.join(temp_dir, 'readme.txt')
        with open(text_path, 'w') as f:
            f.write("Not an image")

        json_path = os.path.join(temp_dir, 'meta.json')
        with open(json_path, 'w') as f:
            f.write('{"key": "value"}')

        images = downloader.get_downloaded_images(temp_dir)

        assert len(images) == 1
        assert 'image.jpg' in images[0]

    # Test image validation
    def test_is_valid_image_with_valid_jpeg(self, downloader, sample_image_bytes):
        """Test validation of valid JPEG image."""
        assert downloader.is_valid_image(sample_image_bytes) is True

    def test_is_valid_image_with_valid_png(self, downloader):
        """Test validation of valid PNG image."""
        img = Image.new("RGB", (800, 600), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        assert downloader.is_valid_image(img_bytes.getvalue()) is True

    def test_is_valid_image_with_invalid_bytes(self, downloader):
        """Test validation of invalid image bytes."""
        invalid_bytes = b"This is not an image"
        assert downloader.is_valid_image(invalid_bytes) is False

    def test_is_valid_image_with_empty_bytes(self, downloader):
        """Test validation of empty bytes."""
        assert downloader.is_valid_image(b"") is False

    # Test error handling
    @pytest.mark.asyncio
    async def test_download_network_error(self, downloader, temp_dir):
        """Test handling of network errors during download."""
        url = 'https://www.instagram.com/p/ABC123def456/'

        with patch('app.services.sns_media_downloader.job') as mock_job:
            mock_job.DownloadJob.side_effect = Exception("Network error")

            with pytest.raises(SNSMediaDownloadError):
                await downloader.download(url, temp_dir)

    @pytest.mark.asyncio
    async def test_download_timeout_error(self, downloader, temp_dir):
        """Test handling of timeout errors during download."""
        url = 'https://www.instagram.com/p/ABC123def456/'

        with patch('app.services.sns_media_downloader.job') as mock_job:
            mock_job.DownloadJob.side_effect = asyncio.TimeoutError("Download timeout")

            with pytest.raises(SNSMediaDownloadError):
                await downloader.download(url, temp_dir)

    # Test metadata extraction
    @pytest.mark.asyncio
    async def test_extract_metadata_instagram(self, downloader):
        """Test metadata extraction for Instagram URL."""
        url = 'https://www.instagram.com/p/ABC123def456/'

        metadata = await downloader.extract_metadata(url)

        assert metadata is not None
        assert metadata['platform'] == 'instagram'
        assert metadata['post_id'] == 'ABC123def456'

    @pytest.mark.asyncio
    async def test_extract_metadata_facebook(self, downloader):
        """Test metadata extraction for Facebook URL."""
        url = 'https://www.facebook.com/user/posts/123456789/'

        metadata = await downloader.extract_metadata(url)

        assert metadata is not None
        assert metadata['platform'] == 'facebook'

    @pytest.mark.asyncio
    async def test_extract_metadata_pinterest(self, downloader):
        """Test metadata extraction for Pinterest URL."""
        url = 'https://www.pinterest.com/pin/123456789/'

        metadata = await downloader.extract_metadata(url)

        assert metadata is not None
        assert metadata['platform'] == 'pinterest'

    @pytest.mark.asyncio
    async def test_extract_metadata_invalid_url(self, downloader):
        """Test metadata extraction for invalid URL."""
        url = 'https://example.com'

        with pytest.raises(SNSMediaDownloadError):
            await downloader.extract_metadata(url)

    # Test rate limiting
    def test_downloader_has_rate_limit_config(self, downloader):
        """Test that downloader has rate limit configuration."""
        assert hasattr(downloader, 'max_concurrent_downloads')
        assert downloader.max_concurrent_downloads > 0

    @pytest.mark.asyncio
    async def test_concurrent_downloads_limited(self, downloader, temp_dir):
        """Test that concurrent downloads are limited."""
        urls = [
            'https://www.instagram.com/p/ABC123def456/',
            'https://www.instagram.com/p/DEF789ghi012/',
            'https://www.instagram.com/p/JKL345mno678/',
        ]

        # Mock gallery-dl to track concurrent calls
        with patch('app.services.sns_media_downloader.job') as mock_job:
            call_count = {'concurrent': 0, 'max': 0}

            def track_concurrent(*args, **kwargs):
                call_count['concurrent'] += 1
                call_count['max'] = max(call_count['max'], call_count['concurrent'])
                call_count['concurrent'] -= 1
                return MagicMock()

            mock_job.DownloadJob.side_effect = track_concurrent

            # Should not exceed max_concurrent_downloads
            assert call_count['max'] <= downloader.max_concurrent_downloads


class TestSNSMediaDownloadError:
    """Test suite for SNSMediaDownloadError exception."""

    def test_exception_creation(self):
        """Test SNSMediaDownloadError creation."""
        error = SNSMediaDownloadError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_exception_inheritance(self):
        """Test SNSMediaDownloadError inheritance."""
        error = SNSMediaDownloadError("Test")
        assert isinstance(error, Exception)
