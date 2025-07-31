import os
from celery import Celery

# Django 설정을 Celery에 알려줍니다
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'issue_tracker.settings')

app = Celery('issue_tracker')

# Django 설정에서 Celery 설정을 가져옵니다
app.config_from_object('django.conf:settings', namespace='CELERY')

# 등록된 Django 앱에서 작업을 자동으로 로드합니다
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 