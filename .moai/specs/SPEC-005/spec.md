# SPEC-005: Video Studio System

---
spec_id: SPEC-005
title: Video Studio - AI Video Generation Workflow with Storyboard
status: PLANNED
version: 2.0.0
created_at: 2025-12-11
updated_at: 2025-12-12
author: AI Video Marketing Team
tags: [video-studio, workflow, storyboard, image-generation, video-generation, scene-editor]
---

## Overview

Video Studio는 AI 마케팅 영상 제작을 위한 통합 워크플로우 시스템입니다. 사용자가 브랜드/제품과 레퍼런스 분석 결과를 선택하면, AI가 자동으로 스토리보드를 생성하고, 사용자가 이를 편집한 후 장면별 이미지를 생성하여 최종 영상을 제작할 수 있는 단계별 마법사 인터페이스를 제공합니다.

## Core Workflow (v2.0 - Storyboard-Centric)

```
Step 1: 입력 선택
    - 레퍼런스 분석 결과 선택
    - 브랜드 + 상품 선택
    ↓
Step 2: 스토리보드 생성 옵션 선택
    - 옵션 A: 레퍼런스 구조 유지 (장면 수/타임라인 동일)
    - 옵션 B: AI 최적화 재구성 (브랜드/상품에 맞게 최적화)
    ↓
Step 3: AI 스토리보드 자동 생성
    - 후킹포인트, 페인포인트, 셀링포인트, CTA 분석 활용
    - 브랜드/상품에 맞는 새로운 스토리보드 자동 생성
    ↓
Step 4: 스토리보드 편집
    - 각 장면의 문구/내용 수정
    - 장면 추가/삭제/순서 변경
    - 수정 히스토리 관리
    ↓
Step 5: 장면별 이미지 생성
    - description + visual_direction 기반 AI 이미지 생성
    - 문구 수정 후 재생성 가능
    - 이미지 버전 관리
    ↓
Step 6: 영상 생성
    - 모든 장면에 이미지 준비 완료 시 영상 생성
```

## Environment (E)

### System Context

- **Backend Framework**: FastAPI (Python 3.12+)
- **Database**: MariaDB + SQLAlchemy 2.0 (async)
- **Object Storage**: MinIO (S3 compatible)
- **Image Generation**: Gemini Imagen / DALL-E / Midjourney API
- **Video Generation**: Luma AI / Runway ML / HeyGen
- **TTS (Text-to-Speech)**: Google Cloud TTS / ElevenLabs
- **Real-time Updates**: WebSocket
- **Frontend Framework**: Next.js 14 + React Query + TailwindCSS

### External Dependencies

- SPEC-001 (Reference Analysis): 레퍼런스 분석 데이터 소스
- SPEC-002 (Brand/Product): 브랜드 및 제품 정보
- SPEC-003 (Brand Knowledge RAG): 컨텍스트 검색 (선택적)
- MinIO Server: 에셋 저장소
- Image Generation API: 장면 이미지 생성
- Video Generation API: 최종 영상 생성
- TTS API: 나레이션 음성 생성

### Configuration

- `IMAGE_GENERATION_PROVIDER`: "gemini_imagen" | "dalle" | "midjourney"
- `VIDEO_GENERATION_PROVIDER`: "luma" | "runway" | "heygen"
- `TTS_PROVIDER`: "google_cloud" | "elevenlabs"
- `MINIO_ENDPOINT`: MinIO 서버 주소
- `MINIO_ACCESS_KEY`: MinIO 접근 키
- `MINIO_SECRET_KEY`: MinIO 시크릿 키
- `MINIO_BUCKET`: 에셋 저장 버킷 (default: "ai-video-marketing")

## Assumptions (A)

### Business Assumptions

- 사용자는 레퍼런스 영상 분석을 통해 원하는 영상 스타일/구조를 파악합니다
- 브랜드와 제품 정보가 스토리보드/이미지/스크립트 생성에 반영됩니다
- AI가 생성한 스토리보드를 사용자가 편집하여 커스터마이징할 수 있습니다
- 장면별 이미지는 AI 자동 생성과 사용자 업로드를 모두 지원합니다
- 영상 생성 비용(API 호출)을 사용자가 인지하고 승인합니다

### Technical Assumptions

- 레퍼런스 분석 결과가 DB에 영구 저장됩니다
- 이미지 생성 API가 안정적으로 서비스됩니다
- 생성된 에셋은 MinIO에 안전하게 저장됩니다
- 영상 생성 시간은 수 분이 소요될 수 있습니다 (비동기 처리 필수)
- 스토리보드 수정 시 버전 관리가 필요합니다

