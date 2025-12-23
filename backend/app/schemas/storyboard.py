"""
Pydantic schemas for Storyboard Generation API.

This module defines the request/response schemas for the new storyboard
generation endpoint that uses Gemini to generate storyboards based on
content type, purpose, and either prompt or reference analysis.
"""

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field


# ========== Selected Items from Reference Analysis ==========


class SelectedAnalysisItems(BaseModel):
    """
    Selected items from reference analysis to inform storyboard generation.

    These items are selected by the user from the reference analysis results
    and guide the AI to create storyboards that incorporate specific hooks,
    emotional triggers, and selling points.
    """
    hook_points: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Selected hook points from reference analysis for attention-grabbing opening"
    )
    edge_points: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Selected differentiation elements from reference"
    )
    triggers: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Selected emotional triggers for emotional appeal slides"
    )
    selling_points: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Selected selling points for benefit slides"
    )
    recommendations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Selected recommendations to improve overall structure"
    )


# ========== Request Schema ==========


class StoryboardGenerateV2Request(BaseModel):
    """
    Request schema for the new storyboard generation endpoint.

    Supports multiple content types (single, carousel, story), purposes
    (ad, info, lifestyle), and generation methods (reference, prompt).
    """
    content_type: Literal["single", "carousel", "story"] = Field(
        ...,
        description="Type of content to generate: 'single' (single image), 'carousel' (multi-slide), 'story' (vertical format)"
    )
    purpose: Literal["ad", "info", "lifestyle"] = Field(
        ...,
        description="Purpose of the content: 'ad' (advertising), 'info' (informational), 'lifestyle' (casual/emotional)"
    )
    method: Literal["reference", "prompt"] = Field(
        ...,
        description="Generation method: 'reference' (based on analysis) or 'prompt' (free-form text)"
    )

    # For prompt method
    prompt: Optional[str] = Field(
        default=None,
        description="Free-form prompt describing the desired storyboard (required for method='prompt')"
    )

    # For ad purpose - brand and product context
    brand_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Brand ID for context (recommended for method='ad')"
    )
    product_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Product ID for context (recommended for method='ad')"
    )

    # For reference method
    reference_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Reference analysis ID (required for method='reference')"
    )
    selected_items: Optional[SelectedAnalysisItems] = Field(
        default=None,
        description="Selected items from reference analysis to incorporate"
    )

    # Optional configuration
    language: Optional[str] = Field(
        default="ko",
        description="Output language code (ko, en, ja, zh)"
    )
    aspect_ratio: Optional[str] = Field(
        default=None,
        pattern=r"^\d+:\d+$",
        description="Aspect ratio for visual prompts (e.g., '16:9', '9:16', '1:1')"
    )


# ========== Response Schema ==========


class StoryboardSlide(BaseModel):
    """
    A single slide in the generated storyboard.

    Each slide contains content direction, visual prompts for image generation,
    and text overlay information.
    """
    slide_number: int = Field(
        ...,
        ge=1,
        description="Sequential slide number starting from 1"
    )
    section_type: Literal["hook", "problem", "solution", "benefit", "cta", "intro", "outro", "transition", "feature"] = Field(
        ...,
        description="Type of section this slide represents"
    )
    title: str = Field(
        ...,
        description="Short title for this slide"
    )
    description: str = Field(
        ...,
        description="Detailed description of what this slide should convey"
    )
    visual_prompt: str = Field(
        ...,
        description="Detailed prompt for AI image generation (English, optimized for image generators)"
    )
    visual_prompt_display: Optional[str] = Field(
        default=None,
        description="Visual prompt in user's language for display purposes"
    )
    text_overlay: Optional[str] = Field(
        default=None,
        description="Text to overlay on the slide image"
    )
    narration_script: Optional[str] = Field(
        default=None,
        description="Optional narration script for this slide"
    )
    duration_seconds: Optional[float] = Field(
        default=3.0,
        ge=0.5,
        le=30,
        description="Recommended duration for this slide in seconds"
    )


