# SPEC-CONTENT-FACTORY-001: Acceptance Criteria

---
spec_id: SPEC-CONTENT-FACTORY-001
document_type: acceptance
version: 1.1.0
created_at: 2025-12-18
updated_at: 2025-12-19
---

## Overview

이 문서는 AI Content Factory 워크플로우의 수락 기준을 정의합니다. 각 Phase별 테스트 시나리오와 Given-When-Then 형식의 검증 기준을 포함합니다.

## Phase 1-2 Acceptance (VERIFIED)

### AC-1.1: Navigation Structure

**Status**: VERIFIED

Given: 사용자가 애플리케이션에 접속했을 때
When: 네비게이션 바를 확인하면
Then: 다음 메뉴가 순서대로 표시되어야 합니다
- 홈
- 콘텐츠 생성
- 레퍼런스
- 브랜드 관리

### AC-1.2: Dashboard Page

**Status**: VERIFIED

Given: 사용자가 홈(/)에 접속했을 때
When: 대시보드 페이지가 로드되면
Then: 다음 요소들이 표시되어야 합니다
- Hero 섹션 (AI Content Factory 제목, 새 콘텐츠 만들기 버튼)
- 통계 카드 3개 (이번 주 생성, 전체 콘텐츠, 저장된 레퍼런스)
- 빠른 생성 섹션 (단일 이미지, 캐러셀, 스토리 링크)
- 최근 작업 섹션

### AC-1.3: Create Wizard UI

**Status**: VERIFIED

Given: 사용자가 콘텐츠 생성(/create)에 접속했을 때
When: 마법사 페이지가 로드되면
Then: 6단계 진행 표시기가 표시되어야 합니다
- Step 1: 유형
- Step 2: 용도
- Step 3: 방식
- Step 4: 생성
- Step 5: 선택
- Step 6: 편집

### AC-1.4: References Page UI

**Status**: VERIFIED

Given: 사용자가 레퍼런스(/references)에 접속했을 때
When: 페이지가 로드되면
Then: 다음 요소들이 표시되어야 합니다
- 페이지 제목 (레퍼런스 라이브러리)
- 새 레퍼런스 버튼
- 검색 입력창
- 유형 필터 드롭다운
- 레퍼런스 그리드 (또는 빈 상태 메시지)

### AC-1.5: Toast Notifications

**Status**: VERIFIED

Given: sonner 패키지가 설치되어 있을 때
When: 알림이 필요한 액션이 발생하면
Then: 화면 상단 중앙에 Toast 알림이 표시되어야 합니다

## Phase 3 Acceptance Criteria - VERIFIED

### AC-3.1: SNS Link Analysis

**Status**: VERIFIED

Given: 사용자가 레퍼런스 추가 모달에서 Instagram 링크를 입력했을 때
When: 분석 버튼을 클릭하면
Then:
- 로딩 인디케이터가 표시되어야 합니다
- "링크 분석 중..." Toast가 표시되어야 합니다
- 분석 완료 시 레퍼런스가 목록에 추가되어야 합니다
- 분석 결과에 composition, colorScheme, style, elements가 포함되어야 합니다

**Error Case**:
Given: 유효하지 않은 링크가 입력되었을 때
When: 분석 버튼을 클릭하면
Then: 에러 Toast가 표시되어야 합니다 (예: "지원하지 않는 링크입니다")

### AC-3.2: Image Upload Analysis

**Status**: VERIFIED

Given: 사용자가 레퍼런스 추가 모달에서 이미지를 업로드했을 때
When: 파일이 선택되면
Then:
- 업로드 및 분석이 자동으로 시작되어야 합니다
- "이미지 분석 중..." Toast가 표시되어야 합니다
- 분석 완료 시 레퍼런스가 목록에 추가되어야 합니다
- 썸네일이 표시되어야 합니다

**File Size Limit**:
Given: 50MB를 초과하는 파일이 선택되었을 때
When: 업로드를 시도하면
Then: "파일 크기가 50MB를 초과합니다" Toast가 표시되어야 합니다

