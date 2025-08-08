from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('crawl/', views.CrawlRSSView.as_view(), name='crawl-rss'),
    path('summary/', views.RSSSummaryView.as_view(), name='rss-summary'),
    path('entries/', views.RSSEntriesAPIView.as_view(), name='entries-api'),
    path('feeds/', views.RSSFeedsAPIView.as_view(), name='feeds-api'),
] 