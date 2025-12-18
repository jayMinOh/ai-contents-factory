import os
import asyncio
import json
import re
import tempfile
from typing import Optional, List, Dict, Any
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
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
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

            # 3. 키 프레임 추출 (영상 전체를 균등하게 샘플링)
            frames = await self._extract_frames(
                video_path,
                duration=metadata.get("duration", 0),
                target_frames=20
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

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"영상 다운로드 실패: {stderr.decode()}")

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

        # 프레임 샘플링 (최대 15개로 Gemini에 전송)
        max_gemini_frames = 15
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

다음 항목들을 마케팅 관점에서 분석해주세요:

1. **타임라인 세그먼트**: 영상 전체 길이({duration:.1f}초)를 빠짐없이 분석하여 각 구간의 유형과 역할을 파악
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

2. **후킹 포인트**: 시청자가 스크롤을 멈추는 순간
   - 기법: curiosity_gap(궁금증 유발), pattern_interrupt(패턴 파괴), shocking_statement(충격적 발언), question(질문형), contradiction(역설)
   - 효과 점수와 재사용 가능한 템플릿

3. **엣지 포인트**: 경쟁사와 차별화되는 독특한 요소
   - 시각적 차별화 (색상, 구도, 스타일)
   - 메시지 차별화 (톤앤매너, 표현 방식)
   - 포지셔닝 차별화

4. **감정 트리거**: 소비자 심리를 자극하는 요소
   - FOMO(놓칠까봐 두려움), 공포/불안, 희망/기대, 욕망, 소속감, 자아실현
   - 각 트리거가 나타나는 시점과 강도

5. **페인포인트 활용**: 소비자 고충점을 어떻게 건드리는가
   - 명시적 페인포인트 (직접 언급)
   - 암시적 페인포인트 (이미지/상황으로 암시)
   - 공감 유도 기법

6. **활용 포인트**: 이 영상에서 바로 적용할 수 있는 요소
   - 복사 가능한 문구/스크립트 템플릿
   - 재현 가능한 촬영 기법
   - 적용 가능한 편집 패턴

7. **셀링 포인트**: 설득의 핵심 요소
   - 주장(claim)과 근거(evidence)
   - 설득 기법: social_proof, scarcity, authority, reciprocity, liking, commitment

8. **CTA 분석**: 행동 유도 전략
   - CTA 유형과 위치
   - 긴급성/희소성 요소
   - 장벽 제거 전략

9. **구조 패턴**: 전체 흐름 (예: AIDA, PAS, BAB 등)

10. **적용 권장사항**: 이 영상의 성공 요소를 내 영상에 적용하는 구체적 방법 5개

**중요**: segments는 영상 전체 길이({duration:.1f}초)를 빠짐없이 커버해야 합니다. 처음부터 끝까지 모든 구간을 분석하세요.

JSON 형식으로만 응답하세요:
```json
{{
  "segments": [
    {{"start_time": 0.0, "end_time": 3.0, "segment_type": "hook", "visual_description": "설명", "engagement_score": 0.9, "techniques": ["기법"]}},
    {{"start_time": 3.0, "end_time": 8.0, "segment_type": "problem", "visual_description": "설명", "engagement_score": 0.7, "techniques": ["기법"]}}
  ],
  "hook_points": [
    {{"timestamp": "0:00-0:03", "hook_type": "curiosity_gap", "effectiveness_score": 0.85, "description": "설명", "adaptable_template": "템플릿 문구"}}
  ],
  "edge_points": [
    {{"category": "visual", "description": "차별화 요소 설명", "impact_score": 0.8, "how_to_apply": "적용 방법"}}
  ],
  "emotional_triggers": [
    {{"timestamp": "0:05-0:10", "trigger_type": "FOMO", "intensity": 0.9, "description": "어떻게 감정을 자극하는지"}}
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
    {{"timestamp": "0:10-0:15", "claim": "주장", "evidence_type": "demonstration", "persuasion_technique": "social_proof", "effectiveness": 0.85}}
  ],
  "cta_analysis": {{
    "cta_type": "direct/soft/implied",
    "placement": "ending/throughout/multiple",
    "urgency_elements": ["한정 수량", "기간 한정"],
    "barrier_removal": ["무료 체험", "환불 보장"],
    "effectiveness_score": 0.8
  }},
  "structure_pattern": {{
    "framework": "PAS",
    "flow": ["hook", "problem", "agitation", "solution", "cta"],
    "effectiveness_note": "이 구조가 효과적인 이유"
  }},
  "transcript": "영상 텍스트/나레이션",
  "recommendations": [
    {{"priority": 1, "action": "구체적 행동", "reason": "이유", "example": "예시"}}
  ]
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