class StoryboardGenerateV2Response(BaseModel):
    """
    Response schema for the storyboard generation endpoint.

    Contains the generated storyboard with all slides and metadata.
    """
    storyboard_id: str = Field(
        ...,
        description="Unique identifier for this storyboard"
    )
    slides: List[StoryboardSlide] = Field(
        ...,
        description="List of generated slides"
    )
    total_slides: int = Field(
        ...,
        description="Total number of slides generated"
    )
    storyline: str = Field(
        ...,
        description="Summary of the overall storyline/narrative"
    )
    content_type: str = Field(
        ...,
        description="Content type used for generation"
    )
    purpose: str = Field(
        ...,
        description="Purpose used for generation"
    )
    generation_method: str = Field(
        ...,
        description="Method used for generation (reference or prompt)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the storyboard was generated"
    )


# ========== Light Storyboard / Concept Suggestion Schemas ==========


class ConceptGenerateRequest(BaseModel):
    """
    Request schema for generating AI concept suggestions for single image content.

    This is a "Light Storyboard" that provides visual concept, copy suggestion,
    and style recommendations before generating a single image.

    Supports two modes:
    - reference: Based on reference analysis data (traditional mode)
    - upload: Based on uploaded product/reference images (new mode)
    """
    content_type: Literal["single", "story"] = Field(
        ...,
        description="Type of content: 'single' (single image) or 'story' (vertical format)"
    )
    purpose: Literal["ad", "info", "lifestyle"] = Field(
        ...,
        description="Purpose of the content: 'ad' (advertising), 'info' (informational), 'lifestyle' (casual/emotional)"
    )
    generation_mode: Literal["reference", "upload"] = Field(
        default="reference",
        description="Concept generation mode: 'reference' (based on analysis) or 'upload' (based on uploaded images)"
    )
    # For reference mode
    reference_analysis_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Reference analysis ID to base the concept on (required for reference mode)"
    )
    # For upload mode - reference image URLs or base64 data (multiple allowed)
    reference_image_urls: Optional[List[str]] = Field(
        default=None,
        description="List of reference image URLs or base64 data (for upload mode, multiple allowed)"
    )
    user_prompt: Optional[str] = Field(
        default=None,
        description="Additional user prompt/description for concept generation"
    )
    # Common fields
    brand_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Brand ID for brand context (recommended for 'ad' purpose)"
    )
    product_id: Optional[str] = Field(
        default=None,
        min_length=36,
        max_length=36,
        description="Product ID for product context (recommended for 'ad' purpose)"
    )
    selected_items: Optional[SelectedAnalysisItems] = Field(
        default=None,
        description="Selected items from reference analysis to incorporate (for reference mode)"
    )
    language: Optional[str] = Field(
        default="ko",
        description="Output language code (ko, en, ja, zh)"
    )


class ConceptGenerateResponse(BaseModel):
    """
    Response schema for AI concept suggestion.

    Contains visual concept, copy suggestion, style recommendation,
    and a ready-to-use visual prompt for image generation.
    """
    concept_id: str = Field(
        ...,
        description="Unique identifier for this concept"
    )
    visual_concept: str = Field(
        ...,
        description="Visual concept description including layout and composition suggestions"
    )
    copy_suggestion: str = Field(
        ...,
        description="Suggested hooking text/copy based on reference analysis"
    )
    style_recommendation: str = Field(
        ...,
        description="Style and tone recommendations based on purpose"
    )
    visual_prompt: str = Field(
        ...,
        description="Ready-to-use visual prompt for AI image generation (English)"
    )
    visual_prompt_display: Optional[str] = Field(
        default=None,
        description="Visual prompt in user's language for display"
    )
    text_overlay_suggestion: Optional[str] = Field(
        default=None,
        description="Suggested text overlay for the image"
    )
    content_type: str = Field(
        ...,
        description="Content type used for generation"
    )
    purpose: str = Field(
        ...,
        description="Purpose used for generation"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the concept was generated"
    )


__all__ = [
    "SelectedAnalysisItems",
    "StoryboardGenerateV2Request",
    "StoryboardSlide",
    "StoryboardGenerateV2Response",
    "ConceptGenerateRequest",
    "ConceptGenerateResponse",
]
