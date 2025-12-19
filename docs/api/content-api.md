# AI Content Factory API 문서

## 개요

AI Content Factory API는 SNS 마케팅 이미지 콘텐츠를 생성하고 관리하기 위한 RESTful API입니다.

## Base URL

```
http://localhost:8000/api/v1
```

---

## References API

레퍼런스 이미지 분석 및 관리를 위한 API 엔드포인트입니다.

### SNS 링크 분석

SNS 링크에서 이미지를 추출하고 분석합니다.

**Endpoint**: `POST /references/analyze-link`

**Request Body**:
```json
{
  "url": "https://www.instagram.com/p/..."
}
```

**Response**:
```json
{
  "id": "uuid-string",
  "type": "single",
  "source": "instagram",
  "source_url": "https://www.instagram.com/p/...",
  "thumbnail_url": "/storage/references/{id}/thumbnail.jpg",
  "analysis": {
    "composition": "중앙 집중",
    "colorScheme": "따뜻한 톤",
    "style": "미니멀",
    "elements": ["제품", "배경", "텍스트"]
  },
  "tags": [],
  "created_at": "2025-12-19T00:00:00Z"
}
```

**지원 플랫폼**:
- Instagram (instagram.com, www.instagram.com)
- Facebook (facebook.com, www.facebook.com)

**Error Responses**:
- `400 Bad Request`: 유효하지 않은 URL 형식
- `422 Unprocessable Entity`: 지원하지 않는 플랫폼
- `500 Internal Server Error`: 분석 실패

---

### 이미지 업로드 분석

업로드된 이미지를 분석합니다.

**Endpoint**: `POST /references/analyze-image`

**Content-Type**: `multipart/form-data`

**Request Parameters**:
- `file`: 이미지 파일 (JPEG, PNG, WebP)
- 최대 파일 크기: 50MB

