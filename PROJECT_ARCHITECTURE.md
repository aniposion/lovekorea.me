# LoveKorea Blog - 프로젝트 기술 분석 문서

## 📋 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | LoveKorea Blog |
| **도메인** | https://lovekorea.me |
| **목적** | 한국 문화(K-드라마, K-뷰티, K-푸드, 한국어 학습 등)를 전 세계에 소개하는 블로그 |
| **기본 언어** | 영어 (English) |
| **콘텐츠 수** | 약 48개 포스트 |

---

## 🛠️ 기술 스택 (Tech Stack)

### 1. 정적 사이트 생성기 (Static Site Generator)

```
Hugo (Go 기반 SSG)
```

- **역할**: 마크다운(.md) 파일을 HTML로 변환하여 정적 웹사이트 생성
- **특징**: 
  - 매우 빠른 빌드 속도 (Go 언어 기반)
  - 템플릿 시스템 지원
  - 다국어 지원
  - 내장 에셋 파이프라인

### 2. 테마 (Theme)

```
PaperMod Theme
```

- **테마명**: PaperMod
- **특징**:
  - 미니멀하고 빠른 Hugo 테마
  - 다크/라이트 모드 자동 전환
  - SEO 최적화 내장
  - 반응형 디자인
  - 코드 하이라이팅 지원

### 3. 배포 플랫폼 (Deployment)

```
Netlify (JAMstack 호스팅)
```

- **역할**: 정적 사이트 호스팅 및 CI/CD
- **빌드 명령어**: `hugo --minify && npx pagefind --site public --output-path static/pagefind`
- **배포 방식**: Git push → 자동 빌드 → CDN 배포

### 4. 검색 기능 (Search)

```
Pagefind (정적 사이트 검색 라이브러리)
```

- **역할**: 클라이언트 사이드 전문 검색 기능
- **특징**:
  - 빌드 타임에 검색 인덱스 생성
  - JavaScript 기반 검색
  - 별도 서버 불필요

### 5. 댓글 시스템 (Comments)

```
Giscus (GitHub Discussions 기반)
```

- **저장소**: `aniposion/lovekorea_comments`
- **특징**:
  - GitHub Discussions 활용
  - 서버리스 댓글 시스템
  - GitHub 계정으로 인증

### 6. 분석 도구 (Analytics)

```
Google Analytics 4 (GA4)
```

- **추적 ID**: `G-2RHGK56598`
- **역할**: 방문자 트래픽 및 행동 분석

---

## 📁 프로젝트 디렉토리 구조

```
myblog/
├── archetypes/          # 새 콘텐츠 템플릿
├── assets/              # Hugo 에셋 파이프라인 리소스
├── content/             # 📝 마크다운 콘텐츠 (포스트, 페이지)
│   ├── posts/           # 블로그 포스트 (48개)
│   ├── k-beauty/        # K-뷰티 카테고리
│   ├── k-drama/         # K-드라마 카테고리
│   ├── k-food/          # K-푸드 카테고리
│   ├── k-music/         # K-뮤직 카테고리
│   ├── k-travel/        # K-여행 카테고리
│   ├── k-lifestyle/     # K-라이프스타일 카테고리
│   ├── learn-korean/    # 한국어 학습 카테고리
│   └── _index.md        # 홈페이지 콘텐츠
├── data/                # 데이터 파일 (JSON, YAML)
├── i18n/                # 다국어 번역 파일
├── layouts/             # 🎨 커스텀 레이아웃 템플릿
│   ├── _default/        # 기본 레이아웃 오버라이드
│   │   ├── list.html    # 목록 페이지 템플릿
│   │   └── summary.html # 요약 템플릿
│   ├── partials/        # 재사용 가능한 부분 템플릿
│   │   ├── head.html    # HTML <head> 섹션
│   │   ├── header.html  # 사이트 헤더
│   │   ├── search.html  # 검색 컴포넌트
│   │   └── comments.html# 댓글 컴포넌트
│   └── shortcodes/      # 커스텀 숏코드
├── public/              # 🏗️ 빌드 결과물 (배포용)
├── static/              # 📦 정적 파일
│   ├── images/          # 이미지 파일 (300+)
│   ├── css/custom.css   # 커스텀 CSS
│   ├── media/           # 미디어 파일 (오디오 등)
│   └── pagefind/        # 검색 인덱스 파일
├── themes/              # Hugo 테마
│   └── PaperMod/        # 현재 사용 중인 테마
├── hugo.toml            # ⚙️ Hugo 메인 설정 파일
├── netlify.toml         # Netlify 배포 설정
├── .netlify.toml        # Netlify 상세 설정 (헤더, 빌드)
└── Deploy.bat           # Windows 배포 스크립트
```

