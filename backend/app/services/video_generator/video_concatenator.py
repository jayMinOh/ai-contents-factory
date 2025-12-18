"""
Video Concatenation Service using FFmpeg.

Combines per-scene video clips into a final marketing video with optional transitions.
Supports downloading videos from remote URLs and applying transition effects.
"""

import asyncio
import logging
import os
import shutil
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiofiles
import httpx

from app.core.config import settings

# Video output directory (same as video generator service)
VIDEO_OUTPUT_DIR = Path(settings.UPLOAD_DIR) / "videos"
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


# Transition effect mappings for FFmpeg xfade filter
TRANSITION_EFFECTS: Dict[str, Optional[str]] = {
    "cut": None,  # Direct concatenation, no effect
    "fade": "fade",  # Crossfade transition
    "fade_in": "fade",  # Fade in (uses fade)
    "fade_out": "fade",  # Fade out (uses fade)
    "dissolve": "dissolve",  # Dissolve transition
    "zoom": None,  # Not directly supported, use cut as fallback
    "slide": None,  # Not directly supported, use cut as fallback
    "wipeleft": "wipeleft",  # Wipe from right to left
    "wiperight": "wiperight",  # Wipe from left to right
    "wipeup": "wipeup",  # Wipe from bottom to top
    "wipedown": "wipedown",  # Wipe from top to bottom
    "slideleft": "slideleft",  # Slide from right to left
    "slideright": "slideright",  # Slide from left to right
    "slideup": "slideup",  # Slide from bottom to top
    "slidedown": "slidedown",  # Slide from top to bottom
    "circlecrop": "circlecrop",  # Circle crop transition
    "rectcrop": "rectcrop",  # Rectangle crop transition
    "distance": "distance",  # Distance transition
    "fadeblack": "fadeblack",  # Fade to black then to next
    "fadewhite": "fadewhite",  # Fade to white then to next
    "radial": "radial",  # Radial wipe
    "smoothleft": "smoothleft",  # Smooth slide left
    "smoothright": "smoothright",  # Smooth slide right
    "smoothup": "smoothup",  # Smooth slide up
    "smoothdown": "smoothdown",  # Smooth slide down
    "circleopen": "circleopen",  # Circle opening
    "circleclose": "circleclose",  # Circle closing
    "vertopen": "vertopen",  # Vertical bars opening
    "vertclose": "vertclose",  # Vertical bars closing
    "horzopen": "horzopen",  # Horizontal bars opening
    "horzclose": "horzclose",  # Horizontal bars closing
    "diagtl": "diagtl",  # Diagonal from top-left
    "diagtr": "diagtr",  # Diagonal from top-right
    "diagbl": "diagbl",  # Diagonal from bottom-left
    "diagbr": "diagbr",  # Diagonal from bottom-right
    "hlslice": "hlslice",  # Horizontal slice
    "hrslice": "hrslice",  # Horizontal reverse slice
    "vuslice": "vuslice",  # Vertical up slice
    "vdslice": "vdslice",  # Vertical down slice
    "pixelize": "pixelize",  # Pixelize transition
}


@dataclass
class ConcatenationResult:
    """Result of video concatenation operation."""

    success: bool
    output_url: Optional[str] = None
    output_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    scene_count: Optional[int] = None
    transitions_applied: Optional[int] = None


@dataclass
class SceneVideo:
    """Representation of a scene video for concatenation."""

    video_url: str
    transition_effect: Optional[str] = None
    duration_seconds: Optional[float] = None
    local_path: Optional[str] = None


