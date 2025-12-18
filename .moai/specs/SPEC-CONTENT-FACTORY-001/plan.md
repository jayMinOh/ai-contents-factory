# SPEC-CONTENT-FACTORY-001: Implementation Plan

---
spec_id: SPEC-CONTENT-FACTORY-001
document_type: plan
version: 1.0.0
created_at: 2025-12-18
updated_at: 2025-12-18
---

## Implementation Overview

이 문서는 AI Content Factory 워크플로우 재설계의 구현 계획을 정의합니다. Phase 1-2가 완료된 상태에서 Phase 3-6의 남은 작업을 상세히 기술합니다.

## Completed Work Summary (Phase 1-2)

### Phase 1: Navigation and Structure

**Status**: COMPLETED

완료된 작업:
- 네비게이션 구조 변경 (홈, 콘텐츠 생성, 레퍼런스, 브랜드 관리)
- layout.tsx 수정 완료
- 라우팅 구조 확정

### Phase 2: Core Pages UI

**Status**: COMPLETED

완료된 파일:
- `/frontend/app/page.tsx` - 새 대시보드
  - 통계 표시 (이번 주 생성, 전체 콘텐츠, 저장된 레퍼런스)
  - 빠른 생성 액션 (단일 이미지, 캐러셀, 스토리)
  - 최근 작업 목록

- `/frontend/app/create/page.tsx` - 콘텐츠 생성 마법사
  - Step 1: 콘텐츠 유형 선택 UI
  - Step 2: 용도 선택 + 브랜드/상품 선택 UI
  - Step 3: 생성 방식 선택 + 프롬프트 입력 UI
  - Step 4: 이미지 생성 요약 및 버튼
  - Step 5: 생성된 이미지 선택 UI (Mock 데이터)

- `/frontend/app/references/page.tsx` - 레퍼런스 라이브러리
  - 레퍼런스 그리드 뷰
  - 유형 필터 (전체, 단일, 캐러셀, 스토리)
  - 검색 UI
  - 새 레퍼런스 추가 모달 (SNS 링크, 이미지 업로드)
  - 상세 패널 (분석 결과 표시)

설치된 패키지:
- sonner: Toast 알림 시스템

기술적 설정:
- 50MB 파일 업로드 제한 구현

## Remaining Implementation Phases

### Phase 3: Backend SNS Link Parsing and Image Analysis

**Priority**: High
**Milestone**: Primary Goal

#### 3.1 SNS Link Parser Service

구현 목표:
- Instagram/Facebook 링크에서 이미지/콘텐츠 추출
- 메타데이터 파싱 (이미지 URL, 캡션, 유형)

기술 접근:
- Instagram Graph API 또는 웹 스크래핑 (비공개 API 제한 고려)
- yt-dlp 또는 유사 라이브러리 활용
- Fallback: 사용자에게 이미지 직접 업로드 유도

구현 파일:
- `/backend/app/services/sns_parser.py`
- `/backend/app/api/v1/references.py` (확장)

API 엔드포인트:
- `POST /api/v1/references/analyze-link`

#### 3.2 Image Analysis Service

구현 목표:
- 업로드된 이미지의 스타일, 구도, 색감 분석
- Gemini Vision API 또는 유사 멀티모달 AI 활용

분석 출력:
- composition: 구도 (중앙 집중, 좌우 대칭, 황금비 등)
- colorScheme: 색감 (따뜻한/차가운 톤, 주요 색상)
- style: 스타일 (미니멀, 모던, 클래식 등)
- elements: 요소 배열 (제품, 텍스트, 모델, 배경 등)

구현 파일:
- `/backend/app/services/image_analyzer.py`

API 엔드포인트:
- `POST /api/v1/references/analyze-image`

#### 3.3 Database Models

구현 파일:
- `/backend/app/models/reference.py`
- `/backend/alembic/versions/xxx_references.py`

### Phase 4: AI Image Generation Integration

**Priority**: High
**Milestone**: Primary Goal

#### 4.1 Gemini Imagen Integration

구현 목표:
- Gemini Imagen API 연동
- 4개 변형 이미지 병렬 생성
- 생성 진행률 실시간 업데이트

기술 접근:
- google-generativeai Python SDK
- 비동기 처리로 4개 요청 병렬 실행
- WebSocket 또는 폴링으로 진행률 전달

