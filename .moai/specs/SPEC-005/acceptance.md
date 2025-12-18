# SPEC-005: Acceptance Criteria

---
spec_id: SPEC-005
title: Video Studio - Acceptance Criteria
version: 2.0.0
created_at: 2025-12-12
updated_at: 2025-12-12
tags: [video-studio, storyboard, acceptance-criteria, testing]
---

## Overview

이 문서는 SPEC-005 Video Studio 시스템의 스토리보드 중심 워크플로우에 대한 상세 수락 기준을 정의합니다.

## Test Scenarios

### TS-001: Storyboard Generation - Reference Structure Mode

**Scenario**: 레퍼런스 구조 유지 모드로 스토리보드 생성

**Given**:

- 완료된 레퍼런스 분석 결과가 존재합니다
- 레퍼런스 분석에 5개의 segments가 포함되어 있습니다
- 브랜드와 상품이 선택되어 있습니다
- VideoProject가 draft 상태입니다

**When**:

- 사용자가 "reference_structure" 모드로 스토리보드 생성을 요청합니다

**Then**:

- 스토리보드가 정확히 5개의 장면으로 생성됩니다
- 각 장면의 scene_type이 레퍼런스 segments의 유형과 일치합니다
- 각 장면에 title, description, narration_script, visual_direction이 포함됩니다
- 장면 콘텐츠에 브랜드/상품 정보가 반영됩니다
- VideoProject 상태가 storyboard_ready로 변경됩니다
- 생성 시간이 30초 이내입니다

### TS-002: Storyboard Generation - AI Optimized Mode

**Scenario**: AI 최적화 모드로 스토리보드 생성

**Given**:

- 완료된 레퍼런스 분석 결과가 존재합니다
- 브랜드와 상품이 선택되어 있습니다
- 상품에 3개의 주요 selling_points가 있습니다

**When**:

- 사용자가 "ai_optimized" 모드로 스토리보드 생성을 요청합니다

**Then**:

- AI가 브랜드/상품에 최적화된 장면 구조를 생성합니다
- 장면 수가 레퍼런스와 다를 수 있습니다 (4-8개 범위)
- 각 selling_point가 최소 하나의 장면에 반영됩니다
- hook, solution, benefit, cta 유형이 포함됩니다
- total_duration_seconds가 계산되어 저장됩니다

### TS-003: Scene Full Structure Validation

**Scenario**: 장면의 전체 필드 구조 검증

**Given**:

- 스토리보드가 생성되었습니다

**When**:

- 스토리보드의 첫 번째 장면을 조회합니다

**Then**:

- scene_number가 1입니다 (1-based)
- scene_type이 유효한 값입니다 (hook, problem, solution, benefit, cta, transition 중 하나)
- title이 비어있지 않은 문자열입니다
- description이 이미지 생성에 적합한 상세 설명입니다
- narration_script가 TTS에 적합한 문장입니다
- visual_direction이 촬영 가이드를 포함합니다
- background_music_suggestion이 분위기/장르를 포함합니다
- transition_effect가 유효한 값입니다 (fade, cut, zoom 등)
- subtitle_text가 화면 표시용 텍스트입니다
- duration_seconds가 양수입니다
- generated_image_id가 null입니다 (초기 상태)

### TS-004: Storyboard Scene Editing

**Scenario**: 스토리보드 장면 수정

**Given**:

- 3개 장면이 있는 스토리보드가 존재합니다
- 현재 버전이 1입니다

**When**:

- 사용자가 장면 2의 description을 수정합니다
- 수정 내용: "New dramatic product close-up with golden lighting"

**Then**:

- 장면 2의 description이 업데이트됩니다
- 스토리보드 버전이 2로 증가합니다
- 이전 버전 (version 1)이 히스토리에 저장됩니다
- updated_at이 현재 시간으로 갱신됩니다

### TS-005: Scene Addition

**Scenario**: 새로운 장면 추가

**Given**:

- 4개 장면이 있는 스토리보드가 존재합니다
- 장면 번호: 1, 2, 3, 4

**When**:

- 사용자가 장면 2 뒤에 새 장면을 추가합니다
- after_scene_number=2

**Then**:

- 새 장면이 scene_number=3으로 삽입됩니다
- 기존 장면 3, 4가 각각 4, 5로 재번호 부여됩니다
- 총 장면 수가 5개가 됩니다
- total_duration_seconds가 재계산됩니다

