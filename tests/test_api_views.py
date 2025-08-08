import json
from unittest.mock import patch, Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models import RSSFeed, RSSEntry, RSSProcessingLog


class TestAPIViews(TestCase):
    """API 뷰 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.client = Client()
        self.feed = RSSFeed.objects.create(
            title='Test Feed',
            url='https://techcrunch.com/feed/',
            description='Test description'
        )
        self.entry = RSSEntry.objects.create(
            feed=self.feed,
            title='Test Article',
            link='https://techcrunch.com/test',
            description='Test description',
            author='Test Author',
            published_at=timezone.now()
        )

    def test_rss_summary_view_get(self):
        """RSS 요약 API 테스트"""
        # When
        response = self.client.get('/api/summary/')

        # Then
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('period_stats', data['data'])

    def test_rss_feeds_api_view_get(self):
        """RSS 피드 API 테스트"""
        # When
        response = self.client.get('/api/feeds/')

        # Then
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['title'], 'Test Feed')

    def test_rss_entries_api_view_get(self):
        """RSS 엔트리 API 테스트"""
        # When
        response = self.client.get('/api/entries/')

        # Then
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['title'], 'Test Article')

    def test_rss_entries_api_view_with_filters(self):
        """필터링된 RSS 엔트리 API 테스트"""
        # When
        response = self.client.get('/api/entries/?period=today&limit=5')

        # Then
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')

    @patch('api.views.crawl_rss_feed_task')
    def test_crawl_rss_view_post_success(self, mock_task):
        """RSS 크롤링 API 성공 테스트"""
        # Given
        mock_task.delay.return_value = Mock(id='test-task-id')
        
        # When
        response = self.client.post(
            '/api/crawl/',
            data=json.dumps({'feed_url': 'https://techcrunch.com/feed/'}),
            content_type='application/json'
        )

        # Then
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['task_id'], 'test-task-id')

    def test_crawl_rss_view_post_missing_url(self):
        """RSS 크롤링 API URL 누락 테스트"""
        # When
        response = self.client.post(
            '/api/crawl/',
            data=json.dumps({}),
            content_type='application/json'
        )

        # Then
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'feed_url is required')

    def test_crawl_rss_view_post_invalid_json(self):
        """RSS 크롤링 API 잘못된 JSON 테스트"""
        # When
        response = self.client.post(
            '/api/crawl/',
            data='invalid json',
            content_type='application/json'
        )

        # Then
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid JSON') 