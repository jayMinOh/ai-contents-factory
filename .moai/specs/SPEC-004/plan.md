# SPEC-004: Implementation Plan - AI Video Generation System

---
spec_id: SPEC-004
document_type: plan
status: PLANNED
---

## Implementation Overview

AI Video Generation System의 구현 계획입니다. 이 시스템은 레퍼런스 분석과 브랜드 정보를 활용하여 마케팅 영상을 자동 생성합니다.

## Milestones

### Milestone 1: Database & Model Setup

**Priority**: High

**Goals**:

- VideoGeneration DB 모델 정의
- Pydantic 스키마 정의
- 마이그레이션 스크립트 작성

**Deliverables**:

- `/backend/app/models/video_generation.py`
- `/backend/app/schemas/video.py`
- Alembic 마이그레이션

**Technical Approach**:

- SQLAlchemy 2.0 async 모델
- JSON 컬럼으로 script/storyboard 저장
- 상태 추적을 위한 enum 정의

### Milestone 2: Script Generation Service

**Priority**: High

**Goals**:

- Gemini 기반 스크립트 생성
- 레퍼런스 분석 결과 활용
- 브랜드 컨텍스트 통합

**Deliverables**:

- `/backend/app/services/video_generator/script_generator.py`
- 스크립트 생성 프롬프트 엔지니어링
- 레퍼런스 스타일 트랜스퍼 로직

**Technical Approach**:

- SPEC-001 분석 결과에서 구조 패턴 추출
- SPEC-002/003에서 브랜드 컨텍스트 조회
- JSON 형식의 구조화된 스크립트 출력

### Milestone 3: Storyboard Generation

**Priority**: High

**Goals**:

- 장면별 스토리보드 생성
- 비주얼 프롬프트 생성
- 미리보기 이미지 생성 (선택적)

**Deliverables**:

- `/backend/app/services/video_generator/storyboard_generator.py`
- 카메라 앵글/전환 효과 지시 로직
- 이미지 생성 프롬프트 템플릿

**Technical Approach**:

- 스크립트 각 장면에 대한 비주얼 지시 생성
- 레퍼런스 영상의 시각적 스타일 참조
- DALL-E 또는 Gemini 이미지 생성 연동 (선택적)

### Milestone 4: Video Provider Abstraction

**Priority**: High

**Goals**:

- 영상 생성 API 추상화 인터페이스
- Luma AI 클라이언트 구현
- Runway ML 클라이언트 구현 (선택적)
- HeyGen 클라이언트 구현 (선택적)

**Deliverables**:

- `/backend/app/services/video_generator/video_providers/base.py`
- `/backend/app/services/video_generator/video_providers/luma.py`
- `/backend/app/services/video_generator/video_providers/runway.py`
- `/backend/app/services/video_generator/video_providers/heygen.py`

**Technical Approach**:

- 추상 베이스 클래스로 공통 인터페이스 정의
- 각 프로바이더별 API 연동
- 비동기 작업 상태 폴링

### Milestone 5: Asset Management (MinIO)

**Priority**: High

**Goals**:

- MinIO 연동
- 영상 파일 업로드/다운로드
- 썸네일 생성

**Deliverables**:

- `/backend/app/services/video_generator/asset_manager.py`
- MinIO 클라이언트 설정
- 프리사인드 URL 생성

**Technical Approach**:

- boto3 S3 호환 클라이언트 사용
- 버킷 정책 설정 (public read)
- 만료 시간이 있는 다운로드 URL

### Milestone 6: Generation Orchestration

**Priority**: High

**Goals**:

- 전체 생성 파이프라인 오케스트레이션
- 상태 관리
- 에러 핸들링 및 재시도

**Deliverables**:

- `/backend/app/services/video_generator/generation_service.py`
- 백그라운드 태스크 관리
- 상태 업데이트 로직

**Technical Approach**:

- FastAPI BackgroundTasks 또는 Celery
- 상태 머신 패턴
- 실패 시 부분 결과 저장

### Milestone 7: API Layer

**Priority**: High

**Goals**:

- REST API 엔드포인트 구현
- 실시간 상태 조회
- 히스토리 및 필터링

**Deliverables**:

- `/backend/app/api/v1/videos.py`
- API 라우터 및 엔드포인트
- 페이지네이션 및 필터링

**Technical Approach**:

- FastAPI 라우터
- Depends를 통한 인증/권한 (향후)
- 스트리밍 응답 (선택적)

### Milestone 8: Frontend - Generation UI

**Priority**: High

**Goals**:

- 영상 생성 요청 폼
- 옵션 설정 UI
- 생성 시작 플로우

**Deliverables**:

- `/frontend/app/generate/page.tsx`
- 브랜드/제품/레퍼런스 선택 UI
- 스타일 옵션 설정

**Technical Approach**:

- React Query mutations
- 폼 상태 관리
- 비용 예측 표시

### Milestone 9: Frontend - Progress & Result

**Priority**: High

**Goals**:

- 생성 진행률 표시
- 스크립트 미리보기/편집
- 결과 영상 재생

**Deliverables**:

- `/frontend/app/generate/[id]/page.tsx`
- `/frontend/components/video/GenerationProgress.tsx`
- `/frontend/components/video/ScriptEditor.tsx`
- `/frontend/components/video/VideoPreview.tsx`