프롬프트 구성:
- 기본 프롬프트 + 콘텐츠 유형 템플릿
- 레퍼런스 스타일 반영 (선택 시)
- 브랜드/상품 정보 반영 (광고/홍보인 경우)

구현 파일:
- `/backend/app/services/image_generator.py`
- `/backend/app/api/v1/content.py`

API 엔드포인트:
- `POST /api/v1/content/generate`
- `GET /api/v1/content/{project_id}/images`
- `GET /api/v1/content/{project_id}/status`

#### 4.2 Frontend Integration

구현 목표:
- create/page.tsx의 Mock 데이터를 실제 API 연동으로 교체
- 생성 중 로딩 상태 및 진행률 표시
- 생성된 이미지 4개 표시 및 선택 UI

수정 파일:
- `/frontend/app/create/page.tsx`
- `/frontend/lib/api/content.ts` (NEW)

#### 4.3 Database Models

구현 파일:
- `/backend/app/models/content_project.py`
- `/backend/app/models/generated_image.py`
- `/backend/alembic/versions/xxx_content_projects.py`

### Phase 5: Canvas Text Editor

**Priority**: High
**Milestone**: Secondary Goal

#### 5.1 Canvas Editor Component

구현 목표:
- Fabric.js 기반 캔버스 에디터 구현
- 선택된 이미지를 배경으로 로드
- 텍스트 레이어 추가/편집/삭제

기술 접근:
- Fabric.js (선호) 또는 Konva.js
- React와 통합을 위한 래퍼 컴포넌트
- 캔버스 상태 JSON 직렬화

기능 상세:
- 텍스트 추가: 클릭하여 텍스트 박스 추가
- 폰트 선택: Noto Sans KR, Pretendard, 기본 웹폰트
- 스타일링: 크기, 색상, 굵기, 기울임, 그림자
- 위치: 드래그 앤 드롭, 회전, 크기 조절
- 레이어: 순서 변경, 삭제

구현 파일:
- `/frontend/app/create/edit/[id]/page.tsx` (NEW)
- `/frontend/components/editor/CanvasEditor.tsx` (NEW)
- `/frontend/components/editor/TextToolbar.tsx` (NEW)
- `/frontend/components/editor/LayerPanel.tsx` (NEW)

#### 5.2 Canvas State Persistence

구현 목표:
- 캔버스 상태 자동 저장
- 이전 작업 불러오기

API 엔드포인트:
- `PUT /api/v1/content/{project_id}/canvas`
- `GET /api/v1/content/{project_id}/canvas`

### Phase 6: Export with Platform Optimization

**Priority**: Medium
**Milestone**: Final Goal

#### 6.1 Export Dialog Component

구현 목표:
- 플랫폼 선택 UI (Instagram, Facebook, Stories)
- 각 플랫폼별 프리뷰
- 출력 형식 선택 (JPEG, PNG, WebP)

플랫폼별 크기:
- Instagram Feed 1:1: 1080x1080
- Instagram Feed 4:5: 1080x1350
- Instagram Story: 1080x1920
- Facebook Feed 1:1: 1200x1200
- Facebook Feed 1.91:1: 1200x630

구현 파일:
- `/frontend/components/editor/ExportDialog.tsx` (NEW)

#### 6.2 Image Processing Service

구현 목표:
- Canvas 렌더링 결과를 서버로 전송
- 플랫폼별 크기로 리사이즈 및 최적화
- 다운로드 URL 생성

기술 접근:
- Pillow (Python Imaging Library)
- 품질 최적화 옵션
- 배치 처리 (캐러셀의 경우)

구현 파일:
- `/backend/app/services/image_exporter.py` (NEW)

API 엔드포인트:
- `POST /api/v1/content/{project_id}/export`
- `GET /api/v1/content/{project_id}/outputs`
- `GET /api/v1/content/{project_id}/download`

#### 6.3 Database Models

구현 파일:
- `/backend/app/models/content_output.py`
- 마이그레이션 업데이트

## Technical Approach

### Package Dependencies (Frontend)

추가 설치 필요:
- fabric: Canvas 에디터 라이브러리
- file-saver: 파일 다운로드 유틸리티
- jszip: ZIP 파일 생성 (배치 다운로드)

### Package Dependencies (Backend)

추가 설치 필요:
- google-generativeai: Gemini API SDK
- Pillow: 이미지 처리
- aiohttp: 비동기 HTTP 클라이언트 (SNS 파싱)

