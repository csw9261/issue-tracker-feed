from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('feeds/', views.RSSFeedListView.as_view(), name='feed-list'),
    path('feeds/<int:pk>/', views.RSSFeedDetailView.as_view(), name='feed-detail'),
    path('entries/', views.RSSEntryListView.as_view(), name='entry-list'),
    path('entries/<int:pk>/', views.RSSEntryDetailView.as_view(), name='entry-detail'),
    path('logs/', views.RSSProcessingLogListView.as_view(), name='log-list'),
] 