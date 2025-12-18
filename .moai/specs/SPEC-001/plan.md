# SPEC-001: Implementation Plan - Reference Video Analysis System

---
spec_id: SPEC-001
document_type: plan
status: IMPLEMENTED
---

## Implementation Overview

Reference Video Analysis System의 구현 계획입니다. 현재 이 기능은 완전히 구현되어 운영 중입니다.

## Milestones

### Milestone 1: Core Backend Infrastructure (COMPLETED)

**Priority**: High

**Goals**:

- FastAPI 백엔드 프로젝트 구조 설정
- 비디오 다운로드 파이프라인 구현
- 프레임 추출 로직 구현

**Deliverables**:

- `/backend/app/services/reference_analyzer/analyzer.py` 구현
- yt-dlp 통합 및 에러 핸들링
- FFmpeg 기반 프레임 추출

**Technical Approach**:

- asyncio를 활용한 비동기 subprocess 실행
- 영상 길이에 따른 동적 fps 계산
- 임시 파일 관리 및 자동 정리

### Milestone 2: Gemini AI Integration (COMPLETED)

**Priority**: High

**Goals**:

- Google Gemini API 연동
- 마케팅 분석 프롬프트 엔지니어링
- JSON 응답 파싱 로직

**Deliverables**:

- Gemini 모델 초기화 및 호출
- 구조화된 분석 프롬프트
- 다중 JSON 파싱 전략 (코드블록, 직접 파싱, 오류 수정)

**Technical Approach**:

- PIL을 사용한 이미지 로딩
- 멀티모달 프롬프트 구성 (텍스트 + 이미지)
- 폴백 분석 결과 제공

### Milestone 3: API Layer Development (COMPLETED)

**Priority**: High

**Goals**:

- RESTful API 엔드포인트 구현
- Pydantic 스키마 정의
- 백그라운드 태스크 관리

**Deliverables**:

- `/backend/app/api/v1/references.py` 구현
- 16개 이상의 Pydantic 모델 정의
- 인메모리 분석 결과 저장소

**Technical Approach**:

- FastAPI BackgroundTasks를 활용한 비동기 분석
- UUID 기반 분석 작업 ID 관리
- 열거형(Enum)을 활용한 타입 안전성

### Milestone 4: Frontend UI Development (COMPLETED)

**Priority**: High

**Goals**:

- 영상 URL 입력 인터페이스
- 실시간 분석 상태 표시
- 분석 결과 시각화

**Deliverables**:

- `/frontend/app/page.tsx` 구현
- 스켈레톤 로딩 UI
- 20개 이상의 React 컴포넌트

**Technical Approach**:

- React Query를 활용한 폴링 (2초 간격)
- TailwindCSS 기반 반응형 디자인
- 색상 코딩된 세그먼트 배지

### Milestone 5: UX Enhancement (COMPLETED)

**Priority**: Medium

**Goals**:

- 마케팅 용어 툴팁 시스템
- 프로그레스 바 및 상태 표시
- 에러 처리 UI

**Deliverables**:

- Tooltip 컴포넌트
- LoadingSkeletonView 컴포넌트
- 상태별 프로그레스 바

**Technical Approach**:

- CSS group hover를 활용한 툴팁
- 상태별 프로그레스 width 매핑
- 애니메이션 fade-in-up 효과

## Architecture Design

### System Architecture

```
[User Browser]
    |
    v
[Next.js Frontend] --React Query--> [FastAPI Backend]
    |                                     |
    v                                     v
[/page.tsx]                         [/references.py]
    |                                     |
    v                                     v
[API Client]                        [ReferenceAnalyzer]
                                          |
                    +---------------------+---------------------+
                    |                     |                     |
                    v                     v                     v
              [yt-dlp]             [FFmpeg]              [Gemini API]
              (download)          (frames)               (analysis)
```

### Data Flow

1. 사용자가 URL 입력 및 분석 요청
2. 백엔드가 UUID 발급 및 백그라운드 작업 시작
3. 프론트엔드가 2초마다 상태 폴링
4. 백엔드에서 순차적으로:
   - 영상 다운로드 (yt-dlp)
   - 프레임 추출 (FFmpeg)
   - AI 분석 (Gemini)
5. 분석 완료 시 결과 반환
6. 프론트엔드에서 결과 시각화

## Risk Assessment

### Identified Risks (MITIGATED)

**Risk 1**: Gemini API 응답 형식 불일치

- **Mitigation**: 다중 JSON 파싱 전략 및 폴백 구현
- **Status**: Resolved

**Risk 2**: 대용량 영상 처리 시 타임아웃

- **Mitigation**: 720p 제한, 프레임 샘플링
- **Status**: Resolved

**Risk 3**: yt-dlp 플랫폼 지원 변동

- **Mitigation**: 에러 핸들링 및 사용자 피드백
- **Status**: Ongoing monitoring

### Technical Debt

- 인메모리 저장소 → 추후 데이터베이스 마이그레이션 필요
- 프레임 추출 최적화 여지 (GPU 가속 고려)
- 분석 결과 캐싱 미구현

## Quality Gates

### Code Quality

- Python type hints 전체 적용
- Pydantic 스키마 기반 데이터 검증
- TypeScript strict mode

### Testing Requirements

- Backend unit tests for analyzer
- API endpoint integration tests
- Frontend component tests

### Documentation

- API 스키마 자동 문서화 (FastAPI Swagger)
- 마케팅 용어 UI 내 설명

---

**Plan Status**: COMPLETED
**Implementation Verified**: 2025-12-11