**Technical Approach**:

- 폴링 기반 진행률 업데이트
- 인라인 스크립트 편집기
- HTML5 video player

### Milestone 10: Frontend - History & Management

**Priority**: Medium

**Goals**:

- 생성 히스토리 목록
- 필터링 및 검색
- 삭제 기능

**Deliverables**:

- `/frontend/app/videos/page.tsx`
- 히스토리 리스트 컴포넌트
- 썸네일 그리드 뷰

**Technical Approach**:

- 페이지네이션
- 상태별 필터
- 다운로드 옵션

## Architecture Design

### System Architecture

```
[Frontend: Next.js 14]
    |
[React Query] <--> [Videos API Client]
    |
    v
[FastAPI Backend]
    |
[API Router: /videos/]
    |
[Generation Service]
    |
    +-------------------------+-------------------------+
    |                         |                         |
    v                         v                         v
[Script Generator]    [Storyboard Generator]    [Video Provider]
    |                         |                         |
    v                         v                         v
[Gemini API]           [Gemini/DALL-E]          [Luma/Runway/HeyGen]
    |                         |                         |
    +-------------------------+-------------------------+
                              |
                              v
                      [Asset Manager]
                              |
                              v
                        [MinIO Server]
```

### Data Flow

#### Complete Generation Flow

1. 사용자가 영상 생성 요청 (brand_id, reference_id, options)
2. generation_id 발급 및 DB 레코드 생성 (status: pending)
3. 백그라운드 태스크 시작

4. **Phase 1: Script Generation**
   - status -> script_generating
   - 레퍼런스 분석 결과 조회 (SPEC-001)
   - 브랜드/제품 컨텍스트 조회 (SPEC-002/003)
   - Gemini API로 스크립트 생성
   - DB에 script 저장, status -> script_ready

5. **Phase 2: Storyboard Creation**
   - status -> storyboard_creating
   - 각 장면에 대한 비주얼 지시 생성
   - 선택적으로 미리보기 이미지 생성
   - DB에 storyboard 저장, status -> storyboard_ready

6. **Phase 3: User Review** (선택적)
   - 사용자가 스크립트/스토리보드 검토
   - 필요시 수정
   - 렌더링 승인

7. **Phase 4: Video Rendering**
   - status -> video_rendering
   - 선택된 프로바이더 API 호출
   - 주기적으로 진행률 폴링
   - 완료 시 영상 URL 수신

8. **Phase 5: Post Processing**
   - status -> post_processing
   - 영상 파일 다운로드
   - MinIO에 업로드
   - 썸네일 생성
   - 메타데이터 저장

9. **Completion**
   - status -> completed
   - video_url, thumbnail_url 저장
   - completed_at 기록

### State Machine

```
pending
    |
    v
script_generating --> [error] --> failed
    |
    v
script_ready <-- (user edit)
    |
    v
storyboard_creating --> [error] --> failed
    |
    v
storyboard_ready <-- (user edit)
    |
    v
video_rendering --> [error] --> failed
    |
    v
post_processing --> [error] --> failed
    |
    v
completed
```

## Risk Assessment

### Identified Risks

**Risk 1**: 영상 생성 API 비용

- **Mitigation**: 비용 예측 표시, 생성 전 확인 단계
- **Contingency**: 프리뷰/워터마크 버전 먼저 생성

**Risk 2**: 긴 렌더링 시간

- **Mitigation**: 진행률 표시, 이메일 알림 (선택적)
- **Contingency**: 웹훅 기반 완료 알림

**Risk 3**: API 제공자 서비스 장애

- **Mitigation**: 다중 프로바이더 지원, 폴백
- **Contingency**: 수동 재시도 옵션

**Risk 4**: 생성된 영상 품질 불일치

- **Mitigation**: 스토리보드 미리보기, 수정 기능
- **Contingency**: 재생성 옵션

### Technical Debt Considerations

- 초기에는 단일 프로바이더(Luma)만 지원
- 이메일 알림은 Phase 2에서 구현
- A/B 테스트용 다중 버전 생성은 향후 과제

## Quality Gates

### Code Quality

- 프로바이더 추상화 인터페이스
- 상태 머신 패턴 적용
- 에러 핸들링 및 로깅

### Testing Requirements

- Script Generator 단위 테스트 (mock Gemini)
- Video Provider 통합 테스트 (mock API)
- 전체 파이프라인 E2E 테스트

### Documentation

- API 스키마 문서화
- 프로바이더별 설정 가이드
- 비용 계산 방법 문서화

## Resource Requirements

### Infrastructure

- MinIO Server: 4 vCPU, 8GB RAM, 500GB SSD
- 추가 스토리지: 영상 파일 용량에 따라 확장

### External Services

- Luma AI: ~$0.5-2.0 per video (길이/해상도에 따라)
- Runway ML: ~$0.05/second of video
- HeyGen: 구독 기반 또는 크레딧 기반

---

**Plan Status**: PLANNED
**Prerequisites**: SPEC-001, SPEC-002 완료 필수, SPEC-003 권장
**Estimated Duration**: 4-6 weeks
