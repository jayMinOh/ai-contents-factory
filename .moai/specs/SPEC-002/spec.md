# SPEC-002: Brand and Product Management System

---
spec_id: SPEC-002
title: Brand and Cosmetics Product Management System
status: IMPLEMENTED
version: 2.0.0
created_at: 2025-01-15
updated_at: 2025-12-11
author: AI Video Marketing Team
tags: [brand, product, cosmetics, ingredients, skin-care, crud, management, database]
---

## Overview

Brand and Cosmetics Product Management System은 맞춤형 화장품 마케팅 영상 생성에 필요한 브랜드 및 제품 정보를 관리하는 시스템입니다. 브랜드의 타겟 고객, 톤앤매너, USP(핵심 차별점) 등의 메타데이터와 화장품 제품의 성분, 피부 적합성, 텍스처, 인증 정보를 저장하고 관리합니다.

**v2.0 업데이트**: 화장품 특화 필드 추가 (주요 성분, 피부 타입/고민, 텍스처, 인증/임상결과)

## Environment (E)

### System Context

- **Backend Framework**: FastAPI (Python 3.12+)
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: MariaDB
- **Frontend Framework**: Next.js 14 + React Query + TailwindCSS
- **State Management**: TanStack React Query

### External Dependencies

- MariaDB Server
- SQLAlchemy 2.0+ (asyncio support)
- Pydantic V2

### Configuration

- Database connection string
- SQLAlchemy async session factory

## Assumptions (A)

### Business Assumptions

- 하나의 브랜드는 여러 제품을 가질 수 있습니다 (1:N 관계)
- 브랜드 삭제 시 해당 브랜드의 모든 제품도 함께 삭제됩니다 (CASCADE)
- 브랜드명은 중복될 수 있습니다 (고유성 제약 없음)

### Technical Assumptions

- UUID를 문자열로 저장합니다 (36자)
- JSON 타입 컬럼을 사용하여 배열 데이터(keywords, features, benefits)를 저장합니다
- 비동기 데이터베이스 연결을 사용합니다

### Constraints

- keywords, features, benefits는 문자열 배열로 저장
- 브랜드/제품 ID는 클라이언트에서 생성하지 않고 서버에서 UUID 생성

## Requirements (R)

### Functional Requirements

#### FR-001: Brand Creation (IMPLEMENTED)

- **When** 사용자가 브랜드 생성 요청을 하면
- **The System Shall** 새로운 브랜드를 데이터베이스에 저장합니다
- **Required Fields**: name
- **Optional Fields**: description, logo_url, target_audience, tone_and_manner, usp, keywords, industry
- **Priority**: High

#### FR-002: Brand Listing (IMPLEMENTED)

- **When** 사용자가 브랜드 목록을 요청하면
- **The System Shall** 모든 브랜드를 생성일 역순으로 반환합니다
- **Include**: 각 브랜드의 제품 개수 (product_count)
- **Priority**: High

#### FR-003: Brand Detail Retrieval (IMPLEMENTED)

- **When** 사용자가 특정 브랜드의 상세 정보를 요청하면
- **The System Shall** 브랜드 정보와 해당 브랜드의 모든 제품 목록을 반환합니다
- **Priority**: High

#### FR-004: Brand Update (IMPLEMENTED)

- **When** 사용자가 브랜드 정보 수정을 요청하면
- **The System Shall** 제공된 필드만 업데이트합니다 (partial update)
- **Priority**: High

#### FR-005: Brand Deletion (IMPLEMENTED)

- **When** 사용자가 브랜드 삭제를 요청하면
- **The System Shall** 브랜드와 모든 관련 제품을 삭제합니다 (CASCADE)
- **Priority**: High

#### FR-006: Cosmetics Product Creation (IMPLEMENTED)

- **When** 사용자가 특정 브랜드에 제품 생성을 요청하면
- **The System Shall** 브랜드 존재 여부를 확인하고 새 화장품 제품을 생성합니다
- **Required Fields**: name
- **Cosmetics Fields (v2.0)**:
  - product_category: 제품 카테고리 (serum, cream, toner, essence 등 22종)
  - key_ingredients: 주요 성분 배열 (name, name_ko, effect, category, concentration, is_hero)
  - suitable_skin_types: 적합 피부 타입 (dry, oily, combination, normal, sensitive, all)
  - skin_concerns: 피부 고민 (acne, pores, wrinkles, dark_spots 등 26종)
  - texture_type: 텍스처 타입 (cream, gel, serum, oil 등 15종)
  - finish_type: 마무리감 (matte, dewy, satin, natural 등 8종)
  - certifications: 인증 정보 (vegan, cruelty_free, ewg_verified 등)
  - clinical_results: 임상 결과 (metric, result, test_period, sample_size)
  - volume_ml: 용량 (ml)
- **Legacy Fields**: description, features, benefits, price_range, target_segment
- **Priority**: High

#### FR-007: Product Listing (IMPLEMENTED)

- **When** 사용자가 특정 브랜드의 제품 목록을 요청하면
- **The System Shall** 해당 브랜드의 모든 제품을 생성일 역순으로 반환합니다
- **Priority**: High

