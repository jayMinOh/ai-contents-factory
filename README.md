# AI Video Marketing Platform

AI를 활용한 마케팅 콘텐츠 제작 솔루션

## 기능

1. **AI Content Factory** - SNS 마케팅 이미지 콘텐츠 대량 생산 워크플로우
   - 6단계 마법사: 유형 선택, 용도 선택, 생성 방식, AI 이미지 생성, 이미지 선택, 텍스트 편집
   - SNS 링크 파싱 및 레퍼런스 분석 (Instagram, Facebook)
   - AI 이미지 생성 (Gemini Imagen API, 4개 변형)
   - Canvas 텍스트 에디터 (Fabric.js 기반)
   - 플랫폼별 내보내기 (Instagram Feed, Story, Facebook Feed)

2. **레퍼런스 영상 분석** - 영상 URL을 입력하면 타임라인별 분석, 후킹 포인트, 셀링 포인트 추출

3. **브랜드 관리** - 브랜드 및 제품 정보를 등록하고 관리

4. **브랜드 지식베이스** - 브랜드/상품 데이터를 학습하여 RAG 시스템 구축 (예정)

5. **영상 생성** - 분석 결과와 브랜드 데이터를 기반으로 마케팅 영상 자동 생성 (예정)

## 기술 스택

- **Frontend**: Next.js 14, React Query, Tailwind CSS, Lucide Icons, Fabric.js, JSZip
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), Pillow
- **Database**: MariaDB 11, Qdrant (Vector DB), Redis
- **AI**: Google Gemini (Vision API, Imagen API)
- **SNS Integration**: gallery-dl, yt-dlp
- **Video**: FFmpeg, Luma/Runway/HeyGen (예정)

## 시작하기

### 1. 사전 요구사항

```bash
# Python 3.11+
# Node.js 18+
# Docker & Docker Compose
# FFmpeg
# yt-dlp

# macOS
brew install ffmpeg yt-dlp

# Ubuntu
sudo apt install ffmpeg
pip install yt-dlp
```

### 2. Docker 서비스 시작

```bash
cd docker
docker compose up -d
```

서비스 목록:
- MariaDB (포트 3306)
- Redis (포트 6379)
- Qdrant (포트 6333, 6334)
- MinIO (포트 9000, 9001)

### 3. 백엔드 설정

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY 설정

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 4. 프론트엔드 설정

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 http://localhost:3000 접속

## API 사용법

### 브랜드 관리

```bash
# 브랜드 목록 조회
curl http://localhost:8000/api/v1/brands/

# 브랜드 생성
curl -X POST http://localhost:8000/api/v1/brands/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "브랜드명",
    "description": "브랜드 설명",
    "industry": "IT",
    "tone_and_manner": "professional",
    "keywords": ["AI", "마케팅"]
  }'

# 브랜드 상세 조회
curl http://localhost:8000/api/v1/brands/{brand_id}

# 브랜드 수정
curl -X PUT http://localhost:8000/api/v1/brands/{brand_id} \
  -H "Content-Type: application/json" \
  -d '{"usp": "핵심 차별점"}'

# 브랜드 삭제
curl -X DELETE http://localhost:8000/api/v1/brands/{brand_id}
```

### 제품 관리

```bash
# 제품 생성
curl -X POST http://localhost:8000/api/v1/brands/{brand_id}/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "제품명",
    "description": "제품 설명",
    "features": ["기능1", "기능2"],
    "benefits": ["혜택1", "혜택2"],
    "price_range": "월 99,000원"
  }'

# 제품 목록 조회
curl http://localhost:8000/api/v1/brands/{brand_id}/products

# 제품 수정
curl -X PUT http://localhost:8000/api/v1/brands/{brand_id}/products/{product_id} \
  -H "Content-Type: application/json" \
  -d '{"price_range": "월 149,000원"}'

# 제품 삭제
curl -X DELETE http://localhost:8000/api/v1/brands/{brand_id}/products/{product_id}
```

### 영상 분석

```bash
# 영상 분석 시작
curl -X POST http://localhost:8000/api/v1/references/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/VIDEO_ID"}'

# 분석 결과 조회
curl http://localhost:8000/api/v1/references/{analysis_id}
```

### 분석 결과 예시