### AC-3.3: Reference List and Filter

**Status**: VERIFIED

Given: 여러 레퍼런스가 저장되어 있을 때
When: 유형 필터를 변경하면
Then: 선택된 유형의 레퍼런스만 표시되어야 합니다

Given: 레퍼런스 카드를 클릭했을 때
When: 상세 패널이 열리면
Then: 분석 결과 (구도, 색감, 스타일, 요소)가 표시되어야 합니다

### AC-3.4: Reference Deletion

**Status**: VERIFIED

Given: 레퍼런스 상세 패널이 열려 있을 때
When: 삭제 버튼을 클릭하면
Then:
- 레퍼런스가 목록에서 제거되어야 합니다
- "레퍼런스가 삭제되었습니다" Toast가 표시되어야 합니다

## Phase 4 Acceptance Criteria - VERIFIED

### AC-4.1: Content Type Selection (Step 1)

**Status**: VERIFIED

Given: 사용자가 콘텐츠 생성 Step 1에 있을 때
When: 콘텐츠 유형 (단일/캐러셀/스토리)을 선택하면
Then: 선택된 유형이 강조 표시되고 자동으로 Step 2로 이동해야 합니다

### AC-4.2: Purpose Selection with Brand (Step 2)

**Status**: VERIFIED

Given: 사용자가 Step 2에서 "광고/홍보"를 선택했을 때
When: 브랜드 선택 드롭다운이 표시되면
Then:
- 저장된 브랜드 목록이 표시되어야 합니다
- 브랜드 선택 시 해당 브랜드의 상품 목록이 표시되어야 합니다
- 브랜드 선택 후 "다음" 버튼이 활성화되어야 합니다

Given: "정보성" 또는 "일상/감성"을 선택했을 때
When: 유형이 선택되면
Then: 브랜드 선택 없이 자동으로 Step 3로 이동해야 합니다

### AC-4.3: Generation Method Selection (Step 3)

**Status**: VERIFIED

Given: 사용자가 Step 3에 있을 때
When: "레퍼런스 활용"을 선택하면
Then: 저장된 레퍼런스 목록이 표시되어야 합니다

Given: 사용자가 "직접 만들기"를 선택했을 때
When: 프롬프트 입력창이 표시되면
Then:
- 텍스트 입력이 가능해야 합니다
- 프롬프트 입력 후 "다음" 버튼이 활성화되어야 합니다

### AC-4.4: Image Generation (Step 4)

**Status**: VERIFIED

Given: 사용자가 Step 4에서 설정 요약을 확인했을 때
When: "이미지 생성하기" 버튼을 클릭하면
Then:
- 버튼이 비활성화되고 로딩 상태가 표시되어야 합니다
- "이미지 생성 중..." Toast가 표시되어야 합니다
- 생성 완료 시 자동으로 Step 5로 이동해야 합니다
- "이미지 생성 완료!" Toast가 표시되어야 합니다

**API Integration**:
Given: Gemini Imagen API가 정상 작동할 때
When: 이미지 생성을 요청하면
Then: 4개의 변형 이미지가 생성되어야 합니다

**Error Handling**:
Given: 이미지 생성 중 오류가 발생했을 때
When: API 오류가 반환되면
Then:
- 에러 Toast가 표시되어야 합니다
- "다시 시도" 옵션이 제공되어야 합니다

### AC-4.5: Image Selection (Step 5)

**Status**: VERIFIED

Given: 4개의 생성된 이미지가 표시되었을 때
When: 이미지를 클릭하면
Then:
- 선택된 이미지에 체크 표시가 나타나야 합니다
- "편집하기" 버튼이 활성화되어야 합니다

Given: 이미지가 선택된 상태에서
When: "다시 생성" 버튼을 클릭하면
Then: Step 4로 돌아가서 재생성이 가능해야 합니다

## Phase 5 Acceptance Criteria - VERIFIED