class VideoConcatenator:
    """
    Service for concatenating multiple video clips into a single video.

    Uses FFmpeg for video processing, supporting:
    - Simple concatenation (cut between scenes)
    - Transition effects (fade, dissolve, wipe, slide, etc.)
    - Downloading videos from remote URLs
    - Async file operations
    """

    # HTTP client timeout settings
    DOWNLOAD_TIMEOUT = 120.0  # seconds
    DOWNLOAD_CHUNK_SIZE = 8192  # bytes

    def __init__(
        self,
        output_dir: Optional[str] = None,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
    ):
        """
        Initialize the video concatenator.

        Args:
            output_dir: Directory for output videos. Defaults to VIDEO_OUTPUT_DIR.
            ffmpeg_path: Path to FFmpeg executable. Defaults to "ffmpeg".
            ffprobe_path: Path to FFprobe executable. Defaults to "ffprobe".
        """
        self.output_dir = Path(output_dir) if output_dir else VIDEO_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self._temp_dir: Optional[Path] = None
        logger.info(
            f"VideoConcatenator initialized - output_dir: {self.output_dir}, "
            f"ffmpeg: {self.ffmpeg_path}"
        )

    async def download_video(self, url: str, destination: str) -> bool:
        """
        Download a video from URL to local path.

        Args:
            url: URL of the video to download.
            destination: Local file path to save the video.

        Returns:
            True if download succeeded, False otherwise.
        """
        logger.info(f"Downloading video from {url} to {destination}")

        # Handle local file paths (file:// or absolute paths)
        if url.startswith("file://"):
            local_source = url[7:]  # Remove file:// prefix
            try:
                shutil.copy2(local_source, destination)
                logger.info(f"Copied local file from {local_source}")
                return True
            except Exception as e:
                logger.error(f"Failed to copy local file: {e}")
                return False

        # Handle local paths without file:// prefix
        if os.path.exists(url):
            try:
                shutil.copy2(url, destination)
                logger.info(f"Copied local file from {url}")
                return True
            except Exception as e:
                logger.error(f"Failed to copy local file: {e}")
                return False

        # Handle localhost URLs (local server)
        if "localhost" in url or "127.0.0.1" in url:
            # Extract the file path from localhost URL
            # e.g., http://localhost:8000/uploads/videos/video_abc.mp4
            try:
                from urllib.parse import urlparse

                parsed = urlparse(url)
                # Remove leading slash and construct local path
                local_path = parsed.path.lstrip("/")
                # Check if it's in uploads directory
                if local_path.startswith("uploads"):
                    full_local_path = Path(settings.UPLOAD_DIR).parent / local_path
                    if full_local_path.exists():
                        shutil.copy2(str(full_local_path), destination)
                        logger.info(f"Copied from localhost path: {full_local_path}")
                        return True
            except Exception as e:
                logger.warning(f"Failed to handle localhost URL as local file: {e}")
                # Fall through to HTTP download

        # Download from remote URL using httpx
        try:
            async with httpx.AsyncClient(timeout=self.DOWNLOAD_TIMEOUT) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    # Write to file in chunks
                    async with aiofiles.open(destination, "wb") as f:
                        async for chunk in response.aiter_bytes(
                            chunk_size=self.DOWNLOAD_CHUNK_SIZE
                        ):
                            await f.write(chunk)

            file_size = os.path.getsize(destination)
            logger.info(f"Downloaded video successfully - size: {file_size} bytes")
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error downloading video: {e.response.status_code} - {url}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error downloading video: {e} - {url}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading video: {e} - {url}")
            return False

    async def get_video_duration(self, video_path: str) -> Optional[float]:
        """
        Get the duration of a video file using ffprobe.

        Args:
            video_path: Path to the video file.

        Returns:
            Duration in seconds, or None if failed.
        """
        args = [
            self.ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                duration = float(stdout.decode().strip())
                logger.debug(f"Video duration for {video_path}: {duration}s")
                return duration
            else:
                logger.warning(
                    f"ffprobe failed for {video_path}: {stderr.decode()}"
                )
                return None

        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return None

    async def concatenate(
        self,
        scene_videos: List[Dict],
        output_filename: Optional[str] = None,
        include_transitions: bool = True,
        transition_duration_ms: int = 500,
    ) -> ConcatenationResult:
        """
        Concatenate multiple scene videos into a single video.

        Args:
            scene_videos: List of dicts with keys:
                - video_url: URL or local path to the video
                - transition_effect: Optional transition effect name
                - duration_seconds: Optional duration (auto-detected if not provided)
            output_filename: Optional output filename. Auto-generated if not provided.
            include_transitions: Whether to apply transition effects. Default True.
            transition_duration_ms: Duration of transitions in milliseconds. Default 500.

        Returns:
            ConcatenationResult with output URL/path and metadata.
        """
        start_time = time.time()
        logger.info(
            f"Starting concatenation of {len(scene_videos)} videos, "
            f"transitions: {include_transitions}, duration: {transition_duration_ms}ms"
        )

        # Validate input
        if not scene_videos:
            return ConcatenationResult(
                success=False,
                error_message="No scene videos provided",
                processing_time_ms=0,
            )

        # Create temporary directory for processing
        self._temp_dir = Path(tempfile.mkdtemp(prefix="video_concat_"))
        logger.debug(f"Created temp directory: {self._temp_dir}")

        try:
            # Step 1: Download all videos to temp directory
            local_videos: List[SceneVideo] = []
            for i, scene in enumerate(scene_videos):
                video_url = scene.get("video_url")
                if not video_url:
                    logger.warning(f"Scene {i} has no video_url, skipping")
                    continue

                local_filename = f"scene_{i:03d}.mp4"
                local_path = self._temp_dir / local_filename

                download_success = await self.download_video(
                    video_url, str(local_path)
                )

                if not download_success:
                    logger.error(f"Failed to download scene {i} from {video_url}")
                    # Clean up and return error
                    await self._cleanup_temp_dir()
                    return ConcatenationResult(
                        success=False,
                        error_message=f"Failed to download video for scene {i}",
                        processing_time_ms=int((time.time() - start_time) * 1000),
                    )

                # Get video duration if not provided
                duration = scene.get("duration_seconds")
                if duration is None:
                    duration = await self.get_video_duration(str(local_path))

                local_videos.append(
                    SceneVideo(
                        video_url=video_url,
                        transition_effect=scene.get("transition_effect"),
                        duration_seconds=duration,
                        local_path=str(local_path),
                    )
                )

            if not local_videos:
                await self._cleanup_temp_dir()
                return ConcatenationResult(
                    success=False,
                    error_message="No valid videos to concatenate",
                    processing_time_ms=int((time.time() - start_time) * 1000),
                )

            logger.info(f"Downloaded {len(local_videos)} videos successfully")

            # Step 2: Choose concatenation method based on transitions
            if output_filename is None:
                output_filename = f"final_{uuid.uuid4().hex[:12]}.mp4"

            output_path = self.output_dir / output_filename

            if include_transitions and len(local_videos) > 1:
                # Use xfade filter for transitions
                success, error_msg = await self._concatenate_with_transitions(
                    local_videos,
                    str(output_path),
                    transition_duration_ms,
                )
            else:
                # Use simple concat demuxer (faster, no re-encoding)
                success, error_msg = await self._concatenate_simple(
                    local_videos,
                    str(output_path),
                )

            # Step 3: Calculate results
            processing_time_ms = int((time.time() - start_time) * 1000)

            if success:
                # Get output duration
                output_duration = await self.get_video_duration(str(output_path))

                # Build output URL
                output_url = f"http://localhost:8000/uploads/videos/{output_filename}"

                # Count applied transitions
                transitions_applied = 0
                if include_transitions:
                    for video in local_videos[:-1]:
                        effect = video.transition_effect or "fade"
                        if TRANSITION_EFFECTS.get(effect) is not None:
                            transitions_applied += 1

                logger.info(
                    f"Concatenation completed successfully - "
                    f"output: {output_path}, duration: {output_duration}s, "
                    f"processing time: {processing_time_ms}ms"
                )

                return ConcatenationResult(
                    success=True,
                    output_url=output_url,
                    output_path=str(output_path),
                    duration_seconds=output_duration,
                    processing_time_ms=processing_time_ms,
                    scene_count=len(local_videos),
                    transitions_applied=transitions_applied,
                )
            else:
                logger.error(f"Concatenation failed: {error_msg}")
                return ConcatenationResult(
                    success=False,
                    error_message=error_msg,
                    processing_time_ms=processing_time_ms,
                    scene_count=len(local_videos),
                )

        except Exception as e:
            logger.error(f"Unexpected error during concatenation: {e}", exc_info=True)
            return ConcatenationResult(
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        finally:
            # Clean up temp directory
            await self._cleanup_temp_dir()

    async def _concatenate_simple(
        self,
        videos: List[SceneVideo],
        output_path: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Concatenate videos using FFmpeg concat demuxer (no transitions).

        This method is faster as it doesn't require re-encoding when
        all videos have the same codec and parameters.

        Args:
            videos: List of SceneVideo objects with local paths.
            output_path: Path for the output video.

        Returns:
            Tuple of (success, error_message).
        """
        if not videos:
            return False, "No videos to concatenate"

        # Create concat file
        concat_file_path = self._temp_dir / "concat.txt"
        self._create_concat_file(
            [v.local_path for v in videos if v.local_path],
            str(concat_file_path),
        )

        # Run FFmpeg with concat demuxer
        args = [
            self.ffmpeg_path,
            "-y",  # Overwrite output
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file_path),
            "-c",
            "copy",  # Copy streams without re-encoding
            output_path,
        ]

        return await self._run_ffmpeg(args)

    async def _concatenate_with_transitions(
        self,
        videos: List[SceneVideo],
        output_path: str,
        transition_duration_ms: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Concatenate videos with transition effects using xfade filter.

        Args:
            videos: List of SceneVideo objects with local paths.
            output_path: Path for the output video.
            transition_duration_ms: Duration of each transition in milliseconds.

        Returns:
            Tuple of (success, error_message).
        """
        if not videos:
            return False, "No videos to concatenate"

        if len(videos) == 1:
            # Single video, just copy
            shutil.copy2(videos[0].local_path, output_path)
            return True, None

        transition_duration = transition_duration_ms / 1000.0

        # Build FFmpeg command with xfade filters
        args = [self.ffmpeg_path, "-y"]

        # Add all input files
        for video in videos:
            args.extend(["-i", video.local_path])

        # Build filter_complex for xfade transitions
        filter_parts = []
        current_output = "[0:v]"
        audio_inputs = []

        # Track cumulative offset for each transition
        cumulative_offset = 0.0

        for i in range(len(videos) - 1):
            # Get transition effect for this transition
            effect_name = videos[i].transition_effect or "fade"
            xfade_effect = TRANSITION_EFFECTS.get(effect_name)

            if xfade_effect is None:
                # Unsupported effect, use fade as fallback
                xfade_effect = "fade"
                logger.debug(
                    f"Transition effect '{effect_name}' not supported, using fade"
                )

            # Calculate offset (time in first video when transition starts)
            video_duration = videos[i].duration_seconds or 5.0
            offset = cumulative_offset + video_duration - transition_duration

            # Ensure offset is not negative
            if offset < 0:
                offset = 0.0

            # Create xfade filter
            next_input = f"[{i + 1}:v]"
            output_label = f"[v{i}]" if i < len(videos) - 2 else "[outv]"

            filter_parts.append(
                f"{current_output}{next_input}xfade="
                f"transition={xfade_effect}:"
                f"duration={transition_duration}:"
                f"offset={offset:.3f}{output_label}"
            )

            current_output = output_label

            # Update cumulative offset for next iteration
            # After xfade, the effective duration is reduced by transition_duration
            cumulative_offset = offset + transition_duration

            # Audio handling
            audio_inputs.append(f"[{i}:a]")

        # Add last audio input
        audio_inputs.append(f"[{len(videos) - 1}:a]")

        # Audio concatenation (simple concat, no crossfade)
        audio_filter = "".join(audio_inputs) + f"concat=n={len(videos)}:v=0:a=1[outa]"
        filter_parts.append(audio_filter)

        # Combine all filters
        filter_complex = ";".join(filter_parts)

        args.extend(["-filter_complex", filter_complex])
        args.extend(["-map", "[outv]", "-map", "[outa]"])

        # Output settings
        args.extend([
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            output_path,
        ])

        return await self._run_ffmpeg(args)

    def _create_concat_file(self, video_paths: List[str], concat_file_path: str) -> None:
        """
        Create FFmpeg concat demuxer file.

        Args:
            video_paths: List of video file paths.
            concat_file_path: Path to write the concat file.
        """
        with open(concat_file_path, "w") as f:
            for path in video_paths:
                # Escape single quotes in path for FFmpeg concat demuxer
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        logger.debug(f"Created concat file at {concat_file_path} with {len(video_paths)} entries")

    async def _run_ffmpeg(self, args: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Run FFmpeg command asynchronously.

        Args:
            args: FFmpeg command arguments.

        Returns:
            Tuple of (success, error_message).
        """
        logger.debug(f"Running FFmpeg: {' '.join(args[:10])}...")

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.debug("FFmpeg completed successfully")
                return True, None
            else:
                error_output = stderr.decode()
                logger.error(f"FFmpeg failed with code {process.returncode}: {error_output}")
                return False, f"FFmpeg error: {error_output[-500:]}"  # Last 500 chars

        except FileNotFoundError:
            error_msg = f"FFmpeg not found at {self.ffmpeg_path}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Error running FFmpeg: {e}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    async def _cleanup_temp_dir(self) -> None:
        """Clean up temporary directory and files."""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.debug(f"Cleaned up temp directory: {self._temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
            finally:
                self._temp_dir = None


# Singleton instance
_concatenator_instance: Optional[VideoConcatenator] = None


def get_video_concatenator(
    output_dir: Optional[str] = None,
    ffmpeg_path: str = "ffmpeg",
) -> VideoConcatenator:
    """
    Get or create a VideoConcatenator instance.

    Args:
        output_dir: Optional output directory path.
        ffmpeg_path: Path to FFmpeg executable.

    Returns:
        VideoConcatenator instance.
    """
    global _concatenator_instance
    if _concatenator_instance is None:
        _concatenator_instance = VideoConcatenator(
            output_dir=output_dir,
            ffmpeg_path=ffmpeg_path,
        )
    return _concatenator_instance


__all__ = [
    "VideoConcatenator",
    "ConcatenationResult",
    "SceneVideo",
    "TRANSITION_EFFECTS",
    "get_video_concatenator",
]