### Constraints

- 이미지 생성 API 비용 (건당 과금)
- 영상 생성 API 비용 (건당 과금)
- TTS API 비용 (문자 수 기반 과금)
- 영상 길이 제한 (각 API별 상이)
- 저장 공간 (영상/이미지 파일 크기)

## Requirements (R)

### Functional Requirements

#### FR-001: Reference Analysis Persistence

- **When** 레퍼런스 영상 분석이 완료되면
- **The System Shall** 분석 결과를 데이터베이스에 영구 저장합니다
- **Data**: source_url, title, segments, hook_points, pain_points, selling_points, cta_analysis 등
- **Optional Association**: brand_id로 브랜드에 연결 가능
- **Priority**: High

#### FR-002: Reference Analysis Listing

- **When** 사용자가 저장된 분석 결과를 조회하면
- **The System Shall** 브랜드, 상태, 태그, 날짜로 필터링 가능한 목록을 반환합니다
- **Priority**: High

#### FR-003: Video Project Creation

- **When** 사용자가 영상 프로젝트를 생성하면
- **The System Shall** 브랜드, 제품, 레퍼런스 분석을 연결한 프로젝트를 생성합니다
- **Required Links**: brand_id, product_id, reference_analysis_id
- **Priority**: High

#### FR-004: Storyboard Generation

- **When** 사용자가 스토리보드 생성을 요청하면
- **The System Shall** 두 가지 모드 중 하나로 스토리보드를 자동 생성합니다
- **Mode A (reference_structure)**: 레퍼런스 분석의 장면 수와 타임라인 구조를 유지하며 콘텐츠만 브랜드/상품에 맞게 변경
- **Mode B (ai_optimized)**: AI가 브랜드/상품에 최적화된 새로운 장면 구조를 설계
- **Input Data**: 레퍼런스 분석 결과 (segments, hook_points, pain_points, selling_points, cta_analysis)
- **Output**: 각 장면별 완전한 정보를 포함한 스토리보드
- **Priority**: High

#### FR-005: Storyboard Scene Structure

- **Each Scene Shall Contain**:
  - `scene_number`: 장면 번호 (1-based)
  - `scene_type`: 장면 유형 (hook, problem, solution, benefit, cta, transition 등)
  - `title`: 장면 제목
  - `description`: 장면 설명 텍스트 (이미지 생성용 프롬프트 기반)
  - `narration_script`: 나레이션 스크립트 (TTS용)
  - `visual_direction`: 화면 연출 가이드
  - `background_music_suggestion`: 배경음악 제안 (분위기, 장르)
  - `transition_effect`: 전환 효과 (fade, cut, zoom 등)
  - `subtitle_text`: 자막 텍스트 (화면에 표시될 텍스트)
  - `duration_seconds`: 예상 시간 (초)
- **Priority**: High

#### FR-006: Storyboard Editing

- **When** 사용자가 스토리보드를 편집하면
- **The System Shall** 다음 편집 기능을 제공합니다:
  - 각 장면의 모든 필드 수정 (title, description, narration_script 등)
  - 새로운 장면 추가
  - 기존 장면 삭제
  - 장면 순서 변경 (drag & drop)
- **History**: 수정 히스토리 관리 (버전별 저장)
- **Priority**: High

#### FR-007: Scene Image AI Generation

- **When** 사용자가 특정 장면의 이미지 생성을 요청하면
- **The System Shall** 장면의 description + visual_direction을 조합한 프롬프트로 이미지를 생성합니다
- **Context**: 브랜드 가이드라인, 제품 정보 반영
- **Providers**: Gemini Imagen, DALL-E, Midjourney
- **Priority**: High

#### FR-008: Scene Image User Upload

- **When** 사용자가 장면에 이미지를 업로드하면
- **The System Shall** 이미지를 MinIO에 저장하고 장면에 연결합니다
- **Supported Formats**: JPEG, PNG, WebP
- **Max Size**: 10MB
- **Priority**: High

#### FR-009: Batch Image Generation

- **When** 사용자가 전체 이미지 일괄 생성을 요청하면
- **The System Shall** 이미지 없는 모든 장면에 대해 병렬로 이미지를 생성합니다
- **Priority**: Medium

#### FR-010: Scene Image Versioning

