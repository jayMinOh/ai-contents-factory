"""
AI Video Generation Service using Google Veo API.

Supports multiple providers:
- veo: Google Veo (text-to-video, image-to-video)
- mock: Mock provider for testing
"""

import base64
import logging
import os
import time
import traceback
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.config import settings

# Video output directory
VIDEO_OUTPUT_DIR = Path(settings.UPLOAD_DIR) / "videos"
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


@dataclass
class SceneVideoResult:
    """Result for a single scene video generation."""
    scene_number: int
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    operation_id: Optional[str] = None
    error_message: Optional[str] = None
    generation_time_ms: Optional[int] = None
    prompt_used: Optional[str] = None


@dataclass
class ExtensionHopResult:
    """Result for a single video extension hop."""
    hop_number: int
    status: str  # pending, processing, completed, failed
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    duration_added_seconds: float = 7.0  # Each hop adds 7 seconds
    total_duration_seconds: Optional[float] = None
    prompt_used: Optional[str] = None
    error_message: Optional[str] = None
    generation_time_ms: Optional[int] = None


@dataclass
class ExtendedVideoResult:
    """Result of video extension operation."""
    status: str = "completed"  # pending, processing, completed, failed, partial
    video_url: Optional[str] = None
    video_path: Optional[str] = None
    initial_duration_seconds: float = 0.0
    final_duration_seconds: float = 0.0
    extension_hops_completed: int = 0
    extension_hops_requested: int = 0
    hop_results: Optional[List["ExtensionHopResult"]] = None
    generation_time_ms: int = 0
    error_message: Optional[str] = None
    scenes_processed: int = 0


@dataclass
class VideoGenerationResult:
    """Result of video generation."""
    video_url: Optional[str] = None
    video_data: Optional[str] = None  # Base64 encoded video data
    mime_type: str = "video/mp4"
    duration_seconds: float = 0
    generation_time_ms: int = 0
    operation_id: Optional[str] = None
    status: str = "completed"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    scene_results: Optional[List["SceneVideoResult"]] = None  # Per-scene results


@dataclass
class SceneInput:
    """
    Input for a single scene in video generation.

    This dataclass captures all storyboard metadata required for generating
    a scene within a marketing video, including visual direction, narration,
    and transition effects.

    Attributes:
        scene_number: Sequential identifier for the scene (1-based indexing).
        description: Visual description of what the scene should depict.
        duration_seconds: Length of the scene in seconds.
        image_url: Optional URL to a reference image for the scene.
        image_data: Optional Base64 encoded image data for image-to-video generation.
        scene_type: Marketing strategy type for the scene. Valid values include
            'hook' (attention grabber), 'problem' (pain point identification),
            'solution' (product/service introduction), 'benefit' (value proposition),
            and 'cta' (call to action).
        narration_script: Text content for voiceover narration, used for pacing
            guidance and audio synchronization.
        visual_direction: Cinematography and visual style guidance including
            camera movements, angles, lighting, and composition instructions.
        transition_effect: Effect to use when transitioning to the next scene.
            Common values: 'cut', 'fade', 'dissolve', 'zoom', 'slide'.
        background_music_suggestion: Audio context or mood suggestion for
            background music selection (e.g., 'upbeat', 'dramatic', 'calm').
        subtitle_text: Overlay text to display on screen during the scene,
            such as key messages or captions.
        title: Scene title for identification and organization purposes.
    """
    scene_number: int
    description: str
    duration_seconds: float
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    scene_type: Optional[str] = None
    narration_script: Optional[str] = None
    visual_direction: Optional[str] = None
    transition_effect: Optional[str] = None
    background_music_suggestion: Optional[str] = None
    subtitle_text: Optional[str] = None
    title: Optional[str] = None


