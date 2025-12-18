# SPEC-003: Brand Knowledge Base RAG System

---
spec_id: SPEC-003
title: Brand Knowledge Base RAG System
status: PLANNED
version: 1.0.0
created_at: 2025-12-11
updated_at: 2025-12-11
author: AI Video Marketing Team
tags: [rag, vector-db, qdrant, embedding, knowledge-base]
---

## Overview

Brand Knowledge Base RAG (Retrieval-Augmented Generation) System은 브랜드 및 제품 정보를 벡터 임베딩으로 저장하고, AI 영상 생성 시 관련 컨텍스트를 검색하여 브랜드에 맞는 콘텐츠를 생성할 수 있게 하는 시스템입니다.

## Environment (E)

### System Context

- **Backend Framework**: FastAPI (Python 3.12+)
- **Vector Database**: Qdrant
- **Embedding Model**: OpenAI text-embedding-3-small 또는 Gemini Embedding
- **ORM**: SQLAlchemy 2.0 (기존 Brand/Product 모델 활용)

### External Dependencies

- Qdrant Server (self-hosted 또는 cloud)
- OpenAI API 또는 Google Gemini API (embedding용)
- SPEC-002 (Brand/Product 데이터 소스)

### Configuration

- `QDRANT_URL`: Qdrant 서버 주소
- `QDRANT_API_KEY`: Qdrant 인증 키 (cloud 사용 시)
- `EMBEDDING_MODEL`: 사용할 임베딩 모델
- `EMBEDDING_DIMENSION`: 임베딩 벡터 차원 (예: 1536)

## Assumptions (A)

### Business Assumptions

- 브랜드/제품 정보가 영상 스크립트 생성에 필수적인 컨텍스트를 제공합니다.
- 유사한 브랜드나 제품의 마케팅 전략을 참조할 수 있습니다.
- 브랜드 톤앤매너가 영상 스타일에 직접적인 영향을 미칩니다.

### Technical Assumptions

- 임베딩 생성 비용이 합리적인 수준입니다.
- Qdrant가 프로덕션 수준의 성능을 제공합니다.
- 브랜드/제품 데이터가 자주 변경되지 않습니다 (캐싱 가능).

### Constraints

- 임베딩 API 호출 비용
- 벡터 DB 저장 용량
- 검색 지연 시간 (target: 100ms 이내)

## Requirements (R)

### Functional Requirements

#### FR-001: Brand Embedding Generation

- **When** 새 브랜드가 생성되거나 수정될 때
- **The System Shall** 브랜드 정보(name, description, target_audience, tone_and_manner, usp, keywords, industry)를 결합하여 임베딩 벡터를 생성합니다
- **Priority**: High

#### FR-002: Product Embedding Generation

- **When** 새 제품이 생성되거나 수정될 때
- **The System Shall** 제품 정보(name, description, features, benefits, price_range, target_segment)와 연결된 브랜드 컨텍스트를 결합하여 임베딩 벡터를 생성합니다
- **Priority**: High

#### FR-003: Vector Storage

- **When** 임베딩이 생성되면
- **The System Shall** Qdrant 컬렉션에 메타데이터(brand_id, product_id, entity_type)와 함께 벡터를 저장합니다
- **Priority**: High

#### FR-004: Semantic Search

- **When** 쿼리 텍스트가 제공되면
- **The System Shall** 유사한 브랜드/제품 정보를 검색하여 반환합니다
- **Priority**: High

#### FR-005: Context Retrieval for Video Generation

- **When** 영상 생성 요청에 brand_id가 포함되면
- **The System Shall** 해당 브랜드와 제품의 관련 컨텍스트를 검색하여 스크립트 생성에 제공합니다
- **Priority**: High

#### FR-006: Embedding Sync on Update

- **When** 브랜드나 제품 정보가 수정되면
- **The System Shall** 기존 임베딩을 업데이트합니다
- **Priority**: Medium

#### FR-007: Embedding Deletion on Entity Removal

- **When** 브랜드나 제품이 삭제되면
- **The System Shall** 관련 임베딩도 Qdrant에서 삭제합니다
- **Priority**: Medium

#### FR-008: Batch Embedding Migration

- **When** 기존 브랜드/제품 데이터가 있는 상태에서 RAG 시스템이 활성화되면
- **The System Shall** 모든 기존 데이터에 대한 임베딩을 배치로 생성합니다
- **Priority**: Medium

#### FR-009: Document Chunking (Optional)