- **When** 장면에 새 이미지가 생성/업로드되면
- **The System Shall** 버전을 관리하고 활성 버전을 선택할 수 있게 합니다
- **Priority**: Medium

#### FR-011: Video Generation

- **When** 모든 장면에 이미지가 있고 사용자가 영상 생성을 요청하면
- **The System Shall** 선택된 영상 생성 API를 호출하여 최종 영상을 제작합니다
- **Inputs**: 장면별 이미지, duration_seconds, transition_effect, narration_script
- **Providers**: Luma AI, Runway ML, HeyGen
- **Priority**: High

#### FR-012: Real-time Progress Tracking

- **When** 이미지/영상 생성이 진행 중일 때
- **The System Shall** WebSocket을 통해 실시간 진행률을 제공합니다
- **Priority**: Medium

#### FR-013: Video Studio Wizard UI

- **When** 사용자가 Video Studio에 접근하면
- **The System Shall** 6단계 마법사 인터페이스를 제공합니다
- **Steps**: 입력 선택 → 스토리보드 옵션 → 스토리보드 생성 → 스토리보드 편집 → 이미지 생성 → 영상 생성
- **Priority**: High

### Non-Functional Requirements

#### NFR-001: Generation Performance

- 스토리보드 생성: 30초 이내
- 이미지 생성: 30초 이내 per scene
- 영상 생성: API 제공자 의존 (진행률 표시 필수)

#### NFR-002: Reliability

- 생성 작업 실패 시 자동 재시도 (최대 3회)
- Provider 실패 시 대체 Provider로 Fallback

#### NFR-003: Scalability

- 동시 프로젝트: 10개 이상
- 저장 용량: MinIO 확장성

## Specifications (S)

### Database Models

#### ReferenceAnalysis (Enhanced)

- `id` (VARCHAR(36), PK): UUID
- `source_url` (VARCHAR(1000), NOT NULL): 분석된 영상 URL
- `title` (VARCHAR(255), NOT NULL): 분석 제목
- `brand_id` (VARCHAR(36), FK, NULLABLE, INDEX): 연결된 브랜드
- `status` (VARCHAR(20), NOT NULL): pending, downloading, extracting, analyzing, completed, failed
- `duration` (FLOAT, NULLABLE): 영상 길이 (초)
- `thumbnail_url` (VARCHAR(500), NULLABLE): 썸네일 URL
- `segments` (JSON, DEFAULT []): 타임라인 세그먼트
- `hook_points` (JSON, DEFAULT []): 후킹 포인트
- `pain_points` (JSON, DEFAULT []): 페인포인트
- `selling_points` (JSON, DEFAULT []): 셀링포인트
- `cta_analysis` (JSON, NULLABLE): CTA 분석
- `structure_pattern` (JSON, NULLABLE): 구조 패턴
- `recommendations` (JSON, DEFAULT []): 권장사항
- `transcript` (TEXT, NULLABLE): 스크립트
- `tags` (JSON, DEFAULT []): 사용자 태그
- `notes` (TEXT, NULLABLE): 메모
- `error_message` (TEXT, NULLABLE): 에러 메시지
- `created_at`, `updated_at` (DATETIME)

#### VideoProject (Enhanced)

- `id` (VARCHAR(36), PK): UUID
- `title` (VARCHAR(255), NOT NULL): 프로젝트 제목
- `description` (TEXT, NULLABLE): 설명
- `brand_id` (VARCHAR(36), FK, NOT NULL, INDEX): 브랜드
- `product_id` (VARCHAR(36), FK, NOT NULL, INDEX): 제품
- `reference_analysis_id` (VARCHAR(36), FK, NOT NULL, INDEX): 레퍼런스 분석
- `status` (VARCHAR(30), NOT NULL): draft, storyboard_generating, storyboard_ready, images_generating, video_generating, completed, failed
- `current_step` (INTEGER, DEFAULT 1): 현재 단계 (1-6)
- `metadata` (JSON, NULLABLE): 추가 메타데이터
- `target_duration` (INTEGER, NULLABLE): 목표 영상 길이 (초)
- `aspect_ratio` (VARCHAR(10), DEFAULT "16:9"): 화면 비율
- `video_provider` (VARCHAR(50), NULLABLE): 영상 생성 Provider
- `image_provider` (VARCHAR(50), NULLABLE): 이미지 생성 Provider
- `output_video_url` (VARCHAR(500), NULLABLE): 완성 영상 URL
- `output_thumbnail_url` (VARCHAR(500), NULLABLE): 썸네일 URL
- `output_duration` (FLOAT, NULLABLE): 실제 영상 길이
- `error_message` (TEXT, NULLABLE): 에러 메시지
- `created_at`, `updated_at`, `completed_at` (DATETIME)