### Architecture Design

프론트엔드 아키텍처:
- React Query로 서버 상태 관리
- Zustand 또는 Context API로 에디터 상태 관리
- Toast 알림은 sonner 활용 (이미 설치됨)

백엔드 아키텍처:
- FastAPI async 엔드포인트
- 백그라운드 태스크로 이미지 생성 처리
- WebSocket 또는 SSE로 실시간 업데이트 (선택적)

### Risk Mitigation

위험 요소 1: SNS API 제한
- 대응: 웹 스크래핑 대안 구현
- Fallback: 사용자 직접 업로드 유도

위험 요소 2: Gemini Imagen API 지연/오류
- 대응: 재시도 로직 구현 (최대 3회)
- Fallback: 에러 메시지 및 재시도 버튼 제공

위험 요소 3: Canvas 에디터 성능
- 대응: 이미지 리사이즈 후 편집
- 최적화: Canvas 영역 외 렌더링 제한

## Milestone Summary

### Primary Goal (Phase 3-4)

핵심 기능 구현:
- SNS 링크 파싱 및 이미지 분석 API
- Gemini Imagen 연동 이미지 생성
- 프론트엔드-백엔드 실제 연동

완료 기준:
- 레퍼런스 추가 시 실제 분석 결과 표시
- 이미지 생성 시 실제 AI 생성 이미지 4개 표시

### Secondary Goal (Phase 5)

편집 기능 구현:
- Fabric.js 캔버스 에디터
- 텍스트 추가/편집 전체 기능
- 캔버스 상태 저장/불러오기

완료 기준:
- 선택한 이미지에 텍스트 추가 및 편집 가능
- 작업 중간 저장 및 재개 가능

### Final Goal (Phase 6)

내보내기 기능 구현:
- 플랫폼별 크기 최적화
- 다중 형식 내보내기
- 배치 다운로드

완료 기준:
- 각 플랫폼별 최적화된 이미지 다운로드 가능
- 캐러셀 전체 ZIP 다운로드 가능

## Dependency Graph

```
Phase 1 (COMPLETED)
    ↓
Phase 2 (COMPLETED)
    ↓
Phase 3: Backend APIs
    ├── 3.1 SNS Parser
    ├── 3.2 Image Analyzer
    └── 3.3 Database Models
    ↓
Phase 4: Image Generation
    ├── 4.1 Gemini Integration (depends on 3.3)
    ├── 4.2 Frontend Integration (depends on 4.1)
    └── 4.3 Database Models
    ↓
Phase 5: Canvas Editor (depends on Phase 4)
    ├── 5.1 Editor Component
    └── 5.2 State Persistence
    ↓
Phase 6: Export (depends on Phase 5)
    ├── 6.1 Export Dialog
    ├── 6.2 Image Processing
    └── 6.3 Database Models
```

## File Changes Summary

### New Files

Backend:
- `/backend/app/services/sns_parser.py`
- `/backend/app/services/image_analyzer.py`
- `/backend/app/services/image_generator.py`
- `/backend/app/services/image_exporter.py`
- `/backend/app/api/v1/content.py`
- `/backend/app/models/reference.py`
- `/backend/app/models/content_project.py`
- `/backend/app/models/generated_image.py`
- `/backend/app/models/content_output.py`

Frontend:
- `/frontend/app/create/edit/[id]/page.tsx`
- `/frontend/components/editor/CanvasEditor.tsx`
- `/frontend/components/editor/TextToolbar.tsx`
- `/frontend/components/editor/LayerPanel.tsx`
- `/frontend/components/editor/ExportDialog.tsx`
- `/frontend/lib/api/content.ts`

### Modified Files

Backend:
- `/backend/app/api/v1/references.py` (확장)
- `/backend/app/api/v1/__init__.py` (라우터 추가)

Frontend:
- `/frontend/app/create/page.tsx` (실제 API 연동)
- `/frontend/app/references/page.tsx` (실제 API 연동)

## Next Steps for Implementation

다음 세션에서 시작할 작업:

1. Phase 3.3 데이터베이스 모델 정의 및 마이그레이션 생성
2. Phase 3.1 SNS 파서 서비스 구현 (기본 구조)
3. Phase 3.2 이미지 분석 서비스 구현 (Gemini Vision API 연동)
4. 레퍼런스 API 확장 및 프론트엔드 연동

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-18