class VideoGeneratorBase(ABC):
    """Base class for video generators."""

    @abstractmethod
    async def generate_from_prompt(
        self,
        prompt: str,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        """
        Generate a video from a text prompt.

        Args:
            prompt: Text description of the video to generate
            duration_seconds: Duration of the video (5-8 seconds typically)
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)

        Returns:
            VideoGenerationResult with video URL or data
        """
        pass

    @abstractmethod
    async def generate_from_image(
        self,
        image_data: str,
        prompt: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        """
        Generate a video from an image (image-to-video).

        Args:
            image_data: Base64 encoded image data
            prompt: Optional text prompt to guide the animation
            duration_seconds: Duration of the video
            aspect_ratio: Video aspect ratio

        Returns:
            VideoGenerationResult with video URL or data
        """
        pass

    @abstractmethod
    async def generate_marketing_video(
        self,
        scenes: List[SceneInput],
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        """
        Generate a marketing video from multiple scenes.

        Args:
            scenes: List of scene inputs with descriptions and images
            aspect_ratio: Video aspect ratio

        Returns:
            VideoGenerationResult with combined video
        """
        pass

    @abstractmethod
    async def check_generation_status(
        self,
        operation_id: str,
    ) -> VideoGenerationResult:
        """
        Check the status of a video generation operation.

        Args:
            operation_id: The operation ID from initial generation call

        Returns:
            VideoGenerationResult with current status
        """
        pass

    @abstractmethod
    async def generate_per_scene_videos(
        self,
        scenes: List[SceneInput],
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
        delay_between_scenes: int = 30,
    ) -> VideoGenerationResult:
        """
        Generate individual videos for each scene.

        Unlike generate_marketing_video which creates a single video,
        this method generates separate videos for each scene that can
        later be concatenated.

        Args:
            scenes: List of scene inputs with descriptions and images
            brand_context: Optional brand context for prompt building
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
            delay_between_scenes: Delay in seconds between scene generations to avoid rate limits (default: 30)

        Returns:
            VideoGenerationResult with scene_results populated
        """
        pass

    @abstractmethod
    async def extend_video(
        self,
        video_path: str,
        extension_prompt: str,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Extend an existing video by 7 seconds using Scene Extension.

        Uses the Veo API to extend a video by adding 7 seconds based on
        the extension prompt. The last second of the input video is used
        as context for seamless continuation.

        Args:
            video_path: Local file path to the video to extend
            extension_prompt: Text prompt describing the continuation
            aspect_ratio: Video aspect ratio (16:9 or 9:16, must match input)

        Returns:
            ExtendedVideoResult with the extended video

        Constraints:
            - Input video must be Veo-generated
            - Maximum input video length: 141 seconds
            - Extension adds exactly 7 seconds per hop
            - Resolution limited to 720p for extension
        """
        pass

    @abstractmethod
    async def generate_extended_video(
        self,
        scenes: List[SceneInput],
        target_duration_seconds: int,
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Generate a long video by combining initial generation with scene extensions.

        This method generates an initial video from the first scene (up to 8 seconds),
        then uses Scene Extension to extend the video with subsequent scene prompts
        until the target duration is reached or all scenes are processed.

        Args:
            scenes: List of scene inputs with descriptions
            target_duration_seconds: Target duration for the final video (max 148 seconds)
            brand_context: Optional brand context for prompt building
            aspect_ratio: Video aspect ratio (16:9 or 9:16)

        Returns:
            ExtendedVideoResult with the final extended video

        Extension Process:
            1. Generate initial 8-second video from first scene
            2. For each subsequent scene, extend by 7 seconds
            3. Continue until target duration reached or scenes exhausted
            4. Maximum 20 extension hops (148 seconds total)
        """
        pass


class GeminiVeoGenerator(VideoGeneratorBase):
    """
    Video generator using Google Veo API.

    Uses Veo 3.1 for high-quality video generation.
    Supports text-to-video and image-to-video.
    """

    # Supported aspect ratios
    SUPPORTED_ASPECT_RATIOS = ["16:9", "9:16", "1:1"]

    # Veo model versions
    MODEL_LATEST = "veo-3.1-generate-preview"
    MODEL_V2 = "veo-2.0-generate-001"

    def __init__(self):
        logger.info("Initializing GeminiVeoGenerator...")
        if not settings.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY is not configured")
            raise ValueError("GOOGLE_API_KEY is not configured")

        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_name = self.MODEL_LATEST
        self._pending_operations: dict[str, any] = {}
        logger.info(f"GeminiVeoGenerator initialized with model: {self.model_name}")

    async def generate_from_prompt(
        self,
        prompt: str,
        duration_seconds: int = 6,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        import asyncio

        start_time = time.time()
        logger.info(f"Starting video generation - prompt: {prompt[:100]}...")

        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Clamp duration to Veo API valid range (4-8 seconds)
        clamped_duration = max(4, min(8, int(duration_seconds)))
        logger.info(f"Duration: {duration_seconds} -> clamped to {clamped_duration}")

        def _generate():
            return self.client.models.generate_videos(
                model=self.model_name,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    duration_seconds=clamped_duration,
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                ),
            )

        try:
            operation = await asyncio.to_thread(_generate)
            operation_id = str(uuid.uuid4())
            self._pending_operations[operation_id] = operation

            logger.info(f"Video generation started, operation_id: {operation_id}")

            # Poll for completion (with timeout)
            max_wait_seconds = 300  # 5 minutes
            poll_interval = 10  # 10 seconds
            elapsed = 0

            while not operation.done and elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                operation = await asyncio.to_thread(
                    lambda: self.client.operations.get(operation=operation)
                )
                logger.info(f"Polling video generation... elapsed: {elapsed}s")

            if not operation.done:
                return VideoGenerationResult(
                    operation_id=operation_id,
                    status="processing",
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

            # Get result
            if operation.result and operation.result.generated_videos:
                generated_video = operation.result.generated_videos[0]
                generation_time_ms = int((time.time() - start_time) * 1000)

                # Download and save video locally
                video_filename = f"video_{uuid.uuid4().hex[:12]}.mp4"
                video_path = VIDEO_OUTPUT_DIR / video_filename

                try:
                    # Download video using the API client
                    await asyncio.to_thread(
                        lambda: self.client.files.download(file=generated_video.video)
                    )
                    # Save to local file
                    await asyncio.to_thread(
                        lambda: generated_video.video.save(str(video_path))
                    )
                    logger.info(f"Video saved to: {video_path}")

                    # Return full URL (will be served by static files)
                    local_video_url = f"http://localhost:8000/uploads/videos/{video_filename}"

                    return VideoGenerationResult(
                        video_url=local_video_url,
                        mime_type="video/mp4",
                        generation_time_ms=generation_time_ms,
                        status="completed",
                    )
                except Exception as download_error:
                    logger.error(f"Failed to download video: {download_error}")
                    # Fallback to GCS URI if download fails
                    video = generated_video.video
                    return VideoGenerationResult(
                        video_url=video.uri if hasattr(video, 'uri') else None,
                        mime_type="video/mp4",
                        generation_time_ms=generation_time_ms,
                        status="completed",
                    )
            else:
                return VideoGenerationResult(
                    status="failed",
                    error_message="No video generated",
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

        except Exception as e:
            logger.error(f"Video generation failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return VideoGenerationResult(
                status="failed",
                error_message=str(e),
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

    async def generate_from_image(
        self,
        image_data: str,
        prompt: Optional[str] = None,
        duration_seconds: int = 6,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        import asyncio

        start_time = time.time()
        logger.info(f"Starting image-to-video generation...")

        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            aspect_ratio = "16:9"

        # Clamp duration to Veo API valid range (4-8 seconds)
        clamped_duration = max(4, min(8, int(duration_seconds)))
        logger.info(f"Duration: {duration_seconds} -> clamped to {clamped_duration}")

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        def _generate():
            return self.client.models.generate_videos(
                model=self.model_name,
                prompt=prompt,
                image=types.Image(
                    image_bytes=image_bytes,
                    mime_type="image/png",
                ),
                config=types.GenerateVideosConfig(
                    duration_seconds=clamped_duration,
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                ),
            )

        try:
            operation = await asyncio.to_thread(_generate)
            operation_id = str(uuid.uuid4())
            self._pending_operations[operation_id] = operation

            # Poll for completion
            max_wait_seconds = 300
            poll_interval = 10
            elapsed = 0

            while not operation.done and elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                operation = await asyncio.to_thread(
                    lambda: self.client.operations.get(operation=operation)
                )

            if not operation.done:
                return VideoGenerationResult(
                    operation_id=operation_id,
                    status="processing",
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

            if operation.result and operation.result.generated_videos:
                generated_video = operation.result.generated_videos[0]
                generation_time_ms = int((time.time() - start_time) * 1000)

                # Download and save video locally
                video_filename = f"video_{uuid.uuid4().hex[:12]}.mp4"
                video_path = VIDEO_OUTPUT_DIR / video_filename

                try:
                    await asyncio.to_thread(
                        lambda: self.client.files.download(file=generated_video.video)
                    )
                    await asyncio.to_thread(
                        lambda: generated_video.video.save(str(video_path))
                    )
                    logger.info(f"Video saved to: {video_path}")

                    local_video_url = f"http://localhost:8000/uploads/videos/{video_filename}"
                    return VideoGenerationResult(
                        video_url=local_video_url,
                        mime_type="video/mp4",
                        generation_time_ms=generation_time_ms,
                        status="completed",
                    )
                except Exception as download_error:
                    logger.error(f"Failed to download video: {download_error}")
                    video = generated_video.video
                    return VideoGenerationResult(
                        video_url=video.uri if hasattr(video, 'uri') else None,
                        mime_type="video/mp4",
                        generation_time_ms=generation_time_ms,
                        status="completed",
                    )
            else:
                # Log detailed error info from operation
                error_msg = "No video generated"

                # Check for RAI (Responsible AI) filtered reasons
                if hasattr(operation, 'result') and operation.result:
                    result = operation.result
                    logger.error(f"Operation result: {result}")

                    # Extract RAI filter reasons if available
                    if hasattr(result, 'rai_media_filtered_reasons') and result.rai_media_filtered_reasons:
                        reasons = result.rai_media_filtered_reasons
                        error_msg = reasons[0] if reasons else "Content filtered by Veo API"
                        logger.error(f"RAI filter reasons: {reasons}")
                else:
                    logger.error(f"Operation has no result. Done: {operation.done}")

                if hasattr(operation, 'error') and operation.error:
                    error_msg = f"Veo API error: {operation.error}"
                    logger.error(f"Veo API returned error: {operation.error}")

                return VideoGenerationResult(
                    status="failed",
                    error_message=error_msg,
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

        except Exception as e:
            logger.error(f"Image-to-video generation failed: {str(e)}")
            return VideoGenerationResult(
                status="failed",
                error_message=str(e),
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

    async def generate_marketing_video(
        self,
        scenes: List[SceneInput],
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        """
        Generate a marketing video by combining multiple scene generations.

        For MVP: Generate video for each scene separately and return the first one.
        Future: Implement proper video concatenation.
        """
        import asyncio

        start_time = time.time()
        logger.info(f"Starting marketing video generation with {len(scenes)} scenes")

        if not scenes:
            return VideoGenerationResult(
                status="failed",
                error_message="No scenes provided",
            )

        # For MVP, generate based on first scene with image
        scene_with_image = next((s for s in scenes if s.image_data or s.image_url), None)

        if scene_with_image and scene_with_image.image_data:
            # Image-to-video for the main scene
            combined_prompt = " ".join([s.description for s in scenes[:3]])
            return await self.generate_from_image(
                image_data=scene_with_image.image_data,
                prompt=combined_prompt,
                duration_seconds=min(8, sum(s.duration_seconds for s in scenes)),
                aspect_ratio=aspect_ratio,
            )
        else:
            # Text-to-video with combined prompts
            combined_prompt = "Marketing video: " + " Then, ".join([
                f"Scene {s.scene_number}: {s.description}"
                for s in scenes[:5]
            ])
            return await self.generate_from_prompt(
                prompt=combined_prompt,
                duration_seconds=min(8, sum(s.duration_seconds for s in scenes)),
                aspect_ratio=aspect_ratio,
            )

    async def check_generation_status(
        self,
        operation_id: str,
    ) -> VideoGenerationResult:
        """Check status of a pending video generation."""
        import asyncio

        if operation_id not in self._pending_operations:
            return VideoGenerationResult(
                operation_id=operation_id,
                status="failed",
                error_message="Operation not found",
            )

        operation = self._pending_operations[operation_id]

        try:
            operation = await asyncio.to_thread(
                lambda: self.client.operations.get(operation=operation)
            )
            self._pending_operations[operation_id] = operation

            if operation.done:
                if operation.result and operation.result.generated_videos:
                    generated_video = operation.result.generated_videos[0]
                    del self._pending_operations[operation_id]

                    # Download and save video locally
                    video_filename = f"video_{uuid.uuid4().hex[:12]}.mp4"
                    video_path = VIDEO_OUTPUT_DIR / video_filename

                    try:
                        await asyncio.to_thread(
                            lambda: self.client.files.download(file=generated_video.video)
                        )
                        await asyncio.to_thread(
                            lambda: generated_video.video.save(str(video_path))
                        )
                        logger.info(f"Video saved to: {video_path}")

                        local_video_url = f"http://localhost:8000/uploads/videos/{video_filename}"
                        return VideoGenerationResult(
                            video_url=local_video_url,
                            mime_type="video/mp4",
                            status="completed",
                        )
                    except Exception as download_error:
                        logger.error(f"Failed to download video: {download_error}")
                        video = generated_video.video
                        return VideoGenerationResult(
                            video_url=video.uri if hasattr(video, 'uri') else None,
                            mime_type="video/mp4",
                            status="completed",
                        )
                else:
                    del self._pending_operations[operation_id]
                    return VideoGenerationResult(
                        status="failed",
                        error_message="No video in result",
                    )
            else:
                return VideoGenerationResult(
                    operation_id=operation_id,
                    status="processing",
                )

        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return VideoGenerationResult(
                operation_id=operation_id,
                status="failed",
                error_message=str(e),
            )

    async def generate_per_scene_videos(
        self,
        scenes: List[SceneInput],
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
        delay_between_scenes: int = 30,  # Delay in seconds to avoid rate limits
    ) -> VideoGenerationResult:
        """
        Generate individual videos for each scene.

        Unlike generate_marketing_video which creates a single video,
        this method generates separate videos for each scene that can
        later be concatenated.

        Args:
            scenes: List of scene inputs with descriptions and images
            brand_context: Optional brand context for prompt building
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
            delay_between_scenes: Delay in seconds between scene generations to avoid rate limits (default: 30)

        Returns:
            VideoGenerationResult with scene_results populated
        """
        # Import prompt builder here to avoid circular import
        from .prompt_builder import create_prompt_builder

        start_time = time.time()
        logger.info(f"Starting per-scene video generation for {len(scenes)} scenes")

        if not scenes:
            return VideoGenerationResult(
                status="failed",
                error_message="No scenes provided",
                generation_time_ms=0,
            )

        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Initialize the prompt builder for optimized prompt construction
        prompt_builder = create_prompt_builder(storyboard_priority=True)

        scene_results: List[SceneVideoResult] = []
        completed_count = 0
        failed_count = 0

        # Process scenes sequentially
        for scene in scenes:
            scene_start_time = time.time()
            logger.info(
                f"Processing scene {scene.scene_number}/{len(scenes)}: "
                f"{scene.description[:50] if scene.description else 'No description'}..."
            )

            # Build optimized prompt using VideoPromptBuilder
            prompt = prompt_builder.build_scene_prompt(
                scene=scene,
                brand_context=brand_context,
            )
            logger.info(f"Scene {scene.scene_number} prompt: {prompt[:100]}...")

            # Respect Veo 4-8 second limit per scene
            scene_duration = int(scene.duration_seconds) if scene.duration_seconds else 6
            # Clamp to valid range: 4-8 seconds (Veo API requirement)
            scene_duration = max(4, min(8, scene_duration))

            try:
                # Choose generation method based on image availability
                if scene.image_data:
                    logger.info(f"Scene {scene.scene_number}: Using image-to-video generation")
                    result = await self.generate_from_image(
                        image_data=scene.image_data,
                        prompt=prompt,
                        duration_seconds=scene_duration,
                        aspect_ratio=aspect_ratio,
                    )
                else:
                    logger.info(f"Scene {scene.scene_number}: Using text-to-video generation")
                    result = await self.generate_from_prompt(
                        prompt=prompt,
                        duration_seconds=scene_duration,
                        aspect_ratio=aspect_ratio,
                    )

                scene_generation_time = int((time.time() - scene_start_time) * 1000)

                if result.status == "completed":
                    completed_count += 1
                    scene_results.append(
                        SceneVideoResult(
                            scene_number=scene.scene_number,
                            status="completed",
                            video_url=result.video_url,
                            duration_seconds=result.duration_seconds or scene_duration,
                            generation_time_ms=scene_generation_time,
                            prompt_used=prompt,
                        )
                    )
                    logger.info(
                        f"Scene {scene.scene_number} completed successfully: {result.video_url}"
                    )
                elif result.status == "processing":
                    # Scene is still processing, track operation_id
                    scene_results.append(
                        SceneVideoResult(
                            scene_number=scene.scene_number,
                            status="processing",
                            operation_id=result.operation_id,
                            generation_time_ms=scene_generation_time,
                            prompt_used=prompt,
                        )
                    )
                    logger.info(
                        f"Scene {scene.scene_number} still processing: {result.operation_id}"
                    )
                else:
                    # Scene failed
                    failed_count += 1
                    scene_results.append(
                        SceneVideoResult(
                            scene_number=scene.scene_number,
                            status="failed",
                            error_message=result.error_message,
                            generation_time_ms=scene_generation_time,
                            prompt_used=prompt,
                        )
                    )
                    logger.error(
                        f"Scene {scene.scene_number} failed: {result.error_message}"
                    )

            except Exception as e:
                # Handle unexpected errors gracefully - don't stop other scenes
                failed_count += 1
                scene_generation_time = int((time.time() - scene_start_time) * 1000)
                error_msg = str(e)
                logger.error(
                    f"Scene {scene.scene_number} unexpected error: {error_msg}",
                    exc_info=True,
                )
                scene_results.append(
                    SceneVideoResult(
                        scene_number=scene.scene_number,
                        status="failed",
                        error_message=error_msg,
                        generation_time_ms=scene_generation_time,
                        prompt_used=prompt,
                    )
                )

            # Add delay between scenes to avoid rate limits (skip for last scene)
            if delay_between_scenes > 0 and scene != scenes[-1]:
                logger.info(f"Waiting {delay_between_scenes} seconds before next scene to avoid rate limits...")
                await asyncio.sleep(delay_between_scenes)

        # Determine overall status
        total_generation_time = int((time.time() - start_time) * 1000)

        if completed_count == len(scenes):
            overall_status = "completed"
        elif completed_count > 0:
            overall_status = "partial"
        elif any(r.status == "processing" for r in scene_results):
            overall_status = "processing"
        else:
            overall_status = "failed"

        # Calculate total duration from completed scenes
        total_duration = sum(
            r.duration_seconds or 0
            for r in scene_results
            if r.status == "completed" and r.duration_seconds
        )

        logger.info(
            f"Per-scene generation complete: {completed_count}/{len(scenes)} succeeded, "
            f"{failed_count} failed, total time: {total_generation_time}ms"
        )

        return VideoGenerationResult(
            status=overall_status,
            scene_results=scene_results,
            duration_seconds=total_duration,
            generation_time_ms=total_generation_time,
            error_message=f"{failed_count} scene(s) failed" if failed_count > 0 else None,
        )

    async def extend_video(
        self,
        video_path: str,
        extension_prompt: str,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Extend an existing video by 7 seconds using Veo Scene Extension.

        Uses the Veo API video extension capability to seamlessly extend
        a video by 7 seconds. The API uses the last second of the input
        video as context for continuation.

        Args:
            video_path: Local file path to the video to extend
            extension_prompt: Text prompt describing the continuation
            aspect_ratio: Video aspect ratio (16:9 or 9:16)

        Returns:
            ExtendedVideoResult with the extended video
        """
        import asyncio

        start_time = time.time()
        logger.info(f"Starting video extension - video: {video_path}, prompt: {extension_prompt[:100]}...")

        # Validate aspect ratio (only 16:9 and 9:16 supported for extension)
        if aspect_ratio not in ["16:9", "9:16"]:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio} for extension, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Validate video file exists
        video_file = Path(video_path)
        if not video_file.exists():
            return ExtendedVideoResult(
                status="failed",
                error_message=f"Video file not found: {video_path}",
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

        # Read video bytes
        try:
            with open(video_path, "rb") as f:
                video_bytes = f.read()
            logger.info(f"Read video file: {len(video_bytes)} bytes")
        except Exception as e:
            return ExtendedVideoResult(
                status="failed",
                error_message=f"Failed to read video file: {str(e)}",
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

        def _extend():
            # Use generate_videos with video input for extension
            # Note: Do NOT pass mime_type - SDK converts it to 'encoding' which Veo 3.1 doesn't support
            return self.client.models.generate_videos(
                model=self.model_name,
                prompt=extension_prompt,
                video=types.Video(
                    video_bytes=video_bytes,
                    # mime_type removed - causes 'encoding' error in Veo 3.1
                ),
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                ),
            )

        try:
            operation = await asyncio.to_thread(_extend)
            operation_id = str(uuid.uuid4())
            self._pending_operations[operation_id] = operation

            logger.info(f"Video extension started, operation_id: {operation_id}")

            # Poll for completion
            max_wait_seconds = 300
            poll_interval = 10
            elapsed = 0

            while not operation.done and elapsed < max_wait_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                operation = await asyncio.to_thread(
                    lambda: self.client.operations.get(operation=operation)
                )
                logger.info(f"Polling video extension... elapsed: {elapsed}s")

            if not operation.done:
                return ExtendedVideoResult(
                    status="processing",
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

            # Get result
            if operation.result and operation.result.generated_videos:
                generated_video = operation.result.generated_videos[0]
                generation_time_ms = int((time.time() - start_time) * 1000)

                # Download and save extended video locally
                video_filename = f"extended_{uuid.uuid4().hex[:12]}.mp4"
                output_path = VIDEO_OUTPUT_DIR / video_filename

                try:
                    await asyncio.to_thread(
                        lambda: self.client.files.download(file=generated_video.video)
                    )
                    await asyncio.to_thread(
                        lambda: generated_video.video.save(str(output_path))
                    )
                    logger.info(f"Extended video saved to: {output_path}")

                    local_video_url = f"http://localhost:8000/uploads/videos/{video_filename}"

                    return ExtendedVideoResult(
                        status="completed",
                        video_url=local_video_url,
                        video_path=str(output_path),
                        extension_hops_completed=1,
                        extension_hops_requested=1,
                        generation_time_ms=generation_time_ms,
                        hop_results=[
                            ExtensionHopResult(
                                hop_number=1,
                                status="completed",
                                video_url=local_video_url,
                                video_path=str(output_path),
                                duration_added_seconds=7.0,
                                prompt_used=extension_prompt,
                                generation_time_ms=generation_time_ms,
                            )
                        ],
                    )
                except Exception as download_error:
                    logger.error(f"Failed to download extended video: {download_error}")
                    video = generated_video.video
                    return ExtendedVideoResult(
                        status="completed",
                        video_url=video.uri if hasattr(video, 'uri') else None,
                        extension_hops_completed=1,
                        extension_hops_requested=1,
                        generation_time_ms=generation_time_ms,
                    )
            else:
                error_msg = "No extended video generated"
                if hasattr(operation, 'result') and operation.result:
                    if hasattr(operation.result, 'rai_media_filtered_reasons') and operation.result.rai_media_filtered_reasons:
                        error_msg = operation.result.rai_media_filtered_reasons[0]
                return ExtendedVideoResult(
                    status="failed",
                    error_message=error_msg,
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )

        except Exception as e:
            logger.error(f"Video extension failed: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return ExtendedVideoResult(
                status="failed",
                error_message=str(e),
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

    async def generate_extended_video(
        self,
        scenes: List[SceneInput],
        target_duration_seconds: int,
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Generate a long video using initial generation + scene extensions.

        This method:
        1. Generates an initial 8-second video from the first scene
        2. Extends the video using subsequent scene prompts (7 seconds each)
        3. Continues until target duration is reached or scenes are exhausted

        Args:
            scenes: List of scene inputs with descriptions
            target_duration_seconds: Target duration (max 148 seconds)
            brand_context: Optional brand context for prompts
            aspect_ratio: Video aspect ratio (16:9 or 9:16)

        Returns:
            ExtendedVideoResult with the final extended video
        """
        # Import prompt builder here to avoid circular import
        from .prompt_builder import create_prompt_builder
        import asyncio

        start_time = time.time()
        logger.info(
            f"Starting extended video generation - "
            f"{len(scenes)} scenes, target: {target_duration_seconds}s"
        )

        if not scenes:
            return ExtendedVideoResult(
                status="failed",
                error_message="No scenes provided",
                generation_time_ms=0,
            )

        # Validate and clamp target duration (max 148 seconds)
        target_duration_seconds = min(148, max(8, target_duration_seconds))

        # Validate aspect ratio
        if aspect_ratio not in ["16:9", "9:16"]:
            logger.warning(f"Unsupported aspect ratio {aspect_ratio}, defaulting to 16:9")
            aspect_ratio = "16:9"

        # Calculate how many extension hops needed
        initial_duration = 8  # First generation is 8 seconds
        extension_per_hop = 7  # Each extension adds 7 seconds
        max_hops = 20  # Maximum 20 extension hops allowed

        hops_needed = max(0, (target_duration_seconds - initial_duration + extension_per_hop - 1) // extension_per_hop)
        hops_needed = min(hops_needed, max_hops, len(scenes) - 1)  # Limited by scenes available

        logger.info(f"Extension plan: {initial_duration}s initial + {hops_needed} hops of {extension_per_hop}s each")

        # Initialize prompt builder
        prompt_builder = create_prompt_builder(storyboard_priority=True)
        hop_results: List[ExtensionHopResult] = []

        # Step 1: Generate initial video from first scene
        first_scene = scenes[0]
        initial_prompt = prompt_builder.build_scene_prompt(
            scene=first_scene,
            brand_context=brand_context,
        )

        logger.info(f"Generating initial {initial_duration}s video...")

        if first_scene.image_data:
            initial_result = await self.generate_from_image(
                image_data=first_scene.image_data,
                prompt=initial_prompt,
                duration_seconds=initial_duration,
                aspect_ratio=aspect_ratio,
            )
        else:
            initial_result = await self.generate_from_prompt(
                prompt=initial_prompt,
                duration_seconds=initial_duration,
                aspect_ratio=aspect_ratio,
            )

        if initial_result.status != "completed":
            return ExtendedVideoResult(
                status="failed",
                error_message=f"Failed to generate initial video: {initial_result.error_message}",
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

        # Extract video path from URL for extension
        current_video_url = initial_result.video_url
        if current_video_url and "localhost" in current_video_url:
            # Extract filename and construct local path
            video_filename = current_video_url.split("/")[-1]
            current_video_path = str(VIDEO_OUTPUT_DIR / video_filename)
        else:
            return ExtendedVideoResult(
                status="failed",
                error_message="Initial video was not saved locally, cannot extend",
                generation_time_ms=int((time.time() - start_time) * 1000),
            )

        current_duration = initial_duration
        scenes_processed = 1

        logger.info(f"Initial video generated: {current_video_path}, duration: {current_duration}s")

        # Step 2: Extend video with subsequent scenes
        for hop_idx in range(hops_needed):
            scene_idx = hop_idx + 1  # Start from second scene
            if scene_idx >= len(scenes):
                logger.info(f"No more scenes available for extension at hop {hop_idx + 1}")
                break

            # Check if we've reached target duration
            if current_duration >= target_duration_seconds:
                logger.info(f"Target duration {target_duration_seconds}s reached at {current_duration}s")
                break

            scene = scenes[scene_idx]
            hop_start_time = time.time()

            # Build extension prompt
            extension_prompt = prompt_builder.build_scene_prompt(
                scene=scene,
                brand_context=brand_context,
            )

            logger.info(f"Extension hop {hop_idx + 1}/{hops_needed}: scene {scene_idx + 1}")

            # Extend the current video
            extension_result = await self.extend_video(
                video_path=current_video_path,
                extension_prompt=extension_prompt,
                aspect_ratio=aspect_ratio,
            )

            hop_time_ms = int((time.time() - hop_start_time) * 1000)

            if extension_result.status == "completed" and extension_result.video_path:
                # Update current video for next iteration
                current_video_path = extension_result.video_path
                current_video_url = extension_result.video_url
                current_duration += extension_per_hop
                scenes_processed += 1

                hop_results.append(
                    ExtensionHopResult(
                        hop_number=hop_idx + 1,
                        status="completed",
                        video_url=extension_result.video_url,
                        video_path=extension_result.video_path,
                        duration_added_seconds=extension_per_hop,
                        total_duration_seconds=current_duration,
                        prompt_used=extension_prompt,
                        generation_time_ms=hop_time_ms,
                    )
                )

                logger.info(
                    f"Extension hop {hop_idx + 1} completed: "
                    f"new duration {current_duration}s"
                )
            else:
                # Extension failed, stop and return partial result
                hop_results.append(
                    ExtensionHopResult(
                        hop_number=hop_idx + 1,
                        status="failed",
                        error_message=extension_result.error_message,
                        prompt_used=extension_prompt,
                        generation_time_ms=hop_time_ms,
                    )
                )

                logger.error(
                    f"Extension hop {hop_idx + 1} failed: {extension_result.error_message}"
                )

                # Return partial result with what we have
                return ExtendedVideoResult(
                    status="partial",
                    video_url=current_video_url,
                    video_path=current_video_path,
                    initial_duration_seconds=initial_duration,
                    final_duration_seconds=current_duration,
                    extension_hops_completed=hop_idx,
                    extension_hops_requested=hops_needed,
                    hop_results=hop_results,
                    generation_time_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Extension stopped at hop {hop_idx + 1}: {extension_result.error_message}",
                    scenes_processed=scenes_processed,
                )

            # Add delay between extension hops to avoid rate limits
            if hop_idx < hops_needed - 1:
                logger.info("Waiting 30 seconds before next extension hop...")
                await asyncio.sleep(30)

        # Step 3: Return final result
        total_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Extended video generation complete: "
            f"final duration {current_duration}s, "
            f"{len(hop_results)} hops, "
            f"{scenes_processed} scenes processed, "
            f"total time {total_time_ms}ms"
        )

        return ExtendedVideoResult(
            status="completed",
            video_url=current_video_url,
            video_path=current_video_path,
            initial_duration_seconds=initial_duration,
            final_duration_seconds=current_duration,
            extension_hops_completed=len([h for h in hop_results if h.status == "completed"]),
            extension_hops_requested=hops_needed,
            hop_results=hop_results,
            generation_time_ms=total_time_ms,
            scenes_processed=scenes_processed,
        )


class MockVideoGenerator(VideoGeneratorBase):
    """Mock video generator for testing."""

    async def generate_from_prompt(
        self,
        prompt: str,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        import asyncio

        start_time = time.time()
        await asyncio.sleep(2)  # Simulate generation delay

        # Return a sample video URL
        return VideoGenerationResult(
            video_url="https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            mime_type="video/mp4",
            duration_seconds=duration_seconds,
            generation_time_ms=int((time.time() - start_time) * 1000),
            status="completed",
        )

    async def generate_from_image(
        self,
        image_data: str,
        prompt: Optional[str] = None,
        duration_seconds: int = 5,
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        import asyncio

        start_time = time.time()
        await asyncio.sleep(2)

        return VideoGenerationResult(
            video_url="https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            mime_type="video/mp4",
            duration_seconds=duration_seconds,
            generation_time_ms=int((time.time() - start_time) * 1000),
            status="completed",
        )

    async def generate_marketing_video(
        self,
        scenes: List[SceneInput],
        aspect_ratio: str = "16:9",
    ) -> VideoGenerationResult:
        import asyncio

        start_time = time.time()
        await asyncio.sleep(3)  # Slightly longer for "complex" generation

        total_duration = sum(s.duration_seconds for s in scenes)

        return VideoGenerationResult(
            video_url="https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            mime_type="video/mp4",
            duration_seconds=total_duration,
            generation_time_ms=int((time.time() - start_time) * 1000),
            status="completed",
        )

    async def check_generation_status(
        self,
        operation_id: str,
    ) -> VideoGenerationResult:
        return VideoGenerationResult(
            video_url="https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            status="completed",
        )

    async def generate_per_scene_videos(
        self,
        scenes: List[SceneInput],
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
        delay_between_scenes: int = 30,  # Not used in mock, just for interface consistency
    ) -> VideoGenerationResult:
        """
        Mock implementation of per-scene video generation.

        Simulates generating individual videos for each scene with mock URLs.
        """
        # Import prompt builder here to avoid circular import
        from .prompt_builder import create_prompt_builder
        import asyncio

        start_time = time.time()

        if not scenes:
            return VideoGenerationResult(
                status="failed",
                error_message="No scenes provided",
                generation_time_ms=0,
            )

        # Initialize prompt builder for consistent mock behavior
        prompt_builder = create_prompt_builder(storyboard_priority=True)

        # Sample video URLs for mock responses
        mock_video_urls = [
            "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        ]

        scene_results: List[SceneVideoResult] = []

        for i, scene in enumerate(scenes):
            scene_start = time.time()
            await asyncio.sleep(0.5)  # Simulate per-scene generation delay

            # Build prompt for consistency
            prompt = prompt_builder.build_scene_prompt(
                scene=scene,
                brand_context=brand_context,
            )

            scene_duration = min(8, scene.duration_seconds) if scene.duration_seconds else 5

            scene_results.append(
                SceneVideoResult(
                    scene_number=scene.scene_number,
                    status="completed",
                    video_url=mock_video_urls[i % len(mock_video_urls)],
                    duration_seconds=scene_duration,
                    generation_time_ms=int((time.time() - scene_start) * 1000),
                    prompt_used=prompt,
                )
            )

        total_duration = sum(
            r.duration_seconds or 0
            for r in scene_results
            if r.duration_seconds
        )

        return VideoGenerationResult(
            status="completed",
            scene_results=scene_results,
            duration_seconds=total_duration,
            generation_time_ms=int((time.time() - start_time) * 1000),
        )

    async def extend_video(
        self,
        video_path: str,
        extension_prompt: str,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Mock implementation of video extension.

        Simulates extending a video by 7 seconds with a mock URL.
        """
        import asyncio

        start_time = time.time()
        await asyncio.sleep(1)  # Simulate extension delay

        # Generate mock extended video URL
        mock_video_url = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4"

        return ExtendedVideoResult(
            status="completed",
            video_url=mock_video_url,
            video_path=f"/mock/extended_{uuid.uuid4().hex[:12]}.mp4",
            initial_duration_seconds=8.0,
            final_duration_seconds=15.0,  # 8 + 7 seconds
            extension_hops_completed=1,
            extension_hops_requested=1,
            hop_results=[
                ExtensionHopResult(
                    hop_number=1,
                    status="completed",
                    video_url=mock_video_url,
                    video_path=f"/mock/extended_{uuid.uuid4().hex[:12]}.mp4",
                    duration_added_seconds=7.0,
                    total_duration_seconds=15.0,
                    prompt_used=extension_prompt,
                    generation_time_ms=int((time.time() - start_time) * 1000),
                )
            ],
            generation_time_ms=int((time.time() - start_time) * 1000),
            scenes_processed=1,
        )

    async def generate_extended_video(
        self,
        scenes: List[SceneInput],
        target_duration_seconds: int,
        brand_context: Optional[str] = None,
        aspect_ratio: str = "16:9",
    ) -> ExtendedVideoResult:
        """
        Mock implementation of extended video generation.

        Simulates generating a long video through initial generation + extensions.
        """
        # Import prompt builder here to avoid circular import
        from .prompt_builder import create_prompt_builder
        import asyncio

        start_time = time.time()

        if not scenes:
            return ExtendedVideoResult(
                status="failed",
                error_message="No scenes provided",
                generation_time_ms=0,
            )

        # Clamp target duration
        target_duration_seconds = min(148, max(8, target_duration_seconds))

        # Calculate extension hops
        initial_duration = 8
        extension_per_hop = 7
        max_hops = 20

        hops_needed = max(0, (target_duration_seconds - initial_duration + extension_per_hop - 1) // extension_per_hop)
        hops_needed = min(hops_needed, max_hops, len(scenes) - 1)

        # Initialize prompt builder
        prompt_builder = create_prompt_builder(storyboard_priority=True)
        hop_results: List[ExtensionHopResult] = []

        # Simulate initial generation
        await asyncio.sleep(0.5)

        current_duration = initial_duration
        mock_video_url = "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

        # Simulate extension hops
        for hop_idx in range(hops_needed):
            scene_idx = hop_idx + 1
            if scene_idx >= len(scenes):
                break

            await asyncio.sleep(0.3)  # Simulate extension delay

            scene = scenes[scene_idx]
            extension_prompt = prompt_builder.build_scene_prompt(
                scene=scene,
                brand_context=brand_context,
            )

            current_duration += extension_per_hop

            hop_results.append(
                ExtensionHopResult(
                    hop_number=hop_idx + 1,
                    status="completed",
                    video_url=mock_video_url,
                    video_path=f"/mock/extended_{uuid.uuid4().hex[:12]}.mp4",
                    duration_added_seconds=extension_per_hop,
                    total_duration_seconds=current_duration,
                    prompt_used=extension_prompt,
                    generation_time_ms=300,
                )
            )

        return ExtendedVideoResult(
            status="completed",
            video_url=mock_video_url,
            video_path=f"/mock/final_extended_{uuid.uuid4().hex[:12]}.mp4",
            initial_duration_seconds=initial_duration,
            final_duration_seconds=current_duration,
            extension_hops_completed=len(hop_results),
            extension_hops_requested=hops_needed,
            hop_results=hop_results,
            generation_time_ms=int((time.time() - start_time) * 1000),
            scenes_processed=1 + len(hop_results),
        )


class VideoGeneratorFactory:
    """Factory for creating video generators."""

    _generators: dict[str, type[VideoGeneratorBase]] = {
        "veo": GeminiVeoGenerator,
        "mock": MockVideoGenerator,
    }

    @classmethod
    def create(cls, provider: str) -> VideoGeneratorBase:
        """Create a video generator for the specified provider."""
        if provider not in cls._generators:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._generators.keys())}")
        return cls._generators[provider]()

    @classmethod
    def available_providers(cls) -> list[str]:
        """Get list of available providers."""
        return list(cls._generators.keys())


# Singleton instances
_generator_instances: dict[str, VideoGeneratorBase] = {}


def get_video_generator(provider: str = "mock") -> VideoGeneratorBase:
    """Get or create a video generator instance."""
    if provider not in _generator_instances:
        _generator_instances[provider] = VideoGeneratorFactory.create(provider)
    return _generator_instances[provider]


__all__ = [
    "VideoGeneratorBase",
    "GeminiVeoGenerator",
    "MockVideoGenerator",
    "VideoGeneratorFactory",
    "get_video_generator",
    "VideoGenerationResult",
    "SceneVideoResult",
    "SceneInput",
    "ExtendedVideoResult",
    "ExtensionHopResult",
]