#### Storyboard (NEW)

- `id` (VARCHAR(36), PK): UUID
- `video_project_id` (VARCHAR(36), FK, NOT NULL, UNIQUE, INDEX): 프로젝트
- `generation_mode` (VARCHAR(30), NOT NULL): "reference_structure" | "ai_optimized"
- `source_reference_analysis_id` (VARCHAR(36), FK, NOT NULL): 원본 레퍼런스 분석
- `scenes` (JSON, NOT NULL): Scene 객체 배열
- `total_duration_seconds` (FLOAT, NULLABLE): 전체 예상 시간
- `version` (INTEGER, DEFAULT 1): 버전 번호
- `is_active` (BOOLEAN, DEFAULT TRUE): 활성 버전 여부
- `previous_version_id` (VARCHAR(36), NULLABLE): 이전 버전 ID
- `created_at`, `updated_at` (DATETIME)

#### Scene (JSON Structure within Storyboard.scenes)

```json
{
  "scene_number": 1,
  "scene_type": "hook",
  "title": "Attention Grabber",
  "description": "Dramatic close-up of the product with sparkling effect",
  "narration_script": "Have you ever wondered how to achieve perfect skin?",
  "visual_direction": "Close-up shot, soft lighting, product in center, bokeh background",
  "background_music_suggestion": "Upbeat, energetic, modern pop",
  "transition_effect": "fade",
  "subtitle_text": "Perfect Skin Secret Revealed",
  "duration_seconds": 3.0,
  "generated_image_id": null
}
```

#### SceneImage (Enhanced)

- `id` (VARCHAR(36), PK): UUID
- `video_project_id` (VARCHAR(36), FK, NOT NULL, INDEX): 프로젝트
- `scene_number` (INTEGER, NOT NULL): 장면 번호 (1-based)
- `source` (VARCHAR(20), NOT NULL): ai_generated, user_uploaded
- `image_url` (VARCHAR(500), NOT NULL): 이미지 URL
- `thumbnail_url` (VARCHAR(500), NULLABLE): 썸네일 URL
- `generation_prompt` (TEXT, NULLABLE): AI 생성 프롬프트 (description + visual_direction)
- `generation_provider` (VARCHAR(50), NULLABLE): 사용된 Provider
- `generation_params` (JSON, NULLABLE): 생성 파라미터
- `generation_duration_ms` (INTEGER, NULLABLE): 생성 소요 시간
- `scene_type` (VARCHAR(50), NULLABLE): hook, problem, solution 등
- `version` (INTEGER, DEFAULT 1): 버전 번호
- `is_active` (BOOLEAN, DEFAULT TRUE): 활성 버전 여부
- `previous_version_id` (VARCHAR(36), NULLABLE): 이전 버전 ID
- `created_at`, `updated_at` (DATETIME)

### API Endpoints

#### Reference Analysis (Enhanced)

- `POST /api/v1/references/analyze` - 분석 요청 (brand_id, title, tags 추가)
- `GET /api/v1/references` - 분석 목록 (필터링: brand_id, status, tags)
- `GET /api/v1/references/{id}` - 분석 상세
- `PUT /api/v1/references/{id}` - 메타데이터 수정 (title, brand_id, tags, notes)
- `DELETE /api/v1/references/{id}` - 삭제 (프로젝트 연결 시 실패)

#### Video Projects

- `POST /api/v1/video-projects` - 프로젝트 생성
- `GET /api/v1/video-projects` - 프로젝트 목록
- `GET /api/v1/video-projects/{id}` - 프로젝트 상세 (스토리보드, 장면 포함)
- `PUT /api/v1/video-projects/{id}` - 프로젝트 수정
- `DELETE /api/v1/video-projects/{id}` - 프로젝트 삭제

#### Storyboard APIs (NEW)

- `POST /api/v1/video-projects/{id}/storyboard/generate` - 스토리보드 자동 생성
  - **Request Body**: `{ "mode": "reference_structure" | "ai_optimized" }`
  - **Response**: 생성된 Storyboard 객체
- `GET /api/v1/video-projects/{id}/storyboard` - 현재 스토리보드 조회
- `PUT /api/v1/video-projects/{id}/storyboard/scenes/{scene_number}` - 장면 수정
  - **Request Body**: Scene 객체 (수정할 필드만)
