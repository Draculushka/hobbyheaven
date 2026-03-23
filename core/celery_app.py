from celery import Celery
from core.config import REDIS_URL

# Инициализируем Celery
# REDIS_URL берется из конфига (например, redis://:password@redis:6379/0)
celery_app = Celery(
    "hobbyhold_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["services.video_service"] # Где искать задачи (tasks)
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # Лимит 1 час на обработку тяжелого видео
)

if __name__ == "__main__":
    celery_app.start()
