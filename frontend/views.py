from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.utils import timezone
from datetime import timedelta

from core.models import RSSFeed, RSSEntry, RSSProcessingLog


class HomeView(ListView):
    """홈페이지 뷰 - 최신 뉴스와 요약 정보"""
    model = RSSEntry
    template_name = 'frontend/home.html'
    context_object_name = 'recent_entries'
    paginate_by = 10
    
    def get_queryset(self):
        return RSSEntry.objects.select_related('feed').order_by('-published_at')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 통계 정보 추가
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        context.update({
            'total_feeds': RSSFeed.objects.filter(is_active=True).count(),
            'today_entries': RSSEntry.objects.filter(published_at__date=today).count(),
            'week_entries': RSSEntry.objects.filter(published_at__date__gte=week_ago).count(),
            'active_feeds': RSSFeed.objects.filter(is_active=True)[:5]
        })
        
        return context


class RSSFeedListView(ListView):
    """RSS 피드 목록 뷰"""
    model = RSSFeed
    template_name = 'frontend/feed_list.html'
    context_object_name = 'feeds'
    
    def get_queryset(self):
        return RSSFeed.objects.filter(is_active=True).order_by('-created_at')


class RSSFeedDetailView(DetailView):
    """RSS 피드 상세 뷰"""
    model = RSSFeed
    template_name = 'frontend/feed_detail.html'
    context_object_name = 'feed'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_entries'] = self.object.entries.order_by('-published_at')[:10]
        context['processing_logs'] = self.object.processing_logs.order_by('-created_at')[:5]
        return context


class RSSEntryListView(ListView):
    """RSS 엔트리 목록 뷰"""
    model = RSSEntry
    template_name = 'frontend/entry_list.html'
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
    template_name = 'frontend/entry_detail.html'
    context_object_name = 'entry'


class RSSProcessingLogListView(ListView):
    """RSS 처리 로그 목록 뷰"""
    model = RSSProcessingLog
    template_name = 'frontend/log_list.html'
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


class DashboardView(ListView):
    """대시보드 뷰 - 요약 통계와 차트"""
    model = RSSEntry
    template_name = 'frontend/dashboard.html'
    context_object_name = 'entries'
    
    def get_queryset(self):
        # 최근 일주일간의 엔트리만 표시
        week_ago = timezone.now().date() - timedelta(days=7)
        return RSSEntry.objects.filter(
            published_at__date__gte=week_ago
        ).select_related('feed').order_by('-published_at')[:50]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # 기간별 통계
        context.update({
            'period_stats': {
                'today': RSSEntry.objects.filter(published_at__date=today).count(),
                'this_week': RSSEntry.objects.filter(published_at__date__gte=week_ago).count(),
                'this_month': RSSEntry.objects.filter(published_at__date__gte=month_ago).count(),
            },
            'feed_stats': RSSFeed.objects.filter(is_active=True).count(),
            'recent_logs': RSSProcessingLog.objects.order_by('-created_at')[:5]
        })
        
        # 키워드 통계
        keyword_stats = {}
        recent_entries = RSSEntry.objects.filter(published_at__date__gte=week_ago)
        for entry in recent_entries:
            for keyword in entry.keywords_list:
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
        
        top_keywords = sorted(keyword_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        context['top_keywords'] = top_keywords
        
        return context
