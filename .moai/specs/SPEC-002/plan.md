# SPEC-002: Implementation Plan - Brand and Product Management System

---
spec_id: SPEC-002
document_type: plan
status: IMPLEMENTED
---

## Implementation Overview

Brand and Product Management System의 구현 계획입니다. 현재 이 기능은 완전히 구현되어 운영 중입니다.

## Milestones

### Milestone 1: Database Models (COMPLETED)

**Priority**: High

**Goals**:

- SQLAlchemy 2.0 async 모델 정의
- Brand-Product 1:N 관계 설정
- Timestamp mixin 적용

**Deliverables**:

- `/backend/app/models/brand.py` 구현
- `/backend/app/models/product.py` 구현
- `/backend/app/models/base.py` TimestampMixin 구현

**Technical Approach**:

- SQLAlchemy 2.0 Mapped 타입 어노테이션 사용
- JSON 컬럼으로 배열 데이터 저장
- selectinload를 기본 lazy 로딩 전략으로 설정
- CASCADE 삭제를 위한 relationship 설정

### Milestone 2: Service Layer (COMPLETED)

**Priority**: High

**Goals**:

- 비즈니스 로직 캡슐화
- 데이터 접근 패턴 표준화
- 브랜드 소유권 검증 구현

**Deliverables**:

- `/backend/app/services/brand_service.py` 구현
- `/backend/app/services/product_service.py` 구현

**Technical Approach**:

- async 함수로 모든 DB 작업 구현
- select() 문을 활용한 쿼리 작성
- exclude_unset=True로 부분 업데이트 지원
- 서브쿼리를 활용한 product_count 계산

### Milestone 3: Pydantic Schemas (COMPLETED)

**Priority**: High

**Goals**:

- 요청/응답 스키마 정의
- 프론트엔드 TypeScript 인터페이스와 일치
- 부분 업데이트를 위한 Optional 필드

**Deliverables**:

- `/backend/app/schemas/brand.py` 구현

**Technical Approach**:

- Pydantic V2 문법 사용 (BaseModel, ConfigDict)
- Base -> Create -> Update -> Response 상속 구조
- from_attributes=True로 ORM 모델 자동 변환

### Milestone 4: API Endpoints (COMPLETED)

**Priority**: High

**Goals**:

- RESTful API 설계
- 적절한 HTTP 상태 코드 반환
- 에러 핸들링

**Deliverables**:

- `/backend/app/api/v1/brands.py` 구현

**Technical Approach**:

- FastAPI Depends를 활용한 DB 세션 주입
- HTTPException으로 404 처리
- 응답 모델 타입 힌트로 자동 문서화

### Milestone 5: Frontend UI (COMPLETED)

**Priority**: High

**Goals**:

- 3단 그리드 레이아웃 (목록 | 상세)
- 모달 기반 폼 UI
- React Query 통합

**Deliverables**:

- `/frontend/app/brands/page.tsx` 구현
- `/frontend/lib/api.ts` brandApi 추가

**Technical Approach**:

- useQuery/useMutation 훅 활용
- invalidateQueries로 캐시 갱신
- 조건부 useQuery (enabled 옵션)
- confirm()을 활용한 삭제 확인

### Milestone 6: UX Enhancements (COMPLETED)

**Priority**: Medium

**Goals**:

- 태그 입력 UX 개선
- 톤앤매너 선택 드롭다운
- 로딩 상태 표시

**Deliverables**:

- 키워드/기능/혜택 태그 컴포넌트
- BrandFormModal 컴포넌트
- ProductFormModal 컴포넌트

**Technical Approach**:

- Enter 키 이벤트로 태그 추가
- 배열 상태 관리
- Loader2 아이콘으로 로딩 표시

## Architecture Design

### System Architecture

```
[Frontend: Next.js 14]
    |
[React Query Cache] <--> [brandApi Client]
    |
    v
[FastAPI Backend]
    |
[API Router: /brands/]
    |
[Service Layer]
    |
    +-- brand_service.py
    +-- product_service.py
    |
[SQLAlchemy ORM]
    |
    v
[MariaDB]
    |
    +-- brands table
    +-- products table (FK: brand_id)
```

### Data Flow

#### Brand Creation Flow

1. 사용자가 BrandFormModal에서 폼 작성
2. createMutation.mutate() 호출
3. POST /api/v1/brands/ 요청
4. brand_service.create_brand() 실행
5. UUID 생성 및 DB INSERT
6. invalidateQueries로 캐시 갱신
7. 모달 닫기 및 새 브랜드 선택

#### Product with Brand Flow

1. 사용자가 브랜드 선택 후 "제품 추가" 클릭
2. ProductFormModal 표시
3. POST /api/v1/brands/{brand_id}/products 요청
4. product_service.create_product() 실행
5. 브랜드 존재 확인 후 제품 생성
6. invalidateQueries(['brand', brand_id])로 상세 캐시 갱신

## Risk Assessment

### Identified Risks (MITIGATED)

**Risk 1**: N+1 쿼리 문제

- **Mitigation**: selectinload 적용
- **Status**: Resolved

**Risk 2**: 브랜드 삭제 시 제품 고아화

- **Mitigation**: CASCADE 삭제 설정
- **Status**: Resolved

**Risk 3**: 동시성 이슈

- **Mitigation**: ORM 레벨 트랜잭션 관리
- **Status**: Ongoing monitoring

### Technical Debt

- 페이지네이션 미구현 (skip/limit 파라미터 존재하나 UI 미적용)
- 브랜드 로고 이미지 업로드 기능 미구현 (URL만 저장)
- 검색/필터링 기능 미구현

## Quality Gates

### Code Quality

- SQLAlchemy 2.0 async 패턴 준수
- Pydantic V2 스키마 검증
- TypeScript strict mode

### Testing Requirements

- Service layer unit tests
- API endpoint integration tests
- React Query mutation tests

### Documentation

- FastAPI Swagger 자동 문서화
- TypeScript 인터페이스 정의

---

**Plan Status**: COMPLETED
**Implementation Verified**: 2025-12-11
