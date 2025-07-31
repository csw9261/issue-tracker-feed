from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .services import RSSCrawlerService
from .models import RSSFeed, RSSProcessingLog


@shared_task(bind=True)
def crawl_rss_feed_task(self, feed_url: str = None):
    """
    RSS 피드를 크롤링하는 Celery 태스크
    
    Args:
        feed_url: 크롤링할 RSS 피드 URL
        
    Returns:
        처리 결과
    """
    try:
        service = RSSCrawlerService()
        log = service.crawl_and_save(feed_url)
        
        return {
            'status': 'success',
            'log_id': log.id,
            'entries_processed': log.entries_processed,
            'entries_new': log.entries_new,
            'processing_time': log.processing_time
        }
        
    except Exception as e:
        # 태스크 실패 시 로그 생성
        if feed_url:
            feed, _ = RSSFeed.objects.get_or_create(
                url=feed_url,
                defaults={'title': 'Unknown Feed'}
            )
            
            RSSProcessingLog.objects.create(
                feed=feed,
                status='error',
                entries_processed=0,
                entries_new=0,
                error_message=str(e),
                processing_time=0
            )
        
        # 태스크 재시도
        raise self.retry(countdown=60, max_retries=3)


@shared_task
def cleanup_old_entries_task():
    """
    오래된 RSS 엔트리를 정리하는 태스크
    """
    from datetime import timedelta
    
    # 30일 이상 된 엔트리 삭제
    cutoff_date = timezone.now() - timedelta(days=30)
    
    from .models import RSSEntry
    deleted_count = RSSEntry.objects.filter(
        published_at__lt=cutoff_date
    ).delete()[0]
    
    return {
        'status': 'success',
        'deleted_entries': deleted_count
    }


@shared_task
def generate_daily_summary_task():
    """
    일일 요약을 생성하는 태스크
    """
    from datetime import timedelta
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    from .models import RSSEntry
    
    # 어제 발행된 엔트리들 조회
    yesterday_entries = RSSEntry.objects.filter(
        published_at__date=yesterday
    ).order_by('-published_at')
    
    # 요약 생성
    summary = {
        'date': yesterday,
        'total_entries': yesterday_entries.count(),
        'top_keywords': [],
        'top_feeds': []
    }
    
    # 키워드 통계
    keyword_stats = {}
    for entry in yesterday_entries:
        for keyword in entry.keywords:
            keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1
    
    summary['top_keywords'] = sorted(
        keyword_stats.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    # 피드별 통계
    feed_stats = {}
    for entry in yesterday_entries:
        feed_name = entry.feed.title
        feed_stats[feed_name] = feed_stats.get(feed_name, 0) + 1
    
    summary['top_feeds'] = sorted(
        feed_stats.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    return summary


@shared_task
def health_check_task():
    """
    RSS 크롤러 상태를 확인하는 태스크
    """
    from .models import RSSFeed, RSSProcessingLog
    
    # 최근 24시간 내 처리 로그 확인
    yesterday = timezone.now() - timedelta(hours=24)
    recent_logs = RSSProcessingLog.objects.filter(
        created_at__gte=yesterday
    )
    
    # 활성 피드 수
    active_feeds = RSSFeed.objects.filter(is_active=True).count()
    
    # 성공/실패 통계
    success_count = recent_logs.filter(status='success').count()
    error_count = recent_logs.filter(status='error').count()
    
    health_status = {
        'active_feeds': active_feeds,
        'recent_logs': recent_logs.count(),
        'success_rate': success_count / max(recent_logs.count(), 1),
        'error_count': error_count,
        'last_check': timezone.now()
    }
    
    return health_status 