### AC-5.1: Canvas Editor Loading

**Status**: VERIFIED

Given: 사용자가 이미지를 선택하고 편집하기를 클릭했을 때
When: 편집 페이지(/create/edit)가 로드되면
Then:
- 선택된 이미지가 캔버스 배경으로 표시되어야 합니다
- 텍스트 도구 툴바가 표시되어야 합니다
- 2초 이내에 로딩이 완료되어야 합니다

### AC-5.2: Text Addition

**Status**: VERIFIED

Given: 캔버스 에디터가 로드된 상태에서
When: "텍스트 추가" 버튼을 클릭하면
Then:
- 캔버스 중앙에 기본 텍스트 박스가 추가되어야 합니다
- 텍스트 박스가 선택된 상태여야 합니다
- 텍스트 편집이 가능해야 합니다

### AC-5.3: Text Styling

**Status**: VERIFIED

Given: 텍스트 박스가 선택된 상태에서
When: 폰트, 크기, 색상을 변경하면
Then:
- 변경 사항이 즉시 캔버스에 반영되어야 합니다
- 반응 시간이 100ms 이내여야 합니다

**Font Options**:
Given: 폰트 선택 드롭다운을 클릭했을 때
Then: 다음 폰트가 포함되어야 합니다
- Noto Sans KR
- Pretendard
- 기본 웹폰트 (Arial, Helvetica 등)

### AC-5.4: Text Positioning

**Status**: VERIFIED

Given: 텍스트 박스가 선택된 상태에서
When: 드래그하면
Then: 텍스트 위치가 이동되어야 합니다

When: 핸들을 드래그하면
Then: 텍스트 크기가 조절되어야 합니다

When: 회전 핸들을 드래그하면
Then: 텍스트가 회전되어야 합니다

### AC-5.5: Canvas State Persistence

**Status**: VERIFIED

Given: 텍스트 편집 작업이 진행 중일 때
When: 일정 시간(예: 5초)이 경과하면
Then: 캔버스 상태가 자동으로 저장되어야 합니다

Given: 저장된 프로젝트가 있을 때
When: 해당 프로젝트를 다시 열면
Then: 이전 편집 상태가 복원되어야 합니다

### AC-5.6: Layer Management

**Status**: VERIFIED

Given: 여러 텍스트 요소가 캔버스에 있을 때
When: 레이어 순서를 변경하면
Then: 텍스트의 앞/뒤 순서가 변경되어야 합니다

When: 텍스트를 삭제하면
Then: 해당 텍스트가 캔버스에서 제거되어야 합니다

## Phase 6 Acceptance Criteria - VERIFIED

### AC-6.1: Export Dialog

**Status**: VERIFIED

Given: 캔버스 편집이 완료된 상태에서
When: "내보내기" 버튼을 클릭하면
Then: 내보내기 다이얼로그가 표시되어야 합니다

**Export Options**:
Given: 내보내기 다이얼로그가 열린 상태에서
Then: 다음 플랫폼 옵션이 표시되어야 합니다
- Instagram Feed (1:1, 4:5)
- Instagram Story
- Facebook Feed (1:1, 1.91:1)

### AC-6.2: Platform-Specific Export

**Status**: VERIFIED

Given: Instagram Feed 1:1을 선택했을 때
When: 내보내기를 실행하면
Then:
- 1080x1080 크기의 이미지가 생성되어야 합니다
- 3초 이내에 완료되어야 합니다
- 다운로드가 자동으로 시작되어야 합니다

Given: Instagram Story를 선택했을 때
When: 내보내기를 실행하면
Then: 1080x1920 크기의 이미지가 생성되어야 합니다

### AC-6.3: Multi-Platform Export

**Status**: VERIFIED

Given: 여러 플랫폼이 선택된 상태에서
When: 내보내기를 실행하면
Then:
- 각 플랫폼별 이미지가 생성되어야 합니다
- 모든 이미지가 ZIP 파일로 다운로드되어야 합니다

