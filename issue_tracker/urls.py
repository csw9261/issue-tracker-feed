"""issue_tracker URL Configuration"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('frontend.urls')),           # 웹 페이지 (HTML)
    path('api/', include('api.urls')),            # REST API (JSON)
    path('crawler/', include('crawler.urls')),    # 크롤링 관리
] 