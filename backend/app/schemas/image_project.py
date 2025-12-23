"""
ImageProject Schemas for the AI Video Marketing Platform.

Defines Pydantic models for ImageProject CRUD operations.
Supports step-by-step and bulk generation modes with reference image system.
"""

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


# ========== Generated Image Schemas ==========

class GeneratedImageBase(BaseModel):
    """Base schema for generated image."""
    slide_number: int = Field(default=1, ge=1)
    variant_index: int = Field(default=0, ge=0, le=3)
    image_url: str
    prompt: Optional[str] = None
    is_selected: bool = False
    approval_status: str = Field(default="pending", pattern=r"^(pending|approved|rejected)$")
    is_reference_image: bool = False
    generation_provider: Optional[str] = None
    generation_duration_ms: Optional[int] = None


class GeneratedImageCreate(GeneratedImageBase):
    """Schema for creating a generated image."""
    pass


class GeneratedImageResponse(GeneratedImageBase):
    """Schema for generated image response."""
    id: str
    image_project_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Image Project Schemas ==========

class ImageProjectCreate(BaseModel):
    """Schema for creating an image project."""
    title: Optional[str] = Field(None, max_length=255)
    content_type: str = Field(..., pattern=r"^(single|carousel|story)$")
    purpose: str = Field(..., pattern=r"^(ad|info|lifestyle)$")
    method: str = Field(..., pattern=r"^(reference|prompt)$")
    generation_mode: str = Field(default="bulk", pattern=r"^(step_by_step|bulk)$")
    brand_id: Optional[str] = None
    product_id: Optional[str] = None
    reference_analysis_id: Optional[str] = None
    storyboard_data: Optional[dict] = None
    prompt: Optional[str] = None
    aspect_ratio: str = Field(default="1:1", pattern=r"^\d+:\d+$")


class ImageProjectUpdate(BaseModel):
    """Schema for updating an image project."""
    title: Optional[str] = Field(None, max_length=255)
    storyboard_data: Optional[dict] = None
    prompt: Optional[str] = None
    status: Optional[str] = None
    current_step: Optional[int] = None
    current_slide: Optional[int] = None
    generation_mode: Optional[str] = Field(None, pattern=r"^(step_by_step|bulk)$")
    reference_image_id: Optional[str] = None
    error_message: Optional[str] = None


class ImageProjectResponse(BaseModel):
    """Schema for image project response."""
    id: str
    title: str
    content_type: str
    purpose: str
    method: str
    generation_mode: str = "bulk"
    reference_image_id: Optional[str] = None
    brand_id: Optional[str] = None
    product_id: Optional[str] = None
    reference_analysis_id: Optional[str] = None
    storyboard_data: Optional[dict] = None
    prompt: Optional[str] = None
    aspect_ratio: str
    status: str
    current_step: int
    current_slide: int = 1
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    generated_images: List[GeneratedImageResponse] = []

    class Config:
        from_attributes = True


class ImageProjectSummary(BaseModel):
    """Schema for image project list item."""
    id: str
    title: str
    content_type: str
    purpose: str
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Image Generation Request Schemas ==========

class GenerateImagesRequest(BaseModel):
    """Schema for requesting image generation."""
    slide_number: int = Field(default=1, ge=1)
    prompt: str = Field(..., min_length=1)
    num_variants: int = Field(default=4, ge=1, le=4)
    aspect_ratio: Optional[str] = Field(default="1:1", pattern=r"^\d+:\d+$")


class GenerateImagesResponse(BaseModel):
    """Schema for image generation response."""
    project_id: str
    slide_number: int
    images: List[GeneratedImageResponse]
    generation_time_ms: int


class SelectImageRequest(BaseModel):
    """Schema for selecting an image variant."""
    slide_number: int = Field(..., ge=1)
    variant_index: int = Field(..., ge=0, le=3)


# ========== Step-by-Step Generation Schemas ==========

class GenerateSingleRequest(BaseModel):
    """Schema for generating a single scene (step-by-step mode)."""
    slide_number: int = Field(default=1, ge=1)
    prompt: str = Field(..., min_length=1)
    num_variants: int = Field(default=2, ge=1, le=4)
    aspect_ratio: Optional[str] = Field(default="1:1", pattern=r"^\d+:\d+$")
    use_reference_image: bool = Field(default=True)


class GenerateSingleResponse(BaseModel):
    """Schema for single scene generation response."""
    project_id: str
    slide_number: int
    images: List[GeneratedImageResponse]
    generation_time_ms: int
    reference_image_used: bool = False
    is_first_slide: bool = False


class ApproveImageRequest(BaseModel):
    """Schema for approving an image (step-by-step mode)."""
    set_as_reference: bool = Field(default=True)


class ApproveImageResponse(BaseModel):
    """Schema for image approval response."""
    image_id: str
    approval_status: str
    is_reference_image: bool
    next_slide_number: Optional[int] = None
    all_slides_complete: bool = False


class RegenerateImageRequest(BaseModel):
    """Schema for regenerating a single image."""
    prompt: Optional[str] = None
    use_reference_image: bool = Field(default=True)
    num_variants: int = Field(default=1, ge=1, le=4)


class RegenerateImageResponse(BaseModel):
    """Schema for image regeneration response."""
    slide_number: int
    new_images: List[GeneratedImageResponse]
    generation_time_ms: int
    reference_image_used: bool = False


class SetReferenceImageRequest(BaseModel):
    """Schema for setting reference image."""
    image_id: str


class SetReferenceImageResponse(BaseModel):
    """Schema for set reference image response."""
    project_id: str
    reference_image_id: str
    previous_reference_id: Optional[str] = None


# ========== Simplified Step-by-Step Workflow Schemas ==========

class GenerateSingleSectionRequest(BaseModel):
    """Schema for generating images for a single section/slide."""
    slide_number: int = Field(..., ge=1, description="Slide number to generate images for")
    use_reference: bool = Field(default=True, description="Whether to use reference image for style consistency")


class GenerateSingleSectionResponse(BaseModel):
    """Schema for single section generation response."""
    project_id: str
    slide_number: int
    images: List[GeneratedImageResponse]
    generation_time_ms: int
    reference_image_used: bool = False


class RegenerateRequest(BaseModel):
    """Schema for regenerating images for a slide."""
    slide_number: int = Field(..., ge=1, description="Slide number to regenerate")


class RegenerateSectionResponse(BaseModel):
    """Schema for section regeneration response."""
    project_id: str
    slide_number: int
    deleted_count: int
    new_images: List[GeneratedImageResponse]
    generation_time_ms: int
    reference_image_used: bool = False


__all__ = [
    "GeneratedImageBase",
    "GeneratedImageCreate",
    "GeneratedImageResponse",
    "ImageProjectCreate",
    "ImageProjectUpdate",
    "ImageProjectResponse",
    "ImageProjectSummary",
    "GenerateImagesRequest",
    "GenerateImagesResponse",
    "SelectImageRequest",
    "GenerateSingleRequest",
    "GenerateSingleResponse",
    "ApproveImageRequest",
    "ApproveImageResponse",
    "RegenerateImageRequest",
    "RegenerateImageResponse",
    "SetReferenceImageRequest",
    "SetReferenceImageResponse",
    "GenerateSingleSectionRequest",
    "GenerateSingleSectionResponse",
    "RegenerateRequest",
    "RegenerateSectionResponse",
]
