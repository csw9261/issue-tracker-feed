import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from django.test import TestCase
from django.utils import timezone as django_timezone

from rss_crawler.models import RSSFeed, RSSEntry
from rss_crawler.services import RSSCrawlerService
from rss_crawler.exceptions import RSSFeedError


class TestRSSCrawlerService(TestCase):
    """RSS 크롤러 서비스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.service = RSSCrawlerService()
        self.mock_feed_data = {
            'feed': {
                'title': 'TechCrunch',
                'link': 'https://techcrunch.com',
                'description': 'TechCrunch RSS Feed'
            },
            'entries': [
                {
                    'title': 'Test Article 1',
                    'link': 'https://techcrunch.com/test1',
                    'description': 'Test description 1',
                    'published': '2024-01-15T10:00:00Z',
                    'author': 'Test Author 1'
                },
                {
                    'title': 'Test Article 2',
                    'link': 'https://techcrunch.com/test2',
                    'description': 'Test description 2',
                    'published': '2024-01-15T11:00:00Z',
                    'author': 'Test Author 2'
                }
            ]
        }

    @patch('rss_crawler.services.feedparser')
    def test_crawl_rss_feed_success(self, mock_feedparser):
        """RSS 피드 크롤링 성공 테스트"""
        # Given
        mock_feed = Mock()
        mock_feed.bozo = 0
        mock_feed.feed = self.mock_feed_data['feed']
        mock_feed.entries = self.mock_feed_data['entries']
        mock_feedparser.parse.return_value = mock_feed

        # When
        result = self.service.crawl_rss_feed('https://techcrunch.com/feed/')

        # Then
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Test Article 1')
        self.assertEqual(result[1]['title'], 'Test Article 2')
        mock_feedparser.parse.assert_called_once_with('https://techcrunch.com/feed/')

    @patch('rss_crawler.services.feedparser')
    def test_crawl_rss_feed_invalid_feed(self, mock_feedparser):
        """잘못된 RSS 피드 처리 테스트"""
        # Given
        mock_feed = Mock()
        mock_feed.bozo = 1
        mock_feed.bozo_exception = Exception("Invalid RSS feed")
        mock_feedparser.parse.return_value = mock_feed

        # When & Then
        with self.assertRaises(RSSFeedError):
            self.service.crawl_rss_feed('https://invalid-feed.com/feed/')

    @patch('rss_crawler.services.feedparser')
    def test_crawl_rss_feed_network_error(self, mock_feedparser):
        """네트워크 오류 처리 테스트"""
        # Given
        mock_feedparser.parse.side_effect = Exception("Network error")

        # When & Then
        with self.assertRaises(RSSFeedError):
            self.service.crawl_rss_feed('https://techcrunch.com/feed/')

    def test_parse_entry_date_valid(self):
        """유효한 날짜 파싱 테스트"""
        # Given
        entry = {'published': '2024-01-15T10:00:00Z'}

        # When
        result = self.service._parse_entry_date(entry)

        # Then
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 15)

    def test_parse_entry_date_invalid(self):
        """잘못된 날짜 파싱 테스트"""
        # Given
        entry = {'published': 'invalid-date'}

        # When
        result = self.service._parse_entry_date(entry)

        # Then
        self.assertIsInstance(result, datetime)

    def test_clean_text(self):
        """텍스트 정제 테스트"""
        # Given
        dirty_text = '<p>Test <b>HTML</b> content</p>'

        # When
        result = self.service._clean_text(dirty_text)

        # Then
        self.assertEqual(result, 'Test HTML content')

    def test_extract_keywords(self):
        """키워드 추출 테스트"""
        # Given
        text = "AI artificial intelligence machine learning technology"

        # When
        result = self.service._extract_keywords(text)

        # Then
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)


class TestRSSFeedModel(TestCase):
    """RSS 피드 모델 테스트"""

    def test_rss_feed_creation(self):
        """RSS 피드 생성 테스트"""
        # Given & When
        feed = RSSFeed.objects.create(
            title='Test Feed',
            url='https://techcrunch.com/feed/',
            description='Test description'
        )

        # Then
        self.assertEqual(feed.title, 'Test Feed')
        self.assertEqual(feed.url, 'https://techcrunch.com/feed/')
        self.assertIsNotNone(feed.created_at)
        self.assertIsNotNone(feed.updated_at)

    def test_rss_feed_str_representation(self):
        """RSS 피드 문자열 표현 테스트"""
        # Given
        feed = RSSFeed.objects.create(
            title='Test Feed',
            url='https://techcrunch.com/feed/'
        )

        # When & Then
        self.assertEqual(str(feed), 'Test Feed')


class TestRSSEntryModel(TestCase):
    """RSS 엔트리 모델 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.feed = RSSFeed.objects.create(
            title='Test Feed',
            url='https://techcrunch.com/feed/'
        )

    def test_rss_entry_creation(self):
        """RSS 엔트리 생성 테스트"""
        # Given & When
        entry = RSSEntry.objects.create(
            feed=self.feed,
            title='Test Article',
            link='https://techcrunch.com/test',
            description='Test description',
            author='Test Author',
            published_at=django_timezone.now()
        )

        # Then
        self.assertEqual(entry.title, 'Test Article')
        self.assertEqual(entry.feed, self.feed)
        self.assertIsNotNone(entry.created_at)

    def test_rss_entry_str_representation(self):
        """RSS 엔트리 문자열 표현 테스트"""
        # Given
        entry = RSSEntry.objects.create(
            feed=self.feed,
            title='Test Article',
            link='https://techcrunch.com/test',
            published_at=django_timezone.now()
        )

        # When & Then
        self.assertEqual(str(entry), 'Test Article')

    def test_rss_entry_keywords(self):
        """RSS 엔트리 키워드 테스트"""
        # Given
        entry = RSSEntry.objects.create(
            feed=self.feed,
            title='Test Article',
            link='https://techcrunch.com/test',
            published_at=django_timezone.now()
        )
        entry.set_keywords(['AI', 'technology', 'innovation'])
        entry.save()

        # When & Then
        self.assertEqual(entry.keywords_list, ['AI', 'technology', 'innovation'])


class TestRSSFeedError(TestCase):
    """RSS 피드 오류 테스트"""

    def test_rss_feed_error_creation(self):
        """RSS 피드 오류 생성 테스트"""
        # Given & When
        error = RSSFeedError("Test error message")

        # Then
        self.assertEqual(str(error), "Test error message") 