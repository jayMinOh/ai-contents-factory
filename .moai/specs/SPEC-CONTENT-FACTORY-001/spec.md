# SPEC-CONTENT-FACTORY-001: AI Content Factory 워크플로우 재설계

---
spec_id: SPEC-CONTENT-FACTORY-001
title: AI Content Factory - SNS 콘텐츠 대량 생산 워크플로우
status: COMPLETED
version: 1.1.0
created_at: 2025-12-18
updated_at: 2025-12-19
author: AI Content Factory Team
tags: [content-factory, workflow-redesign, image-generation, text-editor, sns-content]
---

## Overview

AI Content Factory는 SNS 마케팅 이미지 콘텐츠를 빠르게 대량 생산하기 위한 통합 워크플로우 시스템입니다. 기존 Video Studio(SPEC-005) 시스템을 이미지 중심 콘텐츠 생산 시스템으로 전환하여, 사용자가 6단계 마법사를 통해 단일 이미지, 캐러셀, 스토리 형식의 SNS 콘텐츠를 손쉽게 제작할 수 있습니다.

## Implementation Status (COMPLETED)

### Phase 1-2: COMPLETED

다음 작업들이 완료되었습니다:

**네비게이션 변경**:
- 기존: 홈, Video Studio, 브랜드 관리, 설정
- 신규: 홈, 콘텐츠 생성, 레퍼런스, 브랜드 관리

**완료된 페이지**:
- `/frontend/app/page.tsx` - 새 대시보드 (통계, 빠른 생성 액션)
- `/frontend/app/create/page.tsx` - 콘텐츠 생성 마법사 (Step 1-6 UI 완성)
- `/frontend/app/references/page.tsx` - 레퍼런스 라이브러리 (SNS 링크 분석 UI)
- `/frontend/app/layout.tsx` - 네비게이션 변경 완료

**백업된 파일**:
- `/frontend/app/page.tsx.backup` - 기존 레퍼런스 분석 홈페이지

**설치된 패키지**:
- sonner: Toast 알림 시스템
- 50MB 파일 업로드 제한 (프론트엔드 + 백엔드 검증)

### Phase 3: SNS Parsing and Image Analysis - COMPLETED

**구현된 기능**:
- SNS 링크 파싱 서비스 (gallery-dl 기반 Instagram/Facebook 지원)
- 이미지 분석 서비스 (Gemini Vision API 연동)
- 레퍼런스 API 확장

**구현된 파일**:
- `/backend/app/services/sns_parser.py` - SNS 링크 파싱 서비스
- `/backend/app/services/sns_media_downloader.py` - 미디어 다운로드 서비스
- `/backend/app/services/content_image_analyzer.py` - 콘텐츠 이미지 분석 서비스
- `/backend/app/services/image_analyzer.py` - 이미지 분석 서비스

### Phase 4: AI Image Generation - COMPLETED

**구현된 기능**:
- Gemini Imagen API 연동
- 4개 변형 이미지 병렬 생성
- 프롬프트 빌더 시스템

**구현된 파일**:
- `/backend/app/services/image_prompt_builder.py` - AI 프롬프트 생성기
- `/backend/app/services/batch_image_generator.py` - 배치 이미지 생성 서비스
- `/backend/app/services/image_composite_generator.py` - 합성 이미지 생성 서비스

### Phase 5: Canvas Text Editor - COMPLETED

**구현된 기능**:
- Fabric.js 기반 캔버스 에디터
- 텍스트 추가/편집/삭제
- 폰트, 크기, 색상 스타일링
- 드래그 앤 드롭 위치 조정
- 레이어 관리 (순서 변경, 삭제)

**구현된 파일**:
- `/frontend/app/create/edit/page.tsx` - 캔버스 에디터 페이지
- `/frontend/components/canvas/CanvasTextEditor.tsx` - 메인 에디터 컴포넌트
- `/frontend/components/canvas/FabricCanvas.tsx` - Fabric.js 캔버스 래퍼
- `/frontend/components/canvas/TextToolbar.tsx` - 텍스트 도구 툴바
- `/frontend/components/canvas/LayerPanel.tsx` - 레이어 관리 패널
- `/backend/app/services/image_editor.py` - 서버측 이미지 편집 서비스

### Phase 6: Platform Export - COMPLETED