### TS-006: Scene Deletion

**Scenario**: 장면 삭제

**Given**:

- 5개 장면이 있는 스토리보드가 존재합니다
- 장면 3에 생성된 이미지가 있습니다

**When**:

- 사용자가 장면 3을 삭제합니다

**Then**:

- 장면 3이 스토리보드에서 제거됩니다
- 장면 4, 5가 각각 3, 4로 재번호 부여됩니다
- 총 장면 수가 4개가 됩니다
- 삭제된 장면의 이미지는 orphan 상태가 됩니다 (자동 삭제 또는 유지)
- total_duration_seconds가 재계산됩니다

### TS-007: Scene Reordering

**Scenario**: 장면 순서 변경

**Given**:

- 5개 장면이 있는 스토리보드가 존재합니다
- 현재 순서: 1, 2, 3, 4, 5

**When**:

- 사용자가 새로운 순서를 지정합니다: [3, 1, 2, 5, 4]

**Then**:

- 장면이 새로운 순서로 재배열됩니다
- scene_number가 1, 2, 3, 4, 5로 재할당됩니다
- 기존 장면 3의 내용이 이제 scene_number=1입니다
- 연결된 이미지의 scene_number도 업데이트됩니다

### TS-008: Storyboard Version Restore

**Scenario**: 이전 버전 복원

**Given**:

- 스토리보드 버전 1, 2, 3이 존재합니다
- 현재 활성 버전은 3입니다
- 버전 1에는 4개 장면, 버전 3에는 6개 장면이 있습니다

**When**:

- 사용자가 버전 1로 복원을 요청합니다

**Then**:

- 새로운 버전 4가 생성됩니다 (버전 1의 복사본)
- 버전 4가 is_active=true가 됩니다
- 버전 4에 4개 장면이 있습니다
- previous_version_id가 버전 3을 가리킵니다
- 기존 버전들은 그대로 유지됩니다

### TS-009: Scene Image Generation from Storyboard

**Scenario**: 스토리보드 기반 이미지 생성

**Given**:

- 스토리보드 장면 2가 존재합니다
- 장면 2 정보:
  - description: "Hero shot of vitamin serum bottle with morning light"
  - visual_direction: "45-degree angle, soft shadows, white background, product in focus"
- 브랜드 가이드라인에 "clean, minimal, pastel colors" 포함

**When**:

- 사용자가 장면 2의 이미지 생성을 요청합니다

**Then**:

- 프롬프트가 description + visual_direction + 브랜드 가이드라인을 조합합니다
- SceneImage가 생성되어 저장됩니다
- SceneImage.generation_prompt에 조합된 프롬프트가 저장됩니다
- SceneImage.scene_number가 2입니다
- 스토리보드 장면 2의 generated_image_id가 업데이트됩니다
- 생성 시간이 30초 이내입니다

### TS-010: Image Regeneration After Edit

**Scenario**: 장면 수정 후 이미지 재생성

**Given**:

- 장면 1에 이미 생성된 이미지가 있습니다 (version 1)
- 사용자가 장면 1의 description을 수정했습니다

**When**:

- 사용자가 장면 1의 이미지 재생성을 요청합니다

**Then**:

- 새로운 SceneImage가 생성됩니다 (version 2)
- 새 이미지가 is_active=true가 됩니다
- 기존 이미지는 is_active=false가 됩니다
- 새 프롬프트가 수정된 description을 반영합니다
- 스토리보드 장면의 generated_image_id가 새 이미지 ID로 업데이트됩니다

### TS-011: Batch Image Generation

**Scenario**: 전체 이미지 일괄 생성

**Given**:

- 6개 장면이 있는 스토리보드가 존재합니다
- 장면 1, 3에는 이미지가 있고, 장면 2, 4, 5, 6에는 이미지가 없습니다

**When**:

- 사용자가 전체 이미지 일괄 생성을 요청합니다

**Then**:

- 장면 2, 4, 5, 6에 대해서만 이미지가 생성됩니다
- 장면 1, 3의 기존 이미지는 유지됩니다
- 4개 이미지가 병렬로 생성됩니다
- WebSocket으로 각 장면별 진행률이 전달됩니다
- 전체 완료 시간이 60초 이내입니다 (병렬 처리 시)

### TS-012: Video Generation Readiness Check

**Scenario**: 영상 생성 준비 상태 확인

**Given**:

- 5개 장면이 있는 스토리보드가 존재합니다

