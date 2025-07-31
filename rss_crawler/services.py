import feedparser
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
from django.utils import timezone as django_timezone
from django.conf import settings

from .exceptions import RSSFeedError, RSSProcessingError
from .models import RSSFeed, RSSEntry, RSSProcessingLog


class RSSCrawlerService:
    """RSS 크롤링 서비스"""

    def __init__(self):
        self.feed_url = getattr(settings, 'RSS_FEED_URL', 'https://techcrunch.com/feed/')

    def crawl_rss_feed(self, feed_url: str = None) -> List[Dict[str, Any]]:
        """
        RSS 피드를 크롤링하여 엔트리 목록을 반환
        
        Args:
            feed_url: 크롤링할 RSS 피드 URL
            
        Returns:
            처리된 RSS 엔트리 목록
            
        Raises:
            RSSFeedError: RSS 피드 처리 중 오류 발생 시
        """
        if feed_url is None:
            feed_url = self.feed_url

        try:
            # RSS 피드 파싱
            feed = feedparser.parse(feed_url)
            
            # RSS 피드 유효성 검사
            if feed.bozo:
                raise RSSFeedError(f"Invalid RSS feed: {feed.bozo_exception}")
            
            # 엔트리 처리
            processed_entries = []
            for entry in feed.entries:
                processed_entry = self._process_entry(entry)
                if processed_entry:
                    processed_entries.append(processed_entry)
            
            return processed_entries
            
        except Exception as e:
            raise RSSFeedError(f"Failed to crawl RSS feed: {str(e)}")

    def _process_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        RSS 엔트리를 처리하여 정제된 데이터로 변환
        
        Args:
            entry: 원본 RSS 엔트리
            
        Returns:
            처리된 엔트리 데이터
        """
        try:
            # 기본 정보 추출
            title = self._clean_text(entry.get('title', ''))
            link = entry.get('link', '')
            description = self._clean_text(entry.get('description', ''))
            author = entry.get('author', '')
            
            # 날짜 파싱
            published_at = self._parse_entry_date(entry)
            
            # 키워드 추출
            keywords = self._extract_keywords(f"{title} {description}")
            
            return {
                'title': title,
                'link': link,
                'description': description,
                'author': author,
                'published_at': published_at,
                'keywords': keywords
            }
            
        except Exception as e:
            # 개별 엔트리 처리 실패 시 로그만 남기고 계속 진행
            print(f"Failed to process entry: {str(e)}")
            return None

    def _parse_entry_date(self, entry: Dict[str, Any]) -> datetime:
        """
        RSS 엔트리의 날짜를 파싱
        
        Args:
            entry: RSS 엔트리
            
        Returns:
            파싱된 날짜 (실패 시 현재 시간 반환)
        """
        try:
            # 다양한 날짜 형식 지원
            date_fields = ['published', 'pubDate', 'updated']
            
            for field in date_fields:
                if field in entry and entry[field]:
                    # feedparser가 자동으로 파싱한 시간 사용
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    
                    # 문자열 날짜 파싱 시도
                    date_str = entry[field]
                    # 간단한 파싱 (실제로는 더 정교한 파싱이 필요)
                    try:
                        from dateutil import parser
                        return parser.parse(date_str)
                    except:
                        pass
            
            # 파싱 실패 시 현재 시간 반환
            return django_timezone.now()
            
        except Exception:
            return django_timezone.now()

    def _clean_text(self, text: str) -> str:
        """
        HTML 태그를 제거하고 텍스트를 정제
        
        Args:
            text: 정제할 텍스트
            
        Returns:
            정제된 텍스트
        """
        if not text:
            return ""
        
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # 여러 공백을 하나로 변환
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        텍스트에서 키워드를 추출
        
        Args:
            text: 키워드를 추출할 텍스트
            
        Returns:
            추출된 키워드 목록
        """
        if not text:
            return []
        
        # 간단한 키워드 추출 (실제로는 TF-IDF나 다른 알고리즘 사용)
        # 일반적인 기술 키워드들
        tech_keywords = [
            'AI', 'artificial intelligence', 'machine learning', 'ML',
            'blockchain', 'cryptocurrency', 'bitcoin', 'ethereum',
            'startup', 'venture capital', 'funding', 'investment',
            'technology', 'innovation', 'disruption', 'digital',
            'cloud', 'AWS', 'Azure', 'Google Cloud',
            'mobile', 'app', 'application', 'software',
            'cybersecurity', 'privacy', 'data', 'analytics',
            'fintech', 'healthtech', 'edtech', 'proptech'
        ]
        
        # 텍스트를 소문자로 변환
        text_lower = text.lower()
        
        # 키워드 매칭
        found_keywords = []
        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords[:10]  # 최대 10개 키워드만 반환

    def save_entries_to_db(self, feed: RSSFeed, entries: List[Dict[str, Any]]) -> RSSProcessingLog:
        """
        처리된 엔트리들을 데이터베이스에 저장
        
        Args:
            feed: RSS 피드 모델 인스턴스
            entries: 저장할 엔트리 목록
            
        Returns:
            처리 로그
        """
        start_time = time.time()
        processed_count = 0
        new_count = 0
        error_message = ""
        
        try:
            for entry_data in entries:
                try:
                    # 중복 체크
                    existing_entry = RSSEntry.objects.filter(
                        feed=feed,
                        link=entry_data['link']
                    ).first()
                    
                    if existing_entry:
                        # 기존 엔트리 업데이트
                        existing_entry.title = entry_data['title']
                        existing_entry.description = entry_data['description']
                        existing_entry.author = entry_data['author']
                        existing_entry.keywords = entry_data['keywords']
                        existing_entry.save()
                    else:
                        # 새 엔트리 생성
                        entry = RSSEntry.objects.create(
                            feed=feed,
                            title=entry_data['title'],
                            link=entry_data['link'],
                            description=entry_data['description'],
                            author=entry_data['author'],
                            published_at=entry_data['published_at']
                        )
                        entry.set_keywords(entry_data['keywords'])
                        entry.save()
                        new_count += 1
                    
                    processed_count += 1
                    
                except Exception as e:
                    error_message += f"Entry processing error: {str(e)}\n"
            
            # 피드 업데이트 시간 갱신
            feed.last_crawled_at = django_timezone.now()
            feed.save()
            
            # 처리 로그 생성
            processing_time = time.time() - start_time
            log = RSSProcessingLog.objects.create(
                feed=feed,
                status='success' if not error_message else 'partial',
                entries_processed=processed_count,
                entries_new=new_count,
                error_message=error_message,
                processing_time=processing_time
            )
            
            return log
            
        except Exception as e:
            # 전체 처리 실패 시 로그 생성
            processing_time = time.time() - start_time
            log = RSSProcessingLog.objects.create(
                feed=feed,
                status='error',
                entries_processed=processed_count,
                entries_new=new_count,
                error_message=str(e),
                processing_time=processing_time
            )
            raise RSSProcessingError(f"Failed to save entries: {str(e)}")

    def crawl_and_save(self, feed_url: str = None) -> RSSProcessingLog:
        """
        RSS 피드를 크롤링하고 데이터베이스에 저장
        
        Args:
            feed_url: 크롤링할 RSS 피드 URL
            
        Returns:
            처리 로그
        """
        if feed_url is None:
            feed_url = self.feed_url
        
        # RSS 피드 모델 가져오기 또는 생성
        feed, created = RSSFeed.objects.get_or_create(
            url=feed_url,
            defaults={
                'title': 'TechCrunch',
                'description': 'TechCrunch RSS Feed'
            }
        )
        
        # RSS 피드 크롤링
        entries = self.crawl_rss_feed(feed_url)
        
        # 데이터베이스에 저장
        return self.save_entries_to_db(feed, entries) 