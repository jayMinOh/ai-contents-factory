# SPEC-003: Implementation Plan - Brand Knowledge Base RAG System

---
spec_id: SPEC-003
document_type: plan
status: PLANNED
---

## Implementation Overview

Brand Knowledge Base RAG System의 구현 계획입니다. 이 기능은 브랜드/제품 정보를 벡터화하여 AI 영상 생성 시 관련 컨텍스트를 제공합니다.

## Milestones

### Milestone 1: Infrastructure Setup

**Priority**: High

**Goals**:

- Qdrant 서버 설정 (Docker 또는 Cloud)
- 환경 변수 및 설정 파일 구성
- 기본 연결 테스트

**Deliverables**:

- docker-compose.yml에 Qdrant 서비스 추가
- `/backend/app/core/qdrant.py` 클라이언트 설정
- 연결 테스트 스크립트

**Technical Approach**:

- Docker를 사용한 로컬 개발 환경
- qdrant-client Python 라이브러리 사용
- 환경별 설정 분리 (dev/prod)

### Milestone 2: Embedding Service

**Priority**: High

**Goals**:

- 임베딩 생성 서비스 구현
- 텍스트 템플릿 정의
- 임베딩 모델 추상화

**Deliverables**:

- `/backend/app/services/brand_knowledge/embedding_service.py`
- 텍스트 전처리 로직
- 모델 선택 인터페이스 (OpenAI/Gemini)

**Technical Approach**:

- 추상 클래스로 임베딩 모델 인터페이스 정의
- OpenAI text-embedding-3-small 기본 사용
- 배치 처리를 위한 비동기 구현

### Milestone 3: Qdrant Integration

**Priority**: High

**Goals**:

- Qdrant 컬렉션 생성 및 관리
- 벡터 CRUD 작업 구현
- 메타데이터 관리

**Deliverables**:

- `/backend/app/services/brand_knowledge/qdrant_client.py`
- 컬렉션 초기화 스크립트
- 벡터 업서트/삭제 로직

**Technical Approach**:

- Cosine distance 사용
- 페이로드 인덱싱으로 필터링 성능 최적화
- 재연결 로직 및 에러 핸들링

### Milestone 4: Search Service

**Priority**: High

**Goals**:

- 시맨틱 검색 구현
- 필터링 및 스코어 임계값 적용
- 검색 결과 포맷팅

**Deliverables**:

- `/backend/app/services/brand_knowledge/search_service.py`
- 검색 쿼리 빌더
- 결과 변환 로직

**Technical Approach**:

- 쿼리 텍스트 임베딩 생성
- Qdrant search API 활용
- 스코어 기반 필터링

### Milestone 5: CRUD Sync Service

**Priority**: Medium

**Goals**:

- Brand/Product CRUD 이벤트 연동
- 자동 임베딩 동기화
- 삭제 시 벡터 정리

**Deliverables**:

- `/backend/app/services/brand_knowledge/sync_service.py`
- SPEC-002 서비스 레이어 수정 (이벤트 발행)
- 동기화 상태 추적

**Technical Approach**:

- 서비스 레이어에서 이벤트 발행
- 비동기 백그라운드 태스크로 임베딩 갱신
- 실패 시 재시도 큐

### Milestone 6: API Layer

**Priority**: High

**Goals**:

- REST API 엔드포인트 구현
- 요청/응답 스키마 정의
- 에러 핸들링

**Deliverables**:

- `/backend/app/api/v1/knowledge.py`
- Pydantic 스키마
- API 문서화

**Technical Approach**:

- FastAPI 라우터 구현
- 타입 힌트 기반 자동 문서화
- 적절한 HTTP 상태 코드

### Milestone 7: Batch Migration Tool

**Priority**: Medium

**Goals**:

- 기존 데이터 마이그레이션
- 진행 상황 추적
- 실패 처리

**Deliverables**:

- `/backend/app/services/brand_knowledge/migration.py`
- CLI 스크립트
- 마이그레이션 보고서

**Technical Approach**:

- 배치 단위 처리 (100개씩)
- 진행률 로깅
- 실패 항목 재시도 옵션

## Architecture Design

### System Architecture

```
[Brand/Product Service] --events--> [Sync Service]
                                        |
                                        v
[API Layer] <--> [Search Service] <--> [Embedding Service]
                       |                     |
                       v                     v
                  [Qdrant Client] <---> [Qdrant Server]
                                             |
                                   [brand_knowledge collection]
```

### Data Flow

#### Embedding Creation Flow

1. Brand/Product 생성 또는 수정 이벤트 발생
2. Sync Service가 이벤트 수신
3. Embedding Service가 텍스트 템플릿 생성
4. 임베딩 API 호출 (OpenAI/Gemini)
5. Qdrant Client가 벡터 업서트

#### Search Flow

1. 검색 API 요청 수신
2. 쿼리 텍스트 임베딩 생성
3. Qdrant 벡터 검색 실행
4. 결과 필터링 및 포맷팅
5. 응답 반환

#### Context Retrieval Flow

1. 영상 생성 요청 시 brand_id 전달
2. Knowledge API로 컨텍스트 조회
3. 브랜드 기본 정보 + 관련 제품 정보 조합
4. 선택적으로 유사 브랜드 정보 추가
5. 스크립트 생성에 컨텍스트 제공

## Risk Assessment

### Identified Risks

**Risk 1**: 임베딩 API 비용

- **Mitigation**: 캐싱, 배치 처리, 변경 시에만 갱신
- **Contingency**: 로컬 임베딩 모델 (sentence-transformers) 대안

**Risk 2**: Qdrant 가용성

- **Mitigation**: 재연결 로직, 헬스체크
- **Contingency**: 폴백으로 직접 DB 검색 (정확도 낮음)

**Risk 3**: 데이터 동기화 실패

- **Mitigation**: 재시도 큐, 수동 동기화 API
- **Contingency**: 배치 마이그레이션으로 전체 재동기화

### Technical Debt Considerations

- 초기에는 동기 방식으로 구현 후 비동기 최적화
- 청킹 로직은 Phase 2에서 구현
- 유사 브랜드 검색은 선택적 기능

## Quality Gates

### Code Quality

- 추상화된 임베딩 모델 인터페이스
- 타입 힌트 100% 적용
- 단위 테스트 가능한 구조

### Testing Requirements

- Embedding Service 단위 테스트 (mock API)
- Qdrant Client 통합 테스트 (test container)
- Search API E2E 테스트

### Documentation

- API 스키마 문서화
- 아키텍처 다이어그램
- 운영 가이드 (인덱싱, 마이그레이션)

## Resource Requirements

### Infrastructure

- Qdrant Server: 2 vCPU, 4GB RAM (초기)
- 벡터 저장: ~100MB per 10,000 vectors

### External Services

- OpenAI API: ~$0.0001 per embedding
- 또는 Gemini API: Free tier 가능

---

**Plan Status**: PLANNED
**Prerequisites**: SPEC-002 완료, Qdrant 인프라 준비
