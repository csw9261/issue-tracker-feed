from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils import timezone

from core.models import RSSFeed, RSSEntry, RSSProcessingLog
from crawler.tasks import crawl_rss_feed_task, cleanup_old_entries_task, generate_daily_summary_task


class TestCrawlerTasks(TestCase):
    """Crawler 태스크 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.feed = RSSFeed.objects.create(
            title='Test Feed',
            url='https://techcrunch.com/feed/',
            description='Test description'
        )

    @patch('crawler.tasks.RSSCrawlerService')
    def test_crawl_rss_feed_task_success(self, mock_service_class):
        """RSS 크롤링 태스크 성공 테스트"""
        # Given
        mock_service = Mock()
        mock_log = Mock()
        mock_log.id = 1
        mock_log.entries_processed = 5
        mock_log.entries_new = 3
        mock_log.processing_time = 2.5
        mock_service.crawl_and_save.return_value = mock_log
        mock_service_class.return_value = mock_service

        # When
        result = crawl_rss_feed_task('https://techcrunch.com/feed/')

        # Then
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['log_id'], 1)
        self.assertEqual(result['entries_processed'], 5)
        self.assertEqual(result['entries_new'], 3)

    @patch('crawler.tasks.RSSCrawlerService')
    def test_crawl_rss_feed_task_failure(self, mock_service_class):
        """RSS 크롤링 태스크 실패 테스트"""
        # Given
        mock_service = Mock()
        mock_service.crawl_and_save.side_effect = Exception("Test error")
        mock_service_class.return_value = mock_service

        # When & Then
        with self.assertRaises(Exception):
            # Note: 실제 테스트에서는 Celery의 retry 메커니즘을 mock해야 함
            crawl_rss_feed_task('https://techcrunch.com/feed/')

    def test_cleanup_old_entries_task(self):
        """오래된 엔트리 정리 태스크 테스트"""
        # Given
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=35)
        
        # 오래된 엔트리 생성
        RSSEntry.objects.create(
            feed=self.feed,
            title='Old Article',
            link='https://test.com/old',
            published_at=old_date
        )
        
        # 최신 엔트리 생성
        RSSEntry.objects.create(
            feed=self.feed,
            title='New Article',
            link='https://test.com/new',
            published_at=timezone.now()
        )

        # When
        result = cleanup_old_entries_task()

        # Then
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['deleted_entries'], 1)
        self.assertEqual(RSSEntry.objects.count(), 1)  # 최신 엔트리만 남음

    def test_generate_daily_summary_task(self):
        """일일 요약 생성 태스크 테스트"""
        # Given
        from datetime import timedelta
        yesterday = timezone.now().date() - timedelta(days=1)
        
        entry = RSSEntry.objects.create(
            feed=self.feed,
            title='Yesterday Article',
            link='https://test.com/yesterday',
            published_at=timezone.datetime.combine(yesterday, timezone.datetime.min.time()),
            keywords='["AI", "technology"]'
        )

        # When
        result = generate_daily_summary_task()

        # Then
        self.assertEqual(result['date'], yesterday)
        self.assertEqual(result['total_entries'], 1)
        self.assertIsInstance(result['top_keywords'], list)
        self.assertIsInstance(result['top_feeds'], list) 