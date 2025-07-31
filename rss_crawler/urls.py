from django.urls import path
from . import views

app_name = 'rss_crawler'

urlpatterns = [
    path('feeds/', views.RSSFeedListView.as_view(), name='feed-list'),
    path('feeds/<int:pk>/', views.RSSFeedDetailView.as_view(), name='feed-detail'),
    path('entries/', views.RSSEntryListView.as_view(), name='entry-list'),
    path('entries/<int:pk>/', views.RSSEntryDetailView.as_view(), name='entry-detail'),
    path('crawl/', views.CrawlRSSView.as_view(), name='crawl-rss'),
    path('summary/', views.RSSSummaryView.as_view(), name='rss-summary'),
    path('logs/', views.RSSProcessingLogListView.as_view(), name='log-list'),
] 