# SPEC-002: Acceptance Criteria - Brand and Product Management System

---
spec_id: SPEC-002
document_type: acceptance
status: IMPLEMENTED
---

## Acceptance Criteria Overview

Brand and Product Management System의 수락 기준 및 테스트 시나리오입니다.

## Test Scenarios

### TC-001: Brand Creation

**Given** 사용자가 브랜드 관리 페이지에 접속해 있을 때
**When** "브랜드 추가" 버튼을 클릭하고 브랜드 정보를 입력한 후 "추가" 버튼을 클릭하면
**Then** 새 브랜드가 생성되고 목록에 표시되어야 합니다

**Verification**:

- POST /api/v1/brands/ 성공 (201)
- 브랜드 목록에 새 브랜드 표시
- 생성된 브랜드가 자동 선택됨

### TC-002: Brand Listing with Product Count

**Given** 여러 브랜드와 제품이 등록되어 있을 때
**When** 브랜드 목록을 조회하면
**Then** 각 브랜드의 제품 개수가 정확하게 표시되어야 합니다

**Verification**:

- GET /api/v1/brands/ 응답에 product_count 포함
- 제품이 없는 브랜드는 "제품 0개" 표시
- 생성일 역순 정렬

### TC-003: Brand Detail View

**Given** 브랜드 목록에서 브랜드를 선택했을 때
**When** 브랜드 상세 정보를 확인하면
**Then** 다음 정보가 표시되어야 합니다:

- 브랜드명
- 업종 (있는 경우)
- 설명 (있는 경우)
- 타겟 고객층
- 톤앤매너
- USP (핵심 차별점)
- 키워드 태그
- 제품 목록

**Verification**:

- GET /api/v1/brands/{id} 성공
- 모든 필드가 UI에 적절하게 표시됨
- 제품 목록이 별도 카드로 표시됨

### TC-004: Brand Update

**Given** 브랜드 상세 화면에서 편집 버튼을 클릭했을 때
**When** 일부 필드를 수정하고 "수정" 버튼을 클릭하면
**Then** 수정된 정보만 업데이트되어야 합니다

**Verification**:

- PUT /api/v1/brands/{id} 성공
- 수정하지 않은 필드는 유지
- UI가 즉시 갱신됨

### TC-005: Brand Deletion with Cascade

**Given** 제품이 포함된 브랜드가 있을 때
**When** 브랜드 삭제 버튼을 클릭하고 확인하면
**Then** 브랜드와 모든 제품이 삭제되어야 합니다

**Verification**:

- DELETE /api/v1/brands/{id} 성공
- 삭제 전 확인 대화상자 표시
- 브랜드 목록에서 제거
- 관련 제품도 함께 삭제됨 (CASCADE)

### TC-006: Product Creation

**Given** 브랜드가 선택된 상태에서
**When** "제품 추가" 버튼을 클릭하고 제품 정보를 입력한 후 "추가" 버튼을 클릭하면
**Then** 해당 브랜드에 새 제품이 추가되어야 합니다

**Verification**:

- POST /api/v1/brands/{brand_id}/products 성공
- 제품 목록에 새 제품 표시
- 브랜드의 product_count 증가

### TC-007: Product Features and Benefits Tags

**Given** 제품 추가/수정 모달에서
**When** 기능/혜택 입력 필드에 텍스트를 입력하고 Enter 키를 누르면
**Then** 태그가 추가되어야 합니다

**Verification**:

- 태그가 칩 형태로 표시됨
- X 버튼으로 태그 제거 가능
- 중복 태그 방지
- 저장 시 배열로 전송됨

### TC-008: Product Update

**Given** 제품 목록에서 편집 버튼을 클릭했을 때
**When** 제품 정보를 수정하고 "수정" 버튼을 클릭하면
**Then** 제품 정보가 업데이트되어야 합니다

**Verification**:

- PUT /api/v1/brands/{brand_id}/products/{product_id} 성공
- 브랜드 소유권 검증됨
- UI가 즉시 갱신됨

### TC-009: Product Deletion

**Given** 제품이 표시된 상태에서
**When** 제품의 삭제 버튼을 클릭하고 확인하면
**Then** 제품이 삭제되어야 합니다

**Verification**:

- DELETE /api/v1/brands/{brand_id}/products/{product_id} 성공
- 삭제 전 확인 대화상자 표시
- 제품 목록에서 제거
- 브랜드의 product_count 감소

### TC-010: Brand Form Validation

**Given** 브랜드 추가 모달이 열린 상태에서
**When** 브랜드명을 입력하지 않고 "추가" 버튼을 클릭하면
**Then** 폼 제출이 방지되어야 합니다

**Verification**:

- HTML5 required 속성으로 검증
- 브라우저 기본 유효성 메시지 표시
- API 호출되지 않음

### TC-011: Tone and Manner Selection

**Given** 브랜드 추가/수정 모달에서
**When** 톤앤매너 드롭다운을 클릭하면
**Then** 다음 옵션이 표시되어야 합니다:

- 전문적
- 친근한
- 캐주얼
- 고급스러운
- 유머러스
- 감성적
- 신뢰감있는

**Verification**:

- select 요소로 구현
- 선택된 값이 저장됨
- 미선택 시 빈 문자열

### TC-012: Empty State Handling

**Given** 등록된 브랜드가 없을 때
**When** 브랜드 목록을 조회하면
**Then** "등록된 브랜드가 없습니다" 메시지와 "첫 브랜드 추가하기" 링크가 표시되어야 합니다

**Verification**:

- 빈 상태 UI 표시
- 링크 클릭 시 추가 모달 열림

### TC-013: Brand Selection State

**Given** 브랜드가 선택되지 않은 상태에서
**When** 상세 영역을 확인하면
**Then** "브랜드를 선택하세요" 안내 메시지가 표시되어야 합니다

**Verification**:

- 초기 상태에서 안내 메시지 표시
- 브랜드 선택 시 상세 정보로 교체

### TC-014: Non-existent Brand Access

**Given** 존재하지 않는 brand_id로
**When** API를 호출하면
**Then** 404 에러가 반환되어야 합니다

**Verification**:

- GET /api/v1/brands/{invalid_id} -> 404
- PUT /api/v1/brands/{invalid_id} -> 404
- DELETE /api/v1/brands/{invalid_id} -> 404
- POST /api/v1/brands/{invalid_id}/products -> 404

## Quality Gate Criteria

### Performance Criteria

- 브랜드 목록 조회: 100ms 이내
- 브랜드 생성: 200ms 이내
- 제품 CRUD: 200ms 이내

### Data Integrity Criteria

- CASCADE 삭제 정상 동작
- 브랜드 소유권 검증 100%
- JSON 배열 데이터 정합성

### Usability Criteria

- 모든 CRUD 작업이 페이지 새로고침 없이 수행
- 삭제 작업에 확인 대화상자 필수
- 로딩 상태 표시

## Definition of Done

- [ ] 모든 TC 통과
- [ ] 코드 리뷰 완료
- [ ] 90% 테스트 커버리지
- [ ] API 문서 업데이트
- [ ] CASCADE 삭제 테스트 완료
- [ ] 소유권 검증 테스트 완료

---

**Acceptance Status**: VERIFIED
**Last Tested**: 2025-12-11
**Verified By**: Implementation Review
