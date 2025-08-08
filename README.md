# 🚀 TechCrunch RSS 이슈 트래커

TechCrunch RSS를 자동으로 크롤링하여 뉴스 이슈를 수집, 분석, 시각화하는 **기능별 분리 구조**의 Django 웹 애플리케이션

## ✨ 주요 특징

- 🕷️ **자동 RSS 크롤링**: TechCrunch 피드를 주기적으로 수집
- 📊 **스마트 분류**: 날짜별 (오늘/이번주/이번달) 자동 분류  
- 🔍 **키워드 분석**: AI, 블록체인, 스타트업 등 기술 키워드 자동 추출
- 🎨 **웹 대시보드**: 직관적인 사용자 인터페이스
- 🔌 **REST API**: 프로그래밍 인터페이스 제공
- ⚡ **비동기 처리**: Celery를 통한 백그라운드 작업
- 📈 **실시간 통계**: 처리 현황 및 트렌드 모니터링

## 🏗️ 아키텍처 개요

### 기능별 분리 구조 (Modular Architecture)

```
┌─ 🎨 Frontend (웹 인터페이스)     ┌─ 🔌 API (JSON 엔드포인트)
│  ├─ 홈페이지 & 대시보드          │  ├─ 피드/엔트리 API
│  ├─ 뉴스 목록 & 상세 페이지      │  ├─ 통계 요약 API  
│  └─ 처리 로그 모니터링           │  └─ 크롤링 실행 API
│                                 │
└─ 📊 Core (공통 데이터)          └─ 🕷️ Crawler (백그라운드)
   ├─ RSSFeed 모델                   ├─ RSS 크롤링 서비스
   ├─ RSSEntry 모델                  ├─ 데이터 정제 & 키워드 추출
   └─ RSSProcessingLog 모델          └─ Celery 백그라운드 태스크
```

### 데이터 플로우

```
TechCrunch RSS → 🕷️ Crawler → 📊 Core → { 🎨 Frontend
                                           🔌 API     }
     ↑                                         ↓
[Celery Beat] ←─────── Redis ←─────── 사용자 요청
```

## 📁 프로젝트 구조

```
issue-tracker-feed/
├── 📊 core/                    # 공통 데이터 모델
│   ├── models.py              # RSSFeed, RSSEntry, RSSProcessingLog
│   └── admin.py               # Django 관리자 설정
├── 🎨 frontend/               # 웹 사용자 인터페이스  
│   ├── views.py               # HTML 뷰 (홈, 대시보드, 목록)
│   ├── urls.py                # 웹페이지 URL 라우팅
│   └── templates/             # HTML 템플릿 (예정)
├── 🔌 api/                    # REST API 엔드포인트
│   ├── views.py               # JSON API 뷰
│   └── urls.py                # API URL 라우팅  
├── 🕷️ crawler/                # RSS 크롤링 & 백그라운드
│   ├── services.py            # RSS 크롤링 서비스
│   ├── tasks.py               # Celery 백그라운드 태스크
│   ├── exceptions.py          # 커스텀 예외
│   └── urls.py                # 크롤링 관리 URL
├── ⚙️ issue_tracker/          # Django 프로젝트 설정
│   ├── settings.py            # 데이터베이스, Celery 설정
│   ├── urls.py                # 메인 URL 라우팅
│   └── celery.py              # Celery 설정
├── 🧪 tests/                  # 테스트 코드
│   ├── test_core_models.py    # 모델 & 서비스 테스트
│   ├── test_api_views.py      # API 엔드포인트 테스트
│   └── test_crawler_tasks.py  # Celery 태스크 테스트
├── 🐳 docker-compose.yml      # PostgreSQL & Redis 설정
├── 📋 requirements.txt        # Python 의존성
└── 📖 README.md              # 프로젝트 문서
```

## 🌐 URL 구조

