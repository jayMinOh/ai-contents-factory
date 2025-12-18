# SPEC-004: AI Video Generation System

---
spec_id: SPEC-004
title: AI Video Generation System
status: PLANNED
version: 1.0.0
created_at: 2025-12-11
updated_at: 2025-12-11
author: AI Video Marketing Team
tags: [video-generation, ai, script, storyboard, luma, runway, heygen]
---

## Overview

AI Video Generation System은 레퍼런스 영상 분석 결과와 브랜드 지식 베이스를 활용하여 마케팅 영상의 스크립트, 스토리보드를 자동 생성하고, AI 영상 생성 API와 연동하여 최종 영상을 렌더링하는 시스템입니다.

## Environment (E)

### System Context

- **Backend Framework**: FastAPI (Python 3.12+)
- **AI Script Generation**: Google Gemini API
- **Video Generation APIs**: Luma AI / Runway ML / HeyGen (선택적)
- **Asset Storage**: MinIO (S3 compatible)
- **Frontend Framework**: Next.js 14 + React Query + TailwindCSS

### External Dependencies

- SPEC-001 (Reference Video Analysis): 레퍼런스 분석 결과
- SPEC-002 (Brand/Product Management): 브랜드/제품 정보
- SPEC-003 (Brand Knowledge RAG): 컨텍스트 검색
- Google Gemini API (스크립트 생성)
- Luma AI API / Runway ML API / HeyGen API (영상 생성)
- MinIO Server (에셋 저장)

### Configuration

- `VIDEO_GENERATION_PROVIDER`: "luma" | "runway" | "heygen"
- `LUMA_API_KEY`: Luma AI API 키
- `RUNWAY_API_KEY`: Runway ML API 키
- `HEYGEN_API_KEY`: HeyGen API 키
- `MINIO_ENDPOINT`: MinIO 서버 주소
- `MINIO_ACCESS_KEY`: MinIO 접근 키
- `MINIO_SECRET_KEY`: MinIO 시크릿 키
- `MINIO_BUCKET`: 에셋 저장 버킷명

## Assumptions (A)

### Business Assumptions

- 사용자는 레퍼런스 영상 분석을 통해 원하는 영상 스타일을 파악합니다.
- 브랜드와 제품 정보가 스크립트 내용에 반영되어야 합니다.
- 영상 생성 비용(API 호출)을 사용자가 인지하고 승인합니다.

### Technical Assumptions

- 영상 생성 API가 안정적으로 서비스됩니다.
- 생성된 영상은 MinIO에 안전하게 저장됩니다.
- 영상 생성 시간은 수 분이 소요될 수 있습니다 (비동기 처리 필수).

### Constraints

- 영상 생성 API 비용 (건당 과금)
- 영상 길이 제한 (각 API별 상이)
- 렌더링 시간 (1분 영상 기준 5~10분)
- 저장 공간 (영상 파일 크기)

## Requirements (R)

### Functional Requirements

#### FR-001: Script Generation

- **When** 사용자가 영상 생성을 요청하면
- **The System Shall** 레퍼런스 분석 결과와 브랜드 컨텍스트를 기반으로 마케팅 스크립트를 생성합니다
- **Input**: reference_analysis_id, brand_id, product_id (optional), target_duration, style_preferences
- **Output**: 타임라인 기반 스크립트 (장면별 나레이션, 비주얼 지시사항)
- **Priority**: High

#### FR-002: Storyboard Generation

- **When** 스크립트가 생성되면
- **The System Shall** 각 장면에 대한 스토리보드를 생성합니다
- **Output**: 장면별 시각적 설명, 카메라 앵글, 전환 효과, 참조 이미지 프롬프트
- **Priority**: High

#### FR-003: Style Transfer from Reference

- **When** 레퍼런스 분석 결과가 제공되면
- **The System Shall** 레퍼런스 영상의 구조, 톤, 페이싱을 새 스크립트에 적용합니다
- **Priority**: High

#### FR-004: Video Generation API Integration

- **When** 사용자가 영상 렌더링을 승인하면
- **The System Shall** 선택된 영상 생성 API(Luma/Runway/HeyGen)를 호출합니다
- **Priority**: High

#### FR-005: Generation Status Tracking

- **When** 영상 생성이 진행 중일 때
- **The System Shall** 실시간으로 생성 진행 상태를 추적하고 표시합니다
- **Status Types**: pending, script_generating, storyboard_creating, video_rendering, post_processing, completed, failed
- **Priority**: High

