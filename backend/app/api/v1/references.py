from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum
from datetime import datetime
from pathlib import Path
import uuid
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.reference_analysis import ReferenceAnalysis
from app.services.reference_analyzer.analyzer import ReferenceAnalyzer

router = APIRouter()


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    tags: Optional[List[str]] = []
    extract_audio: bool = True


class ScoreBreakdownItem(BaseModel):
    score: float
    weight: str
    reason: str


class ScoreBreakdown(BaseModel):
    class Config:
        extra = "allow"  # Allow dynamic keys


class AnalysisResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    message: str


class SegmentType(str, Enum):
    HOOK = "hook"
    PROBLEM = "problem"
    AGITATION = "agitation"
    SOLUTION = "solution"
    FEATURE = "feature"
    BENEFIT = "benefit"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency"
    CTA = "cta"
    TRANSITION = "transition"
    DEMONSTRATION = "demonstration"
    INTRO = "intro"
    OUTRO = "outro"
    TESTIMONIAL = "testimonial"
    COMPARISON = "comparison"
    OFFER = "offer"
    OTHER = "other"


class TimelineSegment(BaseModel):
    start_time: float
    end_time: float
    segment_type: SegmentType
    visual_description: str
    audio_transcript: Optional[str] = None
    text_overlay: Optional[str] = None
    engagement_score: float
    techniques: List[str]
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class HookPoint(BaseModel):
    timestamp: str
    hook_type: str
    effectiveness_score: float
    description: Optional[str] = None
    elements: Optional[List[str]] = []
    adaptable_template: Optional[str] = None
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class EdgePoint(BaseModel):
    category: str
    description: str
    impact_score: float
    how_to_apply: str
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class EmotionalTrigger(BaseModel):
    timestamp: str
    trigger_type: str
    intensity: float
    description: str
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class PainPoint(BaseModel):
    timestamp: str
    pain_type: str
    description: str
    empathy_technique: str


class ApplicationPoint(BaseModel):
    type: str
    content: str
    context: str


class SellingPoint(BaseModel):
    timestamp: str
    claim: str
    evidence_type: str
    persuasion_technique: str
    effectiveness: Optional[float] = None
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class CTAAnalysis(BaseModel):
    cta_type: Optional[str] = None
    placement: Optional[str] = None
    urgency_elements: Optional[List[str]] = []
    barrier_removal: Optional[List[str]] = []
    effectiveness_score: Optional[float] = None
    score_reasoning: Optional[str] = None
    score_breakdown: Optional[dict] = None
    total_reason: Optional[str] = None


class OverallEvaluation(BaseModel):
    total_score: Optional[float] = None
    one_line_review: Optional[str] = None
    strengths: Optional[List[str]] = []
    weaknesses: Optional[List[str]] = []


class StructurePattern(BaseModel):
    framework: Optional[str] = None
    flow: Optional[List[str]] = []
    effectiveness_note: Optional[str] = None


class Recommendation(BaseModel):
    priority: Optional[int] = None
    action: str
    reason: Optional[str] = None
    example: Optional[str] = None


class AnalysisResult(BaseModel):
    analysis_id: str
    source_url: str
    title: str
    status: AnalysisStatus
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    images: List[str] = []
    segments: List[TimelineSegment] = []
    hook_points: List[HookPoint] = []
    edge_points: List[EdgePoint] = []
    emotional_triggers: List[EmotionalTrigger] = []
    pain_points: List[PainPoint] = []
    application_points: List[ApplicationPoint] = []
    selling_points: List[SellingPoint] = []
    cta_analysis: Optional[CTAAnalysis] = None
    structure_pattern: Optional[StructurePattern] = None
    recommendations: List[Recommendation] = []
    transcript: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None
    error_message: Optional[str] = None
    overall_evaluation: Optional[OverallEvaluation] = None


class AnalysisUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


# Valid segment types
VALID_SEGMENT_TYPES = {e.value for e in SegmentType}


def sanitize_segment(segment: dict) -> dict:
    """Sanitize segment data, converting invalid segment_type to 'other'"""
    s = segment.copy()
    seg_type = s.get("segment_type", "other")
    if seg_type not in VALID_SEGMENT_TYPES:
        s["segment_type"] = "other"
    return s