### 웹 사용자 인터페이스 (Frontend)
```
http://localhost:8000/              # 🏠 홈페이지
http://localhost:8000/dashboard/    # 📊 대시보드  
http://localhost:8000/feeds/        # 📋 RSS 피드 목록
http://localhost:8000/feeds/1/      # 📄 피드 상세 페이지
http://localhost:8000/entries/      # 📰 뉴스 기사 목록
http://localhost:8000/entries/1/    # 📄 기사 상세 페이지
http://localhost:8000/logs/         # 📋 처리 로그 목록
```

### REST API 엔드포인트 (API)
```
http://localhost:8000/api/feeds/    # 📋 피드 목록 (JSON)
http://localhost:8000/api/entries/  # 📰 기사 목록 (JSON)  
http://localhost:8000/api/summary/  # 📊 요약 통계 (JSON)
http://localhost:8000/api/crawl/    # 🕷️ 크롤링 실행 (POST)
```

### 관리 인터페이스
```
http://localhost:8000/admin/           # ⚙️ Django 관리자
http://localhost:8000/crawler/start/   # 🕷️ 크롤링 관리
```

## 🚀 설치 및 실행

### 1. 프로젝트 클론 & 환경 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd issue-tracker-feed

# 가상환경 생성 및 활성화 (Windows)
python -m venv venv
.\venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 & Redis 실행

```bash
# Docker로 PostgreSQL & Redis 시작
docker-compose up -d

# 또는 개별 실행
docker run -d --name rss_postgres -p 5432:5432 \
  -e POSTGRES_DB=issue_tracker_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=1234 \
  postgres:15.5

docker run -d --name rss_redis -p 6379:6379 redis:7.2-alpine
```

### 3. Django 애플리케이션 설정

```bash
# 데이터베이스 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성 (선택사항)
python manage.py createsuperuser
```

### 4. 서비스 실행

**터미널 1 - Django 웹 서버**
```bash
python manage.py runserver
# → http://localhost:8000 접속 가능
```

**터미널 2 - Celery Worker (백그라운드 처리)**
```bash
celery -A issue_tracker worker --loglevel=info
```

**터미널 3 - Celery Beat (스케줄러)**
```bash
celery -A issue_tracker beat --loglevel=info
```

## 📊 데이터 모델

### RSSFeed (RSS 피드)
- `title`: 피드 제목
- `url`: RSS URL  
- `description`: 피드 설명
- `is_active`: 활성 상태
- `last_crawled_at`: 마지막 크롤링 시간

### RSSEntry (뉴스 기사)
- `feed`: RSS 피드 (ForeignKey)
- `title`: 기사 제목
- `link`: 기사 링크
- `description`: 기사 설명
- `author`: 작성자
- `published_at`: 발행일
- `keywords`: 키워드 (JSON)
- `summary`: 요약

### RSSProcessingLog (처리 로그)
- `feed`: RSS 피드 (ForeignKey)
- `status`: 처리 상태 (success/error/partial)
- `entries_processed`: 처리된 엔트리 수
- `entries_new`: 새로운 엔트리 수
- `processing_time`: 처리 시간

## 🔧 API 사용법

### RSS 크롤링 실행
```bash
curl -X POST http://localhost:8000/api/crawl/ \
  -H "Content-Type: application/json" \
  -d '{"feed_url": "https://techcrunch.com/feed/"}'
```

### 뉴스 목록 조회 (필터링)
```bash
# 오늘 뉴스만
curl "http://localhost:8000/api/entries/?period=today"

# 키워드 필터링  
curl "http://localhost:8000/api/entries/?keyword=AI"

# 특정 피드의 뉴스
curl "http://localhost:8000/api/entries/?feed=1&limit=10"
```

### 요약 통계 조회
```bash
curl http://localhost:8000/api/summary/
```

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=core --cov=api --cov=crawler --cov=frontend

