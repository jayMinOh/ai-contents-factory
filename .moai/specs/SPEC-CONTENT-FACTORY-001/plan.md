# SPEC-CONTENT-FACTORY-001: Implementation Plan

---
spec_id: SPEC-CONTENT-FACTORY-001
document_type: plan
version: 1.1.0
created_at: 2025-12-18
updated_at: 2025-12-19
---

## Implementation Overview

이 문서는 AI Content Factory 워크플로우 재설계의 구현 계획을 정의합니다. 모든 Phase(1-6)가 완료되었습니다.

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

## Completed Implementation Phases

### Phase 3: Backend SNS Link Parsing and Image Analysis - COMPLETED

**Priority**: High
**Milestone**: Primary Goal
**Status**: COMPLETED

#### 3.1 SNS Link Parser Service - COMPLETED

구현된 기능:
- Instagram/Facebook 링크에서 이미지/콘텐츠 추출
- 메타데이터 파싱 (이미지 URL, 캡션, 유형)
- gallery-dl 라이브러리 기반 구현

구현된 파일:
- `/backend/app/services/sns_parser.py` - SNS URL 파싱 및 메타데이터 추출
- `/backend/app/services/sns_media_downloader.py` - 미디어 파일 다운로드
- `/backend/app/api/v1/references.py` - 레퍼런스 API 확장

API 엔드포인트:
- `POST /api/v1/references/analyze-link`

#### 3.2 Image Analysis Service - COMPLETED

구현된 기능:
- 업로드된 이미지의 스타일, 구도, 색감 분석
- Gemini Vision API 연동

분석 출력:
- composition: 구도 (중앙 집중, 좌우 대칭, 황금비 등)
- colorScheme: 색감 (따뜻한/차가운 톤, 주요 색상)
- style: 스타일 (미니멀, 모던, 클래식 등)
- elements: 요소 배열 (제품, 텍스트, 모델, 배경 등)

구현된 파일:
- `/backend/app/services/image_analyzer.py` - 이미지 분석 서비스
- `/backend/app/services/content_image_analyzer.py` - 콘텐츠 이미지 분석

API 엔드포인트:
- `POST /api/v1/references/analyze-image`

#### 3.3 Database Models - COMPLETED

구현된 파일:
- `/backend/app/models/reference_analysis.py` - 레퍼런스 분석 모델

### Phase 4: AI Image Generation Integration - COMPLETED

**Priority**: High
**Milestone**: Primary Goal
**Status**: COMPLETED

#### 4.1 Gemini Imagen Integration - COMPLETED

구현된 기능:
- Gemini Imagen API 연동
- 4개 변형 이미지 병렬 생성
- 생성 진행률 실시간 업데이트

기술 구현:
- google-generativeai Python SDK
- 비동기 처리로 4개 요청 병렬 실행
- Toast 알림으로 진행률 전달

프롬프트 구성:
- 기본 프롬프트 + 콘텐츠 유형 템플릿
- 레퍼런스 스타일 반영 (선택 시)
- 브랜드/상품 정보 반영 (광고/홍보인 경우)

구현된 파일:
- `/backend/app/services/image_prompt_builder.py` - AI 프롬프트 생성기
- `/backend/app/services/batch_image_generator.py` - 배치 이미지 생성
- `/backend/app/services/image_composite_generator.py` - 합성 이미지 생성

#### 4.2 Frontend Integration - COMPLETED

구현된 기능:
- create/page.tsx의 실제 API 연동
- 생성 중 로딩 상태 및 진행률 표시
- 생성된 이미지 4개 표시 및 선택 UI

수정된 파일:
- `/frontend/app/create/page.tsx` - 콘텐츠 생성 마법사 (전체 Step 연동)

### Phase 5: Canvas Text Editor - COMPLETED

**Priority**: High
**Milestone**: Secondary Goal
**Status**: COMPLETED

#### 5.1 Canvas Editor Component - COMPLETED

구현된 기능:
- Fabric.js 기반 캔버스 에디터 구현
- 선택된 이미지를 배경으로 로드
- 텍스트 레이어 추가/편집/삭제

