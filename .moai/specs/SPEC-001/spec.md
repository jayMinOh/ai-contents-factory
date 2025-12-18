# SPEC-001: Reference Video Analysis System

---
spec_id: SPEC-001
title: Reference Video Analysis System
status: IMPLEMENTED
version: 1.0.0
created_at: 2025-01-15
updated_at: 2025-12-11
author: AI Video Marketing Team
tags: [video-analysis, ai, gemini, marketing, reference]
---

## Overview

Reference Video Analysis System은 마케팅 영상(YouTube, TikTok, Instagram)을 AI로 분석하여 타임라인별 세그먼트, 후킹 포인트, 셀링 포인트, 감정 트리거 등 마케팅 관점의 인사이트를 추출하는 시스템입니다.

## Environment (E)

### System Context

- **Backend Framework**: FastAPI (Python 3.12+)
- **AI Engine**: Google Gemini API (gemini-pro-vision)
- **Video Download**: yt-dlp
- **Frame Extraction**: FFmpeg
- **Frontend Framework**: Next.js 14 + React Query + TailwindCSS
- **State Management**: TanStack React Query

### External Dependencies

- Google Gemini API (API Key Required)
- yt-dlp (system binary)
- FFmpeg (system binary)
- Pillow (image processing)

### Configuration

- `GOOGLE_API_KEY`: Gemini API 인증 키
- `GEMINI_MODEL`: 사용할 Gemini 모델 (default: gemini-pro-vision)
- `TEMP_DIR`: 임시 파일 저장 경로

## Assumptions (A)

### Business Assumptions

- 사용자는 분석하고자 하는 영상의 URL을 알고 있습니다.
- 영상은 공개적으로 접근 가능한 상태입니다.
- 마케팅 영상은 일반적으로 30초~5분 길이입니다.

### Technical Assumptions

- yt-dlp가 지원하는 플랫폼의 영상만 분석 가능합니다.
- Gemini API는 이미지 분석을 지원하며, 동시에 최대 15개 프레임을 처리합니다.
- 영상 다운로드 및 프레임 추출에 충분한 디스크 공간이 있습니다.
- 네트워크 연결이 안정적입니다.

### Constraints

- Gemini API 토큰 제한에 따른 분석 깊이 제약
- 영상 길이에 따른 프레임 샘플링 (최대 20개 프레임)
- 임시 파일 저장 공간 필요 (영상 크기에 따라 가변)

## Requirements (R)

### Functional Requirements

#### FR-001: Video URL Input and Validation (IMPLEMENTED)

- **When** 사용자가 영상 URL을 입력하면
- **The System Shall** URL 형식의 유효성을 검사합니다
- **Priority**: High

#### FR-002: Video Download (IMPLEMENTED)

- **When** 유효한 URL이 제출되면
- **The System Shall** yt-dlp를 사용하여 720p 이하의 최적 품질로 영상을 다운로드합니다
- **Priority**: High

#### FR-003: Frame Extraction (IMPLEMENTED)

- **When** 영상 다운로드가 완료되면
- **The System Shall** FFmpeg를 사용하여 영상 전체에서 균등한 간격으로 프레임을 추출합니다 (최대 20개)
- **Priority**: High

#### FR-004: AI-Powered Video Analysis (IMPLEMENTED)

- **When** 프레임 추출이 완료되면
- **The System Shall** Google Gemini API를 호출하여 마케팅 관점에서 영상을 분석합니다
- **Priority**: High

#### FR-005: Timeline Segmentation (IMPLEMENTED)

- **When** AI 분석이 수행되면
- **The System Shall** 영상을 마케팅 세그먼트로 구분합니다
- **Segment Types**: hook, problem, agitation, solution, feature, benefit, social_proof, urgency, cta, transition, demonstration, intro, outro, testimonial, comparison, offer, other
- **Priority**: High

#### FR-006: Hook Point Extraction (IMPLEMENTED)

- **When** AI 분석이 수행되면
- **The System Shall** 후킹 포인트(시청자의 주의를 끄는 순간)를 식별합니다
- **Hook Types**: curiosity_gap, pattern_interrupt, shocking_statement, question, contradiction
- **Priority**: High

#### FR-007: Engagement Score Calculation (IMPLEMENTED)

- **When** 각 세그먼트가 분석되면
- **The System Shall** 다음 기준으로 engagement_score(0.0~1.0)를 계산합니다
- 시각적 자극 강도 (25%)
- 정보 밀도 (25%)
- 감정적 자극 (25%)
- 시청 유지력 (25%)
- **Priority**: Medium

#### FR-008: Real-time Status Polling (IMPLEMENTED)