# 특정 앱 테스트
pytest tests/test_core_models.py
pytest tests/test_api_views.py
pytest tests/test_crawler_tasks.py
```

## 🛠️ 기술 스택

| 구성 요소 | 기술 | 버전 |
|----------|------|------|
| **백엔드** | Django | 4.2.7 |
| **데이터베이스** | PostgreSQL | 15.5 |
| **캐시/큐** | Redis | 7.2 |
| **비동기 작업** | Celery | 5.3.4 |
| **RSS 파싱** | feedparser | 6.0.10 |
| **테스트** | pytest | 7.4.3 |
| **컨테이너** | Docker | latest |

## ⚙️ 설정

### 주요 설정 값 (settings.py)
```python
# RSS 크롤링 설정
RSS_FEED_URL = 'https://techcrunch.com/feed/'
RSS_CRAWL_INTERVAL = 3600  # 1시간마다

# Celery 설정
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'

# 데이터베이스
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'issue_tracker_db',
        'USER': 'postgres',
        'PASSWORD': '1234',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

## 📈 모니터링

### 처리 현황 확인
- **웹 대시보드**: http://localhost:8000/dashboard/
- **처리 로그**: http://localhost:8000/logs/
- **API 통계**: http://localhost:8000/api/summary/

### Celery 모니터링
```bash
# Celery 상태 확인
celery -A issue_tracker inspect active

# 태스크 통계
celery -A issue_tracker inspect stats
```

## 🔄 백그라운드 태스크

### 자동 실행 태스크
- **RSS 크롤링**: 1시간마다 자동 실행
- **데이터 정리**: 30일 이상 된 기사 삭제
- **일일 요약**: 매일 전날 뉴스 요약 생성
- **헬스체크**: 시스템 상태 모니터링

## 🚧 개발 로드맵

### ✅ 완료된 기능
- [x] 기능별 앱 분리 (core, frontend, api, crawler)
- [x] RSS 크롤링 및 데이터 정제
- [x] 키워드 자동 추출
- [x] REST API 엔드포인트
- [x] Celery 백그라운드 태스크
- [x] 종합 테스트 코드

### 🔄 진행 중
- [ ] HTML 템플릿 및 프론트엔드 UI
- [ ] Docker 개발 환경 구성

<<<<<<< HEAD
### 📋 계획된 기능
- [ ] 사용자 인증 및 권한 관리
- [ ] 다중 RSS 피드 지원
- [ ] 고급 키워드 분석 (TF-IDF, NLP)
- [ ] 알림 시스템 (이메일, Slack)
- [ ] 관리자 대시보드 개선
- [ ] 성능 최적화 및 캐싱
=======
### 📋 예정된 기능
- [ ] MCP 서버 구축
- [ ] 뉴스 요약 AI 기능
- [ ] 키워드 분석 고도화
- [ ] 사용자 인증 시스템
- [ ] 모바일 반응형 UI
- [ ] 성능 모니터링
- [ ] CI/CD 파이프라인
>>>>>>> 27c30292bca461c4b48d439490d0775f5a20168b

---

<<<<<<< HEAD
**🚀 TechCrunch RSS 이슈 트래커로 기술 뉴스를 체계적으로 관리하세요!**
=======
### PostgreSQL 연결 오류
```bash
# 컨테이너 상태 확인
docker-compose ps

# 컨테이너 재시작
docker-compose restart postgres
```

### Celery 연결 오류
```bash
# Redis 컨테이너 확인
docker-compose ps redis

# Celery 재시작
celery -A issue_tracker worker --loglevel=info
```

## 📝 개발 노트

### TDD 방식으로 개발
1. 테스트 작성 (`tests/test_rss_crawler.py`)
2. 기능 구현 (`rss_crawler/services.py`)
3. 테스트 통과 확인
4. 리팩토링

### 다음 단계
1. 프론트엔드 템플릿 구현
2. Elasticsearch 검색 기능 추가
3. 알림 시스템 구현
4. 성능 최적화

## 🤝 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 
>>>>>>> 27c30292bca461c4b48d439490d0775f5a20168b