### AC-6.4: Format Selection

**Status**: VERIFIED

Given: 출력 형식을 JPEG로 선택했을 때
When: 내보내기를 실행하면
Then: .jpg 확장자 파일이 생성되어야 합니다

Given: 출력 형식을 PNG로 선택했을 때
When: 내보내기를 실행하면
Then: .png 확장자 파일이 생성되어야 합니다 (투명 배경 지원)

### AC-6.5: Carousel Export

**Status**: VERIFIED

Given: 캐러셀 유형의 콘텐츠인 경우
When: 내보내기를 실행하면
Then:
- 모든 슬라이드가 동일한 규격으로 내보내져야 합니다
- 10초 이내에 완료되어야 합니다
- 전체 다운로드 시 ZIP 파일로 제공되어야 합니다

## Quality Gate Criteria

### Performance Requirements

- 이미지 생성 완료: 30초 이내
- 캔버스 에디터 로딩: 2초 이내
- 텍스트 편집 반응: 100ms 이내
- 단일 이미지 내보내기: 3초 이내
- 캐러셀 내보내기: 10초 이내

### Reliability Requirements

- API 호출 실패 시 최대 3회 자동 재시도
- 에러 발생 시 사용자 친화적 메시지 표시
- 작업 중단 시 데이터 손실 없이 복구 가능

### Usability Requirements

- 모든 상태 변화에 Toast 알림 제공
- 진행 중인 작업에 로딩 인디케이터 표시
- 각 단계에서 이전 단계로 돌아가기 가능

## Definition of Done - ALL VERIFIED

### Phase 3 Complete When: VERIFIED

- SNS 링크 입력 시 실제 분석 결과 반환
- 이미지 업로드 시 AI 분석 결과 반환
- 레퍼런스가 데이터베이스에 영구 저장됨
- 모든 AC-3.x 테스트 통과

### Phase 4 Complete When: VERIFIED

- Gemini Imagen API 연동 완료
- 4개 변형 이미지 실제 생성
- 프론트엔드에서 생성된 이미지 표시
- 모든 AC-4.x 테스트 통과

### Phase 5 Complete When: VERIFIED

- Fabric.js 캔버스 에디터 완전 동작
- 텍스트 추가/편집/삭제/스타일링 가능
- 캔버스 상태 저장 및 복원 가능
- 모든 AC-5.x 테스트 통과

### Phase 6 Complete When: VERIFIED

- 모든 플랫폼별 내보내기 기능 동작
- 다중 형식(JPEG, PNG, WebP) 지원
- 캐러셀 배치 다운로드 동작
- 모든 AC-6.x 테스트 통과

## Test Scenarios Summary

### End-to-End Flow Test

Scenario: 전체 워크플로우 완료
1. 홈에서 "새 콘텐츠 만들기" 클릭
2. Step 1: "단일 이미지" 선택
3. Step 2: "광고/홍보" 선택, 브랜드/상품 선택
4. Step 3: "직접 만들기" 선택, 프롬프트 입력
5. Step 4: "이미지 생성하기" 클릭, 완료 대기
6. Step 5: 생성된 이미지 중 하나 선택
7. Step 6: 텍스트 추가 및 편집
8. 내보내기: Instagram Feed 1:1 선택, 다운로드 확인

Expected Result: 1080x1080 JPEG 이미지 다운로드 완료

### Reference-Based Flow Test

Scenario: 레퍼런스 기반 콘텐츠 생성
1. 레퍼런스 페이지에서 Instagram 링크로 레퍼런스 추가
2. 콘텐츠 생성에서 "레퍼런스 활용" 선택
3. 추가된 레퍼런스 선택
4. 이미지 생성 및 편집
5. 내보내기

Expected Result: 레퍼런스 스타일이 반영된 이미지 생성

---

**Document Version**: 1.1.0
**Last Updated**: 2025-12-19
**Test Coverage**: 330 tests passing
**Status**: ALL CRITERIA VERIFIED