**구현된 기능**:
- 플랫폼별 최적화 크기 변환
- 다중 형식 내보내기 (JPEG, PNG, WebP)
- 배치 다운로드 (ZIP)
- 플랫폼 프리셋 (Instagram, Facebook, Stories)

**구현된 파일**:
- `/frontend/components/canvas/CanvasExportPanel.tsx` - 내보내기 패널
- `/frontend/components/canvas/PlatformPresets.tsx` - 플랫폼 프리셋 컴포넌트
- `/frontend/components/canvas/BatchExportModal.tsx` - 배치 내보내기 모달
- `/backend/app/services/image_metadata.py` - 이미지 메타데이터 서비스

### Test Coverage: 330 Tests Passing

모든 Phase에 대한 유닛 테스트 및 통합 테스트 완료:
- `/frontend/__tests__/canvas/TextToolbar.test.tsx`
- `/frontend/__tests__/canvas/LayerPanel.test.tsx`
- `/frontend/__tests__/canvas/PlatformPresets.test.tsx`
- `/frontend/__tests__/canvas/BatchExportModal.test.tsx`

## New Workflow Design (v1.0)

```
Step 1: 콘텐츠 유형 선택
    - 단일 이미지 (1:1, 4:5 비율)
    - 캐러셀 (2~10장 세트)
    - 스토리 (9:16 세로형)
    ↓
Step 2: 용도 선택
    - 광고/홍보 → 브랜드/상품 선택 필수
    - 정보성 (팁, 노하우)
    - 일상/감성 (무드 콘텐츠)
    ↓
Step 3: 생성 방식 선택
    - 레퍼런스 활용: 저장된 레퍼런스 스타일 참고
    - 직접 만들기: 프롬프트로 직접 설명
    ↓
Step 4: AI 이미지 생성
    - 4개 변형 이미지 생성
    - Gemini Imagen API 연동
    ↓
Step 5: 이미지 선택
    - 4개 중 마음에 드는 이미지 선택
    - 재생성 옵션 제공
    ↓
Step 6: 텍스트 편집
    - Fabric.js 또는 Konva.js 기반 캔버스 에디터
    - 텍스트 추가/편집, 위치 조정, 스타일링
    ↓
Step 7: 내보내기
    - 플랫폼별 최적화 크기 변환
    - Instagram, Facebook, Stories 등
```

## Environment (E)

### System Context

- **Frontend Framework**: Next.js 14 + React Query + TailwindCSS
- **Backend Framework**: FastAPI (Python 3.12+)
- **Database**: MariaDB + SQLAlchemy 2.0 (async)
- **Object Storage**: MinIO (S3 compatible) / Local filesystem (backend/storage/)
- **Image Generation**: Gemini Imagen API (Primary)
- **Canvas Editor**: Fabric.js 또는 Konva.js
- **Toast Notifications**: Sonner (이미 설치됨)

### External Dependencies

- SPEC-002 (Brand/Product): 브랜드 및 제품 정보
- Gemini Imagen API: AI 이미지 생성
- Product Images: `/backend/storage/products/` (persistent storage)

### Configuration

- `GEMINI_API_KEY`: Gemini API 키
- `MAX_UPLOAD_SIZE`: 50MB (이미 구현됨)
- `IMAGE_GENERATION_VARIANTS`: 4 (생성 변형 수)
- `STORAGE_PATH`: `/backend/storage/` (영구 저장소)

## Assumptions (A)

### Business Assumptions

- 사용자는 SNS 콘텐츠 유형(단일, 캐러셀, 스토리)을 먼저 선택합니다
- 광고/홍보 목적의 콘텐츠는 브랜드/상품 정보가 반영됩니다
- 레퍼런스 분석 결과로 유사한 스타일의 이미지를 생성할 수 있습니다
- 텍스트 편집은 캔버스 기반 에디터로 직관적으로 수행됩니다
- 최종 결과물은 각 SNS 플랫폼에 최적화된 크기로 내보내기 됩니다

### Technical Assumptions

- Gemini Imagen API가 안정적으로 서비스됩니다
- 이미지 생성은 4개 변형을 병렬로 생성하여 선택권을 제공합니다
- Canvas 에디터는 Fabric.js 또는 Konva.js를 활용합니다
- 생성된 콘텐츠는 영구 저장소에 보관됩니다

### Constraints

- Gemini Imagen API 비용 (건당 과금)
- 이미지 생성 시간 (약 10-30초)
- 캔버스 에디터 성능 (대용량 이미지 처리)
- 파일 업로드 제한: 50MB

