# AI Content Factory 시스템 아키텍처

## 개요

AI Content Factory는 SNS 마케팅 이미지 콘텐츠를 대량으로 생산하기 위한 통합 워크플로우 시스템입니다. 6단계 마법사를 통해 사용자가 단일 이미지, 캐러셀, 스토리 형식의 SNS 콘텐츠를 손쉽게 제작할 수 있습니다.

---

## 시스템 구성도

```
사용자 인터페이스 (Frontend)
    │
    ├── 대시보드 (/)
    │   └── 통계, 빠른 생성 액션, 최근 작업
    │
    ├── 콘텐츠 생성 마법사 (/create)
    │   ├── Step 1: 콘텐츠 유형 선택
    │   ├── Step 2: 용도 선택
    │   ├── Step 3: 생성 방식 선택
    │   ├── Step 4: AI 이미지 생성
    │   ├── Step 5: 이미지 선택
    │   └── Step 6: 텍스트 편집
    │
    ├── Canvas 에디터 (/create/edit)
    │   ├── Fabric.js 캔버스
    │   ├── 텍스트 도구 툴바
    │   ├── 레이어 패널
    │   └── 내보내기 패널
    │
    └── 레퍼런스 라이브러리 (/references)
        ├── 레퍼런스 그리드
        ├── 필터 및 검색
        └── 상세 분석 패널
    │
    ▼
API 게이트웨이 (FastAPI)
    │
    ├── /api/v1/references - 레퍼런스 관리
    ├── /api/v1/content - 콘텐츠 생성
    └── /api/v1/brands - 브랜드 관리
    │
    ▼
비즈니스 로직 서비스 계층
    │
    ├── SNS Parser Service
    │   ├── sns_parser.py
    │   └── sns_media_downloader.py
    │
    ├── Image Analysis Service
    │   ├── image_analyzer.py
    │   └── content_image_analyzer.py
    │
    ├── Image Generation Service
    │   ├── image_prompt_builder.py
    │   ├── batch_image_generator.py
    │   └── image_composite_generator.py
    │
    └── Image Export Service
        ├── image_editor.py
        └── image_metadata.py
    │
    ▼
외부 서비스 연동
    │
    ├── Gemini Vision API (이미지 분석)
    ├── Gemini Imagen API (이미지 생성)
    └── gallery-dl (SNS 미디어 다운로드)
    │
    ▼
데이터 저장소
    │
    ├── MariaDB (관계형 데이터)
    │   ├── brands
    │   ├── products
    │   └── reference_analysis
    │
    └── File Storage (/backend/storage/)
        ├── references/
        ├── projects/
        └── temp/
```

---

## 데이터 흐름

### 레퍼런스 분석 플로우

```
1. 사용자 입력
   │
   ├── SNS 링크 입력
   │   └── POST /api/v1/references/analyze-link
   │
   └── 이미지 업로드
       └── POST /api/v1/references/analyze-image
   │
   ▼
2. SNS Parser Service
   │
   ├── URL 유효성 검사
   ├── 플랫폼 식별 (Instagram/Facebook)
   └── gallery-dl로 미디어 추출
   │
   ▼
3. Image Analysis Service
   │
   ├── Gemini Vision API 호출
   └── 분석 결과 추출
       ├── composition (구도)
       ├── colorScheme (색감)
       ├── style (스타일)
       └── elements (요소)
   │
   ▼
4. 저장
   │
   ├── 이미지 파일 저장 (/storage/references/)
   └── 분석 데이터 저장 (MariaDB)
   │
   ▼
5. 응답 반환
   └── Reference 객체 JSON
```

### 이미지 생성 플로우

```
1. 생성 요청
   │
   └── POST /api/v1/content/generate
       ├── type: single/carousel/story
       ├── purpose: ad/info/lifestyle
       ├── method: reference/prompt
       └── brand_id, product_id (선택적)
   │
   ▼
2. Image Prompt Builder Service
   │
   ├── 기본 프롬프트 구성
   ├── 콘텐츠 유형별 템플릿 적용
   ├── 레퍼런스 스타일 반영 (선택)
   └── 브랜드/상품 정보 반영 (선택)
   │
   ▼
3. Batch Image Generator Service
   │
   ├── 4개 변형 프롬프트 생성
   └── Gemini Imagen API 병렬 호출
   │
   ▼
4. 저장
   │
   ├── 생성된 이미지 저장 (/storage/projects/)
   └── 프로젝트 메타데이터 저장 (MariaDB)
   │
   ▼
5. 응답 반환
   └── 4개 변형 이미지 URL
```

### 캔버스 편집 플로우

```
1. 에디터 로드
   │
   └── GET /api/v1/content/{project_id}/canvas
   │
   ▼
2. Fabric.js 캔버스 초기화
   │
   ├── 선택된 이미지 배경 로드
   └── 저장된 캔버스 상태 복원
   │
   ▼
3. 사용자 편집
   │
   ├── 텍스트 추가/편집
   ├── 스타일 변경 (폰트, 색상, 크기)
   ├── 위치/회전/크기 조정
   └── 레이어 순서 변경
   │
   ▼
4. 자동 저장
   │
   └── PUT /api/v1/content/{project_id}/canvas
       └── Fabric.js JSON 데이터 저장
```

### 내보내기 플로우

