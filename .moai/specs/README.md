# AI Video Marketing - SPEC Documents

## Overview

AI Video Marketing 플랫폼의 기능 명세 문서입니다. EARS (Easy Approach to Requirements Syntax) 형식으로 작성되었습니다.

## SPEC Index

### Implemented (구현 완료)

#### SPEC-CONTENT-FACTORY-001: AI Content Factory
- **Status**: COMPLETED
- **Location**: `SPEC-CONTENT-FACTORY-001/`
- **Version**: 1.1.0
- **Completion Date**: 2025-12-19
- **Description**: SNS 마케팅 이미지 콘텐츠를 빠르게 대량 생산하기 위한 통합 워크플로우 시스템
- **Key Features**:
  - 6단계 콘텐츠 생성 마법사 (유형, 용도, 방식, 생성, 선택, 편집)
  - SNS 링크 파싱 및 이미지 분석 (gallery-dl, Gemini Vision API)
  - AI 이미지 생성 (Gemini Imagen API, 4개 변형)
  - Fabric.js 캔버스 텍스트 에디터
  - 플랫폼별 내보내기 (Instagram, Facebook, Stories)
  - 배치 다운로드 (JSZip)
- **Backend**: `/backend/app/services/sns_parser.py`, `/backend/app/services/image_analyzer.py`, `/backend/app/services/image_prompt_builder.py`
- **Frontend**: `/frontend/app/create/`, `/frontend/components/canvas/`
- **Tests**: 330 tests passing

#### SPEC-001: Reference Video Analysis System
- **Status**: IMPLEMENTED
- **Location**: `SPEC-001/`
- **Description**: 마케팅 영상(YouTube, TikTok, Instagram)을 AI로 분석하여 타임라인별 세그먼트, 후킹 포인트, 셀링 포인트 등 마케팅 인사이트를 추출하는 시스템
- **Key Features**:
  - YouTube/TikTok/Instagram URL 입력 및 검증
  - yt-dlp를 통한 영상 다운로드
  - FFmpeg 프레임 추출
  - Google Gemini API 마케팅 분석
  - 17개 마케팅 세그먼트 타입 지원
  - 실시간 폴링 상태 추적
- **Backend**: `/backend/app/api/v1/references.py`, `/backend/app/services/reference_analyzer/`
- **Frontend**: `/frontend/app/page.tsx`

#### SPEC-002: Brand and Product Management System
- **Status**: IMPLEMENTED
- **Location**: `SPEC-002/`
- **Description**: 마케팅 영상 생성에 필요한 브랜드 및 제품 정보를 관리하는 시스템
- **Key Features**:
  - Brand/Product CRUD 작업
  - SQLAlchemy 2.0 async ORM
  - 1:N 관계 (Brand -> Products) with CASCADE
  - React Query 기반 프론트엔드
  - 모달 기반 폼 UI
- **Backend**: `/backend/app/api/v1/brands.py`, `/backend/app/services/brand_service.py`, `/backend/app/services/product_service.py`
- **Frontend**: `/frontend/app/brands/page.tsx`

### Planned (구현 예정)

#### SPEC-005: Video Studio System (NEW)
- **Status**: PLANNED
- **Location**: `SPEC-005/`
- **Description**: AI 마케팅 영상 제작을 위한 통합 워크플로우 시스템
- **Key Features**:
  - 레퍼런스 분석 결과 DB 저장 (ReferenceAnalysis 모델)
  - 4단계 마법사 UI (브랜드/제품 → 레퍼런스 → 장면 편집 → 영상 생성)
  - 장면별 AI 이미지 생성 + 사용자 업로드 지원
  - 영상 생성 (Luma/Runway/HeyGen 통합)
  - 실시간 진행률 WebSocket
- **Dependencies**: SPEC-001, SPEC-002 (필수), SPEC-003 (선택)
- **Replaces**: SPEC-004 (기존 Video Generation 개념 확장)

#### SPEC-003: Brand Knowledge Base RAG System
- **Status**: PLANNED
- **Location**: `SPEC-003/`
- **Description**: 브랜드 및 제품 정보를 벡터 임베딩으로 저장하고, AI 영상 생성 시 관련 컨텍스트를 검색하여 제공하는 시스템
- **Key Features**:
  - Qdrant 벡터 데이터베이스 통합
  - OpenAI/Gemini 임베딩 생성
  - 시맨틱 검색 기능
  - CRUD 이벤트와 임베딩 동기화
- **Dependencies**: SPEC-002 (데이터 소스)
- **Stub Location**: `/backend/app/services/brand_knowledge/`

#### SPEC-004: AI Video Generation System
- **Status**: PLANNED
- **Location**: `SPEC-004/`
- **Description**: 레퍼런스 영상 분석 결과와 브랜드 지식을 활용하여 마케팅 영상 스크립트, 스토리보드를 생성하고 AI 영상 생성 API와 연동하는 시스템
- **Key Features**:
  - 레퍼런스 분석 기반 스크립트 생성
  - 스토리보드 자동 생성
  - Luma AI/Runway ML/HeyGen API 연동
  - MinIO 에셋 관리
- **Dependencies**: SPEC-001, SPEC-002 (필수), SPEC-003 (권장)
- **Stub Location**: `/backend/app/services/video_generator/`

## Document Structure

Each SPEC directory contains:
- `spec.md`: EARS 형식의 핵심 명세서 (Environment, Assumptions, Requirements, Specifications)
- `plan.md`: 구현 계획 및 마일스톤
- `acceptance.md`: 수락 기준 및 테스트 시나리오

## Dependency Graph

```
SPEC-CONTENT-FACTORY-001 (AI Content Factory) ─── COMPLETED
    └── Depends on: SPEC-002 (Brand/Product)

SPEC-001 (Reference Analysis) ──────────────┐
                                            │
SPEC-002 (Brand/Product) ──┬─── SPEC-003 ───┴─── SPEC-004 (Video Generation)
                           │   (RAG System)
                           └─────────────────────────┘
```

## Version History

- **2025-12-19**: SPEC-CONTENT-FACTORY-001 완료
  - AI Content Factory 전체 구현 완료 (Phase 1-6)
  - SNS 링크 파싱, 이미지 분석, AI 이미지 생성
  - Canvas 텍스트 에디터, 플랫폼별 내보내기
  - 330개 테스트 통과

- **2025-12-11**: Initial SPEC documentation created
  - SPEC-001: Documented existing Reference Video Analysis implementation
  - SPEC-002: Documented existing Brand/Product Management implementation
  - SPEC-003: Defined Brand Knowledge RAG requirements
  - SPEC-004: Defined AI Video Generation requirements

## Next Steps

1. SPEC-003 (Brand Knowledge RAG) 구현
   - Qdrant 인프라 설정
   - 임베딩 서비스 개발
   - CRUD 동기화 구현

2. SPEC-004 (Video Generation) 구현
   - 스크립트 생성 로직
   - 영상 생성 API 통합
   - MinIO 에셋 관리

3. 테스트 커버리지 확보
   - 각 SPEC별 90% 유닛 테스트 목표
   - E2E 테스트 플로우 구현