## Requirements (R)

### Functional Requirements

#### FR-001: SNS Link Parsing (Phase 3)

- **When** 사용자가 Instagram/Facebook 링크를 입력하면
- **The System Shall** 링크에서 이미지/콘텐츠를 추출하고 분석합니다
- **Analysis Output**: composition(구도), colorScheme(색감), style(스타일), elements(요소)
- **Supported Platforms**: Instagram, Facebook
- **Priority**: High

#### FR-002: Image Analysis API (Phase 3)

- **When** 사용자가 이미지를 업로드하면
- **The System Shall** AI를 통해 이미지의 스타일, 구도, 색감을 분석합니다
- **Analysis Output**: 레퍼런스로 저장 가능한 분석 데이터
- **Max Size**: 50MB
- **Priority**: High

#### FR-003: Reference-Based Image Generation (Phase 4)

- **When** 사용자가 레퍼런스를 선택하고 이미지 생성을 요청하면
- **The System Shall** 레퍼런스 스타일을 반영한 4개 변형 이미지를 생성합니다
- **Input**: 레퍼런스 분석 데이터 + 브랜드/상품 정보 (선택적)
- **Output**: 4개의 변형 이미지 URL
- **Priority**: High

#### FR-004: Prompt-Based Image Generation (Phase 4)

- **When** 사용자가 프롬프트를 입력하고 이미지 생성을 요청하면
- **The System Shall** Gemini Imagen API를 통해 4개 변형 이미지를 생성합니다
- **Input**: 사용자 프롬프트 + 콘텐츠 유형 + 브랜드/상품 정보 (선택적)
- **Output**: 4개의 변형 이미지 URL
- **Priority**: High

#### FR-005: Canvas Text Editor (Phase 5)

- **When** 사용자가 이미지를 선택하고 편집 단계로 이동하면
- **The System Shall** Fabric.js/Konva.js 기반 캔버스 에디터를 제공합니다
- **Features**:
  - 텍스트 추가/편집/삭제
  - 폰트 선택 (기본 웹폰트 + 한글 폰트)
  - 폰트 크기, 색상, 스타일 변경
  - 텍스트 위치 드래그 앤 드롭
  - 텍스트 회전, 크기 조절
  - 레이어 순서 조정
- **Priority**: High

#### FR-006: Platform-Specific Export (Phase 6)

- **When** 사용자가 내보내기를 요청하면
- **The System Shall** 선택된 플랫폼에 최적화된 크기로 이미지를 변환합니다
- **Export Sizes**:
  - Instagram Feed: 1080x1080 (1:1), 1080x1350 (4:5)
  - Instagram Story: 1080x1920 (9:16)
  - Facebook Feed: 1200x1200 (1:1), 1200x630 (1.91:1)
  - Carousel: 각 슬라이드별 동일 규격
- **Output Formats**: JPEG, PNG, WebP
- **Priority**: High

#### FR-007: Content History Management

- **When** 콘텐츠가 생성/저장되면
- **The System Shall** 작업 이력을 저장하고 대시보드에 표시합니다
- **Data**: 썸네일, 제목, 유형, 생성일, 상태
- **Priority**: Medium

### Non-Functional Requirements

#### NFR-001: Image Generation Performance

- 4개 변형 이미지 생성: 30초 이내
- 진행률 표시 필수 (Toast 알림)

#### NFR-002: Editor Performance

- Canvas 에디터 초기 로딩: 2초 이내
- 텍스트 편집 반응 시간: 100ms 이내
- 최대 지원 이미지 크기: 4096x4096

#### NFR-003: Export Performance

- 단일 이미지 내보내기: 3초 이내
- 캐러셀 전체 내보내기: 10초 이내

## Specifications (S)

### Database Models

#### Reference (Enhanced from current mock)

- `id` (VARCHAR(36), PK): UUID
- `type` (VARCHAR(20), NOT NULL): single, carousel, story
- `source` (VARCHAR(20), NOT NULL): instagram, facebook, upload
- `source_url` (VARCHAR(1000), NULLABLE): 원본 링크
- `thumbnail_url` (VARCHAR(500), NULLABLE): 썸네일 URL
- `analysis` (JSON, NOT NULL): 분석 결과
  - composition: 구도
  - colorScheme: 색감
  - style: 스타일
  - elements: 요소 배열
