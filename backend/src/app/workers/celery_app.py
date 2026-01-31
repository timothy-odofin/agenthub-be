from celery import Celery

# Initialize Celery app
celery_app = Celery(
    'app.workers',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['app.workers.tasks']
)

# Celery configuration
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
)