#### FR-008: Product Update (IMPLEMENTED)

- **When** 사용자가 제품 정보 수정을 요청하면
- **The System Shall** 브랜드 소유권을 확인하고 제공된 필드만 업데이트합니다
- **Priority**: High

#### FR-009: Product Deletion (IMPLEMENTED)

- **When** 사용자가 제품 삭제를 요청하면
- **The System Shall** 브랜드 소유권을 확인하고 제품을 삭제합니다
- **Priority**: High

#### FR-010: Brand Form Modal (IMPLEMENTED)

- **When** 사용자가 "브랜드 추가" 또는 "편집" 버튼을 클릭하면
- **The System Shall** 브랜드 정보 입력 모달을 표시합니다
- **Fields**: 브랜드명, 설명, 업종, 타겟 고객층, 톤앤매너(선택), USP, 키워드
- **Priority**: High

#### FR-011: Cosmetics Product Form Modal (IMPLEMENTED)

- **When** 사용자가 "제품 추가" 또는 "편집" 버튼을 클릭하면
- **The System Shall** 탭 기반의 화장품 제품 정보 입력 모달을 표시합니다
- **Tab 1 - 기본 정보**: 제품명, 제품 카테고리, 용량, 설명, 가격대
- **Tab 2 - 주요 성분**: 성분 카드 목록 (성분명, 한글명, 효능, 카테고리, 함량, 히어로 여부)
- **Tab 3 - 피부 적합성**: 적합 피부 타입 (멀티 선택), 피부 고민 (태그 선택기)
- **Tab 4 - 텍스처/마무리감**: 텍스처 타입, 마무리감 (버튼 그룹)
- **레거시 섹션**: 기능, 혜택, 타겟 세그먼트 (접기/펼치기)
- **Priority**: High

#### FR-012: Keyword/Feature/Benefit Tag Management (IMPLEMENTED)

- **When** 사용자가 키워드/기능/혜택을 입력하면
- **The System Shall** Enter 키 또는 "추가" 버튼으로 태그를 추가하고 X 버튼으로 제거할 수 있게 합니다
- **Priority**: Medium

### Non-Functional Requirements

#### NFR-001: Data Integrity

- 브랜드 삭제 시 관련 제품 자동 삭제 (CASCADE)
- 제품 조회/수정/삭제 시 브랜드 소유권 검증

#### NFR-002: Performance

- 브랜드 목록 조회 시 product_count 서브쿼리 최적화
- selectinload를 사용한 N+1 문제 방지

#### NFR-003: Usability

- 모달 기반 폼으로 페이지 이동 없이 CRUD 수행
- 삭제 전 확인 대화상자 표시

## Specifications (S)

### API Specifications

#### POST /api/v1/brands/

브랜드 생성

**Request Body** (BrandCreate):

- `name` (string, required): 브랜드명
- `description` (string, optional): 설명
- `logo_url` (string, optional): 로고 URL
- `target_audience` (string, optional): 타겟 고객층
- `tone_and_manner` (string, optional): 톤앤매너
- `usp` (string, optional): USP (핵심 차별점)
- `keywords` (array, optional): 키워드 목록
- `industry` (string, optional): 업종

**Response** (BrandResponse): 생성된 브랜드 정보

#### GET /api/v1/brands/

브랜드 목록 조회

**Response** (BrandSummary[]): 모든 브랜드 요약 목록 (product_count 포함)

#### GET /api/v1/brands/{brand_id}

브랜드 상세 조회

**Response** (BrandResponse): 브랜드 정보 및 제품 목록

#### PUT /api/v1/brands/{brand_id}

브랜드 수정

**Request Body** (BrandUpdate): 수정할 필드만 포함

**Response** (BrandResponse): 수정된 브랜드 정보

#### DELETE /api/v1/brands/{brand_id}

브랜드 삭제

**Response**: `{"message": "Brand deleted successfully"}`

#### POST /api/v1/brands/{brand_id}/products

제품 생성

**Request Body** (ProductCreate):

- `name` (string, required): 제품명
- `description` (string, optional): 설명
- `features` (array, optional): 기능 목록
- `benefits` (array, optional): 혜택 목록
- `price_range` (string, optional): 가격대
- `target_segment` (string, optional): 타겟 세그먼트

**Response** (ProductResponse): 생성된 제품 정보

#### GET /api/v1/brands/{brand_id}/products

특정 브랜드의 제품 목록 조회

**Response** (ProductResponse[]): 제품 목록

#### GET /api/v1/brands/{brand_id}/products/{product_id}

제품 상세 조회

**Response** (ProductResponse): 제품 정보

#### PUT /api/v1/brands/{brand_id}/products/{product_id}

제품 수정

**Request Body** (ProductUpdate): 수정할 필드만 포함

**Response** (ProductResponse): 수정된 제품 정보

#### DELETE /api/v1/brands/{brand_id}/products/{product_id}

제품 삭제

**Response**: `{"message": "Product deleted successfully"}`

### Database Schema

#### brands 테이블