---

## ⚙️ 핵심 설정 파일 분석

### hugo.toml (메인 설정)

```toml
baseURL = "https://lovekorea.me/"
languageCode = "en"
title = "LoveKorea Blog"
theme = "PaperMod"
```

**주요 설정 항목:**

| 설정 | 값 | 설명 |
|------|------|------|
| `baseURL` | https://lovekorea.me/ | 사이트 기본 URL |
| `theme` | PaperMod | 사용 테마 |
| `defaultTheme` | auto | 다크/라이트 모드 자동 |
| `ShowToc` | true | 목차(TOC) 표시 |
| `ShowReadingTime` | true | 읽기 시간 표시 |
| `ShowShareButtons` | true | 공유 버튼 표시 |
| `comments` | giscus | 댓글 시스템 |

---

## 🎨 커스터마이징 영역

### 1. 커스텀 헤더 (`layouts/partials/header.html`)

```html
<header class="site-header">
  <div class="header-inner">
    <!-- 3열 그리드 레이아웃: 로고 - 메뉴 - 검색 -->
    <a href="/" class="site-title">LoveKorea</a>
    <nav class="main-nav">...</nav>
    <div class="header-right">{{ partial "search.html" . }}</div>
  </div>
</header>
```

**특징:**
- CSS Grid 기반 3열 레이아웃
- Sticky 헤더 (상단 고정)
- 반응형 디자인 (768px 브레이크포인트)
- 호버 애니메이션 (밑줄 효과)

### 2. 커스텀 Head (`layouts/partials/head.html`)

**포함 내용:**
- Google Analytics 추적 코드
- SEO 메타 태그 (description, keywords)
- Open Graph 이미지 설정
- Schema.org 구조화 데이터 (Article)
- Favicon 설정

### 3. 커스텀 목록 페이지 (`layouts/_default/list.html`)

**특징:**
- 그리드 기반 포스트 목록 (`.posts-grid`)
- 홈페이지 오디오 플레이어 내장
- Breadcrumb 네비게이션
- 페이지네이션 지원

---

## 📝 콘텐츠 구조 (Front Matter)

각 포스트는 다음과 같은 메타데이터를 포함합니다:

```yaml
---
title: "포스트 제목"
date: 2025-12-20T07:29:26.564887
slug: "url-slug"
description: "SEO 설명"
categories: ["k-lifestyle"]
tags: ["korea", "shopping", "travel"]
cover:
  image: "/images/cover-image.webp"
  alt: "이미지 설명"
  relative: true
---
```

**카테고리 목록:**
- `k-beauty` - K-뷰티
- `k-drama` - K-드라마
- `k-fashion` - K-패션
- `k-food` - K-푸드
- `k-lifestyle` - K-라이프스타일
- `k-movie` - K-영화
- `k-music` - K-뮤직
- `k-news` - K-뉴스
- `k-tech` - K-테크
- `k-travel` - K-여행
- `k-trends` - K-트렌드
- `learn-korean` - 한국어 학습

---

## 🔄 빌드 및 배포 프로세스

### 로컬 개발

```bash
# Hugo 개발 서버 실행
hugo server -D

# 프로덕션 빌드
hugo --minify
```

### Netlify 자동 배포

```
Git Push → Netlify Webhook 트리거
    ↓
빌드: hugo --minify
    ↓
Pagefind 검색 인덱스 생성
    ↓
CDN 배포 (전 세계 Edge 서버)
```