```
1. 내보내기 요청
   │
   └── POST /api/v1/content/{project_id}/export
       ├── platforms: ["instagram_feed_1x1", ...]
       └── format: "jpeg"
   │
   ▼
2. Image Export Service
   │
   ├── Canvas 렌더링 결과 수신
   └── 플랫폼별 크기 변환
       ├── Instagram Feed 1:1: 1080x1080
       ├── Instagram Feed 4:5: 1080x1350
       ├── Instagram Story: 1080x1920
       ├── Facebook Feed 1:1: 1200x1200
       └── Facebook Feed 1.91:1: 1200x630
   │
   ▼
3. 이미지 최적화
   │
   ├── Pillow로 리사이즈
   ├── 형식 변환 (JPEG/PNG/WebP)
   └── 품질 최적화
   │
   ▼
4. 저장
   │
   └── 출력 파일 저장 (/storage/projects/{id}/outputs/)
   │
   ▼
5. 응답 반환
   │
   ├── 단일 플랫폼: 이미지 URL
   └── 다중 플랫폼: ZIP 다운로드 URL
```

---

## 컴포넌트 관계도

### Frontend 컴포넌트

```
app/
├── page.tsx (대시보드)
│   ├── 통계 카드 컴포넌트
│   ├── 빠른 생성 액션
│   └── 최근 작업 목록
│
├── create/
│   ├── page.tsx (6단계 마법사)
│   │   ├── StepIndicator
│   │   ├── TypeSelector (Step 1)
│   │   ├── PurposeSelector (Step 2)
│   │   ├── MethodSelector (Step 3)
│   │   ├── GeneratePanel (Step 4)
│   │   └── ImageSelector (Step 5)
│   │
│   └── edit/page.tsx (캔버스 에디터)
│       └── CanvasTextEditor
│           ├── FabricCanvas (Fabric.js 래퍼)
│           ├── TextToolbar (텍스트 도구)
│           ├── LayerPanel (레이어 관리)
│           └── CanvasExportPanel (내보내기)
│               ├── PlatformPresets (플랫폼 프리셋)
│               └── BatchExportModal (배치 내보내기)
│
└── references/
    └── page.tsx (레퍼런스 라이브러리)
        ├── ReferenceCard
        ├── ReferenceDetail
        └── AddReferenceModal
```

### Backend 서비스

```
services/
├── SNS 관련
│   ├── sns_parser.py
│   │   ├── parse_instagram_url()
│   │   ├── parse_facebook_url()
│   │   └── extract_metadata()
│   │
│   └── sns_media_downloader.py
│       └── download_media()
│
├── 이미지 분석
│   ├── image_analyzer.py
│   │   └── analyze_image()
│   │
│   └── content_image_analyzer.py
│       └── analyze_content_image()
│
├── 이미지 생성
│   ├── image_prompt_builder.py
│   │   ├── build_base_prompt()
│   │   ├── apply_content_type_template()
│   │   └── inject_brand_context()
│   │
│   ├── batch_image_generator.py
│   │   └── generate_variants()
│   │
│   └── image_composite_generator.py
│       └── generate_composite()
│
└── 내보내기
    ├── image_editor.py
    │   ├── apply_text_overlay()
    │   └── resize_for_platform()
    │
    └── image_metadata.py
        └── extract_metadata()
```

---

## 기술 스택

### Frontend

- **Framework**: Next.js 14 (App Router)
- **상태 관리**: React Query (서버 상태), useState (로컬 상태)
- **스타일링**: Tailwind CSS
- **캔버스**: Fabric.js 5.x
- **알림**: Sonner (Toast)
- **아이콘**: Lucide Icons
- **압축**: JSZip (배치 다운로드)
- **파일 저장**: FileSaver.js

### Backend

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **이미지 처리**: Pillow
- **SNS 다운로드**: gallery-dl
- **AI 연동**: google-generativeai (Gemini API)

### Database

- **관계형 DB**: MariaDB 11
- **파일 스토리지**: 로컬 파일시스템 (/backend/storage/)

### 외부 서비스

- **이미지 분석**: Gemini Vision API
- **이미지 생성**: Gemini Imagen API

---

## 보안 고려사항

### 파일 업로드

- 최대 파일 크기: 50MB
- 허용 형식: JPEG, PNG, WebP
- MIME 타입 검증
- 악성 파일 검사

### API 보안

- CORS 설정
- Rate Limiting
- 입력 검증 (Pydantic)
- SQL Injection 방지 (ORM 사용)

### 데이터 보안

- 사용자별 데이터 격리
- 민감 정보 암호화
- 임시 파일 자동 정리

---

## 성능 최적화

### 이미지 처리

- 썸네일 자동 생성
- 지연 로딩 (Lazy Loading)
- 이미지 캐싱

### API 응답

- 비동기 처리 (async/await)
- 병렬 이미지 생성 (4개 동시)
- 응답 압축 (gzip)

### 프론트엔드

- 코드 스플리팅
- 이미지 최적화 (Next.js Image)
- 캔버스 성능 최적화

---

## 확장성

### 수평 확장

- 상태 비저장 API 설계
- 파일 스토리지 분리 가능 (S3/MinIO)
- 작업 큐 도입 가능 (Celery)

### 기능 확장

- 새 플랫폼 프리셋 추가
- 추가 AI 모델 연동
- 템플릿 시스템 도입

---

**문서 버전**: 1.0.0
**최종 수정일**: 2025-12-19
