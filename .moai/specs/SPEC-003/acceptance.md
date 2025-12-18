# SPEC-003: Acceptance Criteria - Brand Knowledge Base RAG System

---
spec_id: SPEC-003
document_type: acceptance
status: PLANNED
---

## Acceptance Criteria Overview

Brand Knowledge Base RAG System의 수락 기준 및 테스트 시나리오입니다.

## Test Scenarios

### TC-001: Brand Embedding Generation

**Given** 브랜드가 데이터베이스에 존재할 때
**When** 임베딩 생성 API를 호출하면
**Then** 해당 브랜드의 벡터가 Qdrant에 저장되어야 합니다

**Verification**:

- POST /api/v1/knowledge/embed/brand/{brand_id} 성공
- Qdrant 컬렉션에 해당 point 존재
- payload에 entity_type="brand", entity_id 포함

### TC-002: Product Embedding Generation

**Given** 제품이 데이터베이스에 존재할 때
**When** 임베딩 생성 API를 호출하면
**Then** 해당 제품의 벡터가 브랜드 컨텍스트와 함께 Qdrant에 저장되어야 합니다

**Verification**:

- POST /api/v1/knowledge/embed/product/{product_id} 성공
- payload에 brand_id 포함
- content에 브랜드명 포함

### TC-003: Semantic Search - Brand

**Given** 여러 브랜드의 임베딩이 저장되어 있을 때
**When** "뷰티 브랜드 20대 여성 타겟"으로 검색하면
**Then** 관련 브랜드가 유사도 순으로 반환되어야 합니다

**Verification**:

- POST /api/v1/knowledge/search 성공
- entity_type="brand" 필터 적용
- score 내림차순 정렬
- 결과에 관련 메타데이터 포함

### TC-004: Semantic Search - Product

**Given** 여러 제품의 임베딩이 저장되어 있을 때
**When** "안티에이징 스킨케어"로 검색하면
**Then** 관련 제품이 유사도 순으로 반환되어야 합니다

**Verification**:

- entity_type="product" 필터 적용
- 제품명, 브랜드 정보 포함
- features/benefits 기반 매칭

### TC-005: Context Retrieval for Video Generation

**Given** 브랜드와 제품 임베딩이 저장되어 있을 때
**When** 브랜드 컨텍스트 조회 API를 호출하면
**Then** 영상 생성에 필요한 종합 컨텍스트가 반환되어야 합니다

**Verification**:

- GET /api/v1/knowledge/context/{brand_id} 성공
- brand 객체에 전체 정보 포함
- products 배열에 관련 제품 포함
- include_products=true 시 제품 목록 반환

### TC-006: Auto-Sync on Brand Creation

**Given** RAG 시스템이 활성화된 상태에서
**When** 새 브랜드가 생성되면
**Then** 자동으로 임베딩이 생성되어야 합니다

**Verification**:

- POST /api/v1/brands/ 후 임베딩 존재 확인
- 백그라운드 태스크 완료 후 Qdrant 조회
- 타임아웃 내 임베딩 생성 (10초)

### TC-007: Auto-Sync on Brand Update

**Given** 브랜드 임베딩이 존재할 때
**When** 브랜드 정보가 수정되면
**Then** 임베딩이 갱신되어야 합니다

**Verification**:

- PUT /api/v1/brands/{id} 후 임베딩 확인
- updated_at 타임스탬프 갱신
- 새 정보가 content에 반영

### TC-008: Auto-Delete on Brand Removal

**Given** 브랜드와 관련 제품 임베딩이 존재할 때
**When** 브랜드가 삭제되면
**Then** 브랜드와 모든 관련 제품의 임베딩이 삭제되어야 합니다

**Verification**:

- DELETE /api/v1/brands/{id} 후 확인
- 브랜드 임베딩 삭제됨
- 관련 제품 임베딩도 삭제됨 (CASCADE)

### TC-009: Batch Migration

**Given** 임베딩이 없는 기존 브랜드/제품 데이터가 있을 때
**When** 배치 마이그레이션을 실행하면
**Then** 모든 데이터에 대한 임베딩이 생성되어야 합니다

**Verification**:

- POST /api/v1/knowledge/batch/migrate 성공
- total_brands/total_products 반환
- 모든 엔티티에 임베딩 존재
- failed 배열로 실패 항목 추적

### TC-010: Search Score Threshold

**Given** 검색 요청에 score_threshold가 설정되어 있을 때
**When** 검색을 실행하면
**Then** 임계값 이상의 결과만 반환되어야 합니다

**Verification**:

- score_threshold=0.7 설정
- 모든 결과의 score >= 0.7
- 낮은 점수 결과 제외됨

### TC-011: Search Limit

**Given** 많은 임베딩이 저장되어 있을 때
**When** limit=3으로 검색하면
**Then** 최대 3개의 결과만 반환되어야 합니다

**Verification**:

- limit 파라미터 적용
- 결과 배열 길이 <= 3
- 상위 점수 결과 우선

### TC-012: Non-existent Entity Embedding

**Given** 존재하지 않는 brand_id로
**When** 임베딩 생성 API를 호출하면
**Then** 404 에러가 반환되어야 합니다

**Verification**:

- POST /api/v1/knowledge/embed/brand/{invalid_id} -> 404
- 명확한 에러 메시지

### TC-013: Empty Search Results

**Given** 저장된 임베딩이 없거나 매칭이 없을 때
**When** 검색을 실행하면
**Then** 빈 결과 배열이 반환되어야 합니다

**Verification**:

- results 배열 길이 = 0
- 에러 없이 정상 응답 (200)

### TC-014: Search Performance

**Given** 1,000개 이상의 임베딩이 저장되어 있을 때
**When** 검색을 실행하면
**Then** 100ms 이내에 응답해야 합니다

**Verification**:

- 응답 시간 < 100ms (p95)
- 대용량 데이터에서도 성능 유지

## Quality Gate Criteria

### Performance Criteria

- 임베딩 생성: 2초 이내
- 시맨틱 검색: 100ms 이내 (p95)
- 배치 마이그레이션: 100 entities/min 이상

### Data Consistency Criteria

- CRUD 이벤트와 임베딩 동기화 100%
- CASCADE 삭제 정확성
- 메타데이터 일관성

### Availability Criteria

- Qdrant 연결 실패 시 graceful degradation
- 재시도 로직 동작
- 헬스체크 엔드포인트 제공

## Definition of Done

- [ ] 모든 TC 통과
- [ ] Qdrant 통합 테스트 완료
- [ ] 임베딩 API mock 테스트 완료
- [ ] 성능 벤치마크 통과
- [ ] 마이그레이션 스크립트 테스트 완료
- [ ] API 문서 업데이트
- [ ] 운영 가이드 작성

---

**Acceptance Status**: PENDING
**Prerequisites**: SPEC-002 구현 완료
