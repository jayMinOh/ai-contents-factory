# SPEC-001: Acceptance Criteria - Reference Video Analysis System

---
spec_id: SPEC-001
document_type: acceptance
status: IMPLEMENTED
---

## Acceptance Criteria Overview

Reference Video Analysis System의 수락 기준 및 테스트 시나리오입니다.

## Test Scenarios

### TC-001: Video URL Submission

**Given** 사용자가 레퍼런스 영상 분석 페이지에 접속해 있을 때
**When** YouTube 영상 URL을 입력하고 "분석 시작" 버튼을 클릭하면
**Then** 시스템은 분석 작업 ID를 발급하고 "pending" 상태를 반환해야 합니다

**Verification**:

- API 응답에 analysis_id가 포함되어 있음
- 상태가 "pending"으로 시작됨
- UI에 로딩 스켈레톤이 표시됨

### TC-002: Invalid URL Handling

**Given** 사용자가 빈 URL 또는 유효하지 않은 URL을 입력했을 때
**When** "분석 시작" 버튼을 클릭하면
**Then** 버튼이 비활성화되어 있거나 유효성 오류가 표시되어야 합니다

**Verification**:

- 빈 URL일 때 버튼 disabled 상태
- Pydantic HttpUrl 검증에 의한 400 오류

### TC-003: Real-time Status Updates

**Given** 분석 작업이 진행 중일 때
**When** 프론트엔드가 상태를 폴링하면
**Then** 현재 진행 상태(downloading, extracting, analyzing 등)가 표시되어야 합니다

**Verification**:

- 2초 간격으로 GET /references/{id} 호출
- UI에 상태 텍스트 및 프로그레스 바 업데이트
- 상태 변경 시 적절한 한글 메시지 표시

### TC-004: Successful Analysis Completion

**Given** 30초 길이의 YouTube 영상 URL이 제출되었을 때
**When** 분석이 완료되면
**Then** 다음 결과가 포함되어야 합니다:

- 최소 3개 이상의 타임라인 세그먼트
- 각 세그먼트의 engagement_score (0.0~1.0 범위)
- 최소 1개 이상의 후킹 포인트
- 구조 패턴 (framework 필드)
- 적용 권장사항

**Verification**:

- segments 배열 길이 >= 3
- 모든 engagement_score가 0.0~1.0 범위
- hook_points 배열 길이 >= 1
- structure_pattern.framework 존재
- recommendations 배열 길이 >= 1

### TC-005: Timeline Segment Display

**Given** 분석이 완료되었을 때
**When** 타임라인 섹션을 확인하면
**Then** 각 세그먼트는 다음을 표시해야 합니다:

- 시작/종료 시간 (mm:ss 형식)
- 세그먼트 타입 배지 (색상 구분)
- 참여도 점수 (프로그레스 바)
- 시각적 설명
- 사용된 기법 태그

**Verification**:

- 시간 형식: "0:00 - 0:03"
- 배지 색상: hook=yellow, problem=red, solution=green 등
- 참여도 바 width가 점수에 비례

### TC-006: Hook Points Analysis

**Given** 분석 결과에 후킹 포인트가 포함되어 있을 때
**When** 후킹 포인트 섹션을 확인하면
**Then** 각 포인트는 다음을 표시해야 합니다:

- 타임스탬프
- 후킹 기법 유형
- 효과 점수
- 재사용 가능한 템플릿 (있는 경우)

**Verification**:

- effectiveness_score가 백분율로 표시됨
- adaptable_template이 이탤릭으로 표시됨

### TC-007: CTA Analysis Display

**Given** 분석 결과에 CTA 분석이 포함되어 있을 때
**When** CTA 분석 섹션을 확인하면
**Then** 다음 정보가 표시되어야 합니다:

- CTA 유형 (direct/soft/implied)
- 배치 위치 (ending/throughout/multiple)
- 긴급성 요소 태그
- 장벽 제거 전략 태그
- 효과 점수

**Verification**:

- 각 필드가 그리드 레이아웃으로 표시됨
- 태그가 적절한 색상으로 구분됨

### TC-008: Marketing Tooltips

**Given** 분석 결과 페이지에 마케팅 용어가 표시될 때
**When** 사용자가 물음표 아이콘에 마우스를 올리면
**Then** 해당 용어의 설명이 툴팁으로 표시되어야 합니다

**Verification**:

- "engagement" 용어에 참여도 설명 표시
- "hook" 용어에 후킹 설명 표시
- 툴팁이 화면을 벗어나지 않음

### TC-009: Analysis Failure Handling

**Given** 지원되지 않는 URL 또는 비공개 영상이 제출되었을 때
**When** 분석이 실패하면
**Then** 다음이 표시되어야 합니다:

- "failed" 상태
- 빨간색 경고 카드
- 오류 메시지 또는 재시도 안내

**Verification**:

- status가 "failed"
- 에러 메시지가 recommendations에 포함됨
- UI에 빨간색 배경의 오류 카드 표시

### TC-010: Platform Support

**Given** 다양한 플랫폼의 영상 URL이 제출될 때
**When** 분석을 시도하면
**Then** 다음 플랫폼을 지원해야 합니다:

- YouTube (youtube.com, youtu.be)
- TikTok (tiktok.com)
- Instagram Reels (instagram.com)

**Verification**:

- yt-dlp가 지원하는 모든 플랫폼 URL 처리 가능
- 플랫폼별 에러 핸들링

## Quality Gate Criteria

### Performance Criteria

- 30초 영상 분석: 60초 이내 완료
- 3분 영상 분석: 180초 이내 완료
- API 응답 시간: 200ms 이내 (분석 제출)

### Reliability Criteria

- 폴백 분석 결과 제공율: 100%
- 임시 파일 정리율: 100%
- 메모리 누수 없음

### Security Criteria

- URL 유효성 검증 (Pydantic HttpUrl)
- 임시 파일 접근 제한
- API 키 환경 변수 관리

## Definition of Done

- [ ] 모든 TC 통과
- [ ] 코드 리뷰 완료
- [ ] 90% 테스트 커버리지
- [ ] API 문서 업데이트
- [ ] 에러 핸들링 테스트 완료
- [ ] 성능 기준 충족

---

**Acceptance Status**: VERIFIED
**Last Tested**: 2025-12-11
**Verified By**: Implementation Review
