from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from enum import Enum
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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


class HookPoint(BaseModel):
    timestamp: str
    hook_type: str
    effectiveness_score: float
    description: Optional[str] = None
    elements: Optional[List[str]] = []
    adaptable_template: Optional[str] = None


class EdgePoint(BaseModel):
    category: str
    description: str
    impact_score: float
    how_to_apply: str


class EmotionalTrigger(BaseModel):
    timestamp: str
    trigger_type: str
    intensity: float
    description: str


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


class CTAAnalysis(BaseModel):
    cta_type: Optional[str] = None
    placement: Optional[str] = None
    urgency_elements: Optional[List[str]] = []
    barrier_removal: Optional[List[str]] = []
    effectiveness_score: Optional[float] = None


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
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a video URL for analysis"""
    analysis_id = str(uuid.uuid4())

    # Generate title from URL if not provided
    title = request.title
    if not title:
        title = f"분석 - {str(request.url).split('/')[-1][:50]}"

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


async def run_analysis(analysis_id: str, url: str, extract_audio: bool):
    """Background task to run video analysis"""
    from app.core.database import async_session_factory

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

            # Update status: ANALYZING before Gemini call
            analysis.status = AnalysisStatus.ANALYZING.value
            await db.commit()

            # Run analysis
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

            await db.commit()

        except Exception as e:
            error_msg = str(e)
            # Improve timeout error message
            if "504" in error_msg or "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_msg = "Gemini 분석 실패: 504 The request timed out. 영상이 너무 길거나 서버가 바쁩니다. 잠시 후 다시 시도해주세요."

            # Update analysis with error
            result = await db.execute(
                select(ReferenceAnalysis).where(ReferenceAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()

            if analysis:
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = error_msg
                analysis.recommendations = [{"action": f"분석 실패: {error_msg}"}]
                await db.commit()