- `id` (VARCHAR(36), PK): UUID
- `name` (VARCHAR(255), NOT NULL, INDEX): 브랜드명
- `description` (TEXT, NULLABLE): 설명
- `logo_url` (VARCHAR(500), NULLABLE): 로고 URL
- `target_audience` (VARCHAR(500), NULLABLE): 타겟 고객층
- `tone_and_manner` (VARCHAR(100), NULLABLE): 톤앤매너
- `usp` (TEXT, NULLABLE): USP
- `keywords` (JSON, NOT NULL, DEFAULT []): 키워드 배열
- `industry` (VARCHAR(100), NULLABLE): 업종
- `created_at` (DATETIME, NOT NULL): 생성일시
- `updated_at` (DATETIME, NOT NULL): 수정일시

#### products 테이블

**기본 필드**:
- `id` (VARCHAR(36), PK): UUID
- `brand_id` (VARCHAR(36), FK, NOT NULL, INDEX): 브랜드 ID
- `name` (VARCHAR(255), NOT NULL): 제품명
- `description` (TEXT, NULLABLE): 설명

**화장품 필드 (v2.0)**:
- `product_category` (VARCHAR(50), NULLABLE, INDEX): 제품 카테고리
- `key_ingredients` (JSON, NOT NULL, DEFAULT []): 주요 성분 배열
  - 구조: [{name, name_ko, effect, category, concentration, is_hero}]
- `suitable_skin_types` (JSON, NOT NULL, DEFAULT []): 적합 피부 타입
- `skin_concerns` (JSON, NOT NULL, DEFAULT []): 피부 고민
- `texture_type` (VARCHAR(50), NULLABLE): 텍스처 타입
- `finish_type` (VARCHAR(50), NULLABLE): 마무리감
- `certifications` (JSON, NOT NULL, DEFAULT []): 인증 정보
  - 구조: [{name, grade, details, badge_icon}]
- `clinical_results` (JSON, NOT NULL, DEFAULT []): 임상 결과
  - 구조: [{metric, result, test_period, sample_size, source}]
- `volume_ml` (INTEGER, NULLABLE): 용량 (ml)

**레거시 필드**:
- `features` (JSON, NOT NULL, DEFAULT []): 기능 배열
- `benefits` (JSON, NOT NULL, DEFAULT []): 혜택 배열
- `price_range` (VARCHAR(100), NULLABLE): 가격대
- `target_segment` (VARCHAR(255), NULLABLE): 타겟 세그먼트

**메타데이터**:
- `created_at` (DATETIME, NOT NULL): 생성일시
- `updated_at` (DATETIME, NOT NULL): 수정일시

**Foreign Key**: `products.brand_id` -> `brands.id` (ON DELETE CASCADE)

### Cosmetics Enums (v2.0)

**ProductCategory** (22종):
serum, cream, toner, essence, oil, mask, cleanser, sunscreen, moisturizer, eye_care, lip_care, mist, ampoule, lotion, emulsion, balm, gel, foam, shampoo, conditioner, treatment, other

**SkinType** (6종):
dry, oily, combination, normal, sensitive, all

**SkinConcern** (26종):
acne, pores, wrinkles, fine_lines, dark_spots, pigmentation, dullness, redness, dryness, oiliness, sagging, elasticity, uneven_tone, dark_circles, sensitivity, dehydration, blackheads, whiteheads, aging, sun_damage, texture, barrier_damage, hair_loss, dandruff, scalp_trouble, other

**IngredientCategory** (12종):
active, moisturizing, soothing, antioxidant, exfoliant, brightening, firming, barrier, anti_aging, hydrating, cleansing, other

**TextureType** (15종):
cream, gel, serum, oil, water, milk, balm, foam, mousse, mist, powder, stick, sheet, patch, other

**FinishType** (8종):
matte, dewy, satin, natural, luminous, velvet, glossy, invisible

**CertificationType** (15종):
vegan, cruelty_free, organic, ewg_verified, dermatologist_tested, hypoallergenic, non_comedogenic, fragrance_free, paraben_free, sulfate_free, alcohol_free, silicone_free, clinical_tested, kfda_approved, other

### Implementation Files

**Backend**:

- `/backend/app/api/v1/brands.py`: API 라우터
- `/backend/app/services/brand_service.py`: 브랜드 서비스 레이어
- `/backend/app/services/product_service.py`: 제품 서비스 레이어
- `/backend/app/models/brand.py`: Brand ORM 모델
- `/backend/app/models/product.py`: Product ORM 모델
- `/backend/app/schemas/brand.py`: Pydantic 스키마

**Frontend**:

- `/frontend/app/brands/page.tsx`: 브랜드 관리 페이지
- `/frontend/lib/api.ts`: API 클라이언트 (brandApi)

## Traceability

### Related SPECs

- SPEC-003 (Brand Knowledge RAG): 브랜드/제품 정보를 벡터 임베딩으로 저장
- SPEC-004 (Video Generation): 브랜드 정보를 활용한 스크립트 생성

### Test Coverage Target

- Unit Tests: 90%
- Integration Tests: 모든 API 엔드포인트
- E2E Tests: 브랜드/제품 CRUD 플로우

---

**Implementation Status**: COMPLETED
**Last Verified**: 2025-12-11