#### FR-006: Asset Management

- **When** 영상이 생성되면
- **The System Shall** MinIO에 영상 파일을 저장하고 접근 URL을 제공합니다
- **Priority**: High

#### FR-007: Script Editing

- **When** 자동 생성된 스크립트가 표시되면
- **The System Shall** 사용자가 스크립트를 수정할 수 있게 합니다
- **Priority**: Medium

#### FR-008: Storyboard Preview

- **When** 스토리보드가 생성되면
- **The System Shall** 각 장면의 미리보기 이미지를 생성하여 표시합니다
- **Priority**: Medium

#### FR-009: Multi-variant Generation

- **When** 사용자가 요청하면
- **The System Shall** 동일 브랜드/제품에 대해 여러 버전의 스크립트를 생성합니다
- **Priority**: Low

#### FR-010: Generation History

- **When** 사용자가 히스토리를 조회하면
- **The System Shall** 이전 생성 작업 목록과 결과물을 표시합니다
- **Priority**: Medium

#### FR-011: Cost Estimation

- **When** 영상 생성 전에
- **The System Shall** 예상 비용을 계산하여 사용자에게 안내합니다
- **Priority**: Medium

#### FR-012: Export Options

- **When** 영상이 완료되면
- **The System Shall** 다양한 포맷(MP4, MOV) 및 해상도(1080p, 4K)로 다운로드 옵션을 제공합니다
- **Priority**: Medium

### Non-Functional Requirements

#### NFR-001: Generation Performance

- 스크립트 생성: 30초 이내
- 스토리보드 생성: 60초 이내
- 영상 렌더링: API 제공자 의존 (진행률 표시 필수)

#### NFR-002: Reliability

- 생성 작업 실패 시 자동 재시도 (최대 3회)
- 영상 저장 실패 시 로컬 백업

#### NFR-003: Scalability

- 동시 생성 작업: 10개 이상
- 저장 용량: 무제한 (MinIO 확장성)

## Specifications (S)

### API Specifications

#### POST /api/v1/videos/generate

영상 생성 요청

**Request Body**:

- `reference_analysis_id` (string, optional): 레퍼런스 분석 ID
- `brand_id` (string, required): 브랜드 ID
- `product_id` (string, optional): 제품 ID
- `target_duration` (number, required): 목표 영상 길이 (초)
- `style_preferences` (object, optional):
  - `tone` (string): "professional" | "casual" | "dramatic" | "humorous"
  - `pacing` (string): "fast" | "medium" | "slow"
  - `visual_style` (string): "realistic" | "animated" | "mixed"
- `generation_provider` (string, optional): "luma" | "runway" | "heygen"

**Response** (VideoGenerationResponse):

- `generation_id` (string): 생성 작업 ID
- `status` (string): 현재 상태
- `estimated_completion` (datetime, optional): 예상 완료 시간

#### GET /api/v1/videos/{generation_id}

생성 작업 상태 및 결과 조회

**Response** (VideoGenerationResult):

- `generation_id` (string): 생성 작업 ID
- `status` (string): 상태
- `progress` (number): 진행률 (0-100)
- `script` (object, optional): 생성된 스크립트
- `storyboard` (array, optional): 스토리보드 장면 목록
- `video_url` (string, optional): 완성된 영상 URL
- `thumbnail_url` (string, optional): 썸네일 이미지 URL
- `metadata` (object):
  - `duration` (number): 영상 길이
  - `resolution` (string): 해상도
  - `file_size` (number): 파일 크기
- `created_at` (datetime): 생성 시작 시간
- `completed_at` (datetime, optional): 완료 시간

#### PUT /api/v1/videos/{generation_id}/script

스크립트 수정

**Request Body**:

- `script` (object): 수정된 스크립트

**Response**: 수정된 VideoGenerationResult

#### POST /api/v1/videos/{generation_id}/render

영상 렌더링 시작 (스크립트 확정 후)

**Response**:

- `status` (string): "rendering_started"
- `estimated_time` (number): 예상 소요 시간 (초)

#### GET /api/v1/videos/

생성 히스토리 조회

**Query Parameters**:

- `brand_id` (string, optional): 브랜드 필터
- `status` (string, optional): 상태 필터
- `skip` (number, optional): 페이지네이션 offset
- `limit` (number, optional): 페이지 크기

