"""
Pydantic schemas for SNS (Social Network Service) API endpoints.

These schemas handle URL parsing, media downloading, and image extraction
from social media platforms (Instagram, Facebook, Pinterest).
"""

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


# ========== SNS Parse Schemas ==========


class SNSParseRequest(BaseModel):
    """Request schema for parsing an SNS URL."""
    url: str = Field(
        ...,
        min_length=10,
        max_length=2048,
        description="SNS URL to parse (Instagram, Facebook, or Pinterest)",
        examples=["https://www.instagram.com/p/ABC123def456/"],
    )


class SNSParseResponse(BaseModel):
    """Response schema for SNS URL parsing result."""
    platform: str = Field(
        ...,
        description="Detected platform (instagram, facebook, pinterest)",
        examples=["instagram"],
    )
    post_id: Optional[str] = Field(
        None,
        description="Extracted post ID (for Instagram/Facebook)",
        examples=["ABC123def456"],
    )
    pin_id: Optional[str] = Field(
        None,
        description="Extracted pin ID (for Pinterest)",
    )
    url: str = Field(
        ...,
        description="Original URL that was parsed",
    )
    valid: bool = Field(
        ...,
        description="Whether the URL is valid and supported",
    )


# ========== SNS Download Schemas ==========


class SNSImageInfo(BaseModel):
    """Information about a downloaded image."""
    url: str = Field(
        ...,
        description="Local path or URL of the downloaded image",
    )
    size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes",
    )
    format: Optional[str] = Field(
        None,
        description="Image format (jpg, png, webp, etc.)",
        examples=["jpg", "png", "webp"],
    )


class SNSDownloadRequest(BaseModel):
    """Request schema for downloading media from an SNS URL."""
    url: str = Field(
        ...,
        min_length=10,
        max_length=2048,
        description="SNS URL to download media from",
        examples=["https://www.instagram.com/p/ABC123def456/"],
    )


class SNSDownloadResponse(BaseModel):
    """Response schema for SNS media download result."""
    platform: str = Field(
        ...,
        description="Platform the media was downloaded from",
        examples=["instagram"],
    )
    images: List[SNSImageInfo] = Field(
        default_factory=list,
        description="List of downloaded images with metadata",
    )
    success: bool = Field(
        ...,
        description="Whether the download was successful",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if download failed",
    )


# ========== SNS Extract Images Schemas ==========


class SNSExtractImagesRequest(BaseModel):
    """Request schema for extracting images from an SNS URL."""
    url: str = Field(
        ...,
        min_length=10,
        max_length=2048,
        description="SNS URL to extract images from",
        examples=["https://www.instagram.com/p/ABC123def456/"],
    )


class SNSExtractImagesResponse(BaseModel):
    """Response schema for extracted images (as base64)."""
    images: List[str] = Field(
        default_factory=list,
        description="List of base64-encoded images",
    )
    count: int = Field(
        ...,
        ge=0,
        description="Number of images extracted",
    )
    success: bool = Field(
        ...,
        description="Whether extraction was successful",
    )
    platform: Optional[str] = Field(
        None,
        description="Platform the images were extracted from",
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if extraction failed",
    )


__all__ = [
    "SNSParseRequest",
    "SNSParseResponse",
    "SNSImageInfo",
    "SNSDownloadRequest",
    "SNSDownloadResponse",
    "SNSExtractImagesRequest",
    "SNSExtractImagesResponse",
]
