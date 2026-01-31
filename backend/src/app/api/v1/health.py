from fastapi import APIRouter
from app.workers.tasks import example_task

router = APIRouter()


@router.get("/test-celery")
async def test_celery():
    """Test endpoint to verify Celery is working."""
    result = example_task.delay(4, 4)
    return {"task_id": result.id, "message": "Task sent to Celery"}
