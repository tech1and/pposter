# medik/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Устанавливаем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pposter.settings')

# Создаём экземпляр Celery
app = Celery('pposter')

# Загружаем конфигурацию из Django-настроек
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находить и загружать задачи из файлов tasks.py в приложениях
app.autodiscover_tasks()

# Опционально: тестовая задача
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')