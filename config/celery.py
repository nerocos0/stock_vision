import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

app = Celery('stock_vision')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-candles-every-5-minutes': {
        'task': 'data.tasks.update_realtime_all_candles',
        'schedule': crontab(minute='*/5'),
    },
}