기능 상세:
- 텍스트 추가: 클릭하여 텍스트 박스 추가
- 폰트 선택: Noto Sans KR, Pretendard, 기본 웹폰트
- 스타일링: 크기, 색상, 굵기, 기울임, 그림자
- 위치: 드래그 앤 드롭, 회전, 크기 조절
- 레이어: 순서 변경, 삭제

구현된 파일:
- `/frontend/app/create/edit/page.tsx` - 캔버스 에디터 페이지
- `/frontend/components/canvas/CanvasTextEditor.tsx` - 메인 에디터 컴포넌트
- `/frontend/components/canvas/FabricCanvas.tsx` - Fabric.js 캔버스 래퍼
- `/frontend/components/canvas/TextToolbar.tsx` - 텍스트 도구 툴바
- `/frontend/components/canvas/LayerPanel.tsx` - 레이어 관리 패널

#### 5.2 Canvas State Persistence - COMPLETED

구현된 기능:
- 캔버스 상태 자동 저장
- 이전 작업 불러오기

구현된 파일:
- `/backend/app/services/image_editor.py` - 서버측 이미지 편집 서비스

### Phase 6: Export with Platform Optimization - COMPLETED

**Priority**: Medium
**Milestone**: Final Goal
**Status**: COMPLETED

#### 6.1 Export Dialog Component - COMPLETED

구현된 기능:
- 플랫폼 선택 UI (Instagram, Facebook, Stories)
- 각 플랫폼별 프리뷰
- 출력 형식 선택 (JPEG, PNG, WebP)

플랫폼별 크기:
- Instagram Feed 1:1: 1080x1080
- Instagram Feed 4:5: 1080x1350
- Instagram Story: 1080x1920
- Facebook Feed 1:1: 1200x1200
- Facebook Feed 1.91:1: 1200x630

구현된 파일:
- `/frontend/components/canvas/CanvasExportPanel.tsx` - 내보내기 패널
- `/frontend/components/canvas/PlatformPresets.tsx` - 플랫폼 프리셋
- `/frontend/components/canvas/BatchExportModal.tsx` - 배치 내보내기 모달

#### 6.2 Image Processing Service - COMPLETED

구현된 기능:
- Canvas 렌더링 결과를 서버로 전송
- 플랫폼별 크기로 리사이즈 및 최적화
- 다운로드 URL 생성
- ZIP 파일 배치 다운로드 (JSZip)

구현된 파일:
- `/backend/app/services/image_metadata.py` - 이미지 메타데이터 서비스

## Technical Approach

### Package Dependencies (Frontend) - INSTALLED

설치 완료:
- fabric: Canvas 에디터 라이브러리
- file-saver: 파일 다운로드 유틸리티
- jszip: ZIP 파일 생성 (배치 다운로드)

### Package Dependencies (Backend) - INSTALLED

설치 완료:
- google-generativeai: Gemini API SDK
- Pillow: 이미지 처리
- gallery-dl: SNS 미디어 다운로드

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

## Milestone Summary - ALL COMPLETED

### Primary Goal (Phase 3-4) - COMPLETED

핵심 기능 구현:
- SNS 링크 파싱 및 이미지 분석 API
- Gemini Imagen 연동 이미지 생성
- 프론트엔드-백엔드 실제 연동

완료 기준: VERIFIED
- 레퍼런스 추가 시 실제 분석 결과 표시
- 이미지 생성 시 실제 AI 생성 이미지 4개 표시

### Secondary Goal (Phase 5) - COMPLETED

편집 기능 구현:
- Fabric.js 캔버스 에디터
- 텍스트 추가/편집 전체 기능
- 캔버스 상태 저장/불러오기

완료 기준: VERIFIED
- 선택한 이미지에 텍스트 추가 및 편집 가능
- 작업 중간 저장 및 재개 가능

### Final Goal (Phase 6) - COMPLETED

내보내기 기능 구현:
- 플랫폼별 크기 최적화
- 다중 형식 내보내기
- 배치 다운로드

완료 기준: VERIFIED
- 각 플랫폼별 최적화된 이미지 다운로드 가능
- 캐러셀 전체 ZIP 다운로드 가능