- **If** 브랜드 설명이나 USP가 매우 길 경우
- **The System Shall** 적절한 크기로 청킹하여 여러 벡터로 저장합니다
- **Priority**: Low

### Non-Functional Requirements

#### NFR-001: Search Performance

- 시맨틱 검색 응답 시간: 100ms 이내 (p95)
- 동시 검색 요청 처리: 50 RPS 이상

#### NFR-002: Data Consistency

- 브랜드/제품 CRUD와 임베딩 동기화 보장
- 실패 시 재시도 메커니즘

#### NFR-003: Scalability

- 1,000개 브랜드, 10,000개 제품 규모 지원
- 향후 확장 가능한 아키텍처

## Specifications (S)

### API Specifications

#### POST /api/v1/knowledge/embed/brand/{brand_id}

브랜드 임베딩 수동 생성/갱신

**Response**:

- `status` (string): "success" | "failed"
- `vector_id` (string): Qdrant point ID
- `dimensions` (number): 벡터 차원

#### POST /api/v1/knowledge/embed/product/{product_id}

제품 임베딩 수동 생성/갱신

**Response**:

- `status` (string): "success" | "failed"
- `vector_id` (string): Qdrant point ID
- `dimensions` (number): 벡터 차원

#### POST /api/v1/knowledge/search

시맨틱 검색

**Request Body**:

- `query` (string, required): 검색 쿼리
- `entity_type` (string, optional): "brand" | "product" | "all"
- `limit` (number, optional): 반환 결과 수 (default: 5)
- `score_threshold` (number, optional): 최소 유사도 점수

**Response**:

- `results` (array): 검색 결과 목록
  - `id` (string): entity ID
  - `entity_type` (string): "brand" | "product"
  - `score` (number): 유사도 점수
  - `content` (object): 원본 데이터

#### GET /api/v1/knowledge/context/{brand_id}

영상 생성용 브랜드 컨텍스트 조회

**Query Parameters**:

- `include_products` (boolean, optional): 제품 정보 포함 여부
- `max_products` (number, optional): 포함할 최대 제품 수

**Response**:

- `brand` (object): 브랜드 정보
- `products` (array): 관련 제품 목록
- `similar_brands` (array, optional): 유사 브랜드 목록

#### POST /api/v1/knowledge/batch/migrate

기존 데이터 배치 마이그레이션

**Response**:

- `total_brands` (number): 처리된 브랜드 수
- `total_products` (number): 처리된 제품 수
- `failed` (array): 실패한 항목 목록

### Qdrant Collection Schema

#### Collection: brand_knowledge

- **Vector Size**: 1536 (OpenAI) 또는 768 (Gemini)
- **Distance**: Cosine

**Payload Fields**:

- `entity_id` (string): Brand ID 또는 Product ID
- `entity_type` (string): "brand" | "product"
- `brand_id` (string): 상위 브랜드 ID (제품의 경우)
- `name` (string): 엔티티 이름
- `content` (string): 임베딩에 사용된 텍스트
- `created_at` (datetime): 생성 시각
- `updated_at` (datetime): 수정 시각

### Embedding Text Template

#### Brand Embedding Text

```
Brand: {name}
Industry: {industry}
Target Audience: {target_audience}
Tone and Manner: {tone_and_manner}
USP: {usp}
Description: {description}
Keywords: {keywords joined by comma}
```

#### Product Embedding Text

```
Product: {name}
Brand: {brand_name}
Description: {description}
Features: {features joined by comma}
Benefits: {benefits joined by comma}
Price Range: {price_range}
Target Segment: {target_segment}
```

### Implementation Files (Planned)

**Backend**:

- `/backend/app/services/brand_knowledge/` (stub directory - to be implemented)
  - `embedding_service.py`: 임베딩 생성 로직
  - `qdrant_client.py`: Qdrant 클라이언트 래퍼
  - `search_service.py`: 시맨틱 검색 로직
  - `sync_service.py`: CRUD 동기화 로직
- `/backend/app/api/v1/knowledge.py`: API 라우터

## Traceability

### Related SPECs

- SPEC-002 (Brand/Product Management): 데이터 소스
- SPEC-004 (Video Generation): 컨텍스트 소비자

### Dependencies

- SPEC-002 완료 필수 (데이터 소스)
- Qdrant 인프라 준비 필요

### Test Coverage Target

- Unit Tests: 90%
- Integration Tests: Qdrant 연동
- E2E Tests: 검색-컨텍스트 조회 플로우

---

**Implementation Status**: PLANNED
**Target Start**: TBD
**Estimated Effort**: Medium
