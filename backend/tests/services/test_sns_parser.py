"""
RED PHASE: SNS Parser Service Tests

Tests for Instagram, Facebook, and Pinterest URL parsing and image extraction.
Following TDD: Write failing tests first.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.sns_parser import SNSParser, SNSParseError


class TestSNSParser:
    """Tests for SNS URL parsing service."""

    @pytest.fixture
    def parser(self):
        """Create SNS parser instance."""
        return SNSParser()

    # RED PHASE: Test Instagram URL parsing
    @pytest.mark.asyncio
    async def test_parse_instagram_url_valid(self, parser):
        """Test parsing valid Instagram post URL."""
        url = "https://www.instagram.com/p/ABC123def456/"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "instagram"
        assert result["post_id"] == "ABC123def456"
        assert "url" in result

    @pytest.mark.asyncio
    async def test_parse_instagram_url_short(self, parser):
        """Test parsing short Instagram URL."""
        url = "https://instagram.com/p/ABC123/"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "instagram"
        assert result["post_id"] == "ABC123"

    @pytest.mark.asyncio
    async def test_parse_instagram_url_with_query_params(self, parser):
        """Test parsing Instagram URL with query parameters."""
        url = "https://www.instagram.com/p/ABC123def456/?utm_source=ig_web"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "instagram"
        assert result["post_id"] == "ABC123def456"

    # RED PHASE: Test Facebook URL parsing
    @pytest.mark.asyncio
    async def test_parse_facebook_url_valid(self, parser):
        """Test parsing valid Facebook post URL."""
        url = "https://www.facebook.com/username/posts/123456789"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "facebook"
        assert result["post_id"] == "123456789"

    @pytest.mark.asyncio
    async def test_parse_facebook_url_photo(self, parser):
        """Test parsing Facebook photo URL."""
        url = "https://www.facebook.com/photo/?fbid=123456789&set=a.987654321"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "facebook"
        assert "post_id" in result

    # RED PHASE: Test Pinterest URL parsing
    @pytest.mark.asyncio
    async def test_parse_pinterest_url_valid(self, parser):
        """Test parsing valid Pinterest pin URL."""
        url = "https://www.pinterest.com/pin/123456789/"

        result = await parser.parse_url(url)

        assert result is not None
        assert result["platform"] == "pinterest"
        assert result["pin_id"] == "123456789"

    # RED PHASE: Test invalid URLs
    @pytest.mark.asyncio
    async def test_parse_invalid_url(self, parser):
        """Test parsing invalid URL raises SNSParseError."""
        url = "https://www.example.com/page"

        with pytest.raises(SNSParseError):
            await parser.parse_url(url)

    @pytest.mark.asyncio
    async def test_parse_empty_url(self, parser):
        """Test parsing empty URL raises SNSParseError."""
        with pytest.raises(SNSParseError):
            await parser.parse_url("")

    @pytest.mark.asyncio
    async def test_parse_none_url(self, parser):
        """Test parsing None URL raises SNSParseError."""
        with pytest.raises(SNSParseError):
            await parser.parse_url(None)

    # RED PHASE: Test image extraction
    @pytest.mark.asyncio
    async def test_extract_instagram_image(self, parser):
        """Test extracting image data from Instagram URL."""
        # Note: This would require mocking actual Instagram scraping
        url = "https://www.instagram.com/p/ABC123/"

        # This test is placeholder - real implementation needs mocking
        # of network calls to Instagram
        result = await parser.parse_url(url)
        assert result is not None

    # RED PHASE: Test URL validation
    def test_validate_url_format_instagram(self, parser):
        """Test URL format validation for Instagram."""
        valid_urls = [
            "https://instagram.com/p/ABC123/",
            "https://www.instagram.com/p/ABC123/",
            "https://instagram.com/p/ABC123",
        ]

        for url in valid_urls:
            assert parser.is_valid_url(url) is True

    def test_validate_url_format_facebook(self, parser):
        """Test URL format validation for Facebook."""
        valid_urls = [
            "https://facebook.com/username/posts/123",
            "https://www.facebook.com/photo/?fbid=123",
            "https://facebook.com/photo/123",
        ]

        for url in valid_urls:
            assert parser.is_valid_url(url) is True

    def test_validate_url_format_pinterest(self, parser):
        """Test URL format validation for Pinterest."""
        valid_urls = [
            "https://pinterest.com/pin/123/",
            "https://www.pinterest.com/pin/123456789/",
        ]

        for url in valid_urls:
            assert parser.is_valid_url(url) is True

    def test_validate_invalid_url_format(self, parser):
        """Test invalid URL format returns False."""
        invalid_urls = [
            "https://twitter.com/user/status/123",
            "https://example.com/page",
            "not-a-url",
        ]

        for url in invalid_urls:
            assert parser.is_valid_url(url) is False
