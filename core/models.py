from django.db import models
from django.utils import timezone
import json


class RSSFeed(models.Model):
    """RSS 피드 모델"""
    title = models.CharField(max_length=200, verbose_name="피드 제목")
    url = models.URLField(unique=True, verbose_name="RSS URL")
    description = models.TextField(blank=True, verbose_name="피드 설명")
    is_active = models.BooleanField(default=True, verbose_name="활성 상태")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    last_crawled_at = models.DateTimeField(null=True, blank=True, verbose_name="마지막 크롤링 시간")

    class Meta:
        verbose_name = "RSS 피드"
        verbose_name_plural = "RSS 피드들"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_recent_entries(self, days=7):
        """최근 N일간의 엔트리들을 반환"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.entries.filter(published_at__gte=cutoff_date)


class RSSEntry(models.Model):
    """RSS 엔트리 모델"""
    feed = models.ForeignKey(
        RSSFeed, 
        on_delete=models.CASCADE, 
        related_name='entries',
        verbose_name="RSS 피드"
    )
    title = models.CharField(max_length=500, verbose_name="제목")
    link = models.URLField(verbose_name="링크")
    description = models.TextField(blank=True, verbose_name="설명")
    author = models.CharField(max_length=200, blank=True, verbose_name="작성자")
    published_at = models.DateTimeField(verbose_name="발행일")
    keywords = models.TextField(
        blank=True,
        default='[]',
        verbose_name="키워드"
    )
    summary = models.TextField(blank=True, verbose_name="요약")
    is_processed = models.BooleanField(default=False, verbose_name="처리 완료")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "RSS 엔트리"
        verbose_name_plural = "RSS 엔트리들"
        ordering = ['-published_at']
        unique_together = ['feed', 'link']

    def __str__(self):
        return self.title

    def get_time_period(self):
        """엔트리의 시간대 분류 (오늘/이번주/이번달)"""
        now = timezone.now()
        published_date = self.published_at.date()
        today = now.date()
        
        if published_date == today:
            return 'today'
        elif published_date >= today - timezone.timedelta(days=7):
            return 'this_week'
        elif published_date >= today - timezone.timedelta(days=30):
            return 'this_month'
        else:
            return 'older'

    @property
    def clean_description(self):
        """HTML 태그가 제거된 깨끗한 설명"""
        import re
        clean_text = re.sub(r'<[^>]+>', '', self.description)
        return clean_text.strip()

    def get_keywords(self):
        """키워드 리스트 반환"""
        try:
            return json.loads(self.keywords)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_keywords(self, keywords_list):
        """키워드 리스트 설정"""
        self.keywords = json.dumps(keywords_list)

    @property
    def keywords_list(self):
        """키워드 리스트 프로퍼티"""
        return self.get_keywords()


class RSSProcessingLog(models.Model):
    """RSS 처리 로그 모델"""
    PROCESSING_STATUS_CHOICES = [
        ('success', '성공'),
        ('error', '오류'),
        ('partial', '부분 성공'),
    ]

    feed = models.ForeignKey(
        RSSFeed, 
        on_delete=models.CASCADE, 
        related_name='processing_logs',
        verbose_name="RSS 피드"
    )
    status = models.CharField(
        max_length=10, 
        choices=PROCESSING_STATUS_CHOICES,
        verbose_name="처리 상태"
    )
    entries_processed = models.IntegerField(default=0, verbose_name="처리된 엔트리 수")
    entries_new = models.IntegerField(default=0, verbose_name="새로운 엔트리 수")
    error_message = models.TextField(blank=True, verbose_name="오류 메시지")
    processing_time = models.FloatField(null=True, blank=True, verbose_name="처리 시간(초)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "RSS 처리 로그"
        verbose_name_plural = "RSS 처리 로그들"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.feed.title} - {self.get_status_display()} ({self.created_at})"