**Response**:
```json
{
  "id": "uuid-string",
  "type": "single",
  "source": "upload",
  "source_url": null,
  "thumbnail_url": "/storage/references/{id}/thumbnail.jpg",
  "analysis": {
    "composition": "좌우 대칭",
    "colorScheme": "차가운 톤",
    "style": "모던",
    "elements": ["모델", "배경"]
  },
  "tags": [],
  "created_at": "2025-12-19T00:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: 지원하지 않는 파일 형식
- `413 Request Entity Too Large`: 파일 크기 초과 (50MB)
- `500 Internal Server Error`: 분석 실패

---

### 레퍼런스 목록 조회

저장된 레퍼런스 목록을 조회합니다.

**Endpoint**: `GET /references`

**Query Parameters**:
- `type` (optional): 필터링할 유형 (single, carousel, story)
- `source` (optional): 필터링할 소스 (instagram, facebook, upload)
- `limit` (optional): 결과 수 제한 (기본값: 20)
- `offset` (optional): 페이지네이션 오프셋 (기본값: 0)

**Response**:
```json
{
  "items": [
    {
      "id": "uuid-string",
      "type": "single",
      "source": "instagram",
      "thumbnail_url": "/storage/references/{id}/thumbnail.jpg",
      "created_at": "2025-12-19T00:00:00Z"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

---

### 레퍼런스 상세 조회

특정 레퍼런스의 상세 정보를 조회합니다.

**Endpoint**: `GET /references/{reference_id}`

**Path Parameters**:
- `reference_id`: 레퍼런스 UUID

**Response**:
```json
{
  "id": "uuid-string",
  "type": "single",
  "source": "instagram",
  "source_url": "https://www.instagram.com/p/...",
  "thumbnail_url": "/storage/references/{id}/thumbnail.jpg",
  "analysis": {
    "composition": "중앙 집중",
    "colorScheme": "따뜻한 톤",
    "style": "미니멀",
    "elements": ["제품", "배경", "텍스트"]
  },
  "brand_id": null,
  "tags": ["마케팅", "제품"],
  "created_at": "2025-12-19T00:00:00Z",
  "updated_at": "2025-12-19T00:00:00Z"
}
```

---

### 레퍼런스 삭제

레퍼런스를 삭제합니다.

**Endpoint**: `DELETE /references/{reference_id}`

**Path Parameters**:
- `reference_id`: 레퍼런스 UUID

**Response**: `204 No Content`

---

## Content Generation API

AI 이미지 생성을 위한 API 엔드포인트입니다.

### 이미지 생성 요청

AI를 통해 이미지를 생성합니다.

**Endpoint**: `POST /content/generate`

**Request Body**:
```json
{
  "type": "single",
  "purpose": "ad",
  "method": "prompt",
  "brand_id": "uuid-string",
  "product_id": "uuid-string",
  "reference_id": null,
  "prompt": "고급스러운 화장품 광고 이미지, 미니멀한 배경"
}
```

**Parameters**:
- `type`: 콘텐츠 유형 (single, carousel, story)
- `purpose`: 용도 (ad, info, lifestyle)
- `method`: 생성 방식 (reference, prompt)
- `brand_id` (optional): 브랜드 ID (광고/홍보인 경우)
- `product_id` (optional): 상품 ID
- `reference_id` (optional): 레퍼런스 ID (레퍼런스 방식인 경우)
- `prompt` (optional): 사용자 프롬프트 (직접 만들기인 경우)

**Response**:
```json
{
  "project_id": "uuid-string",
  "status": "generating",
  "created_at": "2025-12-19T00:00:00Z"
}
```

---

### 생성된 이미지 조회

생성된 이미지 목록을 조회합니다.

**Endpoint**: `GET /content/{project_id}/images`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Response**:
```json
{
  "project_id": "uuid-string",
  "status": "completed",
  "images": [
    {
      "id": "uuid-string",
      "variant_number": 1,
      "image_url": "/storage/projects/{project_id}/generated/variant_1.jpg",
      "thumbnail_url": "/storage/projects/{project_id}/generated/thumb_1.jpg",
      "is_selected": false
    },
    {
      "id": "uuid-string",
      "variant_number": 2,
      "image_url": "/storage/projects/{project_id}/generated/variant_2.jpg",
      "thumbnail_url": "/storage/projects/{project_id}/generated/thumb_2.jpg",
      "is_selected": false
    },
    {
      "id": "uuid-string",
      "variant_number": 3,
      "image_url": "/storage/projects/{project_id}/generated/variant_3.jpg",
      "thumbnail_url": "/storage/projects/{project_id}/generated/thumb_3.jpg",
      "is_selected": false
    },
    {
      "id": "uuid-string",
      "variant_number": 4,
      "image_url": "/storage/projects/{project_id}/generated/variant_4.jpg",
      "thumbnail_url": "/storage/projects/{project_id}/generated/thumb_4.jpg",
      "is_selected": false
    }
  ]
}
```

---

### 이미지 선택

편집할 이미지를 선택합니다.

**Endpoint**: `POST /content/{project_id}/select/{image_id}`

**Path Parameters**:
- `project_id`: 프로젝트 UUID
- `image_id`: 이미지 UUID

**Response**:
```json
{
  "success": true,
  "selected_image_id": "uuid-string"
}
```

---

## Canvas API

캔버스 에디터 상태 관리를 위한 API 엔드포인트입니다.

### 캔버스 상태 조회

저장된 캔버스 상태를 조회합니다.

**Endpoint**: `GET /content/{project_id}/canvas`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Response**:
```json
{
  "project_id": "uuid-string",
  "canvas_data": {
    "version": "5.3.0",
    "objects": [],
    "background": "#ffffff"
  },
  "updated_at": "2025-12-19T00:00:00Z"
}
```

---

### 캔버스 상태 저장

캔버스 상태를 저장합니다.

**Endpoint**: `PUT /content/{project_id}/canvas`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Request Body**:
```json
{
  "canvas_data": {
    "version": "5.3.0",
    "objects": [
      {
        "type": "textbox",
        "text": "Sample Text",
        "left": 100,
        "top": 100,
        "fontSize": 24,
        "fill": "#000000",
        "fontFamily": "Noto Sans KR"
      }
    ],
    "background": "#ffffff"
  }
}
```

**Response**:
```json
{
  "success": true,
  "updated_at": "2025-12-19T00:00:00Z"
}
```

---

## Export API

이미지 내보내기를 위한 API 엔드포인트입니다.

### 플랫폼별 내보내기

선택한 플랫폼에 최적화된 이미지를 내보냅니다.

**Endpoint**: `POST /content/{project_id}/export`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Request Body**:
```json
{
  "platforms": ["instagram_feed_1x1", "instagram_story"],
  "format": "jpeg",
  "quality": 90
}
```

**Parameters**:
- `platforms`: 내보낼 플랫폼 목록
  - `instagram_feed_1x1`: 1080x1080
  - `instagram_feed_4x5`: 1080x1350
  - `instagram_story`: 1080x1920
  - `facebook_feed_1x1`: 1200x1200
  - `facebook_feed_landscape`: 1200x630
- `format`: 출력 형식 (jpeg, png, webp)
- `quality` (optional): JPEG 품질 (1-100, 기본값: 90)

**Response**:
```json
{
  "outputs": [
    {
      "platform": "instagram_feed_1x1",
      "width": 1080,
      "height": 1080,
      "format": "jpeg",
      "url": "/storage/projects/{project_id}/outputs/instagram_feed_1080x1080.jpg"
    },
    {
      "platform": "instagram_story",
      "width": 1080,
      "height": 1920,
      "format": "jpeg",
      "url": "/storage/projects/{project_id}/outputs/instagram_story_1080x1920.jpg"
    }
  ]
}
```

---

### 출력물 목록 조회

생성된 출력물 목록을 조회합니다.

**Endpoint**: `GET /content/{project_id}/outputs`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Response**:
```json
{
  "outputs": [
    {
      "id": "uuid-string",
      "platform": "instagram_feed_1x1",
      "width": 1080,
      "height": 1080,
      "format": "jpeg",
      "output_url": "/storage/projects/{project_id}/outputs/instagram_feed_1080x1080.jpg",
      "created_at": "2025-12-19T00:00:00Z"
    }
  ]
}
```

---

### 전체 다운로드 (ZIP)

모든 출력물을 ZIP 파일로 다운로드합니다.

**Endpoint**: `GET /content/{project_id}/download`

**Path Parameters**:
- `project_id`: 프로젝트 UUID

**Response**: ZIP 파일 (application/zip)

**Headers**:
```
Content-Type: application/zip
Content-Disposition: attachment; filename="content_{project_id}.zip"
```

---

## 플랫폼 프리셋

지원되는 플랫폼별 이미지 크기 프리셋입니다.

### Instagram

- **Feed 1:1**: 1080x1080 (정사각형)
- **Feed 4:5**: 1080x1350 (세로형)
- **Story**: 1080x1920 (9:16)
- **Reel Cover**: 1080x1920 (9:16)

### Facebook

- **Feed 1:1**: 1200x1200 (정사각형)
- **Feed 1.91:1**: 1200x630 (가로형)
- **Cover**: 820x312

### 일반

- **HD**: 1920x1080 (16:9)
- **Square HD**: 1080x1080

---

## 에러 응답

모든 API는 다음 형식의 에러 응답을 반환합니다:

```json
{
  "detail": "에러 메시지",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-12-19T00:00:00Z"
}
```

### 공통 에러 코드

- `400 Bad Request`: 잘못된 요청 형식
- `401 Unauthorized`: 인증 필요
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `413 Request Entity Too Large`: 파일 크기 초과
- `422 Unprocessable Entity`: 유효성 검사 실패
- `500 Internal Server Error`: 서버 내부 오류

---

**문서 버전**: 1.0.0
**최종 수정일**: 2025-12-19