### Windows 수동 배포 (`Deploy.bat`)

```batch
git add .
git commit -m "YYYY-MM-DD deploy"
git push origin main
```

---

## 🛡️ 보안 및 성능 설정

### HTTP 헤더 (`.netlify.toml`)

```toml
[[headers]]
  for = "/*"
  [headers.values]
    Referrer-Policy = "strict-origin-when-cross-origin"
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "SAMEORIGIN"
```

### 캐싱 정책

| 리소스 유형 | Cache-Control |
|------------|---------------|
| CSS 파일 | `max-age=31536000, immutable` (1년) |
| JS 파일 | `max-age=31536000, immutable` (1년) |

### 에셋 핑거프린팅

```toml
[params.assets]
  disableFingerprinting = false
```
- CSS/JS 파일에 해시 기반 핑거프린트 추가
- 캐시 무효화 자동 처리

---

## 🔍 SEO 최적화

### 1. robots.txt
```
enableRobotsTXT = true
```

### 2. 구조화 데이터 (Schema.org)
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "포스트 제목",
  "datePublished": "발행일",
  "author": [{"@type":"Person","name":"LoveKorea"}]
}
```

### 3. Open Graph / Twitter Cards
- 자동 생성되는 소셜 미디어 메타 태그
- 커버 이미지 자동 연동

---

## 📊 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 브라우저                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Netlify CDN (Edge)                        │
│                    https://lovekorea.me                      │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   정적 HTML     │  │   Pagefind      │  │   Giscus        │
│   (Hugo 생성)    │  │   (검색 기능)    │  │   (댓글 시스템)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                                         │
         │                                         ▼
         │                              ┌─────────────────────┐
         │                              │  GitHub Discussions │
         │                              └─────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Google Analytics                        │
│                         (GA4 추적)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 JAMstack 아키텍처 장점

| 장점 | 설명 |
|------|------|
| **빠른 속도** | CDN에서 정적 파일 제공, 서버 렌더링 없음 |
| **높은 보안** | 서버사이드 코드 없음, 공격 표면 최소화 |
| **확장성** | CDN 자동 확장, 트래픽 급증에도 안정적 |
| **낮은 비용** | 서버 운영 불필요, 호스팅 비용 최소화 |
| **개발자 경험** | Git 기반 워크플로우, 마크다운 작성 |

---

## 📚 기술 스택 요약

```
┌────────────────────────────────────────────────────┐
│  프론트엔드      │  Hugo + PaperMod Theme           │
├────────────────────────────────────────────────────┤
│  스타일링        │  CSS (테마 내장 + 커스텀)         │
├────────────────────────────────────────────────────┤
│  검색           │  Pagefind (정적 검색)             │
├────────────────────────────────────────────────────┤
│  댓글           │  Giscus (GitHub Discussions)     │
├────────────────────────────────────────────────────┤
│  분석           │  Google Analytics 4              │
├────────────────────────────────────────────────────┤
│  호스팅         │  Netlify (CDN + CI/CD)           │
├────────────────────────────────────────────────────┤
│  버전 관리       │  Git + GitHub                    │
└────────────────────────────────────────────────────┘
```

---

## 🔧 AI 개발 시 참고사항

### 콘텐츠 추가 방법
1. `content/posts/` 디렉토리에 `.md` 파일 생성
2. Front Matter 작성 (title, date, categories, tags, cover)
3. 마크다운으로 본문 작성
4. 이미지는 `/static/images/`에 저장 후 참조

### 레이아웃 수정 방법
1. `layouts/` 디렉토리에서 테마 템플릿 오버라이드
2. Hugo 템플릿 문법 사용 (`{{ }}`)
3. Partial 템플릿으로 재사용 가능한 컴포넌트 분리

### 설정 변경 방법
1. `hugo.toml` 파일에서 사이트 전체 설정
2. `.netlify.toml`에서 배포 및 헤더 설정
3. `layouts/partials/head.html`에서 메타태그 수정

---

*이 문서는 LoveKorea Blog 프로젝트의 기술 구조를 분석하여 작성되었습니다.*
*최종 업데이트: 2025-12-24*