- `POST /api/v1/video-projects/{id}/storyboard/scenes` - 장면 추가
  - **Request Body**: Scene 객체 (scene_number 제외, 자동 할당)
  - **Query Param**: `after_scene_number` (선택, 해당 장면 뒤에 삽입)
- `DELETE /api/v1/video-projects/{id}/storyboard/scenes/{scene_number}` - 장면 삭제
- `PUT /api/v1/video-projects/{id}/storyboard/scenes/reorder` - 장면 순서 변경
  - **Request Body**: `{ "scene_order": [3, 1, 2, 4, 5] }` (새로운 순서)
- `GET /api/v1/video-projects/{id}/storyboard/history` - 스토리보드 버전 히스토리
- `POST /api/v1/video-projects/{id}/storyboard/restore/{version}` - 특정 버전 복원

#### Scene Images

- `GET /api/v1/video-projects/{id}/scenes` - 장면 이미지 목록
- `POST /api/v1/video-projects/{id}/scenes/{scene_number}/generate-image` - AI 이미지 생성
  - 장면의 description + visual_direction 기반으로 이미지 생성
  - **Request Body**: `{ "provider": "gemini_imagen" | "dalle" | "midjourney" }` (선택)
- `POST /api/v1/video-projects/{id}/scenes/{scene_number}/upload` - 이미지 업로드
- `POST /api/v1/video-projects/{id}/scenes/generate-all` - 전체 이미지 일괄 생성
- `PUT /api/v1/video-projects/{id}/scenes/{scene_number}/select/{image_id}` - 활성 이미지 선택
- `GET /api/v1/video-projects/{id}/scenes/{scene_number}/versions` - 이미지 버전 목록

#### Video Generation

- `POST /api/v1/video-projects/{id}/generate-video` - 영상 생성 시작
- `GET /api/v1/video-projects/{id}/generation-status` - 생성 진행률
- `POST /api/v1/video-projects/{id}/cancel-generation` - 생성 취소
- `GET /api/v1/video-projects/{id}/download` - 영상 다운로드 URL

#### WebSocket

- `WS /api/v1/ws/video-projects/{id}/status` - 실시간 상태 업데이트

### Storyboard Generation Logic

#### Step 1: Extract Reference Analysis Structure

```
Input: reference_analysis_id
Extract:
  - segments (타임라인 세그먼트)
  - hook_points (후킹 포인트)
  - pain_points (페인포인트)
  - selling_points (셀링포인트)
  - cta_analysis (CTA 분석)
  - structure_pattern (구조 패턴)
```

#### Step 2: Combine Brand/Product Information

```
Input: brand_id, product_id
Combine:
  - Brand: 톤앤매너, 브랜드 가이드라인, 타겟 고객
  - Product: 제품명, 특징, 성분, 효능, 타겟 페르소나
```

#### Step 3: Generate Scene Content

```
For each scene:
  1. 장면 유형에 맞는 프롬프트 템플릿 선택
  2. LLM을 통해 다음 필드 생성:
     - title, description, narration_script
     - visual_direction, background_music_suggestion
     - transition_effect, subtitle_text, duration_seconds
  3. 브랜드/제품 컨텍스트 반영
```

#### Mode A: Reference Structure

```
- 레퍼런스 분석의 segments 수만큼 장면 생성
- 각 segment의 타임라인, 유형 유지
- 콘텐츠만 브랜드/제품에 맞게 변경
```

#### Mode B: AI Optimized

```
- AI가 브랜드/제품에 최적화된 새로운 구조 설계
- 장면 수, 순서, 유형을 자유롭게 결정
- 권장 영상 길이와 페이스 고려
```

### MinIO Storage Structure

```
ai-video-marketing/
├── references/
│   └── {analysis_id}/
│       ├── thumbnail.jpg
│       └── frames/
├── projects/
│   └── {project_id}/
│       ├── storyboard/
│       │   └── {version}/
│       │       └── storyboard.json
│       └── scenes/
│           └── {scene_number}/
│               ├── {image_id}.jpg
│               └── {image_id}_thumb.jpg
├── outputs/
│   └── {project_id}/
│       ├── final.mp4
│       └── thumbnail.jpg
└── temp/
```

### Scene Type Prompt Templates

**Hook Scene**:
```
A dramatic close-up product shot with {product_name}, {lighting_style} lighting,
{brand_colors} tones, professional cosmetics photography, high contrast composition.
Visual Direction: {visual_direction}
```

