"""
SNS Parser Service

Handles parsing of SNS URLs (Instagram, Facebook, Pinterest) and extracting
metadata and images from social media posts.

This module integrates with SNSMediaDownloader to provide actual media
downloading capabilities beyond URL parsing.
"""

import logging
import re
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)


class SNSParseError(Exception):
    """Raised when SNS URL parsing fails."""
    pass


class SNSParser:
    """
    Parser for Instagram, Facebook, and Pinterest URLs.

    Supports:
    - Instagram posts (www.instagram.com/p/{post_id}/)
    - Facebook posts (facebook.com/{username}/posts/{post_id})
    - Pinterest pins (pinterest.com/pin/{pin_id}/)
    """

    # Regular expressions for platform URL patterns
    INSTAGRAM_PATTERNS = [
        r"(?:https?://)?(?:www\.)?instagram\.com/p/([a-zA-Z0-9_-]+)",
        r"(?:https?://)?instagram\.com/p/([a-zA-Z0-9_-]+)",
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

    async def parse_url(self, url: Optional[str]) -> Dict[str, Any]:
        """
        Parse SNS URL and extract metadata.

        Args:
            url: SNS URL to parse

        Returns:
            Dictionary with platform, IDs, and extracted data

        Raises:
            SNSParseError: If URL is invalid or unsupported
        """
        if not url:
            raise SNSParseError("URL cannot be empty")

        if not isinstance(url, str):
            raise SNSParseError("URL must be a string")

        url = url.strip()

        # Check Instagram
        instagram_match = self._match_patterns(url, self.INSTAGRAM_PATTERNS)
        if instagram_match:
            return {
                "platform": "instagram",
                "post_id": instagram_match,
                "url": url,
            }

        # Check Facebook
        facebook_match = self._match_patterns(url, self.FACEBOOK_PATTERNS)
        if facebook_match:
            return {
                "platform": "facebook",
                "post_id": facebook_match,
                "url": url,
            }

        # Check Pinterest
        pinterest_match = self._match_patterns(url, self.PINTEREST_PATTERNS)
        if pinterest_match:
            return {
                "platform": "pinterest",
                "pin_id": pinterest_match,
                "url": url,
            }

        raise SNSParseError(f"Unsupported or invalid SNS URL: {url}")

    def is_valid_url(self, url: str) -> bool:
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

        # Check all platforms
        if self._match_patterns(url, self.INSTAGRAM_PATTERNS):
            return True
        if self._match_patterns(url, self.FACEBOOK_PATTERNS):
            return True
        if self._match_patterns(url, self.PINTEREST_PATTERNS):
            return True

        return False

    @staticmethod
    def _match_patterns(url: str, patterns: list) -> Optional[str]:
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

    async def extract_images_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract image metadata from SNS URL using SNSMediaDownloader.

        Downloads media from the SNS URL and extracts image data for
        further processing (analysis, generation, etc.).

        Args:
            url: SNS URL to extract images from

        Returns:
            Dictionary with image metadata and downloaded images

        Raises:
            SNSParseError: If extraction fails
        """
        try:
            # Parse URL first
            parsed = await self.parse_url(url)

            # Import here to avoid circular dependency
            from app.services.sns_media_downloader import SNSMediaDownloader

            downloader = SNSMediaDownloader()

            # Create temporary directory for downloads
            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    # Extract images from post
                    images = await downloader.extract_images_from_post(
                        url,
                        temp_dir
                    )

                    return {
                        "platform": parsed["platform"],
                        "url": url,
                        "images": images,
                        "image_count": len(images),
                        "caption": None,
                        "source": "gallery-dl",
                    }

                except Exception as download_error:
                    logger.warning(f"Failed to extract images via gallery-dl: {download_error}")
                    # Fall back to URL parsing only
                    return {
                        "platform": parsed["platform"],
                        "url": url,
                        "images": [],
                        "image_count": 0,
                        "caption": None,
                        "source": "parse-only",
                    }

        except SNSParseError:
            raise
        except Exception as error:
            logger.error(f"Error extracting images metadata: {error}")
            raise SNSParseError(f"Failed to extract images: {str(error)}")