```json
{
  "analysis_id": "uuid",
  "status": "completed",
  "duration": 45.2,
  "segments": [
    {
      "start_time": 0.0,
      "end_time": 3.0,
      "segment_type": "hook",
      "visual_description": "빠른 줌인으로 제품 클로즈업",
      "engagement_score": 0.92,
      "techniques": ["pattern_interrupt", "curiosity_gap"]
    }
  ],
  "hook_points": [...],
  "selling_points": [...],
  "structure_pattern": "hook-problem-solution-proof-cta",
  "recommendations": [
    "처음 2초 내 핵심 질문으로 시작",
    "화면 전환 3초 이내 유지"
  ]
}
```

## 프로젝트 구조

```
ai-video-marketing/
├── frontend/                    # Next.js 14
│   ├── app/
│   │   ├── page.tsx            # 대시보드
│   │   ├── create/             # AI Content Factory
│   │   │   ├── page.tsx        # 6단계 마법사
│   │   │   └── edit/
│   │   │       └── page.tsx    # Canvas 텍스트 에디터
│   │   ├── references/         # 레퍼런스 라이브러리
│   │   │   └── page.tsx
│   │   ├── brands/             # 브랜드 관리
│   │   │   └── page.tsx
│   │   └── studio/             # Video Studio (레거시)
│   │       └── page.tsx
│   ├── components/
│   │   └── canvas/             # Canvas 에디터 컴포넌트
│   │       ├── CanvasTextEditor.tsx
│   │       ├── FabricCanvas.tsx
│   │       ├── TextToolbar.tsx
│   │       ├── LayerPanel.tsx
│   │       ├── CanvasExportPanel.tsx
│   │       ├── PlatformPresets.tsx
│   │       └── BatchExportModal.tsx
│   ├── __tests__/              # 테스트 파일
│   │   └── canvas/
│   └── lib/
│       └── api.ts              # API 클라이언트
├── backend/                     # FastAPI
│   ├── app/
│   │   ├── api/v1/             # API 엔드포인트
│   │   │   ├── brands.py       # 브랜드/제품 API
│   │   │   ├── references.py   # 레퍼런스 분석 API
│   │   │   ├── studio.py       # Video Studio API
│   │   │   └── health.py       # 헬스체크
│   │   ├── core/               # 설정
│   │   │   ├── config.py       # 환경설정
│   │   │   └── database.py     # DB 연결
│   │   ├── models/             # SQLAlchemy 모델
│   │   │   ├── brand.py
│   │   │   ├── product.py
│   │   │   └── reference_analysis.py
│   │   ├── schemas/            # Pydantic 스키마
│   │   │   ├── brand.py
│   │   │   └── studio.py
│   │   └── services/           # 비즈니스 로직
│   │       ├── brand_service.py
│   │       ├── product_service.py
│   │       ├── sns_parser.py           # SNS 링크 파싱
│   │       ├── sns_media_downloader.py # SNS 미디어 다운로드
│   │       ├── image_analyzer.py       # 이미지 분석
│   │       ├── content_image_analyzer.py
│   │       ├── image_prompt_builder.py # AI 프롬프트 생성
│   │       ├── batch_image_generator.py
│   │       ├── image_composite_generator.py
│   │       ├── image_editor.py         # 이미지 편집
│   │       ├── image_metadata.py       # 메타데이터
│   │       ├── reference_analyzer/     # 영상 분석
│   │       ├── video_generator/        # 영상 생성
│   │       └── brand_knowledge/        # RAG (예정)
│   └── alembic/                # DB 마이그레이션
│       └── versions/
├── docker/
│   └── docker-compose.yml
├── docs/                       # API 문서
│   ├── api/
│   └── architecture/
└── .moai/
    └── specs/                  # SPEC 문서
        ├── SPEC-CONTENT-FACTORY-001/
        ├── SPEC-001/
        └── SPEC-002/
```

## 데이터베이스 마이그레이션

```bash
cd backend

# 마이그레이션 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head

# 마이그레이션 롤백
alembic downgrade -1

# 현재 버전 확인
alembic current
```

## 환경 변수

```env
# .env 파일
GEMINI_API_KEY=your-gemini-api-key
DATABASE_URL=mysql+aiomysql://aivm:aivm_dev_password@localhost:3306/ai_video_marketing
REDIS_URL=redis://localhost:6379/0
DEBUG=true
```

## 라이선스

Private - 내부 사용 전용