**Problem Scene**:
```
A lifestyle photo showing {target_audience} experiencing {pain_point},
natural lighting, documentary style, authentic moment.
Visual Direction: {visual_direction}
```

**Solution Scene**:
```
{product_name} hero shot showing {key_benefit},
{texture_type} texture visible, clean background, professional beauty photography.
Visual Direction: {visual_direction}
```

**Benefit Scene**:
```
Portrait of {target_audience} with radiant skin showing {benefit_result},
natural daylight, satisfaction expression, lifestyle photography.
Visual Direction: {visual_direction}
```

**CTA Scene**:
```
Clean product shot of {product_name} packaging, {brand_logo} visible,
call-to-action ready composition, e-commerce style.
Visual Direction: {visual_direction}
```

**Transition Scene**:
```
Smooth visual transition element with {brand_colors} gradient,
minimal design, professional motion graphics style.
Visual Direction: {visual_direction}
```

### Project State Machine

```
draft
  ↓ (generate storyboard)
storyboard_generating → draft (on failure)
  ↓ (success)
storyboard_ready
  ↓ (edit storyboard - stays in storyboard_ready)
  ↓ (generate images)
images_generating → storyboard_ready (on failure)
  ↓ (all images ready)
  ↓ (generate video)
video_generating
  ↓ (success)        ↓ (failure)
completed          failed → storyboard_ready (reset)
```

## Implementation Files (Planned)

**Backend**:

- `/backend/app/models/reference_analysis.py`: ReferenceAnalysis ORM 모델
- `/backend/app/models/video_project.py`: VideoProject ORM 모델
- `/backend/app/models/storyboard.py`: Storyboard ORM 모델 (NEW)
- `/backend/app/models/scene_image.py`: SceneImage ORM 모델
- `/backend/app/api/v1/references.py`: 레퍼런스 API (확장)
- `/backend/app/api/v1/video_projects.py`: 비디오 프로젝트 API
- `/backend/app/api/v1/storyboards.py`: 스토리보드 API (NEW)
- `/backend/app/services/video_studio/`: 비디오 스튜디오 서비스
  - `storyboard_generator.py`: 스토리보드 생성 (NEW)
  - `scene_content_generator.py`: 장면 콘텐츠 생성 (NEW)
  - `image_generator.py`: 이미지 생성 (Provider 추상화)
  - `video_generator.py`: 영상 생성 (Provider 추상화)
  - `prompt_builder.py`: 프롬프트 구성
  - `storage_manager.py`: MinIO 에셋 관리
- `/backend/alembic/versions/003_video_studio.py`: DB 마이그레이션

**Frontend**:

- `/frontend/app/studio/page.tsx`: Video Studio 대시보드
- `/frontend/app/studio/new/page.tsx`: 프로젝트 생성 마법사
- `/frontend/app/studio/[id]/page.tsx`: 프로젝트 편집기
- `/frontend/components/studio/`: 스튜디오 컴포넌트
  - `InputSelector.tsx`: Step 1 - 입력 선택
  - `StoryboardOptions.tsx`: Step 2 - 스토리보드 옵션
  - `StoryboardGenerator.tsx`: Step 3 - 스토리보드 생성
  - `StoryboardEditor.tsx`: Step 4 - 스토리보드 편집 (NEW)
  - `SceneImageGenerator.tsx`: Step 5 - 이미지 생성
  - `VideoGenerator.tsx`: Step 6 - 영상 생성

## Traceability

### Related SPECs

- SPEC-001 (Reference Analysis): 분석 데이터 소스, hook_points, pain_points, selling_points, cta_analysis 활용
- SPEC-002 (Brand/Product): 브랜드/제품 정보 활용
- SPEC-003 (Brand Knowledge RAG): 컨텍스트 검색 (선택적 통합)
- SPEC-004 (Video Generation): 이 SPEC으로 대체됨

### Dependencies

- SPEC-001, SPEC-002 완료 필수
- MinIO 인프라 준비 필요
- 이미지/영상 생성 API 계정 및 크레딧
- LLM API (스토리보드/스크립트 생성용)

### Test Coverage Target

- Unit Tests: 90%
- Integration Tests: API 엔드포인트 전체
- E2E Tests: 프로젝트 생성 → 스토리보드 생성 → 편집 → 이미지 생성 → 영상 생성 플로우

---

**Implementation Status**: PLANNED
**Version**: 2.0.0
**Priority**: High