## Dependency Graph - ALL COMPLETED

```
Phase 1 (COMPLETED)
    ↓
Phase 2 (COMPLETED)
    ↓
Phase 3: Backend APIs (COMPLETED)
    ├── 3.1 SNS Parser (COMPLETED)
    ├── 3.2 Image Analyzer (COMPLETED)
    └── 3.3 Database Models (COMPLETED)
    ↓
Phase 4: Image Generation (COMPLETED)
    ├── 4.1 Gemini Integration (COMPLETED)
    ├── 4.2 Frontend Integration (COMPLETED)
    └── 4.3 Database Models (COMPLETED)
    ↓
Phase 5: Canvas Editor (COMPLETED)
    ├── 5.1 Editor Component (COMPLETED)
    └── 5.2 State Persistence (COMPLETED)
    ↓
Phase 6: Export (COMPLETED)
    ├── 6.1 Export Dialog (COMPLETED)
    ├── 6.2 Image Processing (COMPLETED)
    └── 6.3 Database Models (COMPLETED)
```

## File Changes Summary - COMPLETED

### Implemented Files

Backend:
- `/backend/app/services/sns_parser.py` - SNS URL 파싱 서비스
- `/backend/app/services/sns_media_downloader.py` - SNS 미디어 다운로드
- `/backend/app/services/image_analyzer.py` - 이미지 분석 서비스
- `/backend/app/services/content_image_analyzer.py` - 콘텐츠 이미지 분석
- `/backend/app/services/image_prompt_builder.py` - AI 프롬프트 생성기
- `/backend/app/services/batch_image_generator.py` - 배치 이미지 생성
- `/backend/app/services/image_composite_generator.py` - 합성 이미지 생성
- `/backend/app/services/image_editor.py` - 이미지 편집 서비스
- `/backend/app/services/image_metadata.py` - 이미지 메타데이터
- `/backend/app/models/reference_analysis.py` - 레퍼런스 분석 모델

Frontend:
- `/frontend/app/create/edit/page.tsx` - 캔버스 에디터 페이지
- `/frontend/components/canvas/CanvasTextEditor.tsx` - 메인 에디터 컴포넌트
- `/frontend/components/canvas/FabricCanvas.tsx` - Fabric.js 캔버스 래퍼
- `/frontend/components/canvas/TextToolbar.tsx` - 텍스트 도구 툴바
- `/frontend/components/canvas/LayerPanel.tsx` - 레이어 관리 패널
- `/frontend/components/canvas/CanvasExportPanel.tsx` - 내보내기 패널
- `/frontend/components/canvas/PlatformPresets.tsx` - 플랫폼 프리셋
- `/frontend/components/canvas/BatchExportModal.tsx` - 배치 내보내기 모달

Tests:
- `/frontend/__tests__/canvas/TextToolbar.test.tsx`
- `/frontend/__tests__/canvas/LayerPanel.test.tsx`
- `/frontend/__tests__/canvas/PlatformPresets.test.tsx`
- `/frontend/__tests__/canvas/BatchExportModal.test.tsx`

### Modified Files

Backend:
- `/backend/app/api/v1/references.py` - 레퍼런스 API 확장
- `/backend/app/api/v1/__init__.py` - 라우터 추가

Frontend:
- `/frontend/app/create/page.tsx` - 콘텐츠 생성 마법사 (전체 Step 연동)
- `/frontend/app/references/page.tsx` - 레퍼런스 라이브러리 (실제 API 연동)

## Implementation Summary

모든 Phase가 성공적으로 완료되었습니다:

- Phase 1-2: 네비게이션 및 UI 구조 완료
- Phase 3: SNS 파싱 및 이미지 분석 완료
- Phase 4: AI 이미지 생성 통합 완료
- Phase 5: Canvas 텍스트 에디터 완료
- Phase 6: 플랫폼 내보내기 완료

테스트 결과: 330개 테스트 모두 통과

---

**Document Version**: 1.1.0
**Last Updated**: 2025-12-19
**Status**: COMPLETED