**When (Case A - Not Ready)**:

- 장면 3에 이미지가 없습니다

**Then**:

- 영상 생성 API가 400 에러를 반환합니다
- 에러 메시지에 "Scene 3 missing image" 포함

**When (Case B - Ready)**:

- 모든 장면에 활성 이미지가 있습니다

**Then**:

- 영상 생성이 시작됩니다
- VideoProject 상태가 video_generating으로 변경됩니다

### TS-013: Video Generation with Storyboard Data

**Scenario**: 스토리보드 데이터 기반 영상 생성

**Given**:

- 모든 장면에 이미지가 준비된 스토리보드가 존재합니다
- 각 장면에 duration_seconds, transition_effect, narration_script가 설정되어 있습니다

**When**:

- 사용자가 영상 생성을 요청합니다

**Then**:

- 영상 생성 API에 다음 데이터가 전달됩니다:
  - 장면별 이미지 URL
  - 장면별 duration_seconds
  - 장면별 transition_effect
  - 장면별 narration_script (TTS 변환용)
- 생성된 영상 총 길이가 total_duration_seconds와 유사합니다
- 완료 시 VideoProject 상태가 completed로 변경됩니다

### TS-014: Wizard UI 6-Step Flow

**Scenario**: 6단계 마법사 UI 전체 흐름

**Given**:

- 사용자가 Video Studio에 접근합니다

**When**:

- 사용자가 전체 워크플로우를 진행합니다

**Then**:

Step 1 - 입력 선택:
- 레퍼런스 분석 목록이 표시됩니다
- 브랜드/상품 선택 드롭다운이 제공됩니다
- 모든 선택 완료 시 다음 버튼 활성화

Step 2 - 스토리보드 옵션:
- 두 가지 생성 모드가 카드 형태로 표시됩니다
- 각 모드의 설명과 예시가 제공됩니다
- 하나를 선택하면 다음 버튼 활성화

Step 3 - 스토리보드 생성:
- 생성 진행률이 표시됩니다
- 완료 시 장면 미리보기가 표시됩니다
- 재생성 버튼과 다음 버튼 제공

Step 4 - 스토리보드 편집:
- 장면 카드 리스트가 표시됩니다
- 각 카드에서 인라인 편집 가능
- Drag & drop으로 순서 변경 가능
- 장면 추가/삭제 버튼 제공

Step 5 - 이미지 생성:
- 각 장면별 이미지 상태가 표시됩니다
- 개별 생성/업로드 버튼 제공
- 일괄 생성 버튼 제공
- 이미지 버전 갤러리 제공

Step 6 - 영상 생성:
- 최종 미리보기가 표시됩니다
- Provider 선택 옵션 제공
- 예상 비용 안내
- 생성 진행률과 예상 시간 표시
- 완료 시 다운로드/공유 버튼 제공

### TS-015: Real-time Progress via WebSocket

**Scenario**: WebSocket을 통한 실시간 진행률

**Given**:

- 사용자가 프로젝트 페이지에 접속해 있습니다
- WebSocket 연결이 수립되어 있습니다

**When**:

- 스토리보드 생성이 진행됩니다

**Then**:

- 다음 이벤트가 WebSocket으로 전달됩니다:
  - storyboard_generation_started
  - storyboard_scene_generated (각 장면마다)
  - storyboard_generation_completed
- 각 이벤트에 progress_percentage가 포함됩니다
- 클라이언트 UI가 실시간으로 업데이트됩니다

## Quality Gate Criteria

### Code Quality

- Unit Test Coverage: 90% 이상
- Integration Test Coverage: 모든 API 엔드포인트
- E2E Test: 전체 6단계 워크플로우

### Performance

- 스토리보드 생성: 30초 이내
- 이미지 생성: 30초 이내/장면
- API 응답 시간: 500ms 이내 (생성 제외)

### Reliability

- 생성 실패 시 자동 재시도: 최대 3회
- 상태 일관성: 실패 시 이전 상태로 롤백
- 데이터 정합성: 스토리보드-이미지-프로젝트 간 참조 무결성

## Definition of Done

- 모든 테스트 시나리오 통과
- 코드 리뷰 완료
- API 문서 업데이트
- 6단계 마법사 UI 완전 동작
- WebSocket 실시간 업데이트 동작
- 버전 히스토리 기능 동작
- 성능 목표 달성

---

**Document Status**: PLANNED
**Last Updated**: 2025-12-12
