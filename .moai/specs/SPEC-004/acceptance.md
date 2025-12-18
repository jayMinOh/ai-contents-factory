# SPEC-004: Acceptance Criteria - AI Video Generation System

---
spec_id: SPEC-004
document_type: acceptance
status: PLANNED
---

## Acceptance Criteria Overview

AI Video Generation System의 수락 기준 및 테스트 시나리오입니다.

## Test Scenarios

### TC-001: Script Generation Request

**Given** 브랜드와 레퍼런스 분석 결과가 존재할 때
**When** 영상 생성 API를 호출하면
**Then** generation_id가 발급되고 스크립트 생성이 시작되어야 합니다

**Verification**:

- POST /api/v1/videos/generate 성공
- generation_id 반환
- status가 "pending" 또는 "script_generating"으로 시작

### TC-002: Script Generation with Reference Style

**Given** 레퍼런스 분석 결과가 PAS 구조를 가질 때
**When** 스크립트 생성이 완료되면
**Then** 생성된 스크립트도 유사한 구조를 가져야 합니다

**Verification**:

- script.scenes에 problem, agitation, solution 세그먼트 포함
- 레퍼런스의 페이싱(구간별 시간 비율)과 유사

### TC-003: Script with Brand Context

**Given** 브랜드에 USP와 타겟 고객이 정의되어 있을 때
**When** 스크립트가 생성되면
**Then** 스크립트에 브랜드 정보가 반영되어야 합니다

**Verification**:

- narration에 USP 관련 내용 포함
- tone이 브랜드 tone_and_manner와 일치
- 타겟 고객에 맞는 언어 사용

### TC-004: Script with Product Information

**Given** product_id가 제공되었을 때
**When** 스크립트가 생성되면
**Then** 제품 특징과 혜택이 스크립트에 포함되어야 합니다

**Verification**:

- features가 feature 세그먼트에 반영
- benefits가 benefit 세그먼트에 반영
- 제품명이 스크립트에 포함

### TC-005: Storyboard Generation

**Given** 스크립트 생성이 완료되었을 때
**When** 스토리보드 생성 단계가 진행되면
**Then** 각 장면에 대한 스토리보드가 생성되어야 합니다

**Verification**:

- storyboard 배열 길이 = script.scenes 길이
- 각 장면에 frame_description, camera_angle, transition 포함
- reference_prompt가 AI 이미지 생성에 사용 가능한 형식

### TC-006: Generation Status Tracking

**Given** 영상 생성이 진행 중일 때
**When** 상태 조회 API를 호출하면
**Then** 현재 상태와 진행률이 반환되어야 합니다

**Verification**:

- GET /api/v1/videos/{generation_id} 성공
- status가 현재 단계를 정확히 반영
- progress가 0-100 범위 내

### TC-007: Script Editing

**Given** 스크립트가 생성되어 script_ready 상태일 때
**When** 스크립트 수정 API를 호출하면
**Then** 수정된 스크립트가 저장되어야 합니다

**Verification**:

- PUT /api/v1/videos/{generation_id}/script 성공
- 수정된 내용이 DB에 저장됨
- 후속 단계에서 수정된 스크립트 사용

### TC-008: Video Rendering Initiation

**Given** 스토리보드가 완성되어 storyboard_ready 상태일 때
**When** 렌더링 시작 API를 호출하면
**Then** 영상 생성 API가 호출되고 렌더링이 시작되어야 합니다

**Verification**:

- POST /api/v1/videos/{generation_id}/render 성공
- status가 video_rendering으로 변경
- 선택된 프로바이더 API 호출 확인

### TC-009: Video Completion and Storage

**Given** 영상 렌더링이 완료되었을 때
**When** 후처리 단계가 완료되면
**Then** 영상이 MinIO에 저장되고 URL이 제공되어야 합니다

**Verification**:

- status가 completed로 변경
- video_url이 유효한 URL
- MinIO에서 영상 다운로드 가능
- thumbnail_url 제공

### TC-010: Video Metadata

**Given** 영상 생성이 완료되었을 때
**When** 결과를 조회하면
**Then** 영상 메타데이터가 포함되어야 합니다

**Verification**:

- duration이 target_duration과 근사
- resolution 정보 포함 (예: "1920x1080")
- file_size 정보 포함 (바이트)
- completed_at 타임스탬프 존재

### TC-011: Generation History

**Given** 여러 영상 생성 작업이 존재할 때
**When** 히스토리 API를 조회하면
**Then** 생성 작업 목록이 반환되어야 합니다

**Verification**:

- GET /api/v1/videos/ 성공
- 생성일 역순 정렬
- 페이지네이션 동작 (skip, limit)
- brand_id 필터 동작

### TC-012: Generation Failure Handling

**Given** 영상 생성 API 호출이 실패했을 때
**When** 시스템이 에러를 감지하면
**Then** 적절한 에러 처리가 되어야 합니다

**Verification**:

- status가 failed로 변경
- error_message에 실패 원인 기록
- 부분 결과(스크립트, 스토리보드) 유지
- 재시도 옵션 제공

### TC-013: Asset Deletion

**Given** 영상 생성 작업이 존재할 때
**When** 삭제 API를 호출하면
**Then** DB 레코드와 MinIO 에셋이 모두 삭제되어야 합니다

**Verification**:

- DELETE /api/v1/videos/{generation_id} 성공
- DB에서 레코드 삭제됨
- MinIO에서 영상 파일 삭제됨
- 썸네일도 삭제됨

### TC-014: Cost Estimation

**Given** 영상 생성 옵션이 설정되었을 때
**When** 비용 예측을 요청하면
**Then** 예상 비용이 반환되어야 합니다

**Verification**:

- 프로바이더별 예상 비용 계산
- 영상 길이에 비례한 비용
- 사용자에게 확인 요청

### TC-015: Multiple Provider Support

**Given** 여러 영상 생성 프로바이더가 설정되어 있을 때
**When** generation_provider를 지정하면
**Then** 해당 프로바이더가 사용되어야 합니다

**Verification**:

- generation_provider="luma" -> Luma API 호출
- generation_provider="runway" -> Runway API 호출
- 프로바이더별 설정 적용

### TC-016: Style Preferences Application

**Given** style_preferences가 설정되었을 때
**When** 스크립트가 생성되면
**Then** 스타일 설정이 반영되어야 합니다

**Verification**:

- tone="humorous" -> 유머러스한 스크립트
- pacing="fast" -> 짧은 장면 전환
- visual_style="animated" -> 애니메이션 관련 지시

## Quality Gate Criteria

### Performance Criteria

- 스크립트 생성: 30초 이내
- 스토리보드 생성: 60초 이내
- 전체 파이프라인 (렌더링 제외): 2분 이내
- API 응답 (상태 조회): 200ms 이내

### Reliability Criteria

- 스크립트 생성 성공률: 95% 이상
- 실패 시 재시도 성공률: 80% 이상
- 에셋 저장 성공률: 99% 이상

### Quality Criteria

- 생성된 스크립트가 브랜드 톤 반영
- 레퍼런스 구조와의 유사도
- 문법적으로 올바른 나레이션

## Definition of Done

- [ ] 모든 TC 통과
- [ ] 영상 생성 API mock 테스트 완료
- [ ] MinIO 통합 테스트 완료
- [ ] 프론트엔드 E2E 테스트 완료
- [ ] 성능 벤치마크 통과
- [ ] API 문서 업데이트
- [ ] 비용 계산 로직 검증
- [ ] 에러 핸들링 테스트 완료

---

**Acceptance Status**: PENDING
**Prerequisites**: SPEC-001, SPEC-002 구현 완료
