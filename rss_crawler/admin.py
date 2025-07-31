from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import RSSFeed, RSSEntry, RSSProcessingLog


@admin.register(RSSFeed)
class RSSFeedAdmin(admin.ModelAdmin):
    """RSS 피드 관리자"""
    list_display = ['title', 'url', 'is_active', 'entry_count', 'last_crawled_at', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_crawled_at']
    search_fields = ['title', 'url', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_crawled_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('title', 'url', 'description', 'is_active')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at', 'last_crawled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def entry_count(self, obj):
        """엔트리 수 표시"""
        count = obj.entries.count()
        url = reverse('admin:rss_crawler_rssentry_changelist') + f'?feed__id__exact={obj.id}'
        return format_html('<a href="{}">{} 개</a>', url, count)
    entry_count.short_description = '엔트리 수'
    
    actions = ['activate_feeds', 'deactivate_feeds']
    
    def activate_feeds(self, request, queryset):
        """선택된 피드들을 활성화"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated}개의 피드가 활성화되었습니다.')
    activate_feeds.short_description = '선택된 피드 활성화'
    
    def deactivate_feeds(self, request, queryset):
        """선택된 피드들을 비활성화"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated}개의 피드가 비활성화되었습니다.')
    deactivate_feeds.short_description = '선택된 피드 비활성화'


@admin.register(RSSEntry)
class RSSEntryAdmin(admin.ModelAdmin):
    """RSS 엔트리 관리자"""
    list_display = ['title', 'feed', 'author', 'published_at', 'keyword_count', 'is_processed']
    list_filter = ['feed', 'is_processed', 'published_at', 'created_at']
    search_fields = ['title', 'description', 'author', 'keywords']
    readonly_fields = ['created_at', 'updated_at', 'clean_description_display']
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('feed', 'title', 'link', 'author', 'published_at')
        }),
        ('내용', {
            'fields': ('description', 'clean_description_display', 'keywords', 'summary')
        }),
        ('상태', {
            'fields': ('is_processed', 'created_at', 'updated_at')
        }),
    )
    
    def keyword_count(self, obj):
        """키워드 수 표시"""
        return len(obj.keywords_list)
    keyword_count.short_description = '키워드 수'
    
    def clean_description_display(self, obj):
        """정제된 설명 표시"""
        return mark_safe(f'<div style="max-height: 200px; overflow-y: auto;">{obj.clean_description}</div>')
    clean_description_display.short_description = '정제된 설명'
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    def mark_as_processed(self, request, queryset):
        """선택된 엔트리들을 처리 완료로 표시"""
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated}개의 엔트리가 처리 완료로 표시되었습니다.')
    mark_as_processed.short_description = '선택된 엔트리 처리 완료 표시'
    
    def mark_as_unprocessed(self, request, queryset):
        """선택된 엔트리들을 미처리로 표시"""
        updated = queryset.update(is_processed=False)
        self.message_user(request, f'{updated}개의 엔트리가 미처리로 표시되었습니다.')
    mark_as_unprocessed.short_description = '선택된 엔트리 미처리 표시'


@admin.register(RSSProcessingLog)
class RSSProcessingLogAdmin(admin.ModelAdmin):
    """RSS 처리 로그 관리자"""
    list_display = ['feed', 'status', 'entries_processed', 'entries_new', 'processing_time', 'created_at']
    list_filter = ['status', 'feed', 'created_at']
    search_fields = ['feed__title', 'error_message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('feed', 'status', 'created_at')
        }),
        ('처리 결과', {
            'fields': ('entries_processed', 'entries_new', 'processing_time')
        }),
        ('오류 정보', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """수동으로 로그를 추가할 수 없도록 설정"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """로그 수정을 금지"""
        return False
    
    actions = ['delete_selected_logs']
    
    def delete_selected_logs(self, request, queryset):
        """선택된 로그들을 삭제"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count}개의 로그가 삭제되었습니다.')
    delete_selected_logs.short_description = '선택된 로그 삭제' 