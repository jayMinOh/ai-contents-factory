"""
SNS Media Downloader Service

Handles downloading media (images, videos) from social media platforms
using gallery-dl integration. Supports Instagram, Facebook, Pinterest.

This module provides a unified interface for downloading media from various
social media platforms. It uses gallery-dl as the underlying downloader and
provides additional validation, error handling, and image processing.

Supported platforms:
- Instagram: Posts and stories
- Facebook: Posts, photos, and albums
- Pinterest: Pins and boards

Example:
    downloader = SNSMediaDownloader()
    result = await downloader.download(
        'https://www.instagram.com/p/ABC123def456/',
        './downloads/'
    )
    images = result['images']
"""

import asyncio
import io
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from PIL import Image

import httpx

try:
    from gallery_dl import job, config as gallery_config
except ImportError:
    job = None
    gallery_config = None

try:
    import instaloader
except ImportError:
    instaloader = None

logger = logging.getLogger(__name__)


class SNSMediaDownloadError(Exception):
    """Raised when SNS media download fails."""
    pass


class SNSMediaDownloader:
    """
    Download media from Instagram, Facebook, and Pinterest using gallery-dl.

    Supports:
    - Instagram posts (images and videos)
    - Facebook posts (images and videos)
    - Pinterest pins (images)
    """

    # Supported platforms
    SUPPORTED_PLATFORMS = ['instagram', 'facebook', 'pinterest']

    # URL patterns for each platform
    INSTAGRAM_PATTERNS = [
        r"(?:https?://)?(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)",
        r"(?:https?://)?instagram\.com/p/([a-zA-Z0-9_-]+)",
        r"(?:https?://)?(?:www\.)?instagram\.com/reel/([a-zA-Z0-9_-]+)",
    ]

    FACEBOOK_PATTERNS = [
        r"(?:https?://)?(?:www\.)?facebook\.com/[^/]+/posts/(\d+)",
        r"(?:https?://)?facebook\.com/[^/]+/posts/(\d+)",
        r"(?:https?://)?(?:www\.)?facebook\.com/photo[/?].*fbid=(\d+)",
        r"(?:https?://)?facebook\.com/photo/(\d+)",
    ]

    PINTEREST_PATTERNS = [
        r"(?:https?://)?(?:www\.)?pinterest\.com/pin/(\d+)",
        r"(?:https?://)?pinterest\.com/pin/(\d+)",
    ]

    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS  # Alias for backward compatibility

    # Supported video formats
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mov', '.webm', '.avi', '.mkv', '.m4v'}

    # Default cookies file paths to check
    DEFAULT_COOKIES_PATHS = [
        '/app/config/instagram_cookies.txt',  # Docker path
        'config/instagram_cookies.txt',
        'config/cookies.txt',
        'instagram_cookies.txt',
        'cookies.txt',
    ]

    def __init__(self, max_concurrent_downloads: int = 3, cookies_file: Optional[str] = None):
        """
        Initialize SNS Media Downloader.

        Args:
            max_concurrent_downloads: Maximum concurrent downloads allowed
            cookies_file: Optional path to cookies file for authentication
        """
        self.supported_platforms = self.SUPPORTED_PLATFORMS
        self.max_concurrent_downloads = max_concurrent_downloads
        self.cookies_file = cookies_file or self._find_cookies_file()

        if job is None:
            logger.warning("gallery-dl not installed. Download functionality limited.")

        if self.cookies_file:
            logger.info(f"Using cookies file: {self.cookies_file}")
        else:
            logger.warning("No cookies file found. Instagram may require login.")

    def _find_cookies_file(self) -> Optional[str]:
        """Find cookies file from default locations."""
        for path in self.DEFAULT_COOKIES_PATHS:
            if os.path.exists(path):
                return path
        return None

    def is_supported_platform(self, platform: Optional[str]) -> bool:
        """
        Check if platform is supported.

        Args:
            platform: Platform name to check

        Returns:
            True if platform is supported
        """
        if not platform or not isinstance(platform, str):
            return False

        return platform.lower().strip() in self.supported_platforms

    def is_valid_url(self, url: Optional[str]) -> bool:
        """
        Check if URL is valid for any supported platform.

        Args:
            url: URL to validate

        Returns:
            True if URL matches any supported platform pattern
        """
        if not url or not isinstance(url, str):
            return False

        url = url.strip()

        # Check Instagram
        if self._match_patterns(url, self.INSTAGRAM_PATTERNS):
            return True

        # Check Facebook
        if self._match_patterns(url, self.FACEBOOK_PATTERNS):
            return True

        # Check Pinterest
        if self._match_patterns(url, self.PINTEREST_PATTERNS):
            return True

        return False

    @staticmethod
    def _match_patterns(url: str, patterns: List[str]) -> Optional[str]:
        """
        Match URL against list of regex patterns.

        Args:
            url: URL to match
            patterns: List of regex patterns

        Returns:
            Extracted ID from first matching pattern, or None
        """
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def _detect_platform(self, url: str) -> Optional[str]:
        """
        Detect platform from URL.

        Args:
            url: URL to detect platform from

        Returns:
            Platform name or None if not detected
        """
        if self._match_patterns(url, self.INSTAGRAM_PATTERNS):
            return 'instagram'
        elif self._match_patterns(url, self.FACEBOOK_PATTERNS):
            return 'facebook'
        elif self._match_patterns(url, self.PINTEREST_PATTERNS):
            return 'pinterest'
        return None

    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from SNS URL.

        Args:
            url: SNS URL to extract metadata from

        Returns:
            Dictionary with platform and extracted IDs

        Raises:
            SNSMediaDownloadError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise SNSMediaDownloadError("URL cannot be empty")

        url = url.strip()

        if not self.is_valid_url(url):
            raise SNSMediaDownloadError(f"Unsupported or invalid SNS URL: {url}")

        platform = self._detect_platform(url)
        if not platform:
            raise SNSMediaDownloadError(f"Could not detect platform for URL: {url}")

        metadata = {
            'platform': platform,
            'url': url,
        }

        # Extract platform-specific IDs
        if platform == 'instagram':
            post_id = self._match_patterns(url, self.INSTAGRAM_PATTERNS)
            metadata['post_id'] = post_id
        elif platform == 'facebook':
            post_id = self._match_patterns(url, self.FACEBOOK_PATTERNS)
            metadata['post_id'] = post_id
        elif platform == 'pinterest':
            pin_id = self._match_patterns(url, self.PINTEREST_PATTERNS)
            metadata['pin_id'] = pin_id

        return metadata

    async def download(
        self,
        url: Optional[str],
        output_dir: str,
        cookies_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download media from SNS URL using gallery-dl.

        Args:
            url: SNS URL to download from
            output_dir: Directory to save downloaded files
            cookies_file: Optional path to cookies file for authentication

        Returns:
            Dictionary with download results and image paths

        Raises:
            SNSMediaDownloadError: If download fails
        """
        if not url or not isinstance(url, str):
            raise SNSMediaDownloadError("URL cannot be empty")

        url = url.strip()

        if not self.is_valid_url(url):
            raise SNSMediaDownloadError(f"Unsupported or invalid SNS URL: {url}")

        try:
            # Extract metadata first
            metadata = await self.extract_metadata(url)
            platform = metadata['platform']

            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # Configure gallery-dl job
            if job is None:
                raise SNSMediaDownloadError("gallery-dl is not installed")

            # Create options dict for gallery-dl
            options = {
                'output': output_dir,
                'quiet': False,
                'retries': 3,
            }

            # Add cookies if provided
            if cookies_file and os.path.exists(cookies_file):
                options['cookies'] = cookies_file

            # Use asyncio to run gallery-dl in thread pool to avoid blocking
            try:
                download_job = await asyncio.to_thread(
                    self._run_gallery_dl_job,
                    url,
                    options
                )

                # Get downloaded images
                images = self.get_downloaded_images(output_dir)

                return {
                    'platform': platform,
                    'url': url,
                    'images': images,
                    'output_dir': output_dir,
                    'success': True,
                }

            except asyncio.TimeoutError:
                raise SNSMediaDownloadError(f"Download timeout for {url}")
            except Exception as download_error:
                raise SNSMediaDownloadError(f"Download failed for {url}: {str(download_error)}")

        except SNSMediaDownloadError:
            raise
        except Exception as error:
            logger.error(f"Unexpected error downloading {url}: {error}")
            raise SNSMediaDownloadError(f"Unexpected error: {str(error)}")

    @staticmethod
    def _run_gallery_dl_job(url: str, options: Dict[str, Any]) -> None:
        """
        Run gallery-dl download job in sync context.

        Args:
            url: URL to download from
            options: gallery-dl options

        Raises:
            Exception: If download fails
        """
        try:
            # Configure gallery-dl using its config module
            if gallery_config is not None:
                gallery_config.clear()
                gallery_config.set(("extractor",), "base-directory", options.get('output', '.'))
                gallery_config.set(("extractor",), "retries", options.get('retries', 3))
                if options.get('cookies'):
                    gallery_config.set(("extractor",), "cookies", options.get('cookies'))

            # Create and run download job without options parameter
            download_job = job.DownloadJob(url)
            download_job.run()
        except Exception as error:
            logger.error(f"gallery-dl job failed: {error}")
            raise

    def get_downloaded_images(self, directory: str) -> List[str]:
        """
        Get list of downloaded image files from directory (including subdirectories).

        Args:
            directory: Directory to scan for images

        Returns:
            List of image file paths
        """
        if not os.path.exists(directory):
            return []

        images = []
        try:
            # Use os.walk to recursively scan all subdirectories
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)

                    # Check if it's an image file
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in self.SUPPORTED_FORMATS:
                        images.append(file_path)

            return sorted(images)

        except Exception as error:
            logger.warning(f"Error scanning directory {directory}: {error}")
            return []

    def get_downloaded_videos(self, directory: str) -> List[str]:
        """
        Get list of downloaded video files from directory (including subdirectories).

        Args:
            directory: Directory to scan for videos

        Returns:
            List of video file paths
        """
        if not os.path.exists(directory):
            return []

        videos = []
        try:
            # Use os.walk to recursively scan all subdirectories
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    file_path = os.path.join(root, filename)

                    # Check if it's a video file
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in self.SUPPORTED_VIDEO_FORMATS:
                        videos.append(file_path)

            return sorted(videos)

        except Exception as error:
            logger.warning(f"Error scanning directory {directory}: {error}")
            return []

    def get_all_media(self, directory: str) -> Dict[str, List[str]]:
        """
        Get all downloaded media files from directory, categorized by type.

        Args:
            directory: Directory to scan for media

        Returns:
            Dictionary with 'images' and 'videos' lists
        """
        return {
            'images': self.get_downloaded_images(directory),
            'videos': self.get_downloaded_videos(directory),
        }

    def is_valid_image(self, image_data: bytes) -> bool:
        """
        Validate if bytes represent a valid image.

        Args:
            image_data: Bytes to validate

        Returns:
            True if valid image, False otherwise
        """
        if not image_data or not isinstance(image_data, bytes):
            return False

        try:
            img = Image.open(io.BytesIO(image_data))
            img.verify()
            return True
        except Exception:
            return False

    async def _extract_instagram_images_instaloader(self, shortcode: str) -> List[bytes]:
        """
        Extract images from Instagram post using Instaloader.

        Args:
            shortcode: Instagram post shortcode (e.g., 'DST5aQCk93z')

        Returns:
            List of image byte data
        """
        if instaloader is None:
            raise SNSMediaDownloadError("instaloader is not installed")

        try:
            L = instaloader.Instaloader(
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
            )

            # Get post info
            post = await asyncio.to_thread(
                instaloader.Post.from_shortcode,
                L.context,
                shortcode
            )

            # Collect image URLs
            image_urls = []
            if post.typename == 'GraphSidecar':
                # Carousel post - multiple images
                for node in post.get_sidecar_nodes():
                    if not node.is_video:
                        image_urls.append(node.display_url)
            elif not post.is_video:
                # Single image post
                image_urls.append(post.url)

            # Download images
            images_data = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for img_url in image_urls:
                    try:
                        response = await client.get(img_url)
                        if response.status_code == 200:
                            image_bytes = response.content
                            if self.is_valid_image(image_bytes):
                                images_data.append(image_bytes)
                    except Exception as e:
                        logger.warning(f"Failed to download image {img_url}: {e}")

            return images_data

        except Exception as error:
            logger.error(f"Instaloader extraction failed: {error}")
            raise SNSMediaDownloadError(f"Instagram extraction failed: {str(error)}")

    async def extract_images_from_post(
        self,
        url: str,
        output_dir: str,
        cookies_file: Optional[str] = None,
    ) -> List[bytes]:
        """
        Download and extract image data from SNS post.

        Args:
            url: SNS URL to extract images from
            output_dir: Temporary directory for downloads
            cookies_file: Optional cookies file for authentication

        Returns:
            List of image byte data

        Raises:
            SNSMediaDownloadError: If extraction fails
        """
        try:
            # Detect platform
            platform = self._detect_platform(url)

            # Use cookies file if available
            effective_cookies = cookies_file or self.cookies_file
            if effective_cookies:
                logger.info(f"Using cookies file for {platform}: {effective_cookies}")

            # Use gallery-dl directly (supports cookies.txt)
            result = await self.download(url, output_dir, effective_cookies)

            if not result.get('success'):
                raise SNSMediaDownloadError(f"Download failed for {url}")

            images_data = []
            for image_path in result.get('images', []):
                try:
                    with open(image_path, 'rb') as f:
                        image_bytes = f.read()
                        if self.is_valid_image(image_bytes):
                            images_data.append(image_bytes)
                except Exception as error:
                    logger.warning(f"Could not read image {image_path}: {error}")

            return images_data

        except SNSMediaDownloadError:
            raise
        except Exception as error:
            raise SNSMediaDownloadError(f"Image extraction failed: {str(error)}")
