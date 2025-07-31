from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import json

from .models import RSSFeed, RSSEntry, RSSProcessingLog
from .services import RSSCrawlerService
from .tasks import crawl_rss_feed_task


class RSSFeedListView(ListView):
    """RSS 피드 목록 뷰"""
    model = RSSFeed
    template_name = 'rss_crawler/feed_list.html'
    context_object_name = 'feeds'
    
    def get_queryset(self):
        return RSSFeed.objects.filter(is_active=True).order_by('-created_at')


class RSSFeedDetailView(DetailView):
    """RSS 피드 상세 뷰"""
    model = RSSFeed
    template_name = 'rss_crawler/feed_detail.html'
    context_object_name = 'feed'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_entries'] = self.object.entries.order_by('-published_at')[:10]
        context['processing_logs'] = self.object.processing_logs.order_by('-created_at')[:5]
        return context


class RSSEntryListView(ListView):
    """RSS 엔트리 목록 뷰"""
    model = RSSEntry
    template_name = 'rss_crawler/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = RSSEntry.objects.select_related('feed').order_by('-published_at')
        
        # 필터링
        feed_id = self.request.GET.get('feed')
        if feed_id:
            queryset = queryset.filter(feed_id=feed_id)
        
        period = self.request.GET.get('period')
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
        
        keyword = self.request.GET.get('keyword')
        if keyword:
            queryset = queryset.filter(keywords__icontains=keyword)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feeds'] = RSSFeed.objects.filter(is_active=True)
        context['periods'] = [
            ('today', '오늘'),
            ('this_week', '이번 주'),
            ('this_month', '이번 달'),
        ]
        return context


class RSSEntryDetailView(DetailView):
    """RSS 엔트리 상세 뷰"""
    model = RSSEntry
    template_name = 'rss_crawler/entry_detail.html'
    context_object_name = 'entry'


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


class RSSProcessingLogListView(ListView):
    """RSS 처리 로그 목록 뷰"""
    model = RSSProcessingLog
    template_name = 'rss_crawler/log_list.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        return RSSProcessingLog.objects.select_related('feed').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 통계 정보
        total_logs = RSSProcessingLog.objects.count()
        success_logs = RSSProcessingLog.objects.filter(status='success').count()
        error_logs = RSSProcessingLog.objects.filter(status='error').count()
        
        context['stats'] = {
            'total': total_logs,
            'success': success_logs,
            'error': error_logs,
            'success_rate': success_logs / max(total_logs, 1) * 100
        }
        
        return context 