- **When** 분석이 진행 중일 때
- **The System Shall** 2초 간격으로 분석 상태를 폴링하여 UI에 표시합니다
- **Status Types**: pending, downloading, extracting, transcribing, analyzing, completed, failed
- **Priority**: Medium

#### FR-009: Rich Analysis Result Display (IMPLEMENTED)

- **When** 분석이 완료되면
- **The System Shall** 다음 분석 결과를 시각적으로 표시합니다
- 타임라인 세그먼트 (색상 구분된 배지)
- 후킹 포인트 (효과 점수 포함)
- 엣지 포인트 (차별화 요소)
- 감정 트리거
- 페인포인트 활용
- 활용 포인트 (복사 가능)
- 셀링 포인트
- CTA 분석
- 적용 권장사항
- **Priority**: High

#### FR-010: Marketing Terminology Tooltips (IMPLEMENTED)

- **When** 마케팅 용어가 UI에 표시될 때
- **The System Shall** 사용자가 이해할 수 있도록 툴팁으로 설명을 제공합니다
- **Priority**: Low

### Non-Functional Requirements

#### NFR-001: Analysis Performance

- 30초 영상 분석 완료 시간: 60초 이내
- 3분 영상 분석 완료 시간: 180초 이내

#### NFR-002: Error Handling

- 영상 다운로드 실패 시 명확한 오류 메시지 제공
- AI 응답 파싱 실패 시 폴백 분석 결과 제공

#### NFR-003: Resource Cleanup

- 분석 완료 후 임시 파일(영상, 프레임) 자동 삭제

## Specifications (S)

### API Specifications

#### POST /api/v1/references/analyze

**Request Body**:

- `url` (string, required): 분석할 영상 URL
- `extract_audio` (boolean, optional): 오디오 추출 여부 (default: true)

**Response** (AnalysisResponse):

- `analysis_id` (string): 분석 작업 ID
- `status` (string): 현재 상태
- `message` (string): 상태 메시지

#### GET /api/v1/references/{analysis_id}

**Response** (AnalysisResult):

- `analysis_id` (string): 분석 작업 ID
- `source_url` (string): 원본 영상 URL
- `status` (string): 분석 상태
- `duration` (number, optional): 영상 길이 (초)
- `segments` (array): 타임라인 세그먼트 목록
- `hook_points` (array): 후킹 포인트 목록
- `edge_points` (array): 엣지 포인트 목록
- `emotional_triggers` (array): 감정 트리거 목록
- `pain_points` (array): 페인포인트 목록
- `application_points` (array): 활용 포인트 목록
- `selling_points` (array): 셀링 포인트 목록
- `cta_analysis` (object, optional): CTA 분석 결과
- `structure_pattern` (object, optional): 구조 패턴
- `recommendations` (array): 적용 권장사항
- `transcript` (string, optional): 음성 스크립트

#### GET /api/v1/references/

**Response**: 모든 분석 결과 목록 (AnalysisResult[])

### Data Models

#### TimelineSegment

- `start_time` (number): 시작 시간 (초)
- `end_time` (number): 종료 시간 (초)
- `segment_type` (enum): 세그먼트 유형
- `visual_description` (string): 시각적 설명
- `audio_transcript` (string, optional): 오디오 스크립트
- `text_overlay` (string, optional): 텍스트 오버레이
- `engagement_score` (number): 참여도 점수 (0.0~1.0)
- `techniques` (array): 사용된 기법 목록

#### HookPoint

- `timestamp` (string): 타임스탬프 (예: "0:00-0:03")
- `hook_type` (string): 후킹 기법 유형
- `effectiveness_score` (number): 효과 점수 (0.0~1.0)
- `description` (string, optional): 설명
- `elements` (array, optional): 구성 요소
- `adaptable_template` (string, optional): 재사용 가능한 템플릿

### Implementation Files

**Backend**:

- `/backend/app/api/v1/references.py`: API 라우터 및 Pydantic 스키마
- `/backend/app/services/reference_analyzer/analyzer.py`: 분석 로직

**Frontend**:

- `/frontend/app/page.tsx`: 메인 분석 UI
- `/frontend/lib/api.ts`: API 클라이언트

## Traceability

### Related SPECs

- SPEC-003 (Brand Knowledge RAG): 분석 결과를 브랜드 지식과 결합
- SPEC-004 (Video Generation): 분석 인사이트를 영상 생성에 활용

### Test Coverage Target

- Unit Tests: 90%
- Integration Tests: API 엔드포인트 전체
- E2E Tests: 영상 분석 플로우

---

**Implementation Status**: COMPLETED
**Last Verified**: 2025-12-11
