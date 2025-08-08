from django.urls import path
from api.views import CrawlRSSView

app_name = 'crawler'

urlpatterns = [
    # 크롤링 관리용 URL (API와 동일한 뷰 재사용)
    path('start/', CrawlRSSView.as_view(), name='start-crawling'),
] 