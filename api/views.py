from django.http import JsonResponse
from django.views import View
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
import json

from core.models import RSSFeed, RSSEntry, RSSProcessingLog
from crawler.tasks import crawl_rss_feed_task


class CrawlRSSView(View):
    """RSS 크롤링 실행 뷰"""
    
    def post(self, request):
        """RSS 크롤링 태스크 실행"""
        try:
            data = json.loads(request.body)
            feed_url = data.get('feed_url')
            
            if not feed_url:
                return JsonResponse({
                    'status': 'error',
                    'message': 'feed_url is required'
                }, status=400)
            
            # 비동기 태스크 실행
            task = crawl_rss_feed_task.delay(feed_url)
            
            return JsonResponse({
                'status': 'success',
                'task_id': task.id,
                'message': 'RSS crawling task started'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class RSSSummaryView(View):
    """RSS 요약 뷰"""
    
    def get(self, request):
        """RSS 요약 정보 반환"""
        try:
            # 기간별 통계
            today = timezone.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # 엔트리 통계
            today_entries = RSSEntry.objects.filter(published_at__date=today).count()
            week_entries = RSSEntry.objects.filter(published_at__date__gte=week_ago).count()
            month_entries = RSSEntry.objects.filter(published_at__date__gte=month_ago).count()
            
            # 키워드 통계
            keyword_stats = {}
            recent_entries = RSSEntry.objects.filter(
                published_at__date__gte=week_ago
            )
            
            for entry in recent_entries:
                for keyword in entry.keywords_list:
                    keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
            
            top_keywords = sorted(
                keyword_stats.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            # 피드별 통계
            feed_stats = recent_entries.values('feed__title').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            # 최근 처리 로그
            recent_logs = RSSProcessingLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).order_by('-created_at')[:5]
            
            summary = {
                'period_stats': {
                    'today': today_entries,
                    'this_week': week_entries,
                    'this_month': month_entries
                },
                'top_keywords': top_keywords,
                'top_feeds': list(feed_stats),
                'recent_logs': [
                    {
                        'feed_title': log.feed.title,
                        'status': log.status,
                        'entries_processed': log.entries_processed,
                        'entries_new': log.entries_new,
                        'created_at': log.created_at.isoformat()
                    }
                    for log in recent_logs
                ]
            }
            
            return JsonResponse({
                'status': 'success',
                'data': summary
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class RSSEntriesAPIView(View):
    """RSS 엔트리 API 뷰"""
    
    def get(self, request):
        """RSS 엔트리 목록을 JSON으로 반환"""
        try:
            # 쿼리 파라미터 처리
            feed_id = request.GET.get('feed')
            period = request.GET.get('period')
            keyword = request.GET.get('keyword')
            limit = int(request.GET.get('limit', 20))
            
            queryset = RSSEntry.objects.select_related('feed').order_by('-published_at')
            
            # 필터링
            if feed_id:
                queryset = queryset.filter(feed_id=feed_id)
            
            if period:
                today = timezone.now().date()
                if period == 'today':
                    queryset = queryset.filter(published_at__date=today)
                elif period == 'this_week':
                    week_ago = today - timedelta(days=7)
                    queryset = queryset.filter(published_at__date__gte=week_ago)
                elif period == 'this_month':
                    month_ago = today - timedelta(days=30)
                    queryset = queryset.filter(published_at__date__gte=month_ago)
            
            if keyword:
                queryset = queryset.filter(keywords__icontains=keyword)
            
            entries = queryset[:limit]
            
            # JSON 직렬화
            entries_data = [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'link': entry.link,
                    'description': entry.clean_description[:200] + '...' if len(entry.clean_description) > 200 else entry.clean_description,
                    'author': entry.author,
                    'published_at': entry.published_at.isoformat(),
                    'keywords': entry.keywords_list,
                    'feed': {
                        'id': entry.feed.id,
                        'title': entry.feed.title,
                        'url': entry.feed.url
                    },
                    'time_period': entry.get_time_period()
                }
                for entry in entries
            ]
            
            return JsonResponse({
                'status': 'success',
                'data': entries_data,
                'count': len(entries_data)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)


class RSSFeedsAPIView(View):
    """RSS 피드 API 뷰"""
    
    def get(self, request):
        """RSS 피드 목록을 JSON으로 반환"""
        try:
            feeds = RSSFeed.objects.filter(is_active=True).order_by('-created_at')
            
            feeds_data = [
                {
                    'id': feed.id,
                    'title': feed.title,
                    'url': feed.url,
                    'description': feed.description,
                    'is_active': feed.is_active,
                    'last_crawled_at': feed.last_crawled_at.isoformat() if feed.last_crawled_at else None,
                    'entry_count': feed.entries.count(),
                    'recent_entry_count': feed.get_recent_entries(7).count()
                }
                for feed in feeds
            ]
            
            return JsonResponse({
                'status': 'success',
                'data': feeds_data,
                'count': len(feeds_data)
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
