from celery import Celery

# Initialize Celery app
celery_app = Celery(
    'app.workers',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['app.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    broker_url='redis://redis:6379/0',
    result_backend='redis://redis:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)
