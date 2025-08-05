# TechCrunch RSS 이슈 트래커

TechCrunch RSS를 크롤링하여 오늘/이번주/이번달 등의 이슈를 정리하고 시각화하는 시스템

## 🎯 프로젝트 목표

- **RSS 크롤링**: TechCrunch RSS를 주기적으로 수집
- **이슈 분류**: 날짜 기준으로 오늘/이번주/이번달 분류
- **뉴스 요약**: 제목, 본문 요약, 키워드 분석
- **시각화 대시보드**: 사용자용 뉴스 피드 웹 UI
- **알림 시스템**: 매일 지정 시간에 알림 전송
- **자동 실행**: Celery로 주기적 작업 실행

## 🏗️ 아키텍처

```
[Django Web Server]
       │
       ├─▶ [비동기 RSS 크롤러 프로세스] ──────▶ pipe ─────▶ [데이터 수집기/저장기]
       │                                        (별도 프로세스)
       │
       └─▶ 사용자 요청 처리 (API, DB 등)
```

## 📁 프로젝트 구조

```
issue-tracker-feed/
├── issue_tracker/                 # Django 프로젝트 설정
│   ├── __init__.py
│   ├── settings.py               # Django 설정 (PostgreSQL, Celery)
│   ├── urls.py                   # 메인 URL 설정
│   ├── wsgi.py                   # WSGI 설정
│   └── celery.py                 # Celery 설정
├── rss_crawler/                  # RSS 크롤러 앱
│   ├── __init__.py
│   ├── apps.py                   # 앱 설정
│   ├── models.py                 # 데이터베이스 모델
│   ├── services.py               # RSS 크롤링 서비스
│   ├── tasks.py                  # Celery 태스크
│   ├── views.py                  # API 뷰
│   ├── urls.py                   # 앱 URL 설정
│   ├── admin.py                  # Django 관리자
│   └── exceptions.py             # 커스텀 예외
├── tests/                        # 테스트 파일
│   └── test_rss_crawler.py      # RSS 크롤러 테스트
├── venv/                         # Python 가상환경
├── manage.py                     # Django 관리 명령어
├── requirements.txt              # Python 의존성
├── pytest.ini                   # pytest 설정
├── docker-compose.yml           # Docker 서비스 설정
└── README.md                    # 프로젝트 문서
```

## 🗄️ 데이터베이스 모델

### RSSFeed (RSS 피드)
- `title`: 피드 제목
- `url`: RSS URL
- `description`: 피드 설명
- `is_active`: 활성 상태
- `last_crawled_at`: 마지막 크롤링 시간

### RSSEntry (RSS 엔트리)
- `feed`: RSS 피드 (ForeignKey)
- `title`: 기사 제목
- `link`: 기사 링크
- `description`: 기사 설명
- `author`: 작성자
- `published_at`: 발행일
- `keywords`: 키워드 (JSON)
- `summary`: 요약
- `is_processed`: 처리 완료 여부

### RSSProcessingLog (처리 로그)
- `feed`: RSS 피드 (ForeignKey)
- `status`: 처리 상태 (success/error/partial)
- `entries_processed`: 처리된 엔트리 수
- `entries_new`: 새로운 엔트리 수
- `processing_time`: 처리 시간

## 🛠️ 기술 스택

| 구성 요소 | 사용 기술 | 상태 |
|---------|---------|------|
| 크롤러 | Python + Feedparser | ✅ 완료 |
| 백엔드 | Django | ✅ 완료 |
| DB | PostgreSQL (Docker) | ✅ 완료 |
| 큐 | Redis (Docker) | ✅ 완료 |
| 스케줄러 | Celery Beat | ✅ 완료 |
| 테스트 | pytest | ✅ 완료 |
| 검색 | Elasticsearch | 🔄 진행 예정 |
| 알림 | Slack API | 🔄 진행 예정 |
| 배포 | Docker | 🔄 진행 예정 |

## 🚀 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt
```

### 2. 데이터베이스 실행
```bash
# PostgreSQL과 Redis 컨테이너 실행
docker-compose up -d
```

### 3. Django 설정
```bash
# 마이그레이션 생성 및 적용
python manage.py makemigrations
python manage.py migrate

# 슈퍼유저 생성
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

### 4. Celery 실행
```bash
# Celery 워커 실행
celery -A issue_tracker worker -l info

# Celery Beat 실행 (스케줄러)
celery -A issue_tracker beat -l info
```

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=rss_crawler

# 특정 테스트 실행
pytest tests/test_rss_crawler.py::TestRSSCrawlerService::test_crawl_rss_feed_success
```

## 📊 API 엔드포인트

- `GET /api/feeds/` - RSS 피드 목록
- `GET /api/entries/` - RSS 엔트리 목록
- `GET /api/summary/` - RSS 요약 정보
- `POST /api/crawl/` - RSS 크롤링 실행
- `GET /api/logs/` - 처리 로그 목록

## 🔄 진행 상황

### ✅ 완료된 기능
- [x] Django 프로젝트 설정
- [x] RSS 크롤러 모델 설계
- [x] RSS 크롤링 서비스 구현
- [x] Celery 태스크 구현
- [x] API 뷰 구현
- [x] Docker 설정 (PostgreSQL, Redis)
- [x] 단위 테스트 작성
- [x] Django 관리자 설정

### 🔄 진행 중인 기능
- [ ] 템플릿 및 프론트엔드 구현
- [ ] Elasticsearch 검색 기능
- [ ] 알림 시스템 (Slack/Email)
- [ ] 대시보드 시각화

### 📋 예정된 기능
- [ ] MCP 서버 구축
- [ ] 뉴스 요약 AI 기능
- [ ] 키워드 분석 고도화
- [ ] 사용자 인증 시스템
- [ ] 모바일 반응형 UI
- [ ] 성능 모니터링
- [ ] CI/CD 파이프라인

## 🐛 문제 해결

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