def model_to_result(analysis: ReferenceAnalysis) -> AnalysisResult:
    """Convert DB model to API response"""
    # Parse structure_pattern
    sp = analysis.structure_pattern
    structure_pattern = None
    if sp:
        if isinstance(sp, dict):
            structure_pattern = StructurePattern(**sp)
        else:
            structure_pattern = StructurePattern(framework=str(sp))

    # Parse cta_analysis
    cta = analysis.cta_analysis
    cta_analysis = CTAAnalysis(**cta) if cta and isinstance(cta, dict) else None

    # Parse recommendations
    recs = analysis.recommendations or []
    recommendations = []
    for r in recs:
        if isinstance(r, dict):
            recommendations.append(Recommendation(**r))
        else:
            recommendations.append(Recommendation(action=str(r)))

    return AnalysisResult(
        analysis_id=analysis.id,
        source_url=analysis.source_url,
        title=analysis.title,
        status=AnalysisStatus(analysis.status),
        duration=analysis.duration,
        thumbnail_url=analysis.thumbnail_url,
        images=analysis.images or [],
        segments=[TimelineSegment(**sanitize_segment(s)) for s in (analysis.segments or [])],
        hook_points=[HookPoint(**h) for h in (analysis.hook_points or [])],
        edge_points=[EdgePoint(**e) for e in (analysis.edge_points or [])],
        emotional_triggers=[EmotionalTrigger(**t) for t in (analysis.emotional_triggers or [])],
        pain_points=[PainPoint(**p) for p in (analysis.pain_points or [])],
        application_points=[ApplicationPoint(**a) for a in (analysis.application_points or [])],
        selling_points=[SellingPoint(**s) for s in (analysis.selling_points or [])],
        cta_analysis=cta_analysis,
        structure_pattern=structure_pattern,
        recommendations=recommendations,
        transcript=analysis.transcript,
        tags=analysis.tags or [],
        notes=analysis.notes,
        error_message=analysis.error_message,
        overall_evaluation=OverallEvaluation(**analysis.overall_evaluation) if analysis.overall_evaluation and isinstance(analysis.overall_evaluation, dict) else None,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a video URL for analysis"""
    analysis_id = str(uuid.uuid4())

    # Generate timestamp-based title if not provided
    title = request.title
    if not title:
        now = datetime.now()
        title = now.strftime("REF-%Y%m%d-%H%M%S-") + f"{now.microsecond // 1000:03d}"

    # Create DB record
    analysis = ReferenceAnalysis(
        id=analysis_id,
        source_url=str(request.url),
        title=title,
        status=AnalysisStatus.PENDING.value,
        tags=request.tags or [],
    )
    db.add(analysis)
    await db.commit()

    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis_id,
        url=str(request.url),
        extract_audio=request.extract_audio,
    )

    return AnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,
        message="Analysis started. Check status with GET /references/{analysis_id}",
    )


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Get analysis result by ID"""
    result = await db.execute(
        select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return model_to_result(analysis)


@router.get("/", response_model=List[AnalysisResult])
async def list_analyses(
    status: Optional[AnalysisStatus] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all analyses with optional filters"""
    query = select(ReferenceAnalysis).order_by(ReferenceAnalysis.created_at.desc())

    if status:
        query = query.where(ReferenceAnalysis.status == status.value)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    analyses = result.scalars().all()

    results = [model_to_result(a) for a in analyses]

    # Filter by tag in Python (JSON field filtering)
    if tag:
        results = [r for r in results if tag in r.tags]

    return results


@router.put("/{analysis_id}", response_model=AnalysisResult)
async def update_analysis(
    analysis_id: str,
    update: AnalysisUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update analysis metadata (title, tags, notes)"""
    result = await db.execute(
        select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    if update.title is not None:
        analysis.title = update.title
    if update.tags is not None:
        analysis.tags = update.tags
    if update.notes is not None:
        analysis.notes = update.notes

    await db.commit()
    await db.refresh(analysis)

    return model_to_result(analysis)


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    """Delete an analysis"""
    result = await db.execute(
        select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await db.delete(analysis)
    await db.commit()

    return {"message": "Analysis deleted successfully"}


@router.post("/{analysis_id}/reanalyze", response_model=AnalysisResponse)
async def reanalyze_reference(
    analysis_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Re-analyze an existing reference by deleting old data and starting fresh analysis"""
    # Find the existing analysis
    result = await db.execute(
        select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
    )
    existing_analysis = result.scalar_one_or_none()

    if not existing_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Store the original data we need to preserve
    original_url = existing_analysis.source_url
    original_title = existing_analysis.title
    original_tags = existing_analysis.tags or []

    # Delete the existing analysis
    await db.delete(existing_analysis)
    await db.commit()

    # Create a new analysis with a new ID
    new_analysis_id = str(uuid.uuid4())

    new_analysis = ReferenceAnalysis(
        id=new_analysis_id,
        source_url=original_url,
        title=original_title,
        status=AnalysisStatus.PENDING.value,
        tags=original_tags,
    )
    db.add(new_analysis)
    await db.commit()

    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=new_analysis_id,
        url=original_url,
        extract_audio=True,
    )

    return AnalysisResponse(
        analysis_id=new_analysis_id,
        status=AnalysisStatus.PENDING,
        message="Re-analysis started. Check status with GET /references/{analysis_id}",
    )


class UploadAnalysisResponse(BaseModel):
    analysis_ids: List[str]
    message: str


@router.post("/upload", response_model=UploadAnalysisResponse)
async def upload_images_for_analysis(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    title: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload images for analysis.

    - Accept multipart/form-data with multiple image files
    - Accept optional title in form data
    - For each uploaded image group, create a ReferenceAnalysis record
    - Run background analysis using analyzer.analyze_images()
    - Return list of analysis IDs for polling
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Validate files are images
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Allowed types: {', '.join(allowed_types)}"
            )

    # Ensure upload directory exists
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate analysis ID
    analysis_id = str(uuid.uuid4())

    # Generate title if not provided
    if not title:
        now = datetime.now()
        title = now.strftime("UPLOAD-%Y%m%d-%H%M%S-") + f"{now.microsecond // 1000:03d}"

    # Save uploaded files and collect paths
    saved_files = []
    image_bytes_list = []

    try:
        for file in files:
            # Generate unique filename
            ext = Path(file.filename).suffix if file.filename else ".jpg"
            unique_filename = f"{analysis_id}_{uuid.uuid4().hex[:8]}{ext}"
            file_path = upload_dir / unique_filename

            # Read file content
            content = await file.read()
            image_bytes_list.append(content)

            # Save to disk
            with open(file_path, "wb") as f:
                f.write(content)
            saved_files.append(str(file_path))

        # Create DB record
        analysis = ReferenceAnalysis(
            id=analysis_id,
            source_url="upload://" + ";".join(saved_files),
            title=title,
            status=AnalysisStatus.PENDING.value,
            tags=[],
        )
        db.add(analysis)
        await db.commit()

        # Run analysis in background
        background_tasks.add_task(
            run_upload_analysis,
            analysis_id=analysis_id,
            image_bytes_list=image_bytes_list,
            saved_files=saved_files,
        )

        return UploadAnalysisResponse(
            analysis_ids=[analysis_id],
            message=f"Upload analysis started for {len(files)} images. Check status with GET /references/{analysis_id}",
        )

    except Exception as e:
        # Clean up saved files on error
        for file_path in saved_files:
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")


async def run_upload_analysis(
    analysis_id: str,
    image_bytes_list: List[bytes],
    saved_files: List[str],
):
    """Background task to run image analysis for uploaded files"""
    from app.core.database import async_session_factory
    import base64
    import io

    async with async_session_factory() as db:
        try:
            # Get analysis record
            result = await db.execute(
                select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                return

            analyzer = ReferenceAnalyzer()

            # Update status: ANALYZING
            analysis.status = AnalysisStatus.ANALYZING.value
            analysis.error_message = None

            # Store images as base64 for display
            all_images_base64 = [
                f"data:image/jpeg;base64,{base64.b64encode(img).decode('utf-8')}"
                for img in image_bytes_list
            ]
            if all_images_base64:
                analysis.thumbnail_url = all_images_base64[0]
                analysis.images = all_images_base64

            await db.commit()

            # Run image analysis
            print(f"업로드 이미지 분석 시작 ({len(image_bytes_list)}개)")
            image_ios = [io.BytesIO(img_bytes) for img_bytes in image_bytes_list]
            result = await analyzer.analyze_images(image_ios, source_url="upload://")

            # Update with results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.duration = result.get("duration")
            analysis.segments = result.get("segments", [])
            analysis.hook_points = result.get("hook_points", [])
            analysis.edge_points = result.get("edge_points", [])
            analysis.emotional_triggers = result.get("emotional_triggers", [])
            analysis.pain_points = result.get("pain_points", [])
            analysis.application_points = result.get("application_points", [])
            analysis.selling_points = result.get("selling_points", [])
            analysis.cta_analysis = result.get("cta_analysis")
            analysis.structure_pattern = result.get("structure_pattern")
            analysis.recommendations = result.get("recommendations", [])
            analysis.transcript = result.get("transcript")
            analysis.overall_evaluation = result.get("overall_evaluation")

            # Update title with AI-generated reference_name if available
            reference_name = result.get("reference_name")
            if reference_name and isinstance(reference_name, str) and reference_name.strip():
                analysis.title = reference_name.strip()

            await db.commit()

        except Exception as e:
            error_msg = str(e)
            print(f"업로드 이미지 분석 실패: {error_msg}")

            # Rollback any pending transaction before handling error
            try:
                await db.rollback()
            except Exception:
                pass

            # Update analysis with error
            try:
                result = await db.execute(
                    select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
                )
                analysis = result.scalar_one_or_none()

                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = error_msg
                    analysis.recommendations = [{"action": f"분석 실패: {error_msg}"}]
                    await db.commit()
            except Exception as commit_error:
                print(f"Failed to update error status: {commit_error}")


async def run_analysis(analysis_id: str, url: str, extract_audio: bool):
    """Background task to run video/image analysis"""
    from app.core.database import async_session_factory
    from app.services.sns_media_downloader import SNSMediaDownloader
    import tempfile
    import io
    import base64

    async with async_session_factory() as db:
        try:
            # Get analysis record
            result = await db.execute(
                select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                return

            analyzer = ReferenceAnalyzer()

            # Update status: DOWNLOADING
            analysis.status = AnalysisStatus.DOWNLOADING.value
            analysis.error_message = None
            await db.commit()

            # Try to download and detect media type
            media_type = None  # 'image', 'video', or None
            image_bytes_list = []
            thumbnail_base64 = None
            all_images_base64 = []
            result = None

            # Check if URL is a supported SNS platform
            downloader = SNSMediaDownloader()
            is_sns_url = downloader.is_valid_url(url)

            if is_sns_url:
                # Download media - try multiple methods in order of reliability
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        downloaded_images = []
                        downloaded_videos = []

                        # 1. Instagram: Try instaloader FIRST (best for public posts)
                        if "instagram" in url.lower():
                            print("Instagram 감지 - instaloader 먼저 시도...")
                            try:
                                extracted_images = await downloader.extract_images_from_post(url, temp_dir)
                                if extracted_images:
                                    media_type = 'image'
                                    image_bytes_list = extracted_images
                                    first_image = image_bytes_list[0]
                                    thumbnail_base64 = f"data:image/jpeg;base64,{base64.b64encode(first_image).decode('utf-8')}"
                                    all_images_base64 = [
                                        f"data:image/jpeg;base64,{base64.b64encode(img).decode('utf-8')}"
                                        for img in image_bytes_list
                                    ]
                                    print(f"instaloader 성공! 이미지 {len(image_bytes_list)}개 추출")
                            except Exception as insta_err:
                                print(f"instaloader 실패: {insta_err}")

                        # 2. If instaloader didn't work or not Instagram, try gallery-dl
                        if not image_bytes_list:
                            print("gallery-dl 시도...")
                            try:
                                download_result = await downloader.download(url, temp_dir)
                                all_media = downloader.get_all_media(temp_dir)
                                downloaded_images = all_media['images']
                                downloaded_videos = all_media['videos']
                                print(f"gallery-dl 결과 - 이미지: {len(downloaded_images)}개, 영상: {len(downloaded_videos)}개")

                                if downloaded_videos:
                                    media_type = 'video'
                                    print(f"영상 발견, 영상 분석으로 전환")
                                elif downloaded_images:
                                    media_type = 'image'
                                    for img_path in downloaded_images:
                                        with open(img_path, 'rb') as f:
                                            image_bytes_list.append(f.read())
                                    if image_bytes_list:
                                        first_image = image_bytes_list[0]
                                        thumbnail_base64 = f"data:image/jpeg;base64,{base64.b64encode(first_image).decode('utf-8')}"
                                        all_images_base64 = [
                                            f"data:image/jpeg;base64,{base64.b64encode(img).decode('utf-8')}"
                                            for img in image_bytes_list
                                        ]
                                    print(f"gallery-dl 성공! 이미지 {len(image_bytes_list)}개 추출")
                            except Exception as gdl_err:
                                print(f"gallery-dl 실패: {gdl_err}")

                        # 3. Still nothing? Will fallback to yt-dlp for video analysis
                        if not image_bytes_list and not downloaded_videos:
                            print("이미지 다운로드 실패, yt-dlp 영상 분석 시도...")

                except Exception as e:
                    print(f"SNS 미디어 다운로드 실패: {e}")
                    media_type = None

            # Save thumbnail and images to DB if we have them
            if thumbnail_base64:
                analysis.thumbnail_url = thumbnail_base64
            if all_images_base64:
                analysis.images = all_images_base64
            await db.commit()

            # Run analysis if not already done
            if result is None:
                # Update status: ANALYZING
                analysis.status = AnalysisStatus.ANALYZING.value
                await db.commit()

                if media_type == 'image' and image_bytes_list:
                    # Image analysis
                    print(f"이미지 분석 시작 ({len(image_bytes_list)}개)")
                    image_ios = [io.BytesIO(img_bytes) for img_bytes in image_bytes_list]
                    result = await analyzer.analyze_images(image_ios, source_url=url)
                else:
                    # Video analysis (fallback for non-SNS URLs or failed downloads)
                    print(f"영상 분석 시작: {url}")
                    result = await analyzer.analyze(url, extract_audio=extract_audio)

            # Update with results
            analysis.status = AnalysisStatus.COMPLETED.value
            analysis.duration = result.get("duration")
            analysis.segments = result.get("segments", [])
            analysis.hook_points = result.get("hook_points", [])
            analysis.edge_points = result.get("edge_points", [])
            analysis.emotional_triggers = result.get("emotional_triggers", [])
            analysis.pain_points = result.get("pain_points", [])
            analysis.application_points = result.get("application_points", [])
            analysis.selling_points = result.get("selling_points", [])
            analysis.cta_analysis = result.get("cta_analysis")
            analysis.structure_pattern = result.get("structure_pattern")
            analysis.recommendations = result.get("recommendations", [])
            analysis.transcript = result.get("transcript")
            analysis.overall_evaluation = result.get("overall_evaluation")

            # Update title with AI-generated reference_name if available
            reference_name = result.get("reference_name")
            if reference_name and isinstance(reference_name, str) and reference_name.strip():
                analysis.title = reference_name.strip()

            await db.commit()

        except Exception as e:
            error_msg = str(e)

            # Rollback any pending transaction before handling error
            try:
                await db.rollback()
            except Exception:
                pass

            # Check if this is a "no media found" error - delete record instead of keeping failed
            is_no_media_error = (
                "No video formats found" in error_msg or
                "no video formats" in error_msg.lower() or
                "다운로드된 미디어 없음" in error_msg
            )

            if is_no_media_error:
                # No media at all (no images, no videos) - delete the record
                try:
                    result = await db.execute(
                        select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
                    )
                    analysis = result.scalar_one_or_none()
                    if analysis:
                        await db.delete(analysis)
                        await db.commit()
                        print(f"미디어 없음 - 분석 레코드 삭제: {analysis_id}")
                except Exception as delete_error:
                    print(f"Failed to delete analysis record: {delete_error}")
                return  # Exit without saving failed record

            # Improve timeout error message
            if "504" in error_msg or "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_msg = "Gemini 분석 실패: 504 The request timed out. 영상이 너무 길거나 서버가 바쁩니다. 잠시 후 다시 시도해주세요."

            # Update analysis with error (for other types of errors)
            try:
                result = await db.execute(
                    select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
                )
                analysis = result.scalar_one_or_none()

                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = error_msg
                    analysis.recommendations = [{"action": f"분석 실패: {error_msg}"}]
                    await db.commit()
            except Exception as commit_error:
                print(f"Failed to update error status: {commit_error}")
