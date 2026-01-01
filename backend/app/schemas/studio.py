"""
Pydantic schemas for Video Studio API.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ========== Video Project Schemas ==========

class VideoProjectCreate(BaseModel):
    """Schema for creating a new video project."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    brand_id: str = Field(..., min_length=36, max_length=36)
    product_id: str = Field(..., min_length=36, max_length=36)
    reference_analysis_id: Optional[str] = Field(None, min_length=36, max_length=36)
    target_duration: Optional[int] = Field(None, ge=5, le=300)
    aspect_ratio: str = Field(default="16:9", pattern=r"^\d+:\d+$")


class VideoProjectUpdate(BaseModel):
    """Schema for updating a video project."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    current_step: Optional[int] = Field(None, ge=1, le=5)
    script: Optional[dict] = None
    storyboard: Optional[dict] = None
    target_duration: Optional[int] = Field(None, ge=5, le=300)
    aspect_ratio: Optional[str] = Field(None, pattern=r"^\d+:\d+$")
    video_provider: Optional[str] = None
    image_provider: Optional[str] = None


class SceneImageResponse(BaseModel):
    """Schema for scene image response."""
    id: str
    scene_number: int
    source: str
    image_url: str
    thumbnail_url: Optional[str] = None
    scene_segment_type: Optional[str] = None
    scene_description: Optional[str] = None
    duration_seconds: Optional[float] = None
    version: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VideoProjectResponse(BaseModel):
    """Schema for video project response."""
    id: str
    title: str
    description: Optional[str] = None
    brand_id: str
    product_id: str
    reference_analysis_id: Optional[str] = None
    status: str
    current_step: int
    script: Optional[dict] = None
    storyboard: Optional[dict] = None
    target_duration: Optional[int] = None
    aspect_ratio: str
    video_provider: Optional[str] = None
    image_provider: Optional[str] = None
    output_video_url: Optional[str] = None
    output_thumbnail_url: Optional[str] = None
    output_duration: Optional[float] = None
    error_message: Optional[str] = None
    scene_images: List[SceneImageResponse] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VideoProjectSummary(BaseModel):
    """Schema for video project list item."""
    id: str
    title: str
    status: str
    current_step: int
    brand_id: str
    product_id: str
    output_thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Scene Image Schemas ==========

class SceneImageCreate(BaseModel):
    """Schema for creating a scene image (upload)."""
    scene_number: int = Field(..., ge=0)
    scene_segment_type: Optional[str] = None
    scene_description: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0.1, le=60)


class SceneImageGenerate(BaseModel):
    """Schema for AI image generation request."""
    scene_number: int = Field(..., ge=0)
    prompt: Optional[str] = None
    scene_segment_type: Optional[str] = None
    scene_description: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0.1, le=60)
    provider: str = Field(default="mock", pattern=r"^(mock|gemini_imagen|dalle|midjourney)$")


class SceneImageUpdate(BaseModel):
    """Schema for updating scene image."""
    scene_description: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0.1, le=60)
    is_active: Optional[bool] = None


# ========== Storyboard Schemas ==========

class SceneSchema(BaseModel):
    """Schema for a single scene in storyboard."""
    scene_number: int
    scene_type: str = Field(..., pattern=r"^(hook|problem|solution|benefit|cta|transition|intro|outro)$")
    title: str
    description: str  # Image generation description
    narration_script: Optional[str] = None
    visual_direction: Optional[str] = None
    background_music_suggestion: Optional[str] = None
    transition_effect: Optional[str] = Field(default="cut", pattern=r"^(cut|fade|fade_in|fade_out|zoom|slide|dissolve)$")
    subtitle_text: Optional[str] = None
    duration_seconds: float = Field(default=3.0, ge=0.5, le=30)
    generated_image_id: Optional[str] = None


class StoryboardGenerateRequest(BaseModel):
    """Request to generate storyboard."""
    mode: str = Field(..., pattern=r"^(reference_structure|ai_optimized)$")
    # Creative input fields from Step 3
    concept: Optional[str] = None
    target_duration: Optional[int] = Field(None, ge=5, le=180)  # seconds
    mood: Optional[str] = None
    style: Optional[str] = None
    additional_notes: Optional[str] = None


class StoryboardResponse(BaseModel):
    """Schema for storyboard response."""
    id: str
    video_project_id: str
    generation_mode: str
    source_reference_analysis_id: Optional[str] = None
    scenes: List[SceneSchema]
    total_duration_seconds: Optional[float] = None
    version: int
    is_active: bool
    previous_version_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SceneUpdateRequest(BaseModel):
    """Request to update a scene."""
    title: Optional[str] = None
    description: Optional[str] = None
    narration_script: Optional[str] = None
    visual_direction: Optional[str] = None
    background_music_suggestion: Optional[str] = None
    transition_effect: Optional[str] = Field(None, pattern=r"^(cut|fade|fade_in|fade_out|zoom|slide|dissolve)$")
    subtitle_text: Optional[str] = None
    duration_seconds: Optional[float] = Field(None, ge=0.5, le=30)


class SceneCreateRequest(BaseModel):
    """Request to add a new scene."""
    scene_type: str = Field(..., pattern=r"^(hook|problem|solution|benefit|cta|transition|intro|outro)$")
    title: str
    description: str
    insert_after: Optional[int] = None  # scene_number to insert after, None = append at end
    narration_script: Optional[str] = None
    visual_direction: Optional[str] = None
    background_music_suggestion: Optional[str] = None
    transition_effect: Optional[str] = Field(default="cut")
    subtitle_text: Optional[str] = None
    duration_seconds: float = Field(default=3.0, ge=0.5, le=30)


class ScenesReorderRequest(BaseModel):
    """Request to reorder scenes."""
    scene_order: List[int]  # List of scene_numbers in new order


# ========== Marketing Image Production Schemas ==========


class ImageAnalysis(BaseModel):
    """Analysis result for a single image."""
    description: str
    detected_type: str
    elements: List[str] = []
    visual_prompt: Optional[str] = None  # Detailed visual description for AI image generation


class MarketingImageInput(BaseModel):
    """Input image data for marketing image generation."""
    temp_url: str
    analysis: Optional[ImageAnalysis] = None


class MarketingImageGenerateRequest(BaseModel):
    """Request to generate a marketing image."""
    images: List[MarketingImageInput] = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    aspect_ratio: Optional[str] = Field(default="1:1", pattern=r"^\d+:\d+$")


class ProductImageEditRequest(BaseModel):
    """Request to edit/generate an image while preserving product appearance.

    This uses Gemini's multimodal capabilities to create new images
    that maintain the exact visual appearance of the input product image.
    """
    product_image_temp_id: Optional[str] = Field(None, description="Temp ID of the uploaded product image (legacy, use image_temp_ids)")
    image_temp_ids: Optional[List[str]] = Field(None, description="List of all image temp IDs to use")
    prompt: str = Field(..., min_length=1, description="Description of desired scene/context")
    aspect_ratio: Optional[str] = Field(default="16:9", pattern=r"^\d+:\d+$")
    product_description: Optional[str] = Field(None, description="Optional text description of the product")
    background_image_temp_id: Optional[str] = Field(None, description="Optional background image temp ID")


class ProductSceneComposeRequest(BaseModel):
    """Request to compose a scene with product on background.

    More advanced composition that places a product onto a specific background.
    """
    product_image_temp_id: str = Field(..., description="Temp ID of the product image")
    background_image_temp_id: Optional[str] = Field(None, description="Temp ID of background image (optional)")
    scene_prompt: str = Field(..., min_length=1, description="How to compose the scene")
    aspect_ratio: Optional[str] = Field(default="16:9", pattern=r"^\d+:\d+$")
    product_description: Optional[str] = Field(None, description="Optional text description of the product")


# ========== Prompt Enhancement Schemas ==========


class ImageContext(BaseModel):
    """Context information for an uploaded image."""
    temp_id: str = Field(..., description="Temp ID of the uploaded image")
    detected_type: str = Field(..., description="Detected type: product, background, reference, person")
    is_realistic: bool = Field(default=True, description="Whether the image is realistic (photo) or illustration")
    description: Optional[str] = Field(None, description="AI-generated description of the image")
    visual_prompt: Optional[str] = Field(None, description="Visual prompt extracted from image analysis")


class PromptEnhanceRequest(BaseModel):
    """Request to enhance a user prompt for image generation.

    Takes a simple user prompt and image context, then returns
    a detailed, optimized prompt for Gemini image generation.
    """
    user_prompt: str = Field(..., min_length=1, description="User's original simple prompt")
    images: List[ImageContext] = Field(default_factory=list, description="List of uploaded image contexts")
    aspect_ratio: Optional[str] = Field(default="1:1", pattern=r"^\d+:\d+$", description="Target aspect ratio")
    language: Optional[str] = Field(default="ko", description="Output language code (ko, en, ja, zh)")


class PromptEnhanceResponse(BaseModel):
    """Response containing the enhanced prompt."""
    original_prompt: str = Field(..., description="The original user prompt")
    enhanced_prompt: str = Field(..., description="Enhanced prompt optimized for AI image generation (English)")
    enhanced_prompt_display: str = Field(..., description="Enhanced prompt in user's language for display")
    composition_suggestion: Optional[str] = Field(None, description="Suggested composition based on image types")
    detected_intent: Optional[str] = Field(None, description="Detected user intent: composite, edit, style_transfer, generate")


# ========== Per-Scene Video Generation Schemas ==========


class SceneVideoStatus(BaseModel):
    """Response schema for individual scene video status."""
    scene_number: int = Field(..., description="The scene number this video belongs to")
    status: str = Field(..., description="Video generation status: pending, processing, completed, failed")
    video_url: Optional[str] = Field(None, description="URL of the generated video when completed")
    thumbnail_url: Optional[str] = Field(None, description="URL of the video thumbnail")
    duration_seconds: Optional[float] = Field(None, description="Duration of the generated video in seconds")
    operation_id: Optional[str] = Field(None, description="Provider operation ID for tracking async generation")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    scene_segment_type: Optional[str] = Field(None, description="Type of scene segment (hook, problem, solution, etc.)")


class SceneVideoResponse(BaseModel):
    """Full response for scene video data."""
    id: str = Field(..., description="Unique identifier for the scene video")
    scene_number: int = Field(..., description="The scene number this video belongs to")
    source: str = Field(..., description="Source of the video: ai_generated, uploaded, stock")
    video_url: Optional[str] = Field(None, description="URL of the video file")
    thumbnail_url: Optional[str] = Field(None, description="URL of the video thumbnail")
    generation_prompt: Optional[str] = Field(None, description="Prompt used for AI video generation")
    scene_segment_type: Optional[str] = Field(None, description="Type of scene segment (hook, problem, solution, etc.)")
    duration_seconds: Optional[float] = Field(None, description="Duration of the video in seconds")
    status: str = Field(..., description="Video status: pending, processing, completed, failed")
    operation_id: Optional[str] = Field(None, description="Provider operation ID for tracking async generation")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    version: int = Field(..., description="Version number for tracking regenerations")
    is_active: bool = Field(..., description="Whether this is the active version for the scene")
    created_at: datetime = Field(..., description="Timestamp when the video record was created")
    updated_at: Optional[datetime] = Field(None, description="Timestamp when the video record was last updated")

    model_config = {"from_attributes": True}


class VideoGenerationStatusResponse(BaseModel):
    """Response for video generation status."""
    status: str = Field(..., description="Overall video generation status: pending, processing, completed, failed")
    video_url: Optional[str] = Field(None, description="URL of the final generated video")
    operation_id: Optional[str] = Field(None, description="Provider operation ID for tracking")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")
    generation_time_ms: Optional[int] = Field(None, description="Time taken for generation in milliseconds")


class ExtendedVideoGenerationStatusResponse(VideoGenerationStatusResponse):
    """Extended status response with per-scene video details.

    Inherits all fields from VideoGenerationStatusResponse and adds
    per-scene tracking and concatenation status.
    """
    scene_videos: List[SceneVideoStatus] = Field(
        default_factory=list,
        description="Status of each individual scene video"
    )
    concatenation_status: Optional[str] = Field(
        None,
        description="Status of video concatenation: pending, processing, completed, failed, or null if not started"
    )
    final_video_url: Optional[str] = Field(
        None,
        description="URL of the final concatenated video"
    )


class SceneVideoGenerateRequest(BaseModel):
    """Request to generate video for a single scene."""
    scene_number: int = Field(..., ge=0, description="The scene number to generate video for")
    provider: Optional[str] = Field(
        default="veo",
        pattern=r"^(veo|mock|runway|pika)$",
        description="Video generation provider to use"
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        pattern=r"^\d+:\d+$",
        description="Aspect ratio for the generated video"
    )


class VideoConcatenateRequest(BaseModel):
    """Request to concatenate scene videos into final output."""
    include_transitions: Optional[bool] = Field(
        default=True,
        description="Whether to include transitions between scenes"
    )
    transition_duration_ms: Optional[int] = Field(
        default=500,
        ge=0,
        le=2000,
        description="Duration of transitions in milliseconds"
    )


# ========== Scene Extension Video Generation Schemas ==========


class ExtendedVideoGenerationRequest(BaseModel):
    """Request schema for Scene Extension video generation.

    This endpoint generates a single continuous video using Veo's Scene Extension
    feature, which extends an initial video by iteratively adding 7-second segments
    until the target duration is reached.
    """
    target_duration_seconds: Optional[int] = Field(
        default=None,
        ge=8,
        le=148,
        description="Target duration for the final video in seconds. Max 148 seconds (8 initial + 20 hops x 7 seconds). If not provided, calculates from total scene durations."
    )
    aspect_ratio: Optional[str] = Field(
        default="16:9",
        pattern=r"^(16:9|9:16)$",
        description="Video aspect ratio. Only 16:9 or 9:16 supported for Scene Extension."
    )
    provider: Optional[str] = Field(
        default="veo",
        pattern=r"^(veo|mock)$",
        description="Video generation provider to use. Only 'veo' and 'mock' support Scene Extension."
    )


class ExtendedVideoGenerationResponse(BaseModel):
    """Response schema for Scene Extension video generation.

    Returns the status and details of a Scene Extension video generation,
    including information about extension hops and the final video.
    """
    status: str = Field(
        ...,
        description="Generation status: pending, processing, completed, failed, partial"
    )
    video_url: Optional[str] = Field(
        None,
        description="URL of the final extended video when completed"
    )
    initial_duration_seconds: Optional[float] = Field(
        None,
        description="Duration of the initial generated video (typically 8 seconds)"
    )
    final_duration_seconds: Optional[float] = Field(
        None,
        description="Total duration of the final extended video"
    )
    extension_hops_completed: int = Field(
        default=0,
        description="Number of successful extension hops completed"
    )
    scenes_processed: int = Field(
        default=0,
        description="Number of scenes from storyboard processed for prompts"
    )
    generation_time_ms: Optional[int] = Field(
        None,
        description="Total time taken for generation in milliseconds"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if generation failed or partially failed"
    )


__all__ = [
    "VideoProjectCreate",
    "VideoProjectUpdate",
    "VideoProjectResponse",
    "VideoProjectSummary",
    "SceneImageCreate",
    "SceneImageGenerate",
    "SceneImageUpdate",
    "SceneImageResponse",
    "SceneSchema",
    "StoryboardGenerateRequest",
    "StoryboardResponse",
    "SceneUpdateRequest",
    "SceneCreateRequest",
    "ScenesReorderRequest",
    "ImageAnalysis",
    "MarketingImageInput",
    "MarketingImageGenerateRequest",
    "ProductImageEditRequest",
    "ProductSceneComposeRequest",
    # Prompt Enhancement Schemas
    "ImageContext",
    "PromptEnhanceRequest",
    "PromptEnhanceResponse",
    # Per-Scene Video Generation Schemas
    "SceneVideoStatus",
    "SceneVideoResponse",
    "VideoGenerationStatusResponse",
    "ExtendedVideoGenerationStatusResponse",
    "SceneVideoGenerateRequest",
    "VideoConcatenateRequest",
    # Scene Extension Video Generation Schemas
    "ExtendedVideoGenerationRequest",
    "ExtendedVideoGenerationResponse",
]
