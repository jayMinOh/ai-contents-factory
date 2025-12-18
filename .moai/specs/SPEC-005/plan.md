# SPEC-005: Implementation Plan

---
spec_id: SPEC-005
title: Video Studio - Implementation Plan
version: 2.0.0
created_at: 2025-12-12
updated_at: 2025-12-12
tags: [video-studio, storyboard, implementation-plan]
---

## Overview

이 문서는 SPEC-005 Video Studio 시스템의 스토리보드 중심 워크플로우 구현 계획을 정의합니다.

## Implementation Phases

### Phase 1: Database Models and Storyboard Core

**Priority**: High
**Dependencies**: SPEC-001, SPEC-002 완료

**Tasks**:

- Storyboard 모델 생성 및 마이그레이션
  - Storyboard 테이블 스키마 정의
  - Scene JSON 구조 검증 로직
  - VideoProject와 1:1 관계 설정
  - 버전 관리 필드 구현

- VideoProject 모델 확장
  - status 필드 업데이트 (storyboard_generating, storyboard_ready 추가)
  - current_step 6단계로 확장
  - script 필드 제거 (Storyboard로 대체)

- SceneImage 모델 수정
  - scene_number를 1-based로 변경
  - scene_description, scene_segment_type 제거 (Storyboard에서 관리)
  - generation_prompt에 description + visual_direction 저장

**Deliverables**:

- `/backend/app/models/storyboard.py`
- `/backend/alembic/versions/xxx_add_storyboard.py`
- 기존 모델 수정사항

### Phase 2: Storyboard Generation Service

**Priority**: High
**Dependencies**: Phase 1 완료

**Tasks**:

- StoryboardGenerator 서비스 구현
  - ReferenceAnalysis 데이터 추출 로직
  - Brand/Product 정보 조합 로직
  - 두 가지 생성 모드 구현 (reference_structure, ai_optimized)

- SceneContentGenerator 서비스 구현
  - 장면 유형별 프롬프트 템플릿
  - LLM 호출을 통한 장면 콘텐츠 생성
  - 각 필드 생성 로직 (title, description, narration_script 등)

- PromptBuilder 확장
  - 스토리보드 생성용 시스템 프롬프트
  - 브랜드/제품 컨텍스트 주입
  - 장면 유형별 프롬프트 구성

**Deliverables**:

- `/backend/app/services/video_studio/storyboard_generator.py`
- `/backend/app/services/video_studio/scene_content_generator.py`
- `/backend/app/services/video_studio/prompt_builder.py` 확장

### Phase 3: Storyboard API Endpoints

**Priority**: High
**Dependencies**: Phase 2 완료

**Tasks**:

- 스토리보드 생성 API
  - POST /api/v1/video-projects/{id}/storyboard/generate
  - 비동기 생성 처리
  - 생성 상태 WebSocket 알림

- 스토리보드 조회/편집 API
  - GET /api/v1/video-projects/{id}/storyboard
  - PUT /api/v1/video-projects/{id}/storyboard/scenes/{scene_number}
  - POST /api/v1/video-projects/{id}/storyboard/scenes
  - DELETE /api/v1/video-projects/{id}/storyboard/scenes/{scene_number}
  - PUT /api/v1/video-projects/{id}/storyboard/scenes/reorder

- 버전 히스토리 API
  - GET /api/v1/video-projects/{id}/storyboard/history
  - POST /api/v1/video-projects/{id}/storyboard/restore/{version}

**Deliverables**:

- `/backend/app/api/v1/storyboards.py`
- `/backend/app/schemas/storyboard.py`
- API 라우터 등록

### Phase 4: Image Generation Enhancement

**Priority**: High
**Dependencies**: Phase 3 완료

**Tasks**:

- 이미지 생성 API 수정
  - POST /api/v1/video-projects/{id}/scenes/{scene_number}/generate-image
  - 스토리보드 장면의 description + visual_direction 조합
  - 브랜드 가이드라인 적용

- 이미지 버전 관리 강화
  - GET /api/v1/video-projects/{id}/scenes/{scene_number}/versions
  - 활성 이미지 선택 시 스토리보드 업데이트

- 일괄 이미지 생성 개선
  - 스토리보드 기반 병렬 생성
  - 진행률 WebSocket 알림

**Deliverables**:

- `/backend/app/api/v1/scene_images.py` 수정
- ImageGenerator 서비스 확장

### Phase 5: Frontend - Wizard UI

**Priority**: High
**Dependencies**: Phase 3 완료

**Tasks**:

- Step 1: InputSelector 컴포넌트
  - 레퍼런스 분석 결과 선택 UI
  - 브랜드/상품 선택 UI
  - 선택 항목 요약 표시

- Step 2: StoryboardOptions 컴포넌트
  - 두 가지 생성 모드 선택 UI
  - 각 모드 설명 및 예시
  - 선택 확인 및 다음 단계 진행

- Step 3: StoryboardGenerator 컴포넌트
  - 생성 진행률 표시
  - 생성 완료 후 미리보기
  - 재생성 옵션