**Response** (VideoGenerationResult[]): 생성 작업 목록

#### DELETE /api/v1/videos/{generation_id}

생성 작업 및 에셋 삭제

**Response**: `{"message": "Video deleted successfully"}`

### Data Models

#### Script

- `title` (string): 영상 제목
- `total_duration` (number): 총 길이 (초)
- `scenes` (array): 장면 목록
  - `scene_id` (number): 장면 번호
  - `start_time` (number): 시작 시간
  - `end_time` (number): 종료 시간
  - `segment_type` (string): 세그먼트 유형 (hook, problem, solution 등)
  - `narration` (string): 나레이션 텍스트
  - `visual_direction` (string): 비주얼 연출 지시
  - `text_overlay` (string, optional): 화면 텍스트
  - `music_mood` (string, optional): 배경음악 분위기

#### Storyboard Scene

- `scene_id` (number): 장면 번호
- `frame_description` (string): 프레임 설명
- `camera_angle` (string): 카메라 앵글
- `transition` (string): 전환 효과 (cut, fade, zoom 등)
- `reference_prompt` (string): AI 이미지 생성 프롬프트
- `preview_image_url` (string, optional): 미리보기 이미지

#### VideoGeneration (DB Model)

- `id` (string, PK): UUID
- `brand_id` (string, FK): 브랜드 ID
- `product_id` (string, FK, nullable): 제품 ID
- `reference_analysis_id` (string, nullable): 레퍼런스 분석 ID
- `status` (string): 상태
- `progress` (number): 진행률
- `script` (JSON): 스크립트 데이터
- `storyboard` (JSON): 스토리보드 데이터
- `video_url` (string, nullable): 영상 URL
- `thumbnail_url` (string, nullable): 썸네일 URL
- `duration` (number, nullable): 영상 길이
- `resolution` (string, nullable): 해상도
- `file_size` (number, nullable): 파일 크기
- `generation_provider` (string): 사용된 API
- `generation_cost` (number, nullable): 비용
- `error_message` (string, nullable): 에러 메시지
- `created_at` (datetime): 생성 시간
- `updated_at` (datetime): 수정 시간
- `completed_at` (datetime, nullable): 완료 시간

### Implementation Files (Planned)

**Backend**:

- `/backend/app/services/video_generator/` (stub directory - to be implemented)
  - `script_generator.py`: 스크립트 생성 로직
  - `storyboard_generator.py`: 스토리보드 생성 로직
  - `video_providers/`: 영상 생성 API 클라이언트
    - `base.py`: 추상 인터페이스
    - `luma.py`: Luma AI 클라이언트
    - `runway.py`: Runway ML 클라이언트
    - `heygen.py`: HeyGen 클라이언트
  - `asset_manager.py`: MinIO 에셋 관리
  - `generation_service.py`: 생성 작업 오케스트레이션
- `/backend/app/api/v1/videos.py`: API 라우터
- `/backend/app/models/video_generation.py`: DB 모델
- `/backend/app/schemas/video.py`: Pydantic 스키마

**Frontend**:

- `/frontend/app/generate/page.tsx`: 영상 생성 페이지
- `/frontend/app/generate/[id]/page.tsx`: 생성 상태/결과 페이지
- `/frontend/components/video/`: 관련 컴포넌트
  - `ScriptEditor.tsx`: 스크립트 편집기
  - `StoryboardViewer.tsx`: 스토리보드 뷰어
  - `VideoPreview.tsx`: 영상 미리보기
  - `GenerationProgress.tsx`: 진행률 표시

## Traceability

### Related SPECs

- SPEC-001 (Reference Video Analysis): 레퍼런스 구조/스타일 참조
- SPEC-002 (Brand/Product Management): 브랜드/제품 정보 활용
- SPEC-003 (Brand Knowledge RAG): 관련 컨텍스트 검색

### Dependencies

- SPEC-001, SPEC-002 완료 필수
- SPEC-003 권장 (RAG 없이도 기본 동작 가능)
- 영상 생성 API 계정 및 크레딧
- MinIO 인프라 준비

### Test Coverage Target

- Unit Tests: 90%
- Integration Tests: 영상 생성 API mock
- E2E Tests: 스크립트 생성 -> 편집 -> 렌더링 플로우

---

**Implementation Status**: PLANNED
**Target Start**: After SPEC-003
**Estimated Effort**: High
