import os
import asyncio
import json
import re
import tempfile
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
import base64

import google.generativeai as genai
from PIL import Image

from app.core.config import settings


class ReferenceAnalyzer:
    """
    Gemini 기반 레퍼런스 영상 분석기
    - 타임라인 세그먼트 (hook, problem, solution 등)
    - 후킹 포인트 및 기법
    - 셀링 포인트 및 설득 기법
    - 구조 패턴 및 권장사항
    """

    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        # 레퍼런스 분석은 안정적인 gemini-2.5-flash 사용 (프리뷰 모델은 할루시네이션 위험)
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def analyze(
        self,
        video_url: str,
        extract_audio: bool = True,
    ) -> Dict[str, Any]:
        """
        분석 파이프라인:
        1. 영상 다운로드
        2. 키 프레임 추출
        3. Gemini로 분석 (통신 오류 시 최대 3회 재시도)
        """
        video_path = None
        frames = []
        try:
            # 1. 영상 다운로드
            video_path = await self._download_video(video_url)

            # 2. 메타데이터 추출
            metadata = await self._get_metadata(video_path)

            # 3. 키 프레임 추출 (영상 길이에 따라 동적 조절)
            duration = metadata.get("duration", 0)
            if duration <= 60:
                # 1분 이하: 1 FPS (최대 60프레임)
                target_frames = min(60, int(duration))
            elif duration <= 600:
                # 1~10분: 0.5 FPS (최대 300프레임)
                target_frames = min(300, int(duration * 0.5))
            else:
                # 10분 이상: 0.25 FPS (최대 1500프레임)
                target_frames = min(1500, int(duration * 0.25))

            frames = await self._extract_frames(
                video_path,
                duration=duration,
                target_frames=target_frames
            )

            # 4. Gemini로 분석 (통신 오류 시 최대 3회 재시도)
            max_retries = 3
            last_error = None

            for attempt in range(1, max_retries + 1):
                try:
                    analysis = await self._analyze_with_gemini(
                        video_path=video_path,
                        frames=frames,
                        duration=metadata.get("duration", 0),
                    )
                    # 분석 성공 시 루프 종료
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()

                    # 통신/네트워크 관련 오류인지 확인
                    is_network_error = any(keyword in error_msg for keyword in [
                        'timeout', 'timed out', 'connection', 'network',
                        'reset', 'refused', 'unavailable', '503', '504',
                        '502', '500', 'internal', 'server error', 'rate limit',
                        'quota', 'overloaded', 'resource exhausted'
                    ])

                    if is_network_error and attempt < max_retries:
                        wait_time = attempt * 5  # 5초, 10초, 15초 대기
                        print(f"통신 오류 발생 (시도 {attempt}/{max_retries}): {e}")
                        print(f"{wait_time}초 후 재시도...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # 네트워크 오류가 아니거나 마지막 시도인 경우
                        raise
            else:
                # 모든 재시도 실패
                raise Exception(f"Gemini 분석 실패 (최대 {max_retries}회 재시도 후): {last_error}")

            # 5. 프레임 정리
            for frame in frames:
                if os.path.exists(frame["path"]):
                    os.remove(frame["path"])

            return {
                "duration": metadata.get("duration"),
                "reference_name": analysis.get("reference_name"),
                "segments": analysis.get("segments", []),
                "hook_points": analysis.get("hook_points", []),
                "edge_points": analysis.get("edge_points", []),
                "emotional_triggers": analysis.get("emotional_triggers", []),
                "pain_points": analysis.get("pain_points", []),
                "application_points": analysis.get("application_points", []),
                "selling_points": analysis.get("selling_points", []),
                "cta_analysis": analysis.get("cta_analysis", {}),
                "structure_pattern": analysis.get("structure_pattern", {}),
                "recommendations": analysis.get("recommendations", []),
                "transcript": analysis.get("transcript"),
                "overall_evaluation": analysis.get("overall_evaluation", {}),
            }

        finally:
            # 프레임 정리 (예외 발생 시에도 정리)
            for frame in frames:
                if os.path.exists(frame.get("path", "")):
                    try:
                        os.remove(frame["path"])
                    except:
                        pass
            if video_path and os.path.exists(video_path):
                os.remove(video_path)

    async def _download_video(self, url: str) -> str:
        """yt-dlp로 영상 다운로드"""
        output_path = self.temp_dir / f"video_{os.urandom(8).hex()}.mp4"

        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]/best",  # 720p 우선, 없으면 best
            "-o", str(output_path),
            "--no-playlist",
            "--no-check-certificates",
            url,
        ]

        # Add cookies if available
        cookies_file = os.environ.get("YOUTUBE_COOKIES_FILE", "/app/config/youtube_cookies.txt")
        if os.path.exists(cookies_file):
            cmd.insert(-1, "--cookies")
            cmd.insert(-1, cookies_file)

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_text = stderr.decode()
            # Convert technical errors to user-friendly messages
            if "Sign in to confirm you're not a bot" in error_text:
                raise Exception("YouTube에서 봇으로 감지되어 다운로드할 수 없습니다. 직접 영상을 다운로드하여 업로드해주세요.")
            elif "Video unavailable" in error_text or "Private video" in error_text:
                raise Exception("영상이 비공개이거나 삭제되었습니다.")
            elif "age-restricted" in error_text.lower():
                raise Exception("연령 제한 영상은 다운로드할 수 없습니다.")
            else:
                raise Exception(f"영상 다운로드 실패. 직접 영상을 다운로드하여 업로드해주세요.")

        # yt-dlp가 확장자를 바꿀 수 있으므로 실제 파일 찾기
        if not output_path.exists():
            possible_files = list(self.temp_dir.glob(f"video_{output_path.stem.split('_')[1]}*"))
            if possible_files:
                return str(possible_files[0])
            raise Exception("다운로드된 영상 파일을 찾을 수 없습니다")

        return str(output_path)

    async def _get_metadata(self, video_path: str) -> Dict[str, Any]:
        """ffprobe로 메타데이터 추출"""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {"duration": 0}

        try:
            data = json.loads(stdout.decode())
            duration = float(data.get("format", {}).get("duration", 0))
            return {"duration": duration}
        except:
            return {"duration": 0}

    async def _extract_frames(
        self,
        video_path: str,
        duration: float = 0,
        target_frames: int = 20,
    ) -> List[Dict[str, Any]]:
        """프레임 추출 - 영상 전체를 균등하게 샘플링"""
        frames_dir = self.temp_dir / f"frames_{os.urandom(8).hex()}"
        frames_dir.mkdir(exist_ok=True)

        # 영상 길이에 맞게 fps 계산 (전체 영상을 target_frames개로 균등 분할)
        if duration > 0:
            fps = target_frames / duration
            fps = max(0.1, min(fps, 2))  # 0.1 ~ 2 fps 범위로 제한
        else:
            fps = 1

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-q:v", "2",
            str(frames_dir / "frame_%04d.jpg"),
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await process.communicate()

        frames = []
        for i, frame_file in enumerate(sorted(frames_dir.glob("frame_*.jpg"))):
            frames.append({
                "path": str(frame_file),
                "timestamp": i / fps,
                "index": i,
            })

        return frames

    async def _analyze_with_gemini(
        self,
        video_path: str,
        frames: List[Dict[str, Any]],
        duration: float,
    ) -> Dict[str, Any]:
        """Gemini로 영상 분석"""

        # 프레임 샘플링 (영상 길이에 따라 Gemini 전송 수 조절)
        # 짧은 영상: 더 많이, 긴 영상: 효율적으로
        if duration <= 60:
            max_gemini_frames = min(50, len(frames))  # 1분 이하: 최대 50개
        elif duration <= 600:
            max_gemini_frames = min(100, len(frames))  # 1~10분: 최대 100개
        else:
            max_gemini_frames = min(200, len(frames))  # 10분 이상: 최대 200개

        if len(frames) > max_gemini_frames:
            sample_interval = len(frames) // max_gemini_frames
            sampled_frames = frames[::sample_interval][:max_gemini_frames]
        else:
            sampled_frames = frames

        # 이미지 로드
        images = []
        for frame in sampled_frames:
            img = Image.open(frame["path"])
            images.append(img)

        # 분석 프롬프트
        prompt = f"""당신은 10년 경력의 퍼포먼스 마케팅 전문가입니다. 이 영상 프레임들을 심층 분석해주세요.

영상 정보:
- 길이: {duration:.1f}초
- 프레임 수: {len(frames)}개 (샘플: {len(sampled_frames)}개)

다음 항목들을 마케팅 관점에서 **철저하고 상세하게** 분석해주세요.
**중요**: 각 항목을 가능한 한 많이 찾아내세요. 예시는 형식 참고용이며, 실제로는 발견되는 모든 요소를 포함해야 합니다.

1. **타임라인 세그먼트** (영상 전체를 빠짐없이 커버): 영상 전체 길이({duration:.1f}초)를 빠짐없이 분석하여 각 구간의 유형과 역할을 파악
   - hook: 주목 끌기 (보통 0-3초)
   - problem: 문제/고충점 제기
   - agitation: 문제 심화/감정 자극
   - solution: 해결책 제시
   - feature: 기능/특징 설명
   - benefit: 혜택/가치 전달
   - social_proof: 사회적 증거
   - urgency: 긴급성/희소성
   - cta: 행동 유도

   **engagement_score 평가 기준** (0.0~1.0):
   - 시각적 자극 강도 (25%): 화면 움직임, 색상 대비, 줌인/아웃, 전환 효과
   - 정보 밀도 (25%): 새로운 정보가 전달되는 속도, 시청자가 얻는 가치
   - 감정적 자극 (25%): 궁금증, 긴장감, 공감, 흥미 유발 정도
   - 시청 유지력 (25%): 이 구간에서 시청자가 이탈하지 않고 계속 볼 확률

   예시: hook 구간에서 강렬한 비주얼+궁금증 유발 = 0.9, 단조로운 설명 = 0.4

2. **후킹 포인트** (최소 2-5개 이상 찾기): 시청자가 스크롤을 멈추는 순간
   - 기법: curiosity_gap(궁금증 유발), pattern_interrupt(패턴 파괴), shocking_statement(충격적 발언), question(질문형), contradiction(역설)
   - 효과 점수와 재사용 가능한 템플릿
   - 영상 전체에서 발견되는 모든 후킹 요소를 빠짐없이 추출

3. **엣지 포인트** (최소 3-5개 이상 찾기): 경쟁사와 차별화되는 독특한 요소
   - 시각적 차별화 (색상, 구도, 스타일)
   - 메시지 차별화 (톤앤매너, 표현 방식)
   - 포지셔닝 차별화
   - 각 카테고리별로 최소 1개 이상 분석

4. **감정 트리거** (최소 3-5개 이상 찾기): 소비자 심리를 자극하는 요소
   - FOMO(놓칠까봐 두려움), 공포/불안, 희망/기대, 욕망, 소속감, 자아실현
   - 각 트리거가 나타나는 시점과 강도
   - 영상에서 사용된 모든 감정 자극 요소 분석

5. **페인포인트 활용** (최소 2-4개 이상 찾기): 소비자 고충점을 어떻게 건드리는가
   - 명시적 페인포인트 (직접 언급)
   - 암시적 페인포인트 (이미지/상황으로 암시)
   - 공감 유도 기법

6. **활용 포인트** (최소 5-8개 이상 찾기): 이 영상에서 바로 적용할 수 있는 요소
   - 복사 가능한 문구/스크립트 템플릿 (최소 2개)
   - 재현 가능한 촬영 기법 (최소 2개)
   - 적용 가능한 편집 패턴 (최소 2개)

7. **셀링 포인트** (최소 3-5개 이상 찾기): 설득의 핵심 요소
   - 주장(claim)과 근거(evidence)
   - 설득 기법: social_proof, scarcity, authority, reciprocity, liking, commitment
   - 영상에서 사용된 모든 설득 요소 분석

8. **CTA 분석**: 행동 유도 전략
   - CTA 유형과 위치
   - 긴급성/희소성 요소
   - 장벽 제거 전략

9. **구조 패턴**: 전체 흐름 (예: AIDA, PAS, BAB 등)

10. **적용 권장사항**: 이 영상의 성공 요소를 내 영상에 적용하는 구체적 방법 5개

**중요 - 점수 피드백 형식**:
모든 점수에 대해 반드시 **평가 기준별 세부 점수와 이유**를 제공하세요.

**engagement_score (세그먼트용)**:
"score_breakdown": {{
  "visual_impact": {{"score": 0.85, "weight": "25%", "reason": "구체적인 평가 이유"}},
  "info_density": {{"score": 0.7, "weight": "25%", "reason": "구체적인 평가 이유"}},
  "emotional_appeal": {{"score": 0.9, "weight": "25%", "reason": "구체적인 평가 이유"}},
  "retention_power": {{"score": 0.8, "weight": "25%", "reason": "구체적인 평가 이유"}}
}},
"total_reason": "위 기준들을 종합한 최종 점수 산출 이유"

**effectiveness_score (후킹 포인트용)**:
"score_breakdown": {{
  "attention_grab": {{"score": 0.9, "weight": "30%", "reason": "스크롤 멈춤 효과 평가"}},
  "curiosity_trigger": {{"score": 0.8, "weight": "30%", "reason": "궁금증 유발 정도"}},
  "memorability": {{"score": 0.7, "weight": "20%", "reason": "기억에 남는 정도"}},
  "reusability": {{"score": 0.85, "weight": "20%", "reason": "다른 콘텐츠에 재활용 가능성"}}
}},
"total_reason": "종합 평가 이유"

**impact_score (엣지 포인트용)**:
"score_breakdown": {{
  "uniqueness": {{"score": 0.9, "weight": "40%", "reason": "경쟁사 대비 독창성"}},
  "brand_fit": {{"score": 0.8, "weight": "30%", "reason": "브랜드 아이덴티티 적합성"}},
  "scalability": {{"score": 0.7, "weight": "30%", "reason": "다른 콘텐츠에 확장 적용 가능성"}}
}},
"total_reason": "종합 평가 이유"

**intensity (감정 트리거용)**:
"score_breakdown": {{
  "emotional_depth": {{"score": 0.85, "weight": "40%", "reason": "감정 자극 깊이"}},
  "trigger_clarity": {{"score": 0.9, "weight": "30%", "reason": "감정 트리거의 명확성"}},
  "action_motivation": {{"score": 0.8, "weight": "30%", "reason": "행동 유도 연결성"}}
}},
"total_reason": "종합 평가 이유"

**effectiveness (셀링 포인트용)**:
"score_breakdown": {{
  "claim_credibility": {{"score": 0.8, "weight": "35%", "reason": "주장의 신뢰성"}},
  "evidence_strength": {{"score": 0.85, "weight": "35%", "reason": "근거의 설득력"}},
  "conversion_potential": {{"score": 0.9, "weight": "30%", "reason": "구매 전환 가능성"}}
}},
"total_reason": "종합 평가 이유"

**cta_analysis.effectiveness_score**:
"score_breakdown": {{
  "clarity": {{"score": 0.9, "weight": "30%", "reason": "CTA 메시지 명확성"}},
  "urgency": {{"score": 0.7, "weight": "25%", "reason": "긴급성/희소성 요소"}},
  "barrier_removal": {{"score": 0.8, "weight": "25%", "reason": "행동 장벽 제거 정도"}},
  "visual_prominence": {{"score": 0.85, "weight": "20%", "reason": "시각적 눈에 띔 정도"}}
}},
"total_reason": "종합 평가 이유"

**중요**: segments는 영상 전체 길이({duration:.1f}초)를 빠짐없이 커버해야 합니다. 처음부터 끝까지 모든 구간을 분석하세요.

JSON 형식으로만 응답하세요:
```json
{{
  "reference_name": "분석 결과를 바탕으로 이 콘텐츠의 핵심 내용을 설명하는 한국어 문장 (30자 이내)",
  "segments": [
    {{
      "start_time": 0.0, "end_time": 3.0, "segment_type": "hook",
      "visual_description": "설명", "engagement_score": 0.85,
      "score_breakdown": {{
        "visual_impact": {{"score": 0.9, "weight": "25%", "reason": "강렬한 색상 대비와 빠른 줌인으로 시선 집중"}},
        "info_density": {{"score": 0.8, "weight": "25%", "reason": "핵심 메시지가 3초 내 전달됨"}},
        "emotional_appeal": {{"score": 0.85, "weight": "25%", "reason": "궁금증과 기대감 효과적 유발"}},
        "retention_power": {{"score": 0.85, "weight": "25%", "reason": "다음 장면 보고 싶은 욕구 자극"}}
      }},
      "total_reason": "시각적 임팩트와 감정 자극이 조화롭게 작용하여 높은 engagement 달성",
      "techniques": ["기법"]
    }}
  ],
  "hook_points": [
    {{
      "timestamp": "0:00-0:03", "hook_type": "curiosity_gap", "effectiveness_score": 0.85,
      "score_breakdown": {{
        "attention_grab": {{"score": 0.9, "weight": "30%", "reason": "예상치 못한 질문으로 즉시 주목"}},
        "curiosity_trigger": {{"score": 0.85, "weight": "30%", "reason": "답을 알고 싶은 욕구 강하게 유발"}},
        "memorability": {{"score": 0.8, "weight": "20%", "reason": "독특한 표현으로 기억에 남음"}},
        "reusability": {{"score": 0.85, "weight": "20%", "reason": "다양한 제품에 쉽게 적용 가능한 구조"}}
      }},
      "total_reason": "질문형 후킹으로 시청자 참여 유도에 성공",
      "description": "설명", "adaptable_template": "템플릿 문구"
    }}
  ],
  "edge_points": [
    {{
      "category": "visual", "description": "차별화 요소 설명", "impact_score": 0.8,
      "score_breakdown": {{
        "uniqueness": {{"score": 0.85, "weight": "40%", "reason": "경쟁사에서 볼 수 없는 앵글과 색감"}},
        "brand_fit": {{"score": 0.8, "weight": "30%", "reason": "브랜드 톤앤매너와 일관성 있음"}},
        "scalability": {{"score": 0.75, "weight": "30%", "reason": "다른 제품 라인에도 적용 가능"}}
      }},
      "total_reason": "독창적인 비주얼 스타일이 브랜드 차별화에 기여",
      "how_to_apply": "적용 방법"
    }}
  ],
  "emotional_triggers": [
    {{
      "timestamp": "0:05-0:10", "trigger_type": "FOMO", "intensity": 0.9,
      "score_breakdown": {{
        "emotional_depth": {{"score": 0.9, "weight": "40%", "reason": "한정 수량 강조로 긴박감 조성"}},
        "trigger_clarity": {{"score": 0.85, "weight": "30%", "reason": "놓치면 후회할 것이라는 메시지 명확"}},
        "action_motivation": {{"score": 0.9, "weight": "30%", "reason": "즉시 구매 행동으로 연결"}}
      }},
      "total_reason": "긴급성과 희소성이 복합적으로 작용하여 강력한 FOMO 유발",
      "description": "어떻게 감정을 자극하는지"
    }}
  ],
  "pain_points": [
    {{"timestamp": "0:03-0:08", "pain_type": "explicit", "description": "페인포인트 내용", "empathy_technique": "공감 유도 기법"}}
  ],
  "application_points": [
    {{"type": "script_template", "content": "복사해서 쓸 수 있는 문구", "context": "사용 상황"}},
    {{"type": "filming_technique", "content": "촬영 기법", "context": "적용 방법"}},
    {{"type": "editing_pattern", "content": "편집 패턴", "context": "적용 방법"}}
  ],
  "selling_points": [
    {{
      "timestamp": "0:10-0:15", "claim": "주장", "evidence_type": "demonstration",
      "persuasion_technique": "social_proof", "effectiveness": 0.85,
      "score_breakdown": {{
        "claim_credibility": {{"score": 0.8, "weight": "35%", "reason": "구체적 수치로 신뢰도 확보"}},
        "evidence_strength": {{"score": 0.9, "weight": "35%", "reason": "실제 사용 영상이 강력한 증거"}},
        "conversion_potential": {{"score": 0.85, "weight": "30%", "reason": "구매 결정에 직접적 영향"}}
      }},
      "total_reason": "실증적 증거와 신뢰성 있는 주장이 설득력 있게 결합됨"
    }}
  ],
  "cta_analysis": {{
    "cta_type": "direct/soft/implied",
    "placement": "ending/throughout/multiple",
    "urgency_elements": ["한정 수량", "기간 한정"],
    "barrier_removal": ["무료 체험", "환불 보장"],
    "effectiveness_score": 0.8,
    "score_breakdown": {{
      "clarity": {{"score": 0.85, "weight": "30%", "reason": "링크 클릭이라는 행동 지시가 명확"}},
      "urgency": {{"score": 0.75, "weight": "25%", "reason": "오늘만 특가라는 시간 제한 효과적"}},
      "barrier_removal": {{"score": 0.8, "weight": "25%", "reason": "무료 배송으로 구매 장벽 낮춤"}},
      "visual_prominence": {{"score": 0.8, "weight": "20%", "reason": "CTA 버튼이 눈에 잘 띔"}}
    }},
    "total_reason": "명확한 행동 지시와 장벽 제거 전략이 효과적으로 결합됨"
  }},
  "structure_pattern": {{
    "framework": "PAS",
    "flow": ["hook", "problem", "agitation", "solution", "cta"],
    "effectiveness_note": "이 구조가 효과적인 이유"
  }},
  "transcript": "영상 텍스트/나레이션",
  "recommendations": [
    {{"priority": 1, "action": "구체적 행동", "reason": "이유", "example": "예시"}}
  ],
  "overall_evaluation": {{
    "total_score": 0.82,
    "one_line_review": "후킹과 감정 자극이 탁월하나, CTA 명확성과 사회적 증거가 보강되면 더욱 효과적일 것",
    "strengths": ["강력한 첫 3초 후킹으로 이탈률 최소화", "FOMO 활용한 감정 자극이 효과적"],
    "weaknesses": ["CTA가 다소 늦게 등장", "구체적인 수치 증거 부족"]
  }}
}}
```"""

        # Gemini API 호출 (이미지 + 텍스트) - timeout 제거, 상위에서 재시도 처리
        response = await asyncio.to_thread(
            self.model.generate_content,
            [prompt] + images
        )

        result_text = response.text

        # JSON 추출 및 파싱
        parsed = self._extract_and_parse_json(result_text)
        if parsed:
            return parsed

        # JSON 파싱 실패 시 재시도 (더 명확한 프롬프트로)
        print("JSON 파싱 실패, 재시도 중...")
        retry_prompt = f"이전 응답의 JSON 형식이 올바르지 않았습니다. 순수한 JSON만 출력해주세요. 마크다운 코드 블록 없이, 설명 없이, 오직 JSON 객체만 출력하세요.\n\n원본 요청:\n{prompt}"

        retry_response = await asyncio.to_thread(
            self.model.generate_content,
            [retry_prompt] + images
        )

        parsed = self._extract_and_parse_json(retry_response.text)
        if parsed:
            return parsed

        print(f"재시도 후에도 JSON 파싱 실패")
        return self._get_fallback_analysis(duration)

    def _extract_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """텍스트에서 JSON 추출 및 파싱 (여러 방법 시도)"""
        import re

        # 방법 1: ```json ... ``` 블록 추출
        if "```json" in text:
            try:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # 방법 2: ``` ... ``` 블록 추출
        if "```" in text:
            try:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass

        # 방법 3: { } 로 둘러싸인 부분 찾기
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except:
            pass

        # 방법 4: 일반적인 JSON 오류 수정 시도
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                # trailing comma 제거
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                # 작은따옴표를 큰따옴표로
                json_str = json_str.replace("'", '"')
                return json.loads(json_str)
        except:
            pass

        return None

    def _get_fallback_analysis(self, duration: float) -> Dict[str, Any]:
        """폴백 분석 결과"""
        return {
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": min(3.0, duration),
                    "segment_type": "hook",
                    "visual_description": "오프닝",
                    "engagement_score": 0.5,
                    "techniques": ["분석 필요"],
                }
            ],
            "hook_points": [],
            "edge_points": [],
            "emotional_triggers": [],
            "pain_points": [],
            "application_points": [],
            "selling_points": [],
            "cta_analysis": {},
            "structure_pattern": {
                "framework": "unknown",
                "flow": [],
                "effectiveness_note": "분석 중 오류가 발생했습니다."
            },
            "recommendations": [
                {
                    "priority": 1,
                    "action": "다시 분석을 시도해주세요",
                    "reason": "AI 응답 파싱 중 오류가 발생했습니다",
                    "example": "영상 URL을 다시 입력하거나 다른 영상을 시도해보세요"
                }
            ],
        }

    async def analyze_images(
        self,
        image_bytes_list: List[Any],
        source_url: str = "",
    ) -> Dict[str, Any]:
        """
        이미지 게시물 분석 (Instagram, Facebook 등)
        - 마케팅 관점 분석
        - 셀링포인트, 후킹요소 등 추출

        Args:
            image_bytes_list: List of bytes, BytesIO, or base64 strings
            source_url: Original URL for context
        """
        import io

        try:
            # 이미지 로드
            images = []
            for img_data in image_bytes_list:
                try:
                    if isinstance(img_data, str):
                        # base64 string
                        img = Image.open(io.BytesIO(base64.b64decode(img_data)))
                    elif isinstance(img_data, io.BytesIO):
                        # BytesIO object
                        img_data.seek(0)
                        img = Image.open(img_data)
                    elif isinstance(img_data, bytes):
                        # raw bytes
                        img = Image.open(io.BytesIO(img_data))
                    else:
                        # Assume it's already a PIL Image
                        img = img_data
                    images.append(img)
                except Exception as e:
                    print(f"이미지 로드 실패: {e}")
                    continue

            if not images:
                raise Exception("분석할 이미지가 없습니다")

            # Gemini 분석
            max_retries = 3
            last_error = None

            for attempt in range(1, max_retries + 1):
                try:
                    analysis = await self._analyze_images_with_gemini(images, source_url)
                    break
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    is_network_error = any(keyword in error_msg for keyword in [
                        'timeout', 'timed out', 'connection', 'network',
                        'reset', 'refused', 'unavailable', '503', '504',
                        '502', '500', 'internal', 'server error', 'rate limit',
                        'quota', 'overloaded', 'resource exhausted'
                    ])

                    if is_network_error and attempt < max_retries:
                        wait_time = attempt * 5
                        print(f"통신 오류 발생 (시도 {attempt}/{max_retries}): {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise
            else:
                raise Exception(f"Gemini 분석 실패 (최대 {max_retries}회 재시도 후): {last_error}")

            return {
                "duration": None,
                "reference_name": analysis.get("reference_name"),
                "segments": analysis.get("segments", []),
                "hook_points": analysis.get("hook_points", []),
                "edge_points": analysis.get("edge_points", []),
                "emotional_triggers": analysis.get("emotional_triggers", []),
                "pain_points": analysis.get("pain_points", []),
                "application_points": analysis.get("application_points", []),
                "selling_points": analysis.get("selling_points", []),
                "cta_analysis": analysis.get("cta_analysis", {}),
                "structure_pattern": analysis.get("structure_pattern", {}),
                "recommendations": analysis.get("recommendations", []),
                "transcript": analysis.get("transcript"),
                "overall_evaluation": analysis.get("overall_evaluation", {}),
            }

        except Exception as e:
            print(f"이미지 분석 실패: {e}")
            raise

    async def _analyze_images_with_gemini(
        self,
        images: List[Image.Image],
        source_url: str = "",
    ) -> Dict[str, Any]:
        """Gemini로 이미지 분석"""

        image_count = len(images)
        is_carousel = image_count > 1

        prompt = f"""당신은 10년 경력의 퍼포먼스 마케팅 전문가입니다. 이 SNS 이미지 게시물을 심층 분석해주세요.

게시물 정보:
- 이미지 수: {image_count}개 {'(캐러셀 게시물)' if is_carousel else '(단일 이미지)'}
- 플랫폼: {'Instagram' if 'instagram' in source_url.lower() else 'Facebook' if 'facebook' in source_url.lower() else 'SNS'}

다음 항목들을 마케팅 관점에서 **철저하고 상세하게** 분석해주세요.
**중요**: 각 항목을 가능한 한 많이 찾아내세요. 예시는 형식 참고용이며, 실제로는 발견되는 모든 요소를 포함해야 합니다.

1. **이미지 세그먼트** (모든 이미지를 분석): 각 이미지(슬라이드)의 역할과 마케팅 기능
   - hook: 주목 끌기 (보통 첫 번째 이미지)
   - problem: 문제/고충점 제기
   - solution: 해결책 제시
   - feature: 기능/특징 설명
   - benefit: 혜택/가치 전달
   - social_proof: 사회적 증거 (후기, 인증)
   - cta: 행동 유도
   - other: 기타

   **engagement_score 평가 기준** (0.0~1.0):
   - 시각적 임팩트 (30%): 색상, 구도, 타이포그래피
   - 정보 전달력 (25%): 메시지 명확성, 가독성
   - 감정적 호소 (25%): 공감, 욕망 자극
   - 스크롤 스토핑력 (20%): 첫 인상의 강렬함

2. **후킹 포인트** (최소 2-5개 이상 찾기): 스크롤을 멈추게 하는 요소
   - 기법: curiosity_gap(궁금증), pattern_interrupt(패턴 파괴), bold_claim(대담한 주장), visual_contrast(시각적 대비), question(질문형)
   - 효과 점수와 재사용 가능한 템플릿
   - 이미지에서 발견되는 모든 후킹 요소를 빠짐없이 추출

3. **엣지 포인트** (최소 3-5개 이상 찾기): 경쟁사와 차별화되는 독특한 요소
   - 시각적 차별화 (색상, 구도, 스타일)
   - 메시지 차별화 (카피, 톤앤매너)
   - 브랜딩 차별화
   - 각 카테고리별로 최소 1개 이상 분석

4. **감정 트리거** (최소 3-5개 이상 찾기): 소비자 심리를 자극하는 요소
   - FOMO, 신뢰, 희망/기대, 욕망, 자아실현 등
   - 이미지에서 사용된 모든 감정 자극 요소 분석

5. **페인포인트 활용** (최소 2-4개 이상 찾기): 소비자 고충점 활용 방식

6. **활용 포인트** (최소 5-8개 이상 찾기): 바로 적용할 수 있는 요소
   - 복사 가능한 카피/문구 (최소 2개)
   - 재현 가능한 디자인 요소 (최소 2개)
   - 레이아웃 패턴 (최소 2개)

7. **셀링 포인트** (최소 3-5개 이상 찾기): 설득의 핵심 요소
   - 주장(claim)과 근거
   - 설득 기법: social_proof, scarcity, authority, before_after, comparison
   - 이미지에서 사용된 모든 설득 요소 분석

8. **CTA 분석**: 행동 유도 전략

9. **구조 패턴**: 캐러셀 흐름 (예: 후킹→문제→해결→증거→CTA)

10. **적용 권장사항**: 이 게시물의 성공 요소를 내 콘텐츠에 적용하는 방법 5개

**중요 - 점수 피드백 형식**:
모든 점수에 대해 반드시 **평가 기준별 세부 점수와 이유**를 제공하세요.

**engagement_score (이미지 세그먼트용)**:
"score_breakdown": {{
  "visual_impact": {{"score": 0.85, "weight": "30%", "reason": "색상, 구도, 타이포그래피 평가"}},
  "info_delivery": {{"score": 0.8, "weight": "25%", "reason": "메시지 명확성, 가독성 평가"}},
  "emotional_appeal": {{"score": 0.85, "weight": "25%", "reason": "공감, 욕망 자극 정도"}},
  "scroll_stopping": {{"score": 0.9, "weight": "20%", "reason": "첫 인상의 강렬함"}}
}},
"total_reason": "종합 평가 이유"

**effectiveness_score (후킹 포인트용)**:
"score_breakdown": {{
  "attention_grab": {{"score": 0.9, "weight": "30%", "reason": "스크롤 멈춤 효과 평가"}},
  "curiosity_trigger": {{"score": 0.85, "weight": "30%", "reason": "궁금증 유발 정도"}},
  "memorability": {{"score": 0.8, "weight": "20%", "reason": "기억에 남는 정도"}},
  "reusability": {{"score": 0.85, "weight": "20%", "reason": "다른 콘텐츠에 재활용 가능성"}}
}},
"total_reason": "종합 평가 이유"

**impact_score (엣지 포인트용)**:
"score_breakdown": {{
  "uniqueness": {{"score": 0.9, "weight": "40%", "reason": "경쟁사 대비 독창성"}},
  "brand_fit": {{"score": 0.8, "weight": "30%", "reason": "브랜드 아이덴티티 적합성"}},
  "scalability": {{"score": 0.75, "weight": "30%", "reason": "다른 콘텐츠에 확장 적용 가능성"}}
}},
"total_reason": "종합 평가 이유"

**intensity (감정 트리거용)**:
"score_breakdown": {{
  "emotional_depth": {{"score": 0.85, "weight": "40%", "reason": "감정 자극 깊이"}},
  "trigger_clarity": {{"score": 0.9, "weight": "30%", "reason": "감정 트리거의 명확성"}},
  "action_motivation": {{"score": 0.85, "weight": "30%", "reason": "행동 유도 연결성"}}
}},
"total_reason": "종합 평가 이유"

**effectiveness (셀링 포인트용)**:
"score_breakdown": {{
  "claim_credibility": {{"score": 0.8, "weight": "35%", "reason": "주장의 신뢰성"}},
  "evidence_strength": {{"score": 0.85, "weight": "35%", "reason": "근거의 설득력"}},
  "conversion_potential": {{"score": 0.9, "weight": "30%", "reason": "구매 전환 가능성"}}
}},
"total_reason": "종합 평가 이유"

**cta_analysis.effectiveness_score**:
"score_breakdown": {{
  "clarity": {{"score": 0.85, "weight": "30%", "reason": "CTA 메시지 명확성"}},
  "urgency": {{"score": 0.7, "weight": "25%", "reason": "긴급성/희소성 요소"}},
  "barrier_removal": {{"score": 0.8, "weight": "25%", "reason": "행동 장벽 제거 정도"}},
  "visual_prominence": {{"score": 0.85, "weight": "20%", "reason": "시각적 눈에 띔 정도"}}
}},
"total_reason": "종합 평가 이유"

JSON 형식으로만 응답하세요:
```json
{{
  "reference_name": "분석 결과를 바탕으로 이 콘텐츠의 핵심 내용을 설명하는 한국어 문장 (30자 이내)",
  "segments": [
    {{
      "start_time": 0, "end_time": 1, "segment_type": "hook",
      "visual_description": "첫 번째 이미지 설명", "engagement_score": 0.85,
      "score_breakdown": {{
        "visual_impact": {{"score": 0.9, "weight": "30%", "reason": "강렬한 색상 대비와 시선 유도 구도"}},
        "info_delivery": {{"score": 0.8, "weight": "25%", "reason": "핵심 메시지가 한눈에 들어옴"}},
        "emotional_appeal": {{"score": 0.85, "weight": "25%", "reason": "궁금증과 기대감 효과적 유발"}},
        "scroll_stopping": {{"score": 0.9, "weight": "20%", "reason": "첫인상이 강렬하여 스크롤 멈춤"}}
      }},
      "total_reason": "시각적 임팩트와 정보 전달력이 균형있게 조화됨",
      "techniques": ["기법"]
    }}
  ],
  "hook_points": [
    {{
      "timestamp": "이미지 1", "hook_type": "curiosity_gap", "effectiveness_score": 0.85,
      "score_breakdown": {{
        "attention_grab": {{"score": 0.9, "weight": "30%", "reason": "예상치 못한 비주얼로 즉시 주목"}},
        "curiosity_trigger": {{"score": 0.85, "weight": "30%", "reason": "다음 슬라이드 보고 싶은 욕구 유발"}},
        "memorability": {{"score": 0.8, "weight": "20%", "reason": "독특한 구도로 기억에 남음"}},
        "reusability": {{"score": 0.85, "weight": "20%", "reason": "다양한 제품에 쉽게 적용 가능"}}
      }},
      "total_reason": "시각적 후킹이 스크롤 멈춤에 효과적으로 작용",
      "description": "설명", "elements": ["요소"], "adaptable_template": "템플릿 문구"
    }}
  ],
  "edge_points": [
    {{
      "category": "visual", "description": "차별화 요소", "impact_score": 0.8,
      "score_breakdown": {{
        "uniqueness": {{"score": 0.85, "weight": "40%", "reason": "경쟁사에서 볼 수 없는 색상 조합"}},
        "brand_fit": {{"score": 0.8, "weight": "30%", "reason": "브랜드 톤앤매너와 일관성 유지"}},
        "scalability": {{"score": 0.75, "weight": "30%", "reason": "다른 캠페인에도 적용 가능"}}
      }},
      "total_reason": "독창적인 비주얼이 브랜드 차별화에 기여",
      "how_to_apply": "적용 방법"
    }}
  ],
  "emotional_triggers": [
    {{
      "timestamp": "이미지 2", "trigger_type": "FOMO", "intensity": 0.9,
      "score_breakdown": {{
        "emotional_depth": {{"score": 0.9, "weight": "40%", "reason": "한정판 강조로 긴박감 조성"}},
        "trigger_clarity": {{"score": 0.85, "weight": "30%", "reason": "놓치면 후회라는 메시지 명확"}},
        "action_motivation": {{"score": 0.9, "weight": "30%", "reason": "즉시 구매 행동으로 연결"}}
      }},
      "total_reason": "긴급성과 희소성이 강력한 FOMO 유발",
      "description": "감정 자극 방식"
    }}
  ],
  "pain_points": [
    {{"timestamp": "이미지 1-2", "pain_type": "explicit", "description": "페인포인트", "empathy_technique": "공감 기법"}}
  ],
  "application_points": [
    {{"type": "copy_template", "content": "복사할 문구", "context": "사용 상황"}},
    {{"type": "design_element", "content": "디자인 요소", "context": "적용 방법"}},
    {{"type": "layout_pattern", "content": "레이아웃", "context": "적용 방법"}}
  ],
  "selling_points": [
    {{
      "timestamp": "이미지 3", "claim": "주장", "evidence_type": "testimonial",
      "persuasion_technique": "social_proof", "effectiveness": 0.85,
      "score_breakdown": {{
        "claim_credibility": {{"score": 0.8, "weight": "35%", "reason": "구체적 수치로 신뢰도 확보"}},
        "evidence_strength": {{"score": 0.9, "weight": "35%", "reason": "실제 후기가 강력한 증거"}},
        "conversion_potential": {{"score": 0.85, "weight": "30%", "reason": "구매 결정에 직접적 영향"}}
      }},
      "total_reason": "신뢰성 있는 후기가 설득력 있게 제시됨"
    }}
  ],
  "cta_analysis": {{
    "cta_type": "direct/soft/implied",
    "placement": "last_slide/throughout",
    "urgency_elements": [],
    "barrier_removal": [],
    "effectiveness_score": 0.8,
    "score_breakdown": {{
      "clarity": {{"score": 0.85, "weight": "30%", "reason": "행동 지시가 명확함"}},
      "urgency": {{"score": 0.7, "weight": "25%", "reason": "시간 제한 요소 효과적"}},
      "barrier_removal": {{"score": 0.8, "weight": "25%", "reason": "무료 배송으로 장벽 낮춤"}},
      "visual_prominence": {{"score": 0.85, "weight": "20%", "reason": "CTA 버튼이 눈에 띔"}}
    }},
    "total_reason": "명확한 행동 지시와 장벽 제거 전략이 효과적"
  }},
  "structure_pattern": {{
    "framework": "AIDA/PAS/Custom",
    "flow": ["hook", "problem", "solution", "proof", "cta"],
    "effectiveness_note": "구조가 효과적인 이유"
  }},
  "transcript": "이미지 내 텍스트 전체",
  "recommendations": [
    {{"priority": 1, "action": "구체적 행동", "reason": "이유", "example": "예시"}}
  ],
  "overall_evaluation": {{
    "total_score": 0.8,
    "one_line_review": "시각적 임팩트가 뛰어나나, 캐러셀 흐름 개선과 CTA 강화가 필요함",
    "strengths": ["첫 이미지 스크롤 스토핑 효과 우수", "브랜드 컬러 일관성 유지"],
    "weaknesses": ["후반부 슬라이드 집중도 저하", "구체적 혜택 설명 부족"]
  }}
}}
```"""

        response = await asyncio.to_thread(
            self.model.generate_content,
            [prompt] + images
        )

        result_text = response.text

        parsed = self._extract_and_parse_json(result_text)
        if parsed:
            return parsed

        # 재시도
        print("JSON 파싱 실패, 재시도 중...")
        retry_prompt = f"이전 응답의 JSON 형식이 올바르지 않았습니다. 순수한 JSON만 출력해주세요.\n\n원본 요청:\n{prompt}"

        retry_response = await asyncio.to_thread(
            self.model.generate_content,
            [retry_prompt] + images
        )

        parsed = self._extract_and_parse_json(retry_response.text)
        if parsed:
            return parsed

        return self._get_fallback_image_analysis(image_count)

    def _get_fallback_image_analysis(self, image_count: int) -> Dict[str, Any]:
        """이미지 분석 폴백 결과"""
        return {
            "segments": [
                {
                    "start_time": i,
                    "end_time": i + 1,
                    "segment_type": "other",
                    "visual_description": f"이미지 {i+1}",
                    "engagement_score": 0.5,
                    "techniques": ["분석 필요"],
                } for i in range(image_count)
            ],
            "hook_points": [],
            "edge_points": [],
            "emotional_triggers": [],
            "pain_points": [],
            "application_points": [],
            "selling_points": [],
            "cta_analysis": {},
            "structure_pattern": {
                "framework": "unknown",
                "flow": [],
                "effectiveness_note": "분석 중 오류가 발생했습니다."
            },
            "recommendations": [
                {
                    "priority": 1,
                    "action": "다시 분석을 시도해주세요",
                    "reason": "AI 응답 파싱 중 오류가 발생했습니다",
                    "example": "다시 시도해보세요"
                }
            ],
        }