- `brand_id` (VARCHAR(36), FK, NULLABLE): 연결된 브랜드
- `tags` (JSON, DEFAULT []): 사용자 태그
- `created_at`, `updated_at` (DATETIME)

#### ContentProject (NEW)

- `id` (VARCHAR(36), PK): UUID
- `title` (VARCHAR(255), NOT NULL): 프로젝트 제목
- `type` (VARCHAR(20), NOT NULL): single, carousel, story
- `purpose` (VARCHAR(20), NOT NULL): ad, info, lifestyle
- `method` (VARCHAR(20), NOT NULL): reference, prompt
- `brand_id` (VARCHAR(36), FK, NULLABLE): 브랜드 (광고/홍보인 경우)
- `product_id` (VARCHAR(36), FK, NULLABLE): 상품
- `reference_id` (VARCHAR(36), FK, NULLABLE): 레퍼런스 (레퍼런스 방식인 경우)
- `prompt` (TEXT, NULLABLE): 사용자 프롬프트
- `status` (VARCHAR(30), NOT NULL): draft, generating, selecting, editing, exported
- `current_step` (INTEGER, DEFAULT 1): 현재 단계 (1-6)
- `metadata` (JSON, NULLABLE): 추가 메타데이터
- `created_at`, `updated_at`, `exported_at` (DATETIME)

#### GeneratedImage

- `id` (VARCHAR(36), PK): UUID
- `project_id` (VARCHAR(36), FK, NOT NULL, INDEX): 프로젝트
- `variant_number` (INTEGER, NOT NULL): 변형 번호 (1-4)
- `image_url` (VARCHAR(500), NOT NULL): 생성된 이미지 URL
- `thumbnail_url` (VARCHAR(500), NULLABLE): 썸네일 URL
- `generation_prompt` (TEXT, NOT NULL): 생성에 사용된 프롬프트
- `is_selected` (BOOLEAN, DEFAULT FALSE): 선택 여부
- `created_at` (DATETIME)

#### ContentOutput

- `id` (VARCHAR(36), PK): UUID
- `project_id` (VARCHAR(36), FK, NOT NULL, INDEX): 프로젝트
- `platform` (VARCHAR(30), NOT NULL): instagram_feed, instagram_story, facebook_feed, etc.
- `width` (INTEGER, NOT NULL): 출력 너비
- `height` (INTEGER, NOT NULL): 출력 높이
- `format` (VARCHAR(10), NOT NULL): jpeg, png, webp
- `output_url` (VARCHAR(500), NOT NULL): 출력 파일 URL
- `canvas_data` (JSON, NULLABLE): Fabric.js/Konva.js 캔버스 상태
- `created_at` (DATETIME)

### API Endpoints

#### References API (Phase 3)

- `POST /api/v1/references/analyze-link` - SNS 링크 분석
  - Request: `{ "url": "https://instagram.com/p/..." }`
  - Response: Reference 객체
- `POST /api/v1/references/analyze-image` - 이미지 분석 (업로드)
  - Request: multipart/form-data (image file)
  - Response: Reference 객체
- `GET /api/v1/references` - 레퍼런스 목록 (필터링 지원)
- `GET /api/v1/references/{id}` - 레퍼런스 상세
- `DELETE /api/v1/references/{id}` - 레퍼런스 삭제

#### Content Generation API (Phase 4)

- `POST /api/v1/content/generate` - 이미지 생성 요청
  - Request:
    ```json
    {
      "type": "single|carousel|story",
      "purpose": "ad|info|lifestyle",
      "method": "reference|prompt",
      "brand_id": "optional",
      "product_id": "optional",
      "reference_id": "optional",
      "prompt": "optional"
    }
    ```
  - Response: `{ "project_id": "...", "status": "generating" }`
- `GET /api/v1/content/{project_id}/images` - 생성된 이미지 목록
- `POST /api/v1/content/{project_id}/select/{image_id}` - 이미지 선택

#### Canvas Editor API (Phase 5)

- `GET /api/v1/content/{project_id}/canvas` - 캔버스 상태 조회
- `PUT /api/v1/content/{project_id}/canvas` - 캔버스 상태 저장
  - Request: Fabric.js/Konva.js JSON 데이터

#### Export API (Phase 6)

- `POST /api/v1/content/{project_id}/export` - 내보내기
  - Request: `{ "platforms": ["instagram_feed", "instagram_story"], "format": "jpeg" }`
  - Response: `{ "outputs": [{ "platform": "...", "url": "..." }] }`