**Deliverables**:

- `/frontend/components/studio/InputSelector.tsx`
- `/frontend/components/studio/StoryboardOptions.tsx`
- `/frontend/components/studio/StoryboardGenerator.tsx`

### Phase 6: Frontend - Storyboard Editor

**Priority**: High
**Dependencies**: Phase 5 완료

**Tasks**:

- StoryboardEditor 메인 컴포넌트
  - 장면 카드 리스트 뷰
  - Drag & Drop 순서 변경
  - 장면 추가/삭제 버튼

- SceneCard 컴포넌트
  - 장면 정보 표시 (title, description, narration 등)
  - 인라인 편집 모드
  - 이미지 미리보기 영역

- SceneEditModal 컴포넌트
  - 전체 필드 편집 폼
  - 필드별 유효성 검사
  - 변경 사항 미리보기

- 버전 히스토리 UI
  - 버전 목록 사이드바
  - 버전 비교 뷰
  - 복원 확인 모달

**Deliverables**:

- `/frontend/components/studio/StoryboardEditor.tsx`
- `/frontend/components/studio/SceneCard.tsx`
- `/frontend/components/studio/SceneEditModal.tsx`
- `/frontend/components/studio/VersionHistory.tsx`

### Phase 7: Frontend - Image Generation and Video

**Priority**: High
**Dependencies**: Phase 6 완료

**Tasks**:

- SceneImageGenerator 컴포넌트
  - 장면별 이미지 생성/업로드 UI
  - 이미지 버전 갤러리
  - 일괄 생성 버튼
  - 진행률 표시

- VideoGenerator 컴포넌트
  - 최종 미리보기 (장면 순서, 이미지, 시간)
  - 영상 생성 옵션 (provider 선택)
  - 생성 진행률 및 예상 시간
  - 완료 후 다운로드/공유

**Deliverables**:

- `/frontend/components/studio/SceneImageGenerator.tsx`
- `/frontend/components/studio/VideoGenerator.tsx`
- `/frontend/hooks/useVideoProject.ts`
- `/frontend/hooks/useStoryboard.ts`

### Phase 8: Integration and Testing

**Priority**: High
**Dependencies**: Phase 7 완료

**Tasks**:

- 전체 워크플로우 통합 테스트
  - 6단계 마법사 E2E 테스트
  - 상태 전이 테스트
  - 에러 복구 시나리오

- API 통합 테스트
  - 스토리보드 CRUD 테스트
  - 동시성 처리 테스트
  - 버전 관리 테스트

- 성능 테스트
  - 스토리보드 생성 30초 목표
  - 이미지 생성 30초/장면 목표
  - WebSocket 안정성 테스트

**Deliverables**:

- `/backend/tests/test_storyboard.py`
- `/backend/tests/test_video_studio_integration.py`
- `/frontend/tests/e2e/video-studio.spec.ts`

## Technical Approach

### Storyboard Generation Architecture

스토리보드 생성 프로세스:

1. 레퍼런스 분석 데이터 로드
2. 브랜드/제품 정보 조회
3. 생성 모드에 따른 장면 구조 결정
4. LLM 호출로 각 장면 콘텐츠 생성
5. 스토리보드 저장 및 버전 관리

### Version Control Strategy

버전 관리 전략:

1. 스토리보드 편집 시 새 버전 생성
2. 이전 버전은 previous_version_id로 연결
3. is_active 플래그로 현재 활성 버전 표시
4. 버전 복원 시 새 버전으로 복사

### State Machine Implementation

상태 전이 구현:

1. VideoProject.status로 현재 상태 관리
2. 각 상태별 허용 액션 정의
3. 실패 시 롤백 상태 정의
4. WebSocket으로 상태 변경 알림

## Risks and Mitigation

### Risk 1: LLM 생성 품질 불일치

**Risk**: LLM이 생성한 스토리보드 콘텐츠 품질이 일관되지 않을 수 있음
**Mitigation**:

- 상세한 프롬프트 템플릿 작성
- 출력 형식 검증 로직 추가
- 재생성 옵션 제공

### Risk 2: 버전 관리 복잡성

**Risk**: 스토리보드 버전과 이미지 버전 간 동기화 어려움
**Mitigation**:

- 이미지는 scene_number로 연결, 스토리보드 버전과 독립적
- 스토리보드 복원 시 이미지는 유지

### Risk 3: 대용량 JSON 처리

**Risk**: scenes 배열이 커질 경우 DB 성능 저하
**Mitigation**:

- 장면 수 제한 (최대 20개 권장)
- JSON 컬럼 인덱싱 고려
- 필요 시 별도 Scene 테이블로 분리

## Success Metrics

- 스토리보드 생성 성공률: 95% 이상
- 스토리보드 생성 시간: 30초 이내
- 사용자 편집 후 저장 성공률: 99% 이상
- 6단계 워크플로우 완료율: 80% 이상

---

**Document Status**: PLANNED
**Last Updated**: 2025-12-12
