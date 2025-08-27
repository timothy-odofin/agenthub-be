from celery import shared_task

@shared_task
def example_task(x, y):
    """Example task that adds two numbers."""
    return x + y