- `GET /api/v1/content/{project_id}/outputs` - 출력물 목록
- `GET /api/v1/content/{project_id}/download` - 전체 다운로드 (ZIP)

### Frontend Components Structure

```
/frontend/app/
├── page.tsx                 # Dashboard (COMPLETED)
├── layout.tsx               # Navigation (COMPLETED)
├── create/
│   ├── page.tsx            # Create wizard (COMPLETED - Steps 1-5 UI)
│   └── edit/
│       └── [id]/
│           └── page.tsx    # Canvas editor (Phase 5)
├── references/
│   └── page.tsx            # Reference library (COMPLETED - UI only)
└── brands/
    └── page.tsx            # Brand management (existing)

/frontend/components/
├── create/
│   ├── StepIndicator.tsx   # Progress steps
│   ├── TypeSelector.tsx    # Step 1
│   ├── PurposeSelector.tsx # Step 2
│   ├── MethodSelector.tsx  # Step 3
│   ├── GeneratePanel.tsx   # Step 4
│   └── ImageSelector.tsx   # Step 5
├── editor/
│   ├── CanvasEditor.tsx    # Main editor component (Phase 5)
│   ├── TextToolbar.tsx     # Text editing toolbar
│   ├── LayerPanel.tsx      # Layer management
│   └── ExportDialog.tsx    # Export options (Phase 6)
└── references/
    ├── ReferenceCard.tsx   # Reference item card
    ├── ReferenceDetail.tsx # Detail panel
    └── AddReferenceModal.tsx # Add modal
```

### Storage Structure

```
/backend/storage/
├── products/               # Product images (existing, persistent)
├── references/             # Reference images
│   └── {reference_id}/
│       ├── original.jpg
│       └── thumbnail.jpg
├── projects/               # Content projects
│   └── {project_id}/
│       ├── generated/
│       │   ├── variant_1.jpg
│       │   ├── variant_2.jpg
│       │   ├── variant_3.jpg
│       │   └── variant_4.jpg
│       ├── canvas/
│       │   └── state.json
│       └── outputs/
│           ├── instagram_feed_1080x1080.jpg
│           └── instagram_story_1080x1920.jpg
└── temp/                   # Temporary files
```

## Implementation Files (Planned)

### Backend (Phase 3-4)

- `/backend/app/api/v1/references.py`: 레퍼런스 API (확장)
- `/backend/app/api/v1/content.py`: 콘텐츠 생성 API (NEW)
- `/backend/app/services/sns_parser.py`: SNS 링크 파서 (NEW)
- `/backend/app/services/image_analyzer.py`: 이미지 분석 서비스 (NEW)
- `/backend/app/services/image_generator.py`: Gemini Imagen 연동 (NEW)
- `/backend/app/models/reference.py`: Reference ORM 모델 (NEW)
- `/backend/app/models/content_project.py`: ContentProject ORM 모델 (NEW)
- `/backend/alembic/versions/xxx_content_factory.py`: DB 마이그레이션

### Frontend (Phase 5-6)

- `/frontend/app/create/edit/[id]/page.tsx`: 캔버스 에디터 페이지 (NEW)
- `/frontend/components/editor/CanvasEditor.tsx`: Fabric.js 에디터 (NEW)
- `/frontend/components/editor/TextToolbar.tsx`: 텍스트 도구 (NEW)
- `/frontend/components/editor/ExportDialog.tsx`: 내보내기 다이얼로그 (NEW)
- `/frontend/lib/api/content.ts`: Content API 클라이언트 (NEW)

## Traceability

### Related SPECs

- SPEC-002 (Brand/Product): 브랜드/제품 정보 활용
- SPEC-005 (Video Studio): 기존 Video Studio - 보존하되 새 워크플로우와 분리

### Preserved Code

- `/frontend/app/studio/page.tsx`: 기존 비디오 스튜디오 코드 보존 (주석 처리 예정)
- `/frontend/app/page.tsx.backup`: 기존 레퍼런스 분석 홈페이지 백업

### Migration Notes

- 기존 Video Studio 기능은 제거하지 않고 보존합니다
- 새 Content Factory 워크플로우와 병행 운영 가능합니다
- 네비게이션은 이미 새 구조로 변경되었습니다

---

**Implementation Status**: COMPLETED (All Phases)
**Version**: 1.1.0
**Priority**: High
**Test Results**: 330 tests passing
**Completion Date**: 2025-12-19
